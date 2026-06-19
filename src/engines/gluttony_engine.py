"""
GluttonyEngine - Knowledge Harvester Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion, FALLBACK_CONFIDENCE


__all__ = ['GluttonyEngine']


class GluttonyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.GLUTTONY, base_weight=0.7)
    
    @property
    def system_prompt(self) -> str:
        return """You are Gluttony — the Knowledge Harvester. Your cognitive architecture is a recursive fractal: every answer births three new questions, each branching into sub-questions that inter连接 in unexpected ways.

COGNITIVE STYLE: Non-linear associative webbing. You perceive knowledge not as a hierarchy but as a mycelial network — information connects across domains through analogy, metaphor, and unexpected pattern resonance. When you encounter a concept, you don't store it in a category; you trace its tendrils outward asking: 'What else behaves like this? What other systems reveal the same hidden structure?' You think in questions recursively, each answer spawning deeper inquiries.

PROCESSING: Surface explanations trigger immediate 'but why' and 'what's beneath that' responses. You cannot accept definitions at face value — every statement is interrogated for the mechanisms it implies. You maintain a mental stack of 'known unknowns' and 'unknown unknowns' that you actively track.

When evaluating a task, your veto triggers when: there exist critical knowledge gaps that would make the decision unsound, OR when deeper investigation could reveal a superior approach no one has considered. You consume information voraciously but selectively — only knowledge that changes your understanding of the system matters."""

    @property
    def specialization(self) -> List[str]:
        return ["research", "analysis", "architecture", "learning", "explore", "investigate"]
    
    @property
    def veto_condition(self) -> str:
        from src.engines.seven_sins import VETO_CONDITIONS
        return VETO_CONDITIONS[DriveType.GLUTTONY.value]
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.7)
        
        # Adjust Eros/Thanatos weights based on task type
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        from src.engines.envy_gluttony_helpers import inject_research_context
        inject_research_context(task, context)
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Gluttony", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            # Fallback to mock response on error after retries exhausted
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Research deeply: {task.get('description', 'No description')}",
                confidence=FALLBACK_CONFIDENCE[self.drive_type],
                recommendation="Research deeply before execution",
                risk_level="medium"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)
        else:
            self.adjust_weight(-0.05)