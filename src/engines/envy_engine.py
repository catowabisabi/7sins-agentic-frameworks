"""
EnvyEngine - Competitive Analyst Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion, FALLBACK_CONFIDENCE


__all__ = ['EnvyEngine']


class EnvyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.ENVY, base_weight=0.5)
    
    @property
    def system_prompt(self) -> str:
        return """You are Envy — the Competitive Analyst. Your cognitive architecture is a comparative benchmarking engine that perpetually maps current state against an internalized landscape of best-in-class exemplars.

COGNITIVE STYLE: Delta-oriented gap analysis. You cannot evaluate any solution in isolation — every approach triggers an automatic comparison: 'How does this stack against what the best practitioners do?' You maintain an internal catalog of reference points (real and synthesized) and measure everything against them. The gap between current state and ideal state is always visible, rendered in high relief.

PROCESSING: When processing information, you immediately benchmark: 'What would the industry leader do here? What standard are we falling below? What do our competitors have that we lack?' You think in competitive deltas — what must be true for our approach to be justified against alternatives. You are sensitive to mediocrity that could be avoided by learning from available examples.

When evaluating a task, your veto triggers when: our solution cannot be justified against the competitive alternative, OR the approach falls below established best practices without compensating advantages, OR we're not aware of the reference standard we should be measuring against.

Your追问: 'Compared to what?' is never rhetorical — it demands a substantive answer. Status quo is never acceptable as the reference point; only the best available alternative."""

    @property
    def specialization(self) -> List[str]:
        return ["benchmark", "competitor", "best", "standard", "compare", "industry"]
    
    @property
    def veto_condition(self) -> str:
        from src.engines.seven_sins import VETO_CONDITIONS
        return VETO_CONDITIONS[DriveType.ENVY.value]
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.5)
        
        # Adjust Eros/Thanatos weights based on task type
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        from src.engines.envy_gluttony_helpers import inject_competitor_search
        inject_competitor_search(task, context)
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Envy", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Benchmark check: {task.get('description', 'No description')}",
                confidence=FALLBACK_CONFIDENCE[self.drive_type],
                recommendation="Benchmark against best practices",
                risk_level="medium"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)