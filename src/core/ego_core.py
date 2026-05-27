"""
7Sins Project - EGO-Core Decision Layer
Central decision engine that coordinates drive agents
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import os

from .drive_engine import DriveEngine, DriveOpinion, DriveType, DriveEngineRegistry
from src.memory.persistence import get_persistence_manager


class AuditLogger:
    """Structured audit logging for decision events"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def log_decision(self, decision: 'DecisionResult', state: 'EGOState'):
        """Log a decision result with full context"""
        log_entry = {
            "event": "decision_made",
            "timestamp": time.time(),
            "recommendation": decision.recommendation,
            "confidence": decision.confidence,
            "phase": decision.phase.value,
            "reasoning": decision.reasoning,
            "selected_drives": [(dt.value, w) for dt, w in decision.selected_drives],
            "active_drives": [dt.value for dt in state.active_drives],
            "opinions": {
                dt.value: {
                    "confidence": op.confidence,
                    "risk_level": op.risk_level,
                    "recommendation": op.recommendation
                }
                for dt, op in state.opinions.items()
            }
        }
        
        log_path = os.path.join(self.log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def log_approval_request(self, decision: 'DecisionResult', approved: bool, reason: str):
        """Log a human approval request result"""
        log_entry = {
            "event": "approval_request",
            "timestamp": time.time(),
            "decision_confidence": decision.confidence,
            "approved": approved,
            "reason": reason
        }
        
        log_path = os.path.join(self.log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


class DecisionPhase(Enum):
    PARSING = "parsing"
    CONSULTATION = "consultation"
    DEBATE = "debate"
    VOTING = "voting"
    EXECUTION = "execution"
    REFLECTION = "reflection"


@dataclass
class TaskInput:
    description: str
    task_type: str
    constraints: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5


@dataclass
class DecisionResult:
    recommendation: str
    selected_drives: List[Tuple[DriveType, float]]
    confidence: float
    phase: DecisionPhase
    reasoning: str


@dataclass 
class EGOState:
    current_task: Optional[TaskInput] = None
    phase: DecisionPhase = DecisionPhase.PARSING
    active_drives: List[DriveType] = field(default_factory=list)
    opinions: Dict[DriveType, DriveOpinion] = field(default_factory=dict)
    votes: Dict[DriveType, float] = field(default_factory=dict)
    decision: Optional[DecisionResult] = None
    last_decision_time: float = 0.0


class EGOCore:
    
    def __init__(self, registry: DriveEngineRegistry):
        self.registry = registry
        self.state = EGOState()
        self.max_debate_rounds = 3
        self.confidence_threshold = 0.6
        self.audit_logger = AuditLogger()
    
    def process_task(self, task: TaskInput) -> DecisionResult:
        self.state.current_task = task
        self.state.phase = DecisionPhase.PARSING
        self.registry.reset_all()
        
        self.state.phase = DecisionPhase.CONSULTATION
        relevant_drives = self.registry.get_by_task_type(task.task_type)
        self.state.active_drives = [d.drive_type for d in relevant_drives]
        
        for engine in relevant_drives:
            opinion = engine.evaluate(task, task.context)
            self.state.opinions[engine.drive_type] = opinion
        
        self.state.phase = DecisionPhase.DEBATE
        self._run_debate()
        
        self.state.phase = DecisionPhase.VOTING
        winner = self._resolve_votes()
        
        self.registry.record_decision_outcome(winner[0].drive)
        
        self.state.phase = DecisionPhase.EXECUTION
        result = DecisionResult(
            recommendation=winner[0].recommendation,
            selected_drives=[(d.drive_type, d.state.weight) for d in relevant_drives],
            confidence=winner[1],
            phase=self.state.phase,
            reasoning=f"Winner: {winner[0].drive.value}"
        )
        self.state.decision = result
        self.state.last_decision_time = time.time()
        
        self.audit_logger.log_decision(result, self.state)
        
        self._log_decision_to_persistence(result, task)
        
        return result
    
    def _run_debate(self):
        for round_num in range(self.max_debate_rounds):
            if self._check_consensus():
                break
    
    def _check_consensus(self) -> bool:
        if not self.state.opinions:
            return False
        high_confidence = [o for o in self.state.opinions.values() if o.confidence >= 0.8]
        return len(high_confidence) > len(self.state.opinions) / 2
    
    def _resolve_votes(self) -> Tuple[DriveOpinion, float]:
        drive_scores: Dict[DriveType, float] = {}
        task_type = self.state.current_task.task_type.lower() if self.state.current_task else ""
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        for drive_type, opinion in self.state.opinions.items():
            engine = self.registry.get(drive_type)
            if engine:
                score = opinion.confidence * engine.state.weight
                if is_creation:
                    score *= engine.state.eros_weight
                elif is_destruction:
                    score *= engine.state.thanatos_weight
                drive_scores[drive_type] = score
        
        winner_type = max(drive_scores, key=drive_scores.get)
        winner_opinion = self.state.opinions[winner_type]
        
        return winner_opinion, drive_scores[winner_type]
    
    def request_human_approval(self) -> bool:
        """
        Determine if human approval is required for the current decision.
        
        Returns:
            True if approved (auto-approved or human approves), False if requires human review
        """
        if not self.state.decision:
            self.audit_logger.log_approval_request(
                DecisionResult("", [], 0.0, DecisionPhase.VOTING, "No decision yet"),
                False,
                "No decision available"
            )
            return False
        
        decision = self.state.decision
        
        # Gate 1: High confidence auto-approves
        if decision.confidence >= 0.8:
            self.audit_logger.log_approval_request(
                decision, True, f"Auto-approved: confidence {decision.confidence} >= 0.8"
            )
            return True
        
        # Gate 2: Any high risk opinion requires human review
        for opinion in self.state.opinions.values():
            if opinion.risk_level == "high":
                self.audit_logger.log_approval_request(
                    decision, False, f"Human review required: {opinion.drive.value} has high risk"
                )
                return False
        
        # Gate 3: Creation tasks with low Eros weight require human review
        if self.state.current_task:
            task_type = self.state.current_task.task_type.lower()
            is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
            if is_creation:
                eros_engine = self.registry.get(DriveType.EROS)
                if eros_engine and eros_engine.state.eros_weight < 0.3:
                    self.audit_logger.log_approval_request(
                        decision, False, f"Human review required: Creation task with Eros weight {eros_engine.state.eros_weight} < 0.3"
                    )
                    return False
        
        # Default: approve
        self.audit_logger.log_approval_request(
            decision, True, "Approved: passes all safety gates"
        )
        return True
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        self.state.phase = DecisionPhase.REFLECTION
        if self.state.decision:
            winning_drive = self.state.decision.selected_drives[0][0]
            engine = self.registry.get(winning_drive)
            if engine:
                engine.on_task_complete(success, feedback)
    
    def _log_decision_to_persistence(self, decision: DecisionResult, task: TaskInput):
        """Log decision to SQLite persistence layer"""
        winning_drive = "unknown"
        eros_weight = 0.5
        thanatos_weight = 0.5
        
        if decision.selected_drives:
            winning_drive = decision.selected_drives[0][0].value
            engine = self.registry.get(decision.selected_drives[0][0])
            if engine:
                eros_weight = engine.state.eros_weight
                thanatos_weight = engine.state.thanatos_weight
        
        weight_snapshot = self.registry.get_weights()
        
        persistence = get_persistence_manager()
        persistence.log_decision(
            task_description=task.description,
            winning_drive=winning_drive,
            confidence=decision.confidence,
            eros_weight=eros_weight,
            thanatos_weight=thanatos_weight,
            weight_snapshot=weight_snapshot
        )