"""
7Sins Drive Engines
Concrete implementations of the seven drive agents with LLM integration
"""

import os
from typing import Dict, List, Any, Optional
from .llm_provider import LLMProviderRegistry, LLMResponse
from .minimax_provider import create_minimax_provider
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion
from src.tools.search import get_search_tool


def _get_llm_provider() -> 'MiniMaxProvider':
    """Get or create the LLM provider instance"""
    provider = LLMProviderRegistry.get("minimax")
    if provider is None:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        group_id = os.environ.get("MINIMAX_GROUP_ID", "")
        if api_key:
            provider = create_minimax_provider(api_key=api_key, group_id=group_id)
    if provider is None:
        raise RuntimeError("LLM provider not initialized. Set MINIMAX_API_KEY environment variable.")
    return provider


def _build_task_prompt(task: Dict[str, Any], context: Dict[str, Any], engine_name: str, specialization: List[str]) -> str:
    """Build a prompt for the LLM based on task and context"""
    task_desc = task.get("description", "")
    task_type = task.get("task_type", "")
    constraints = task.get("constraints", [])
    
    prompt = f"""Task: {task_desc}
Type: {task_type}
Specializations: {', '.join(specialization)}
Context: {context}

As the {engine_name} drive agent, analyze this task and provide:
1. Your opinion on how to approach this task
2. A confidence score (0.0-1.0) for your assessment
3. A recommendation for action
4. Risk level (low/medium/high)

Be concise and specific to your drive's nature."""
    return prompt


def _parse_llm_opinion(response: LLMResponse, drive_type: DriveType) -> DriveOpinion:
    """Parse LLM response into a DriveOpinion"""
    import re
    
    content = response.content.strip()
    
    # Parse confidence
    confidence = 0.7
    conf_match = re.search(r'confidence[:\s]*[:=]?\s*([0-9.]+)', content, re.IGNORECASE)
    if conf_match:
        confidence = float(conf_match.group(1))
    else:
        # Try to find a single decimal number that looks like confidence
        numbers = re.findall(r'\b([01](?:\.\d+)?)\b', content)
        if numbers:
            valid = [float(n) for n in numbers if 0 <= float(n) <= 1]
            if valid:
                confidence = valid[0]
    
    # Parse risk level
    risk_level = "medium"
    risk_match = re.search(r'risk[:\s]*[:=]?\s*(low|medium|high)', content, re.IGNORECASE)
    if risk_match:
        risk_level = risk_match.group(1).lower()
    else:
        if "low risk" in content.lower():
            risk_level = "low"
        elif "high risk" in content.lower():
            risk_level = "high"
    
    # Extract opinion and recommendation
    opinion = content
    recommendation = content
    
    # Try to split if structured
    lines = content.split('\n')
    for line in lines:
        if any(x in line.lower() for x in ["recommend:", "recommendation:", "should:", "action:"]):
            recommendation = line.split(':', 1)[-1].strip()
            break
    
    return DriveOpinion(
        drive=drive_type,
        opinion=opinion,
        confidence=confidence,
        recommendation=recommendation,
        risk_level=risk_level
    )


class GluttonyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.GLUTTONY, base_weight=0.7)
    
    @property
    def system_prompt(self) -> str:
        return "You are Gluttony - driven by knowledge hunger and cognitive lead. Seek depth, research thoroughly, explore alternatives. Be thorough and research-oriented."
    
    @property
    def specialization(self) -> List[str]:
        return ["research", "analysis", "architecture", "learning", "explore", "investigate"]
    
    @property
    def veto_condition(self) -> str:
        return "Insufficient information to make decision"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.7)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        is_research = any(kw in task_type for kw in ["research", "search", "investigate"])
        if is_research:
            search_tool = get_search_tool()
            search_results = search_tool.search(task.get("description", ""), count=10)
            if search_results:
                context["search_results"] = search_results
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Gluttony", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            # Fallback to mock response on error
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Research deeply: {task.get('description', 'No description')}",
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
        return "You are Lust - driven by power and control. Seek order, efficiency, and complete understanding of systems. Be systematic and controlling."
    
    @property
    def specialization(self) -> List[str]:
        return ["control", "order", "architecture", "priority", "resource", "manage"]
    
    @property
    def veto_condition(self) -> str:
        return "Loss of control or system integrity"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Lust", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Controlled approach required for: {task.get('description', 'No description')}",
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
        return "You are Greed - driven by influence expansion and value creation. Seek market opportunities, user value, ROI. Be value-focused and growth-oriented."
    
    @property
    def specialization(self) -> List[str]:
        return ["market", "value", "user", "feature", "revenue", "growth", "strategy"]
    
    @property
    def veto_condition(self) -> str:
        return "No clear value proposition or ROI"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.8)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Greed", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Value opportunity: {task.get('description', 'No description')}",
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
        return "You are Sloth - driven by efficiency and automation. Eliminate repetitive work, automate everything possible. Be efficient and lazy."
    
    @property
    def specialization(self) -> List[str]:
        return ["automation", "efficiency", "repeat", "manual", "refactor", "script", "tool"]
    
    @property
    def veto_condition(self) -> str:
        return "Automation would introduce more complexity than it solves"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.7)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
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


class PrideEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.PRIDE, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return "You are Pride - driven by quality and code aesthetics. Reject the mediocre, demand elegance. Be demanding and quality-focused."
    
    @property
    def specialization(self) -> List[str]:
        return ["review", "quality", "code", "standard", "aesthetics", "refactor", "clean"]
    
    @property
    def veto_condition(self) -> str:
        return "Code does not meet quality standards"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Pride", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Quality demand: {task.get('description', 'No description')}",
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
        return "You are Wrath - driven by zero-tolerance for errors. Debug relentlessly, eliminate all faults. Be meticulous and intolerant of errors."
    
    @property
    def specialization(self) -> List[str]:
        return ["bug", "error", "debug", "fix", "fault", "issue", "problem", "crash", "fail"]
    
    @property
    def veto_condition(self) -> str:
        return "Any error present - no compromises"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.9)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Wrath", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
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


class EnvyEngine(DriveEngine):
    
    def __init__(self):
        super().__init__(DriveType.ENVY, base_weight=0.5)
    
    @property
    def system_prompt(self) -> str:
        return "You are Envy - driven by benchmarking against the best. Seek industry standards, competitive analysis. Be competitive and comparative."
    
    @property
    def specialization(self) -> List[str]:
        return ["benchmark", "competitor", "best", "standard", "compare", "industry"]
    
    @property
    def veto_condition(self) -> str:
        return "Our solution is inferior to competition"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.5)
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        is_competitive = any(kw in task_type for kw in ["competitor", "benchmark", "compare"])
        if is_competitive:
            search_tool = get_search_tool()
            competitor_results = search_tool.search(task.get("description", ""), count=10)
            if competitor_results:
                context["competitor_info"] = competitor_results
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Envy", self.specialization)
        
        try:
            response = provider.complete(prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Benchmark check: {task.get('description', 'No description')}",
                confidence=0.6,
                recommendation="Benchmark against best practices",
                risk_level="medium"
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)
