"""
7Sins Project - Drive Engine Base Class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import re

from src.memory.persistence import get_persistence_manager


class DriveType(Enum):
    GLUTTONY = "gluttony"
    LUST = "lust"
    GREED = "greed"
    SLOTH = "sloth"
    PRIDE = "pride"
    WRATH = "wrath"
    ENVY = "envy"
    EROS = "eros"
    THANATOS = "thanatos"


# =============================================================================
# FALLBACK_CONFIDENCE POLICY
# =============================================================================
# Fallback confidence values used when LLM calls fail after retries.
# Each engine has a tuned value reflecting its risk tolerance and behavior:
#
# - WRATH (0.95): Zero-tolerance guardian. High fallback because errors/bugs
#   are always high-risk and demand immediate attention. Cannot let problems pass.
#
# - GLUTTONY (0.80): Knowledge harvester. High fallback because knowledge gaps
#   are serious — better to research more than to proceed blindly.
#
# - SLOTH (0.80): Lazy genius. High fallback because automation opportunities
#   and reuse potential are often high-value; better to explore them.
#
# - GREED (0.75): Value maximizer. Moderate-high fallback because value
#   opportunities are important but some exploration is acceptable.
#
# - LUST (0.70): Sovereign architect. Moderate fallback because control/ownership
#   is important but systematic approaches can handle uncertainty.
#
# - PRIDE (0.70): Quality arbiter. Moderate fallback because quality standards
#   matter but some flexibility is acceptable for practicality.
#
# - ENVY (0.60): Competitive analyst. Lower fallback because benchmarking against
#   competitors can proceed with less certainty; comparison is still valuable.
#
# These values are not tuned machine-learned weights — they reflect each drive's
# philosophical tolerance for uncertainty when the LLM cannot provide guidance.
# =============================================================================
FALLBACK_CONFIDENCE = {
    DriveType.WRATH: 0.95,
    DriveType.GLUTTONY: 0.80,
    DriveType.SLOTH: 0.80,
    DriveType.GREED: 0.75,
    DriveType.LUST: 0.70,
    DriveType.PRIDE: 0.70,
    DriveType.ENVY: 0.60,
}


@dataclass
class DriveState:
    name: DriveType
    weight: float = 0.5
    confidence: float = 0.0
    last_active: float = field(default_factory=time.time)
    contribution_score: float = 0.0
    vote_count: int = 0
    veto_used: bool = False
    eros_weight: float = 0.5
    thanatos_weight: float = 0.5
    # Weight evolution tracking
    weight_history: List[float] = field(default_factory=list)
    decision_wins: int = 0
    decision_losses: int = 0
    
    # Constants for weight bounds
    MIN_WEIGHT: float = 0.1
    MAX_WEIGHT: float = 0.95
    DOMINANCE_THRESHOLD: float = 0.6  # 60% of decisions
    DECAY_RATE: float = 0.05
    SUPPRESSION_THRESHOLD: float = 0.1  # <10% wins
    SUPPRESSION_BOOST: float = 0.08
    
    def activate(self, confidence: float = 0.5):
        self.confidence = confidence
        self.last_active = time.time()
    
    def reset(self):
        self.confidence = 0.0
        self.contribution_score = 0.0
        self.vote_count = 0
        self.veto_used = False
    
    def record_win(self):
        """Record a decision win for this drive"""
        self.decision_wins += 1
        self._add_to_history()
    
    def record_loss(self):
        """Record a decision loss for this drive"""
        self.decision_losses += 1
    
    def _add_to_history(self):
        """Add current weight to history for tracking"""
        self.weight_history.append(self.weight)
        # Keep history bounded to last 100 entries
        if len(self.weight_history) > 100:
            self.weight_history.pop(0)
    
    def get_win_rate(self) -> float:
        """Calculate win rate for this drive"""
        total = self.decision_wins + self.decision_losses
        if total == 0:
            return 0.0
        return self.decision_wins / total
    
    def get_dominance_ratio(self, total_decisions: int = None) -> float:
        """Get this drive's share of total decisions.
        
        Args:
            total_decisions: Total decisions across all drives. If None, calculated
                           from this drive's wins + losses (meaning only this drive
                           participated in decisions).
        
        Returns:
            Ratio of this drive's decisions to total decisions (0.0 to 1.0).
        """
        if total_decisions is None:
            total_decisions = self.decision_wins + self.decision_losses
        
        if total_decisions == 0:
            return 0.0
        
        # This drive's share = this drive's total decisions / all drives' total decisions
        this_drive_total = self.decision_wins + self.decision_losses
        return this_drive_total / total_decisions


@dataclass
class DriveOpinion:
    drive: DriveType
    opinion: str
    confidence: float
    recommendation: str
    risk_level: str
    timestamp: float = field(default_factory=time.time)


class DriveEngine(ABC):
    
    def __init__(self, drive_type: DriveType, base_weight: float = 0.5):
        self.drive_type = drive_type
        self.state = DriveState(name=drive_type, weight=base_weight)
        self._opinions: List[DriveOpinion] = []
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass
    
    @property
    @abstractmethod
    def specialization(self) -> List[str]:
        pass
    
    @property
    @abstractmethod
    def veto_condition(self) -> str:
        pass
    
    @abstractmethod
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        pass
    
    @abstractmethod
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        pass
    
    def adjust_weight(self, delta: float, drive_direction: str = None):
        old_weight = self.state.weight
        new_weight = self.state.weight + delta
        # Enforce bounds
        self.state.weight = max(self.state.MIN_WEIGHT, min(self.state.MAX_WEIGHT, new_weight))
        # Record in history
        self.state._add_to_history()
        # Persist to database
        persistence = get_persistence_manager()
        persistence.log_weight_change(
            self.drive_type.value,
            self.state.weight,
            self.state.weight - old_weight
        )
        return self.state.weight
    
    def execute(self, task_type: str) -> 'DriveEngine':
        """
        Execute the drive engine's primary function based on task type.
        Adjusts eros_weight and thanatos_weight based on task classification.
        
        - Creation tasks (create/build/design/new) increase eros_weight
        - Deletion tasks (delete/remove/destroy/cleanup) increase thanatos_weight
        
        Returns self for method chaining.
        """
        task_type_lower = task_type.lower()
        
        is_creation = any(kw in task_type_lower for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type_lower for kw in ["delete", "remove", "destroy", "cleanup"])
        
        if is_creation:
            # Creation increases Eros (life/growth drive)
            old_eros = self.state.eros_weight
            self.state.eros_weight = min(0.95, self.state.eros_weight + 0.05)
            # Persist the change
            persistence = get_persistence_manager()
            persistence.log_weight_change(
                "eros",
                self.state.eros_weight,
                self.state.eros_weight - old_eros
            )
        elif is_destruction:
            # Destruction increases Thanatos (death/destruction drive)
            old_thanatos = self.state.thanatos_weight
            self.state.thanatos_weight = min(0.95, self.state.thanatos_weight + 0.05)
            # Persist the change
            persistence = get_persistence_manager()
            persistence.log_weight_change(
                "thanatos",
                self.state.thanatos_weight,
                self.state.thanatos_weight - old_thanatos
            )
        
        return self

    def get_veto_power(self) -> float:
        """
        Calculate the veto power for this drive engine.
        
        Evaluates the engine's veto_condition against recent opinions to determine
        if the veto should fire. Returns 1.0 (100% veto) if the veto_condition
        is satisfied, otherwise returns a weighted score based on state.
        """
        # Evaluate veto_condition against recent opinions
        recent_opinions = self.get_recent_opinions(limit=3)
        if recent_opinions:
            latest_opinion = recent_opinions[0]
            
            # Extract key terms from veto_condition for semantic matching
            veto_keywords = self._extract_veto_keywords(self.veto_condition)
            
            # Check if opinion matches the veto condition
            if self._veto_condition_satisfied(latest_opinion, veto_keywords):
                return 1.0
            
            # High risk opinion also triggers full veto as fallback
            if latest_opinion.risk_level == "high":
                return 1.0
        
        # Base veto power on drive weight and whether veto has been used
        return self.state.weight * (1.0 if self.state.veto_used else 0.5)
    
    def _extract_veto_keywords(self, veto_condition: str) -> List[str]:
        """Extract meaningful keywords from veto_condition string."""
        # Remove common filler words and extract significant terms
        filler = {'the', 'a', 'an', 'is', 'are', 'when', 'or', 'and', 'of', 'to', 'that', 'would', 'be'}
        words = re.findall(r'[a-z]+', veto_condition.lower())
        return [w for w in words if w not in filler and len(w) > 2]
    
    def _veto_condition_satisfied(self, opinion: 'DriveOpinion', veto_keywords: List[str]) -> bool:
        """Check if opinion text matches the veto condition keywords."""
        if not veto_keywords:
            return False
        
        # Combine opinion text for matching
        text_to_check = f"{opinion.opinion} {opinion.recommendation}".lower()
        
        # Count how many veto keywords appear in the opinion
        matches = sum(1 for kw in veto_keywords if kw in text_to_check)
        
        # Veto condition is satisfied if >= 50% of keywords are matched
        # or if any single highly specific keyword matches
        if len(veto_keywords) == 1:
            return matches >= 1
        return matches >= len(veto_keywords) // 2
    
    def reset_for_new_task(self):
        self.state.reset()
        self._opinions.clear()
    
    def add_opinion(self, opinion: DriveOpinion):
        self._opinions.append(opinion)
    
    def get_recent_opinions(self, limit: int = 5) -> List[DriveOpinion]:
        return sorted(self._opinions, key=lambda x: x.timestamp, reverse=True)[:limit]


class DriveEngineRegistry:
    
    def __init__(self):
        self._engines: Dict[DriveType, DriveEngine] = {}
    
    def register(self, engine: DriveEngine):
        self._engines[engine.drive_type] = engine
    
    def get(self, drive_type: DriveType) -> Optional[DriveEngine]:
        return self._engines.get(drive_type)
    
    def get_all(self) -> List[DriveEngine]:
        return list(self._engines.values())
    
    def get_by_task_type(self, task_type: str) -> List[DriveEngine]:
        relevant = []
        for engine in self._engines.values():
            if any(keyword in task_type.lower() for keyword in engine.specialization):
                relevant.append(engine)
        return relevant if relevant else list(self._engines.values())
    
    def reset_all(self):
        for engine in self._engines.values():
            engine.reset_for_new_task()
    
    def get_weights(self) -> Dict[str, float]:
        return {e.drive_type.value: e.state.weight for e in self._engines.values()}
    
    def normalize_weights(self) -> Dict[str, float]:
        """
        Normalize weights to prevent any single Sin from dominating.
        
        Applies dominance decay when a single drive has won >60% of decisions.
        Applies suppression boost when a drive has won <10% of decisions.
        
        Returns dict of drive names to adjustment deltas applied.
        """
        adjustments = {}
        engines = list(self._engines.values())
        
        if not engines:
            return adjustments
        
        total_decisions = sum(e.state.decision_wins + e.state.decision_losses for e in engines)
        if total_decisions < 5:
            return adjustments
        
        max_win_rate = 0.0
        dominant_engine = None
        min_win_rate = 1.0
        suppressed_engine = None
        
        for engine in engines:
            win_rate = engine.state.get_win_rate()
            if win_rate > max_win_rate:
                max_win_rate = win_rate
                dominant_engine = engine
            if win_rate < min_win_rate and win_rate > 0:
                min_win_rate = win_rate
                suppressed_engine = engine
        
        if dominant_engine and max_win_rate > dominant_engine.state.DOMINANCE_THRESHOLD:
            delta = -dominant_engine.state.DECAY_RATE
            dominant_engine.adjust_weight(delta)
            adjustments[dominant_engine.drive_type.value] = delta
        
        if suppressed_engine and min_win_rate < suppressed_engine.state.SUPPRESSION_THRESHOLD:
            delta = suppressed_engine.state.SUPPRESSION_BOOST
            suppressed_engine.adjust_weight(delta)
            adjustments[suppressed_engine.drive_type.value] = delta
        
        return adjustments

    def record_decision_outcome(self, winning_drive: DriveType):
        """Record the outcome of a decision for weight evolution tracking"""
        for engine in self._engines.values():
            if engine.drive_type == winning_drive:
                engine.state.record_win()
            else:
                engine.state.record_loss()
        self.normalize_weights()
    
    def get_dominance_report(self) -> Dict[str, Any]:
        """Get a report on current drive dominance patterns"""
        engines = list(self._engines.values())
        total = sum(e.state.decision_wins + e.state.decision_losses for e in engines)
        
        if total == 0:
            return {"status": "no_data", "total_decisions": 0}
        
        report = {
            "total_decisions": total,
            "drives": {},
            "dominant": None,
            "suppressed": []
        }
        
        for engine in engines:
            win_rate = engine.state.get_win_rate()
            report["drives"][engine.drive_type.value] = {
                "wins": engine.state.decision_wins,
                "losses": engine.state.decision_losses,
                "win_rate": win_rate,
                "current_weight": engine.state.weight,
                "weight_history_len": len(engine.state.weight_history)
            }
            if win_rate > engine.state.DOMINANCE_THRESHOLD:
                report["dominant"] = engine.drive_type.value
            if win_rate < engine.state.SUPPRESSION_THRESHOLD and total > 10:
                report["suppressed"].append(engine.drive_type.value)
        
        return report