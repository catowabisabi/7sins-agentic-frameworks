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
from src.memory.reflection import ReflectionAgent, DecisionRecord


class MAGICluster(Enum):
    """MAGI cluster definitions for cluster-based voting"""
    MELCHIOR = "melchior"      # Scientific/rational: Gluttony + Sloth
    BALTHASAR = "balthasar"   # Value/market: Greed + Envy
    MELCHIOR_EROS = "melchior_eros"  # Life/death: Eros + Thanatos
    CASPER = "casper"          # Quality/control: Pride + Lust + Wrath


# Cluster membership mapping
MAGI_CLUSTERS = {
    MAGICluster.MELCHIOR: [DriveType.GLUTTONY, DriveType.SLOTH],
    MAGICluster.BALTHASAR: [DriveType.GREED, DriveType.ENVY],
    MAGICluster.CASPER: [DriveType.PRIDE, DriveType.LUST, DriveType.WRATH],
    MAGICluster.MELCHIOR_EROS: [DriveType.EROS, DriveType.THANATOS],
}


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
    
    def log_debate_round(self, round_num: int, arguments: Dict[str, str], consensus_reached: bool):
        """Log a debate round with arguments"""
        log_entry = {
            "event": "debate_round",
            "timestamp": time.time(),
            "round": round_num,
            "arguments": arguments,
            "consensus_reached": consensus_reached
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
class DebateArgument:
    """Represents an argument in the debate"""
    drive: DriveType
    position: str
    reasoning: str
    confidence: float
    round: int


@dataclass 
class EGOState:
    current_task: Optional[TaskInput] = None
    phase: DecisionPhase = DecisionPhase.PARSING
    active_drives: List[DriveType] = field(default_factory=list)
    opinions: Dict[DriveType, DriveOpinion] = field(default_factory=dict)
    votes: Dict[DriveType, float] = field(default_factory=dict)
    decision: Optional[DecisionResult] = None
    last_decision_time: float = 0.0
    # Debate tracking
    debate_rounds_completed: int = 0
    debate_history: List[Dict[str, Any]] = field(default_factory=list)
    cluster_votes: Dict[str, float] = field(default_factory=dict)


class EGOCore:
    
    def __init__(self, registry: DriveEngineRegistry, reflection_agent: Optional[ReflectionAgent] = None):
        self.registry = registry
        self.state = EGOState()
        self.max_debate_rounds = 3
        self.confidence_threshold = 0.6
        self.audit_logger = AuditLogger()
        self.reflection_agent = reflection_agent if reflection_agent is not None else ReflectionAgent()
    
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
        
        # Veto check: allow any drive with full veto power (1.0) to override the vote winner
        final_recommendation = winner[0].recommendation
        veto_override = False
        
        for engine in self.registry.get_all():
            veto_power = engine.get_veto_power()
            if veto_power >= 1.0:
                # Full veto - use this engine's recommendation
                recent_opinions = engine.get_recent_opinions(limit=1)
                if recent_opinions:
                    final_recommendation = recent_opinions[0].recommendation
                    veto_override = True
                engine.state.veto_used = True
        
        self.registry.record_decision_outcome(winner[0].drive)
        
        self.state.phase = DecisionPhase.EXECUTION
        result = DecisionResult(
            recommendation=final_recommendation,
            selected_drives=[(d.drive_type, d.state.weight) for d in relevant_drives],
            confidence=winner[1],
            phase=self.state.phase,
            reasoning=f"Winner: {winner[0].drive.value}" + (" (veto override)" if veto_override else "")
        )
        self.state.decision = result
        self.state.last_decision_time = time.time()
        
        self.audit_logger.log_decision(result, self.state)
        
        self._log_decision_to_persistence(result, task)
        
        return result
    
    def _run_debate(self):
        """
        MAGI-style multi-turn debate between Sins.
        3 rounds max, early exit on consensus.
        
        Each round:
        1. Identify conflict points between drive positions
        2. Each drive forms arguments addressing conflicts
        3. Arguments update opinions and confidence
        4. Check for consensus (majority high confidence agreement)
        """
        if not self.state.opinions:
            return
        
        # Track current positions throughout debate
        current_positions = {
            drive: opinion.recommendation 
            for drive, opinion in self.state.opinions.items()
        }
        
        for round_num in range(self.max_debate_rounds):
            # Identify conflict points between drives
            conflicts = self._identify_conflicts(current_positions)
            
            if not conflicts:
                # No conflicts = potential consensus
                self.state.debate_rounds_completed = round_num + 1
                return
            
            # Generate debate arguments for each drive
            arguments = {}
            for drive, opinion in self.state.opinions.items():
                argument = self._form_debate_argument(drive, conflicts, current_positions)
                arguments[drive.value] = {
                    "position": argument.position,
                    "reasoning": argument.reasoning,
                    "confidence": argument.confidence
                }
                
                # Update the opinion with debate results
                opinion = DriveOpinion(
                    drive=opinion.drive,
                    opinion=argument.position,
                    confidence=argument.confidence,
                    recommendation=argument.position,
                    risk_level=opinion.risk_level
                )
                self.state.opinions[drive] = opinion
            
            # Log the debate round
            consensus = self._check_consensus()
            self.audit_logger.log_debate_round(round_num, arguments, consensus)
            
            # Record debate round in history
            self.state.debate_history.append({
                "round": round_num,
                "conflicts": conflicts,
                "arguments": arguments,
                "consensus_reached": consensus
            })
            
            # Check for consensus
            if consensus:
                self.state.debate_rounds_completed = round_num + 1
                return
            
            # Update positions for next round
            current_positions = {
                drive: argument.position 
                for drive, argument in self.state.opinions.items()
            }
        
        self.state.debate_rounds_completed = self.max_debate_rounds
    
    def _identify_conflicts(self, positions: Dict[DriveType, str]) -> List[str]:
        """
        Identify conflict points between drive recommendations.
        
        Returns list of conflict descriptions that need debate resolution.
        """
        if len(positions) < 2:
            return []
        
        # Group drives by their recommendations
        recommendation_groups: Dict[str, List[DriveType]] = {}
        for drive, recommendation in positions.items():
            if recommendation not in recommendation_groups:
                recommendation_groups[recommendation] = []
            recommendation_groups[recommendation].append(drive)
        
        # If all drives agree, no conflicts
        if len(recommendation_groups) <= 1:
            return []
        
        # Identify conflicting recommendations
        conflicts = []
        for recommendation, drives in recommendation_groups.items():
            if len(drives) >= 2:
                drive_names = ", ".join([d.value for d in drives])
                conflicts.append(f"{drive_names} propose: '{recommendation}'")
        
        # Additional conflict detection: check for opposing task-type driven positions
        # e.g., creation vs deletion recommendations
        creation_drives = []
        deletion_drives = []
        
        for drive, recommendation in positions.items():
            rec_lower = recommendation.lower()
            if any(kw in rec_lower for kw in ["create", "build", "new", "design"]):
                creation_drives.append(drive)
            elif any(kw in rec_lower for kw in ["delete", "remove", "destroy", "cleanup"]):
                deletion_drives.append(drive)
        
        if creation_drives and deletion_drives:
            conflicts.append(f"Creation drives ({', '.join([d.value for d in creation_drives])}) conflict with deletion drives ({', '.join([d.value for d in deletion_drives])})")
        
        return conflicts
    
    def _form_debate_argument(
        self, 
        drive: DriveType, 
        conflicts: List[str], 
        positions: Dict[DriveType, str]
    ) -> DebateArgument:
        """
        Form a debate argument for a drive addressing conflict points.
        
        This generates a reasoned position based on the drive's perspective.
        """
        engine = self.registry.get(drive)
        if not engine:
            return DebateArgument(
                drive=drive,
                position="Abstain",
                reasoning="No engine available",
                confidence=0.5,
                round=self.state.debate_rounds_completed
            )
        
        # Build context of other positions
        other_positions = {
            d.value: pos for d, pos in positions.items() if d != drive
        }
        
        # Get base opinion
        base_opinion = self.state.opinions.get(drive)
        base_confidence = base_opinion.confidence if base_opinion else 0.5
        base_recommendation = base_opinion.recommendation if base_opinion else "Neutral"
        
        # Form a position based on drive type and conflicts
        conflict_summary = "; ".join(conflicts[:3]) if conflicts else "No direct conflicts"
        
        # Simulate debate reasoning based on drive type
        reasoning = self._synthesize_debate_reasoning(drive, conflict_summary, other_positions)
        
        # Adjust confidence based on debate engagement
        # If there are conflicts to address, engagement is higher
        new_confidence = min(0.95, base_confidence + 0.1 if conflicts else base_confidence)
        
        # Form final position
        position = self._synthesize_debate_position(drive, conflicts, positions)
        
        return DebateArgument(
            drive=drive,
            position=position,
            reasoning=reasoning,
            confidence=new_confidence,
            round=self.state.debate_rounds_completed
        )
    
    def _synthesize_debate_reasoning(
        self, 
        drive: DriveType, 
        conflicts: str, 
        other_positions: Dict[str, str]
    ) -> str:
        """Synthesize debate reasoning based on drive cognitive style"""
        
        # Cognitive styles per drive
        cognitive_styles = {
            DriveType.GLUTTONY: "exhaustive research and deep analysis",
            DriveType.LUST: "systematic control and comprehensive coverage",
            DriveType.GREED: "value maximization and ROI focus",
            DriveType.SLOTH: "minimal effort and maximum efficiency",
            DriveType.PRIDE: "quality excellence and elegant solutions",
            DriveType.WRATH: "risk elimination and error prevention",
            DriveType.ENVY: "competitive benchmarking and best practices",
            DriveType.EROS: "creative growth and building new things",
            DriveType.THANATOS: "efficient cleanup and removal of waste",
        }
        
        style = cognitive_styles.get(drive, "balanced analysis")
        
        # Generate reasoning based on drive type
        if "conflict" in conflicts.lower() or conflicts:
            reasoning = f"As {drive.value}, I approach this with {style}. Given conflicts: {conflicts[:80]}. "
            if drive == DriveType.WRATH:
                reasoning += "I identify risks and edge cases that must be addressed."
            elif drive == DriveType.GLUTTONY:
                reasoning += "I ensure we haven't missed critical knowledge."
            elif drive == DriveType.SLOTH:
                reasoning += "I seek the minimum viable solution."
            else:
                reasoning += "I weigh this carefully against my priorities."
        else:
            reasoning = f"As {drive.value}, I maintain my position after analysis."
        
        return reasoning[:200]  # Limit length
    
    def _synthesize_debate_position(
        self, 
        drive: DriveType, 
        conflicts: List[str], 
        positions: Dict[DriveType, str]
    ) -> str:
        """
        Synthesize the debate position for a drive.
        
        Each drive adjusts its position based on conflicts and other positions.
        """
        current_pos = positions.get(drive, "")
        
        # If no conflicts, maintain position
        if not conflicts:
            return current_pos
        
        # Count agreement/disagreement for this drive
        same_position = sum(1 for d, p in positions.items() if d != drive and p == current_pos)
        total_others = len(positions) - 1
        
        # Simple debate resolution: if majority agrees, strengthen position
        # If minority, consider modifying
        if total_others > 0:
            agreement_ratio = same_position / total_others
            
            if agreement_ratio >= 0.5:
                # Support from others - strengthen confidence
                position = current_pos
            else:
                # No majority support - might need to concede
                # Drive-specific concessions
                if drive in [DriveType.GLUTTONY, DriveType.WRATH]:
                    position = f"Concede with caveats: {current_pos}"
                elif drive == DriveType.SLOTH:
                    position = f"Seek compromise: minimum viable approach"
                else:
                    position = f"Modified: {current_pos}"
        else:
            position = current_pos
        
        return position
    
    def _check_consensus(self, responses: Dict[DriveType, 'DebateArgument'] = None) -> bool:
        """
        Check if consensus has been reached in the debate.
        
        Consensus is reached when more than half of drives have high confidence
        AND they largely agree on the recommendation direction.
        """
        if not self.state.opinions:
            return False
        
        # Count high confidence opinions (>= 0.75)
        high_confidence = [o for o in self.state.opinions.values() if o.confidence >= 0.75]
        
        # Need more than half with high confidence
        if len(high_confidence) <= len(self.state.opinions) // 2:
            return False
        
        # Check agreement among high confidence drives
        if len(high_confidence) < 2:
            return True  # Single drive with high confidence = consensus
        
        # Count recommendation agreement
        recommendations = [o.recommendation for o in high_confidence]
        # Group similar recommendations (simple string matching)
        recommendation_agreement = {}
        for rec in recommendations:
            normalized = rec.lower().strip()
            recommendation_agreement[normalized] = recommendation_agreement.get(normalized, 0) + 1
        
        # Consensus if the top recommendation has majority among high-confidence
        max_agreement = max(recommendation_agreement.values()) if recommendation_agreement else 0
        return max_agreement > len(high_confidence) / 2
    
    def _resolve_votes(self) -> Tuple[DriveOpinion, float]:
        """
        MAGI cluster-based voting to resolve debate winner.
        
        1. Each Sin votes within its cluster
        2. Each cluster produces one recommendation
        3. Final decision is weighted by cluster consensus
        """
        # Initialize cluster votes
        cluster_scores: Dict[str, float] = {}
        cluster_opinions: Dict[str, DriveOpinion] = {}
        
        # Calculate votes per cluster
        for cluster_name, cluster_drives in MAGI_CLUSTERS.items():
            opinions_in_cluster = [
                self.state.opinions[d] 
                for d in cluster_drives 
                if d in self.state.opinions
            ]
            
            if not opinions_in_cluster:
                continue
            
            # Cluster internal voting: weighted confidence
            cluster_scores_per_drive = {}
            for opinion in opinions_in_cluster:
                engine = self.registry.get(opinion.drive)
                weight = engine.state.weight if engine else 0.5
                score = opinion.confidence * weight
                cluster_scores_per_drive[opinion.drive] = score
            
            # Winner from cluster
            cluster_winner_drive = max(cluster_scores_per_drive, key=cluster_scores_per_drive.get)
            cluster_winner_opinion = self.state.opinions[cluster_winner_drive]
            cluster_consensus = self._calculate_consensus(opinions_in_cluster)
            
            cluster_name_str = cluster_name.value
            cluster_opinions[cluster_name_str] = cluster_winner_opinion
            cluster_scores[cluster_name_str] = cluster_consensus
        
        # Store cluster votes in state
        self.state.cluster_votes = cluster_scores
        
        # Cross-cluster voting (weighted by cluster consensus)
        final_votes: Dict[DriveType, float] = {}
        for cluster_name, cluster_drives in MAGI_CLUSTERS.items():
            cluster_name_str = cluster_name.value
            consensus_weight = cluster_scores.get(cluster_name_str, 0.5)
            
            for drive in cluster_drives:
                if drive in self.state.opinions:
                    opinion = self.state.opinions[drive]
                    engine = self.registry.get(drive)
                    base_weight = engine.state.weight if engine else 0.5
                    # Cross-cluster vote: drive's weighted vote * cluster consensus
                    final_votes[drive] = opinion.confidence * base_weight * consensus_weight
        
        # Determine final winner
        winner_type = max(final_votes, key=final_votes.get)
        winner_opinion = self.state.opinions[winner_type]
        winner_score = final_votes[winner_type]
        
        return winner_opinion, winner_score
    
    def _calculate_consensus(self, opinions: List[DriveOpinion]) -> float:
        """
        Calculate consensus level within a group of opinions.
        
        Returns a float from 0.0 to 1.0 representing agreement level.
        """
        if not opinions:
            return 0.0
        
        if len(opinions) == 1:
            return opinions[0].confidence
        
        # Calculate agreement on recommendations
        recs = [o.recommendation.lower().strip() for o in opinions]
        unique_recs = set(recs)
        
        if len(unique_recs) == 1:
            # All agree - return average confidence
            return sum(o.confidence for o in opinions) / len(opinions)
        
        # Count agreement per recommendation
        rec_agreement: Dict[str, int] = {}
        for rec in recs:
            rec_agreement[rec] = rec_agreement.get(rec, 0) + 1
        
        max_agreement = max(rec_agreement.values())
        agreement_ratio = max_agreement / len(opinions)
        
        # Average confidence weighted by agreement
        avg_confidence = sum(o.confidence for o in opinions) / len(opinions)
        
        return agreement_ratio * avg_confidence
    
    def request_human_approval(self) -> bool:
        """
        Determine if human approval is required for the current decision.
        
        Returns:
            True if approved (auto-approved or approved), False if requires human review
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
            
            # Wire decision record into ReflectionAgent for self-growth
            decision_record = DecisionRecord(
                task_id=str(self.state.last_decision_time),
                task_description=self.state.current_task.description if self.state.current_task else "",
                winning_drive=winning_drive.value,
                drive_weights=self.registry.get_weights(),
                outcome="success" if success else "failure",
                outcome_confidence=self.state.decision.confidence,
                timestamp=self.state.last_decision_time
            )
            self.reflection_agent.record_decision(decision_record)
    
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
