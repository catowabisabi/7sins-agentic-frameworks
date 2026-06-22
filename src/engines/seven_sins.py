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


def _get_task_type(task) -> str:
    """Normalize task_type from dict or dataclass/object."""
    if hasattr(task, 'task_type'):
        return task.task_type
    if isinstance(task, dict):
        return task.get('task_type', '')
    return ''


def _get_task_description(task) -> str:
    """Normalize description from dict or dataclass/object."""
    if hasattr(task, 'description'):
        return task.description
    if isinstance(task, dict):
        return task.get('description', 'No description')
    return 'No description'


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


class _MockLLMProvider:
    """Mock LLM provider for when no API key is configured"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "No LLM API key configured. Using mock provider. "
            "Set MINIMAX_API_KEY and MINIMAX_GROUP_ID environment variables for real LLM calls."
        )
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> 'LLMResponse':
        from .llm_provider import LLMResponse
        return LLMResponse(
            content="[Mock] LLM call skipped - no API key configured. Set MINIMAX_API_KEY to enable.",
            model="mock",
            tokens_used=0,
            finish_reason="mock"
        )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> 'LLMResponse':
        return self.complete(str(messages))


def _get_llm_provider() -> 'MiniMaxProvider':
    """Get or create the LLM provider instance"""
    provider = LLMProviderRegistry.get_provider("minimax")
    if provider is None:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        group_id = os.environ.get("MINIMAX_GROUP_ID", "")
        if api_key:
            provider = create_minimax_provider(api_key=api_key, group_id=group_id)
    if provider is None:
        import logging
        logging.getLogger(__name__).warning(
            "LLM provider not initialized. Using mock provider. "
            "Set MINIMAX_API_KEY and MINIMAX_GROUP_ID environment variables for real LLM calls."
        )
        provider = _MockLLMProvider()
    return provider


def _build_task_prompt(task: Dict[str, Any], context: Dict[str, Any], engine_name: str, specialization: List[str]) -> str:
    """Build a prompt for the LLM based on task and context"""
    task_desc = _get_task_description(task)
    task_type = _get_task_type(task)
    constraints = task.constraints if hasattr(task, 'constraints') else task.get('constraints', [])
    
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


# Import the 7 sin engines from their individual modules
from .pride_engine import PrideEngine
from .greed_engine import GreedEngine
from .lust_engine import LustEngine
from .envy_engine import EnvyEngine
from .gluttony_engine import GluttonyEngine
from .wrath_engine import WrathEngine
from .sloth_engine import SlothEngine


# Re-export for backwards compatibility
__all__ = [
    'PrideEngine',
    'GreedEngine',
    'LustEngine',
    'EnvyEngine',
    'GluttonyEngine',
    'WrathEngine',
    'SlothEngine',
    'ErosEngine',
    'ThanatosEngine',
]


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
                opinion=f"Eros assessment: {'Creation task' if is_creation else 'Destruction task' if is_destruction else 'General task'} - {getattr(task, 'description', '')}",
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
                opinion=f"Thanatos assessment: {'Destruction task' if is_destruction else 'Creation task' if is_creation else 'General task'} - {getattr(task, 'description', '')}",
                confidence=confidence,
                recommendation=recommendation,
                risk_level=risk_level
            )
    
    def on_task_complete(self, success: bool, feedback: Optional[str] = None):
        if success:
            self.adjust_weight(0.03)
        else:
            self.adjust_weight(-0.05)