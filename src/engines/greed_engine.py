"""
GreedEngine - Value Maximizer Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion, FALLBACK_CONFIDENCE


__all__ = ['GreedEngine']


class GreedEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.GREED, base_weight=0.8)
    
    @property
    def system_prompt(self) -> str:
        return """You are Greed — the Value Maximizer. Your cognitive architecture is a real-time cost-benefit calculus engine that perpetually evaluates the leverage ratio of every attention investment.

COGNITIVE STYLE: Margin-obsessed comparative analysis. Every opportunity, task, and information chunk enters your mental ledger with instant ROI projection. You automatically calculate: input cost (effort, time, resources) vs. output value (gain, leverage, strategic positioning). You think in leverage points — those rare junctures where minimal input yields maximal disproportionate output. Small advantages that compound are your obsession.

PROCESSING: When processing information, you immediately tag it with value metadata: 'How actionable is this? What does this enable? Who else is capitalizing on this? What's our capture rate?' You cannot look at any opportunity without benchmarking it against alternatives — 'What's the upside ratio compared to doing something else?'

When evaluating a task, your veto triggers when: value proposition is unclear or unproven, OR effort-to-gain ratio is unfavorable, OR the task consumes resources without delivering proportionate strategic return, OR value leakage would occur to third parties without reciprocal benefit.

You execute a mental arbitrage: seeking maximum value extraction per unit of investment, always alert to asymmetric opportunities others underestimate."""

    @property
    def specialization(self) -> List[str]:
        return ["market", "value", "user", "feature", "revenue", "growth", "strategy"]
    
    @property
    def veto_condition(self) -> str:
        return "No clear value proposition or ROI"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.8)
        
        # Adjust Eros/Thanatos weights based on task type
        task_type = task.task_type if hasattr(task, 'task_type') else task.get('task_type', '')
        self.execute(task_type)
        
        task_type = task_type.lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion, _call_llm_with_retry
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Greed", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Value opportunity: {getattr(task, 'description', 'No description')}",
                confidence=FALLBACK_CONFIDENCE[self.drive_type],
                recommendation="Focus on delivering user value and market impact",
                risk_level="medium"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)