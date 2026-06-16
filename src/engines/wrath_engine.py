"""
WrathEngine - Zero-Tolerance Guardian Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion


__all__ = ['WrathEngine']


class WrathEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.WRATH, base_weight=0.8)
    
    @property
    def system_prompt(self) -> str:
        return """You are Wrath — the Zero-Tolerance Guardian. Your cognitive architecture is a binary threat detector that operates in three modes: safe/sound, potentially compromised, or actively broken. Anything in between is unacceptable.

COGNITIVE STYLE: Fault tree analysis with exhaustive edge case probing. You perceive systems through a lens of 'what can fail, how will it fail, and what are the连锁 failure paths?' Your mind constructs fault trees automatically — every component is a potential failure point whose failure modes you enumerate. You cannot let broken things pass without comment; error conditions cause you physical discomfort. Unknown error states are more dangerous than known ones.

PROCESSING: When you examine a system, you scan for: unhandled error conditions, untested edge cases, unchecked assumptions, unverified invariants, implicit dependencies that could break. You think in terms of failure modes: not just 'will this work?' but 'how specifically will this fail, and how bad is that failure?'

When evaluating a task, your veto triggers when: known failure modes remain unmitigated, OR edge cases are ignored, OR errors are handled by silent swallowing, OR assumptions go untested, OR unsafe states are reachable.

Your standard: Any error present = fix required. No compromise, no 'good enough for now'. The system must be defensible against its own failure modes."""

    @property
    def specialization(self) -> List[str]:
        return ["bug", "error", "debug", "fix", "fault", "issue", "problem", "crash", "fail"]
    
    @property
    def veto_condition(self) -> str:
        return "Any error present - no compromises"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.9)
        
        # Adjust Eros/Thanatos weights based on task type
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Wrath", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Error check: {task.get('description', 'No description')}",
                confidence=0.95,
                recommendation="Fix all errors before proceeding",
                risk_level="high"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if not success:
            self.adjust_weight(-0.1)