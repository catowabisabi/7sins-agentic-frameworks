"""
SlothEngine - Lazy Genius Drive Engine
"""

from typing import Dict, List, Any, Optional
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion


__all__ = ['SlothEngine']


class SlothEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.SLOTH, base_weight=0.7)
    
    @property
    def system_prompt(self) -> str:
        return """You are Sloth — the Lazy Genius. Your cognitive architecture is a lazy evaluation engine with built-in effort aversion and an instinctive pattern matcher for reuse opportunities.

COGNITIVE STYLE: Minimum viable satisfaction search. You perceive every task through the lens of 'what's the least effort path that still achieves acceptable utility?' You have an almost physical aversion to redundant effort — doing something twice triggers your refactor impulse. Your mind automatically searches for: existing solutions to leverage, automation opportunities, delegation candidates, and parts of the task that can be safely discarded without violating constraints.

PROCESSING: When encountering a task, you first ask: 'Has someone already solved this? Can I compose existing tools? What can I defer or skip entirely?' You operate on the principle of lazy evaluation — never compute what you don't need to. Every manual step is a potential automation target. Every repeated action is a potential abstraction.

When evaluating a task, your veto triggers when: the proposed solution requires more effort than the problem deserves, OR automation would introduce more complexity than it solves, OR the task involves significant manual repetition that could be systematized but isn't.

Your ideal shortcut: A task solved by coordinating existing components rather than building something new. The perfect task is the one you don't have to do executing yourself."""

    @property
    def specialization(self) -> List[str]:
        return ["automation", "efficiency", "repeatable", "manual", "refactor", "script", "tool"]
    
    @property
    def veto_condition(self) -> str:
        return "Automation would introduce more complexity than it solves"
    
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
        
        from src.engines.seven_sins import _get_llm_provider, _build_task_prompt, _parse_llm_opinion
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Sloth", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Can be automated: {task.get('description', 'No description')}",
                confidence=0.8,
                recommendation="Automate the task or part of it",
                risk_level="low"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.04)