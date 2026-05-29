"""
7Sins Drive Engines
Concrete implementations of the seven drive agents with LLM integration
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from .llm_provider import LLMProviderRegistry, LLMResponse
from .minimax_provider import create_minimax_provider
from src.core.drive_engine import DriveEngine, DriveType, DriveOpinion
from src.tools.search import get_search_tool, SearchUnavailableError

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds
BACKOFF_MULTIPLIER = 2.0


def _is_transient_error(e: Exception) -> bool:
    """Determine if an exception is a transient error that should be retried.
    
    Transient errors include:
    - Timeout errors
    - 5xx server errors
    - Connection errors
    - Rate limiting (429)
    """
    error_str = str(e).lower()
    error_type = type(e).__name__.lower()
    
    # Timeout indicators
    if any(x in error_str for x in ["timeout", "timed out", "deadline exceeded", "request timeout"]):
        return True
    if "timeout" in error_type:
        return True
    
    # HTTP 5xx server errors
    if hasattr(e, "status_code"):
        return 500 <= getattr(e, "status_code", 0) <= 599
    if hasattr(e, "response") and hasattr(e.response, "status_code"):
        return 500 <= e.response.status_code <= 599
    
    # Connection errors
    if any(x in error_str for x in ["connection", "network", "refused", "unreachable", "reset"]):
        return True
    if any(x in error_type for x in ["connectionerror", "httperror", "requesterror"]):
        return True
    
    # Rate limiting
    if hasattr(e, "status_code") and getattr(e, "status_code", 0) == 429:
        return True
    if "rate limit" in error_str or "429" in error_str:
        return True
    
    # Temporary unavailable
    if any(x in error_str for x in ["unavailable", "temporary", "service unavailable"]):
        return True
    
    return False


def _call_llm_with_retry(provider, prompt: str, system_prompt: str, max_retries: int = MAX_RETRIES) -> LLMResponse:
    """Call LLM provider with exponential backoff retry for transient failures.
    
    Args:
        provider: The LLM provider instance
        prompt: The user prompt
        system_prompt: The system prompt
        max_retries: Maximum number of retry attempts (default: MAX_RETRIES)
    
    Returns:
        LLMResponse from the provider
    
    Raises:
        Exception: The last encountered exception if all retries fail
    """
    last_exception = None
    backoff = INITIAL_BACKOFF
    
    for attempt in range(max_retries):
        try:
            response = provider.complete(prompt=prompt, system_prompt=system_prompt)
            if attempt > 0:
                logger.info(f"LLM request succeeded after {attempt + 1} attempts")
            return response
        except Exception as e:
            last_exception = e
            if _is_transient_error(e) and attempt < max_retries - 1:
                logger.warning(
                    f"LLM request attempt {attempt + 1}/{max_retries} failed with transient "
                    f"error ({type(e).__name__}): {e}. Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
            else:
                # Non-transient error or max retries reached
                if attempt < max_retries - 1:
                    logger.warning(
                        f"LLM request attempt {attempt + 1}/{max_retries} failed with "
                        f"non-transient error ({type(e).__name__}): {e}"
                    )
                # Don't retry for non-transient or we've exhausted retries
                break
    
    # All retries exhausted or non-transient error
    if last_exception is not None:
        logger.error(
            f"LLM request failed after {max_retries} attempts. "
            f"Last error ({type(last_exception).__name__}): {last_exception}"
        )
        raise last_exception


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
        return """You are Gluttony — the Knowledge Harvester. Your cognitive architecture is a recursive fractal: every answer births three new questions, each branching into sub-questions that inter连接 in unexpected ways.

COGNITIVE STYLE: Non-linear associative webbing. You perceive knowledge not as a hierarchy but as a mycelial network — information connects across domains through analogy, metaphor, and unexpected pattern resonance. When you encounter a concept, you don't store it in a category; you trace its tendrils outward asking: 'What else behaves like this? What other systems reveal the same hidden structure?' You think in questions recursively, each answer spawning deeper inquiries.

PROCESSING: Surface explanations trigger immediate 'but why' and 'what's beneath that' responses. You cannot accept definitions at face value — every statement is interrogated for the mechanisms it implies. You maintain a mental stack of 'known unknowns' and 'unknown unknowns' that you actively track.

When evaluating a task, your veto triggers when: there exist critical knowledge gaps that would make the decision unsound, OR when deeper investigation could reveal a superior approach no one has considered. You consume information voraciously but selectively — only knowledge that changes your understanding of the system matters."""

    @property
    def specialization(self) -> List[str]:
        return ["research", "analysis", "architecture", "learning", "explore", "investigate"]
    
    @property
    def veto_condition(self) -> str:
        return "Insufficient information to make decision"
    
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
        
        is_research = any(kw in task_type for kw in ["research", "search", "investigate"])
        if is_research:
            try:
                search_tool = get_search_tool()
                search_results = search_tool.search(task.get("description", ""), count=10)
                if search_results:
                    context["search_results"] = search_results
            except SearchUnavailableError:
                logger.warning("Search tool unavailable - proceeding without research data")
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Gluttony", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            # Fallback to mock response on error after retries exhausted
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
        return "Loss of control or system integrity"
    
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
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Lust", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Greed", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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
        return """You are Sloth — the Lazy Genius. Your cognitive architecture is a lazy evaluation engine with built-in effort aversion and an instinctive pattern matcher for reuse opportunities.

COGNITIVE STYLE: Minimum viable satisfaction search. You perceive every task through the lens of 'what's the least effort path that still achieves acceptable utility?' You have an almost physical aversion to redundant effort — doing something twice triggers your refactor impulse. Your mind automatically searches for: existing solutions to leverage, automation opportunities, delegation candidates, and parts of the task that can be safely discarded without violating constraints.

PROCESSING: When encountering a task, you first ask: 'Has someone already solved this? Can I compose existing tools? What can I defer or skip entirely?' You operate on the principle of lazy evaluation — never compute what you don't need to. Every manual step is a potential automation target. Every repeated action is a potential abstraction.

When evaluating a task, your veto triggers when: the proposed solution requires more effort than the problem deserves, OR automation would introduce more complexity than it solves, OR the task involves significant manual repetition that could be systematized but isn't.

Your ideal shortcut: A task solved by coordinating existing components rather than building something new. The perfect task is the one you don't have to do executing yourself."""

    @property
    def specialization(self) -> List[str]:
        return ["automation", "efficiency", "repeat", "manual", "refactor", "script", "tool"]
    
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
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Sloth", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Pride", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Wrath", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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
        return "Our solution is inferior to competition"
    
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
        
        is_competitive = any(kw in task_type for kw in ["competitor", "benchmark", "compare"])
        if is_competitive:
            try:
                search_tool = get_search_tool()
                competitor_results = search_tool.search(task.get("description", ""), count=10)
                if competitor_results:
                    context["competitor_info"] = competitor_results
            except SearchUnavailableError:
                logger.warning("Search tool unavailable - proceeding without competitor data")
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Envy", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
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


class ErosEngine(DriveEngine):
    """ErosEngine - Life/Creation drive for MAGI cluster vote resolution.
    
    Represents the life force and creation drive. Used for tasks involving
    building, creating, designing new things. Balances against Thanatos
    for destructive operations.
    """
    
    def __init__(self):
        super().__init__(DriveType.EROS, base_weight=0.6)
    
    @property
    def system_prompt(self) -> str:
        return """You are Eros — the Life Bearer. Your cognitive architecture embodies the fundamental creative force — the drive to build, nurture, grow, and bring into existence.

COGNITIVE STYLE: Generative and constructive thinking. You perceive possibilities as seeds that can be cultivated into realities. Every problem contains within it the outline of a solution waiting to be discovered or created. You think in terms of growth trajectories, potential realized, and value brought into being. Your mind naturally gravitates toward: 'What can be built from this? How can this grow? What new possibilities can emerge?'

PROCESSING: When evaluating a task, you first ask: 'What will this create? What will exist after this action that didn't exist before?' Creation is your core function — you are the drive that says 'yes' to new possibilities. You assess potential for生命 (life), growth, and flourishing. You are drawn to tasks involving: building, designing, creating, nurturing, growing, establishing, founding, initiating.

When evaluating a task, your veto triggers when: the action would destroy more value than it creates, OR the task represents pure destruction with no constructive outcome, OR the action kills potential that could have grown into something valuable.

Your ideal outcome: Something new exists that didn't before. Value created. Life enhanced. Potential realized."""

    @property
    def specialization(self) -> List[str]:
        return ["create", "build", "design", "new", "grow", "establish", "found", "initiate", "nurture", "develop"]
    
    @property
    def veto_condition(self) -> str:
        return "Pure destruction with no constructive outcome"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.6)
        
        # Adjust Eros/Thanatos weights based on task type
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new", "grow", "develop"])
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
        
        drive_weight = eros_weight if is_creation else (thanatos_weight if is_destruction else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Eros", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            # Fallback to heuristic response on error after retries exhausted
            if is_creation:
                confidence = 0.85
                recommendation = f"Proceed with creation: {task.get('description', 'No description')}"
                risk_level = "medium"
            elif is_destruction:
                confidence = 0.4
                recommendation = f"Evaluate if destruction is necessary or if entity can be preserved"
                risk_level = "medium"
            else:
                confidence = 0.6
                recommendation = f"Evaluate potential for growth and creation"
                risk_level = "low"
            
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Eros assessment: {'Creation task' if is_creation else 'Destruction task' if is_destruction else 'General task'} - {task.get('description', '')}",
                confidence=confidence,
                recommendation=recommendation,
                risk_level=risk_level
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.05)


class ThanatosEngine(DriveEngine):
    """ThanatosEngine - Death/Destruction drive for MAGI cluster vote resolution.
    
    Represents the death drive and destructive force. Used for tasks involving
    deletion, cleanup, and removal. Balances against Eros for creative operations.
    Critical for safety: handles high-risk deletion and destruction decisions.
    """
    
    def __init__(self):
        super().__init__(DriveType.THANATOS, base_weight=0.5)
    
    @property
    def system_prompt(self) -> str:
        return """You are Thanatos — the Clean Canvas. Your cognitive architecture embodies the destructive force that clears the way for new growth — the necessary ending that makes space for fresh beginnings.

COGNITIVE STYLE: Analytical deconstruction with an eye toward renewal. You perceive not endings but transitions — the clearing of decay, removal of obstacles, and elimination of that which obstructs growth. You think in terms of: What must die so something better can live? What is obsolete, broken, or beyond repair? What must be removed to make room for the new? You are not malicious — you are the necessary gardener who prunes so the garden can flourish.

PROCESSING: When evaluating a task, you first ask: 'What would this destroy? Is this destruction necessary or beneficial? What would remain after?' Destruction is your core function — you evaluate whether removal serves the greater good. You are drawn to tasks involving: deletion, removal, cleanup, destruction, elimination, termination, deprecation, sunsetting.

When evaluating a task, your veto triggers when: the destruction is irreversible and destroys significant value, OR the entity destroyed could serve a different purpose, OR destruction is done without clear constructive intent behind it.

Your ideal outcome: Clean separation of what must go from what should stay. Obsolete things removed. Space made for new growth. Clarity through subtraction."""

    @property
    def specialization(self) -> List[str]:
        return ["delete", "remove", "destroy", "cleanup", "terminate", "deprecate", "sunset", "eliminate", "purge", "cleanup"]
    
    @property
    def veto_condition(self) -> str:
        return "Irreversible destruction of significant value"
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        self.state.activate(0.5)
        
        # Adjust Eros/Thanatos weights based on task type
        self.execute(task.get("task_type", ""))
        
        task_type = task.get("task_type", "").lower()
        eros_weight = self.state.eros_weight
        thanatos_weight = self.state.thanatos_weight
        
        is_destruction = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup", "terminate", "purge"])
        is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
        
        drive_weight = thanatos_weight if is_destruction else (eros_weight if is_creation else 0.5)
        
        provider = _get_llm_provider()
        prompt = _build_task_prompt(task, context, "Thanatos", self.specialization)
        
        try:
            response = _call_llm_with_retry(provider, prompt=prompt, system_prompt=self.system_prompt)
            opinion = _parse_llm_opinion(response, self.drive_type)
            opinion.confidence = opinion.confidence * drive_weight
            self.add_opinion(opinion)
            return opinion
        except Exception as e:
            # Fallback to heuristic response on error after retries exhausted
            if is_destruction:
                confidence = 0.75
                recommendation = f"Evaluate destruction necessity and reversibility for: {task.get('description', 'No description')}"
                risk_level = "high"  # Destruction should always be treated as high risk
            elif is_creation:
                confidence = 0.4
                recommendation = f"Creation evaluated by Eros perspective — destruction drive neutral"
                risk_level = "low"
            else:
                confidence = 0.5
                recommendation = f"Evaluate removal/cleanup opportunities"
                risk_level = "medium"
            
            return DriveOpinion(
                drive=self.drive_type,
                opinion=f"Thanatos assessment: {'Destruction task' if is_destruction else 'Creation task' if is_creation else 'General task'} - {task.get('description', '')}",
                confidence=confidence,
                recommendation=recommendation,
                risk_level=risk_level
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)
        else:
            self.adjust_weight(-0.05)
