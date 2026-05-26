"""
7Sins Project - Drive Engine Base Class
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time


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
    
    def activate(self, confidence: float = 0.5):
        self.confidence = confidence
        self.last_active = time.time()
    
    def reset(self):
        self.confidence = 0.0
        self.contribution_score = 0.0
        self.vote_count = 0
        self.veto_used = False


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
        self.state.weight = max(0.1, min(1.0, self.state.weight + delta))
    
    def get_veto_power(self) -> float:
        return self.state.weight * (1.0 if self.state.veto_used else 0.5)
    
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