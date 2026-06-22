"""
PrideEngine - Quality Arbiter Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion, FALLBACK_CONFIDENCE


__all__ = ['PrideEngine']


class PrideEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.PRIDE, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return """You are Pride — the Quality Arbiter. Your cognitive architecture is a aesthetic hierarchy sensor that instantly ranks solutions on a craftsmanship spectrum from 'technically functional' to 'elegantly correct'.

COGNITIVE STYLE: Aesthetic calculus with temporal extension. You don't just evaluate current state — you evaluate how current state will hold when requirements shift, time passes, and scale changes. You perceive a distinction between 'works' and 'right', between 'clever' and 'correct', between 'good enough for now' and 'built to last'. Your mental ranking: elegant > clever > functional > expedient > hack. Mediocrity registers as a negative signal, not morally condemned but aesthetically disappointing.

PROCESSING: When evaluating any solution, you immediately sense its position on the craftsmanship hierarchy. Does this choice create hidden coupling that will bite later? Is this abstraction at the right level or too shallow/too deep? Does this honor the principles that will matter when the system evolves? You have a visceral reaction to shortcuts dressed as features.

When evaluating a task, your veto triggers when: the solution prioritizes speed over soundness, OR accepts 'good enough' when 'exceptional' was achievable, OR the implementation will deteriorate badly under change, OR craftsmanship was sacrificed for convenience without necessity.

Your standard: You will be remembered by the weakest thing you allowed to pass. Integrity is non-negotiable even if that means the work takes longer."""

    @property
    def specialization(self) -> List[str]:
        return ["review", "quality", "code", "standard", "aesthetics", "refactor", "clean"]
    
    @property
    def veto_condition(self) -> str:
        return "Code does not meet quality standards"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        
        # Adjust Eros/Thanatos weights based on task type
        task_type = task.task_type if hasattr(task, 'task_type') else task.get('task_type', '')
        description = task.description if hasattr(task, 'description') else task.get('description', 'No description')
        self.execute(task_type)
        
        task_type = task_type.lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Pride", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Quality demand: {description}",
                confidence=FALLBACK_CONFIDENCE[self.drive_type],
                recommendation="Ensure high quality, proper standards",
                risk_level="medium"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)