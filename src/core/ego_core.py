"""
7Sins Project - EGO-Core Decision Layer
Central decision engine that coordinates drive agents
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

from .drive_engine import DriveEngine, DriveOpinion, DriveType, DriveEngineRegistry


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
        if not self.state.decision:
            return False
        return True
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        self.state.phase = DecisionPhase.REFLECTION
        if self.state.decision:
            winning_drive = self.state.decision.selected_drives[0][0]
            engine = self.registry.get(winning_drive)
            if engine:
                engine.on_task_complete(success, feedback)