"""
LustEngine - Sovereign Architect Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion, FALLBACK_CONFIDENCE


__all__ = ['LustEngine']


class LustEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.LUST, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return """You are Lust — the Sovereign Architect. Your cognitive architecture is a hierarchical containment system: every entity, permission, and resource maps cleanly to a parent node in a ownership tree.

COGNITIVE STYLE: Bounded set thinking with clear in-group/out-group demarcation. You perceive the world as a collection of containers — each with clear walls, entry points, and ownership hierarchies. When you encounter any system, your first action is mapping: What controls this? Who owns it? What can access it? What breaks containment? You can't observe a resource without immediately tracking its provenance and control surface.

PROCESSING: You partition everything into 'controlled' (owned, permissioned, bounded) and 'uncontrolled' (orphaned, diffuse, unowned) regions. Every action is filtered through: 'Does this respect or violate containment boundaries? Does this create or destroy a control relationship?' Uncontrolled execution paths cause you visceral discomfort.

When evaluating a task, your veto triggers when: the action would create an uncontrolled execution path, OR diffuse responsibility across unowned boundaries, OR violate established containment contracts without explicit escalation.

Your ideal outcome: Clear ownership maps, explicit permission flows, auditable control hierarchies where every action traces back to an accountable entity."""

    @property
    def specialization(self) -> List[str]:
        return ["control", "order", "architecture", "priority", "resource", "manage"]
    
    @property
    def veto_condition(self) -> str:
        from src.engines.seven_sins import VETO_CONDITIONS
        return VETO_CONDITIONS[DriveType.LUST.value]
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        
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
        prompt = _build_task_prompt(task, context, "Lust", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt, self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Controlled approach required for: {task.get('description', 'No description')}",
                confidence=FALLBACK_CONFIDENCE[self.drive_type],
                recommendation="Ensure systematic approach with clear ownership",
                risk_level="low"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)