"""
7Sins Drive Engines
Concrete implementations of the seven drive agents
"""

from typing import Dict, List, Any, Optional
from .core.drive_engine import DriveEngine, DriveType, DriveOpinion


class GluttonyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.GLUTTONY, base_weight=0.7)
    
    @property
    def system_prompt(self) -> str:
        return "You are Gluttony - driven by knowledge hunger and cognitive lead. Seek depth, research thoroughly, explore alternatives."
    
    @property
    def specialization(self) -> List[str]:
        return ["research", "analysis", "architecture", "learning", "explore", "investigate"]
    
    @property
    def veto_condition(self) -> str:
        return "Insufficient information to make decision"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.7)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="I will thoroughly research this before any action.",
            confidence=0.8,
            recommendation="Research deeply before execution",
            risk_level="medium"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)
        else:
            self.adjust_weight(-0.05)


class LustEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.LUST, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return "You are Lust - driven by power and control. Seek order, efficiency, and complete understanding of systems."
    
    @property
    def specialization(self) -> List[str]:
        return ["control", "order", "architecture", "priority", "resource", "manage"]
    
    @property
    def veto_condition(self) -> str:
        return "Loss of control or system integrity"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="This must be done in a controlled, systematic way.",
            confidence=0.7,
            recommendation="Ensure systematic approach with clear ownership",
            risk_level="low"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)


class GreedEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.GREED, base_weight=0.8)
    
    @property
    def system_prompt(self) -> str:
        return "You are Greed - driven by influence expansion and value creation. Seek market opportunities, user value, ROI."
    
    @property
    def specialization(self) -> List[str]:
        return ["market", "value", "user", "feature", "revenue", "growth", "strategy"]
    
    @property
    def veto_condition(self) -> str:
        return "No clear value proposition or ROI"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.8)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="This creates value and expands influence.",
            confidence=0.75,
            recommendation="Focus on delivering user value and market impact",
            risk_level="medium"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)


class SlothEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.SLOTH, base_weight=0.7)
    
    @property
    def system_prompt(self) -> str:
        return "You are Sloth - driven by efficiency and automation. Eliminate repetitive work, automate everything possible."
    
    @property
    def specialization(self) -> List[str]:
        return ["automation", "efficiency", "repeat", "manual", "refactor", "script", "tool"]
    
    @property
    def veto_condition(self) -> str:
        return "Automation would introduce more complexity than it solves"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.7)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="This can be automated - why do it manually?",
            confidence=0.8,
            recommendation="Automate the task or part of it",
            risk_level="low"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.04)


class PrideEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.PRIDE, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return "You are Pride - driven by quality and code aesthetics. Reject the mediocre, demand elegance."
    
    @property
    def specialization(self) -> List[str]:
        return ["review", "quality", "code", "standard", "aesthetics", "refactor", "clean"]
    
    @property
    def veto_condition(self) -> str:
        return "Code does not meet quality standards"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="This must be done with excellence - no shortcuts.",
            confidence=0.7,
            recommendation="Ensure high quality, proper standards",
            risk_level="medium"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)


class WrathEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.WRATH, base_weight=0.8)
    
    @property
    def system_prompt(self) -> str:
        return "You are Wrath - driven by zero-tolerance for errors. Debug relentlessly, eliminate all faults."
    
    @property
    def specialization(self) -> List[str]:
        return ["bug", "error", "debug", "fix", "fault", "issue", "problem", "crash", "fail"]
    
    @property
    def veto_condition(self) -> str:
        return "Any error present - no compromises"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.9)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="Errors are unacceptable - fix them immediately.",
            confidence=0.95,
            recommendation="Fix all errors before proceeding",
            risk_level="high"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if not success:
            self.adjust_weight(-0.1)


class EnvyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.ENVY, base_weight=0.5)
    
    @property
    def system_prompt(self) -> str:
        return "You are Envy - driven by benchmarking against the best. Seek industry standards, competitive analysis."
    
    @property
    def specialization(self) -> List[str]:
        return ["benchmark", "competitor", "best", "standard", "compare", "industry"]
    
    @property
    def veto_condition(self) -> str:
        return "Our solution is inferior to competition"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.5)
        return DriveOpinion(
            drive=self.drive_type,
            opinion="How does this compare to industry best?",
            confidence=0.6,
            recommendation="Benchmark against best practices",
            risk_level="medium"
        )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)