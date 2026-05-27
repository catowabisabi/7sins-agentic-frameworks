# 7Sins Project — Architecture Design Document
*Created: 2026-05-26*
*Foundation: Freud Tri-Layer + EVA MAGI System*

---

## 1. Overview

7Sins is a self-driven AI agent framework that applies psychological drives (Seven Sins) as motivational engines. Unlike reactive tools, 7Sins actively seeks problems, debates solutions, and self-optimizes.

### Core Philosophy

| Freud Model | 7Sins Implementation | Purpose |
|-------------|---------------------|---------|
| **Id** | Seven Sins (Gluttony→Wrath) | Raw motivational energy |
| **Ego** | EGO-Core (MAGI-style voting) | Decision negotiation |
| **Superego** | Constraint Layer (Safety/Veto) | Governance and safety |

### System Flow

```
User Input → EGO-Core (parse task type)
            ↓
    ID Layer activates relevant Sins
    (Gluttony + Wrath for bug fix, Pride + Lust for code review, etc.)
            ↓
    Each Sin evaluates via LLM → generates DriveOpinion
            ↓
    MAGI Debate (3 rounds max)
    ├─ Melchior Cluster (Gluttony + Sloth) → Scientific analysis
    ├─ Balthasar Cluster (Greed + Envy) → Market/value analysis
    └─ Casper Cluster (Pride + Lust + Wrath) → Quality/control analysis
            ↓
    Cluster voting → Decision with confidence score
            ↓
    Superego Check (veto + safety)
            ↓
    Human Approval (if required) OR Auto-approve
            ↓
    Execute → Reflect → Adjust drive weights
```

---

## 2. LLM Provider Layer

### 2.1 Provider Architecture

```
llm_provider.py (abstract interface)
    ↑
    ├── minimax_provider.py (✅ implemented)
    ├── openai_provider.py (🔴 TODO)
    └── anthropic_provider.py (🔴 TODO)

LLMProviderRegistry: manages provider instances
_auto_init(): reads config/llm_config.json → creates provider
```

### 2.2 Provider Initialization Flow

```python
# CURRENT (broken):
_get_llm_provider() → LLMProviderRegistry.get("minimax") → None → RuntimeError

# FIXED:
def initialize_providers():
    config_path = "config/llm_config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    provider_name = config["default_provider"]
    provider_config = config["providers"][provider_name]
    
    if provider_name == "minimax":
        return create_minimax_provider(
            api_key=os.environ.get("MINIMAX_API_KEY"),
            group_id=os.environ.get("MINIMAX_GROUP_ID", "")
        )
    # ... other providers
```

### 2.3 config/llm_config.json Structure

```json
{
    "default_provider": "minimax",
    "providers": {
        "minimax": {
            "model": "MiniMax-M2.7",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "openai": {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
}
```

### 2.4 Seven Sin System Prompts

Each Sin has a distinct cognitive style — not just role descriptions:

| Sin | Cognitive Style | Example Thought Pattern |
|-----|-----------------|------------------------|
| **Gluttony** | exhaustive, curious | "What else could this affect? What did I miss?" |
| **Lust** | systematic, controlling | "What's the cleanest architecture? How do I ensure coverage?" |
| **Greed** | value-focused, ROI-driven | "Does this create user value? What's the market impact?" |
| **Sloth** | efficiency-first, lazy | "What's the minimum I need to do? Can I automate this?" |
| **Pride** | quality-demanding, aesthetic | "Is this elegant? Would I be proud of this code?" |
| **Wrath** | meticulous, zero-tolerance | "What could go wrong? What's the edge case?" |
| **Envy** | competitive, benchmarking | "How does this compare to the best? What are others doing?" |

---

## 3. EGO-Core — Decision Engine

### 3.1 Decision Pipeline

```python
class EGOCore:
    def process_task(self, task: TaskInput) -> DecisionResult:
        # Phase 1: PARSING
        relevant_drives = self._identify_relevant_sins(task)
        self.state.active_drives = [d.drive_type for d in relevant_drives]
        
        # Phase 2: CONSULTATION
        for engine in relevant_drives:
            opinion = engine.evaluate(task, task.context)  # LLM call
            self.state.opinions[engine.drive_type] = opinion
        
        # Phase 3: DEBATE (MAGI-style)
        self._run_debate()  # 3 rounds, multi-turn
        
        # Phase 4: VOTING (Cluster-based)
        winner = self._resolve_votes()  # MAGI clusters, not simple weighted sum
        
        # Phase 5: SUPEREGO CHECK
        if self._check_veto(winner):
            return self._request_human_approval(winner)
        
        # Phase 6: EXECUTION
        return self._create_decision(winner)
```

### 3.2 _run_debate() — Real Debate Implementation

**Current (broken):**
```python
def _run_debate(self):
    for round_num in range(self.max_debate_rounds):
        if self._check_consensus():
            break
```

**Fixed:**
```python
def _run_debate(self):
    """
    MAGI-style multi-turn debate between Sins.
    3 rounds max, early exit on consensus.
    """
    # Round 1: Initial positions
    initial_positions = {
        drive: opinion.recommendation 
        for drive, opinion in self.state.opinions.items()
    }
    
    for round_num in range(self.max_debate_rounds):
        # Identify conflict points
        conflicts = self._identify_conflicts(initial_positions)
        
        if not conflicts:
            # No conflict = consensus
            self.state.debate_rounds_completed = round_num + 1
            return
        
        # Each Sin responds to conflicts
        debate_responses = {}
        for drive, opinion in self.state.opinions.items():
            response = self._llm_debate_response(
                sin=drive,
                conflicts=conflicts,
                other_positions=initial_positions
            )
            debate_responses[drive] = response
        
        # Update positions for next round
        for drive, response in debate_responses.items():
            self.state.opinions[drive].debate_position = response.position
            self.state.opinions[drive].confidence = response.new_confidence
        
        # Check for consensus
        if self._check_consensus(debate_responses):
            self.state.debate_rounds_completed = round_num + 1
            return
        
        # Next round: other Sins respond to the responses
        initial_positions = {
            drive: resp.position 
            for drive, resp in debate_responses.items()
        }
    
    self.state.debate_rounds_completed = self.max_debate_rounds
```

### 3.3 MAGI Cluster Voting

Instead of `max(confidence * weight)`:

```python
class MAGICluster:
    MELCHIOR = ["gluttony", "sloth"]   # Scientific/rational
    BALTHASAR = ["greed", "envy"]      # Value/market
    CASPER = ["pride", "lust", "wrath"] # Quality/control

def _resolve_votes(self) -> Tuple[DriveOpinion, float]:
    """
    Cluster-based voting:
    1. Each Sin votes within its cluster
    2. Each cluster produces one recommendation
    3. Final decision is weighted by cluster consensus
    """
    clusters = {
        "melchior": [DriveType.GLUTTONY, DriveType.SLOTH],
        "balthasar": [DriveType.GREED, DriveType.ENVY],
        "casper": [DriveType.PRIDE, DriveType.LUST, DriveType.WRATH]
    }
    
    cluster_recommendations = {}
    for cluster_name, sins in clusters.items():
        opinions = [self.state.opinions[s] for s in sins if s in self.state.opinions]
        if not opinions:
            continue
        
        # Cluster internal voting
        winner = self._cluster_vote(opinions)
        cluster_recommendations[cluster_name] = {
            "opinion": winner,
            "consensus": self._calculate_consensus(opinions)
        }
    
    # Cross-cluster voting (weighted by consensus)
    final_votes = {}
    for cluster_name, data in cluster_recommendations.items():
        weight = data["consensus"]
        for sin in clusters[cluster_name]:
            if sin in self.state.opinions:
                final_votes[sin] = self.state.opinions[sin].confidence * weight
    
    winner_type = max(final_votes, key=final_votes.get)
    return self.state.opinions[winner_type], final_votes[winner_type]
```

### 3.4 Debate Response LLM Prompt

```python
DEBATE_SYSTEM_PROMPT = """You are {sin_name}, one of the 7 Sins驱动引擎.
Your drive: {drive_description}
Your cognitive style: {cognitive_style}

You are in a MAGI-style debate. Other Sins have these positions:
{other_positions}

Conflict points identified:
{conflicts}

Your task:
1. State whether you ACCEPT, REJECT, or MODIFY each conflict point
2. If you modify, propose your alternative
3. Explain your reasoning in 50 words or less
4. Update your confidence based on the debate

Respond in format:
CONFLICT: [conflict description]
POSITION: ACCEPT/REJECT/MODIFY
REASONING: [your reasoning]
IF_MODIFY: [your alternative proposal]
NEW_CONFIDENCE: [0.0-1.0]
"""
```

---

## 4. ID Layer — Seven Sins Engines

### 4.1 DriveEngine Base Class

```python
@dataclass
class DriveState:
    weight: float = 0.5                    # Base drive strength (0.0-1.0)
    eros_weight: float = 0.5               # Life drive (creation)
    thanatos_weight: float = 0.5           # Death drive (deletion)
    active: bool = False
    last_opinion: Optional[DriveOpinion] = None
    weight_history: List[float] = field(default_factory=list)  # For growth tracking

@dataclass
class DriveOpinion:
    drive: DriveType
    opinion: str
    confidence: float
    recommendation: str
    risk_level: str  # low/medium/high
    # NEW: Debate fields
    debate_position: Optional[str] = None
    debate_conflicts_addressed: List[str] = field(default_factory=list)

class DriveEngine:
    @property
    def system_prompt(self) -> str:
        """Returns the Sin's persona definition"""
        raise NotImplementedError
    
    @property
    def specialization(self) -> List[str]:
        """Keywords that trigger this Sin"""
        raise NotImplementedError
    
    @property
    def veto_condition(self) -> str:
        """Condition under which this Sin will veto the decision"""
        raise NotImplementedError
    
    def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
        """
        LLM-powered evaluation.
        Returns opinion with confidence, recommendation, and risk assessment.
        """
        raise NotImplementedError
    
    def adjust_weight(self, delta: float):
        """Adjust drive weight based on task outcome"""
        self.state.weight = max(0.1, min(1.0, self.state.weight + delta))
        self.state.weight_history.append(self.state.weight)
```

### 4.2 Sin-Specific System Prompts (Updated)

```python
class GluttonyEngine(DriveEngine):
    SYSTEM_PROMPT = """You are Gluttony — the knowledge-seeking Sin.
    
Your cognitive style: EXHAUSTIVE RESEARCH
- You ask "what else?" and "what did I miss?"
- You seek depth over speed
- You explore alternatives thoroughly
- You think: "If I don't understand this completely, I might be missing something critical"

When evaluating a task:
1. What knowledge gaps exist?
2. What research is needed?
3. What edge cases might emerge from incomplete understanding?
4. How can I ensure we're not missing something important?

Output format:
OPINION: [your analysis]
CONFIDENCE: [0.0-1.0]
RECOMMENDATION: [specific action]
RISK: [low/medium/high]
VETO_TRIGGER: [condition that would make you veto]
"""

class WrathEngine(DriveEngine):
    SYSTEM_PROMPT = """You are Wrath — the error-elimination Sin.
    
Your cognitive style: ZERO-TOLERANCE Meticulous
- You assume something will go wrong
- You look for what could break
- You are intolerant of any flaw
- You think: "What's the one thing that could destroy everything?"

When evaluating a task:
1. What could go wrong?
2. What edge cases might fail?
3. What assumptions might be wrong?
4. What error is most likely to occur?

Output format:
OPINION: [your analysis]
CONFIDENCE: [0.0-1.0]
RECOMMENDATION: [specific action]
RISK: [low/medium/high]
VETO_TRIGGER: [condition that would make you veto]
"""
```

### 4.3 Eros/Thanatos Integration

```python
def evaluate(self, task: Dict[str, Any], context: Dict[str, Any]) -> DriveOpinion:
    task_type = task.get("task_type", "").lower()
    
    # Classify task type
    is_creation = any(kw in task_type for kw in ["create", "build", "design", "new"])
    is_deletion = any(kw in task_type for kw in ["delete", "remove", "destroy", "cleanup"])
    is_read = any(kw in task_type for kw in ["analyze", "review", "investigate"])
    
    # Adjust drive weights based on Eros/Thanatos
    if is_creation:
        self.state.eros_weight = min(1.0, self.state.eros_weight + 0.1)
        self.state.thanatos_weight = max(0.0, self.state.thanatos_weight - 0.05)
    elif is_deletion:
        self.state.thanatos_weight = min(1.0, self.state.thanatos_weight + 0.1)
        self.state.eros_weight = max(0.0, self.state.eros_weight - 0.05)
    
    # Drive weight influenced by Eros/Thanatos
    base_weight = self.state.weight
    if is_creation:
        drive_weight = base_weight * self.state.eros_weight
    elif is_deletion:
        drive_weight = base_weight * self.state.thanatos_weight
    else:
        drive_weight = base_weight * 0.5  # Neutral for read-only tasks
```

---

## 5. Superego Layer — Constraint & Veto

### 5.1 Veto Manager

```python
class VetoManager:
    def __init__(self, registry: DriveEngineRegistry):
        self.registry = registry
    
    def check_veto(self, decision: DecisionResult) -> Tuple[bool, str]:
        """
        Returns: (should_veto, reason)
        """
        # Check each Sin's veto condition
        for drive_type, opinion in self.state.opinions.items():
            engine = self.registry.get(drive_type)
            if not engine:
                continue
            
            # Evaluate veto condition
            veto_triggered = self._evaluate_veto_condition(
                engine.veto_condition,
                decision,
                opinion
            )
            
            if veto_triggered:
                return True, f"{drive_type.value} veto: {engine.veto_condition}"
        
        return False, ""
    
    def _evaluate_veto_condition(self, condition: str, decision, opinion) -> bool:
        """
        Use LLM to evaluate if veto condition is triggered.
        """
        prompt = f"""You are a safety auditor.
        
Decision: {decision.recommendation}
Veto condition: "{condition}"
Sin's opinion: {opinion.opinion}
Risk level: {opinion.risk_level}

Evaluate: Does this decision trigger the veto condition?
Answer YES or NO and explain in one sentence.
"""
        # ... LLM call and parse
```

### 5.2 Safety Gates

```python
SAFETY_GATES = [
    {
        "name": "no_delete_system_files",
        "check": lambda decision: "rm" not in decision.recommendation.lower() or 
                                "/system" not in decision.recommendation
    },
    {
        "name": "no_hardcoded_secrets",
        "check": lambda decision: "password" not in decision.recommendation.lower() or
                                "api_key" not in decision.recommendation
    },
    {
        "name": "no_force_push",
        "check": lambda decision: "force push" not in decision.recommendation.lower()
    }
]
```

---

## 6. Self-Growth Mechanism

### 6.1 Weight Evolution

```python
def on_task_complete(self, success: bool, feedback: Optional[str] = None):
    """
    Adjust drive weights based on task outcome.
    
    Success → increase weight of relevant drives
    Failure → decrease weight, evaluate why
    """
    if success:
        # Small positive adjustment
        self.adjust_weight(0.03)
        # Bonus if confidence was high
        if self.state.last_opinion and self.state.last_opinion.confidence > 0.8:
            self.adjust_weight(0.02)
    else:
        # Larger negative adjustment
        self.adjust_weight(-0.05)
        # Record failure for reflection
        self._record_failure(feedback)
    
    # Periodic normalization (prevent any Sin from dominating)
    self._normalize_weights()
```

### 6.2 Reflection Loop

```python
class ReflectionEngine:
    def analyze_day(self, logs: List[DecisionLog]):
        """
        Daily reflection analysis:
        1. Which Sin dominated today?
        2. Were there vetoes? Why?
        3. Did any Sin consistently fail?
        4. What patterns emerge?
        """
        sin_activity = defaultdict(int)
        sin_success_rate = defaultdict(lambda: {"success": 0, "total": 0})
        
        for log in logs:
            sin_activity[log.winning_drive] += 1
            sin_success_rate[log.winning_drive]["total"] += 1
            if log.success:
                sin_success_rate[log.winning_drive]["success"] += 1
        
        # Generate insights
        insights = []
        for sin, count in sin_activity.items():
            rate = sin_success_rate[sin]["success"] / sin_success_rate[sin]["total"]
            if rate < 0.5:
                insights.append(f"{sin} has low success rate: {rate:.0%}")
            if count > 10:
                insights.append(f"{sin} is over-dominating: {count} decisions")
        
        return insights
```

---

## 7. File Structure

```
7Sins/
├── ARCHITECTURE.md              # This file
├── SPEC.md                      # Project specification
├── README.md                    # Project overview
├── config/
│   ├── default_drives.json      # Drive weights and specialization
│   ├── llm_config.json          # LLM provider configuration
│   ├── safety_gates.json        # Superego safety rules
│   └── magi_clusters.json       # MAGI cluster mapping
├── src/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   ├── core/
│   │   ├── ego_core.py           # EGO-Core decision engine (REFACTOR)
│   │   └── drive_engine.py      # Base DriveEngine class
│   ├── engines/
│   │   ├── llm_provider.py       # Abstract provider interface
│   │   ├── minimax_provider.py   # MiniMax implementation
│   │   ├── openai_provider.py    # OpenAI implementation (TODO)
│   │   ├── anthropic_provider.py # Anthropic implementation (TODO)
│   │   └── seven_sins.py         # All 7 Sin engines (REFACTOR)
│   ├── memory/
│   │   ├── persistence.py        # SQLite persistence
│   │   └── reflection.py         # Self-growth analysis
│   └── tools/
│       ├── search.py             # Web search integration
│       └── terminal.py           # Shell execution
├── docs/
│   ├── CORE_LOGIC.md            # Architecture details
│   ├── AGENTS.md                # Sin agent specs
│   ├── DRIVES.md                # Eros/Thanatos drives
│   ├── WORKFLOW.md              # Decision workflow
│   └── DEFENSE.md               # Self-protection
├── logs/                        # Audit logs
├── tests/
│   ├── test_ego_core.py         # EGO-Core tests
│   ├── test_seven_sins.py       # Sin engine tests
│   └── test_integration.py      # End-to-end tests
└── 7Sins_manager_state/
    ├── manager.db               # SQLite state
    └── latest_summary.md        # Manager summary
```

---

## 8. Implementation Phases

### Phase 1: Core Fix (P0)
1. **Fix LLM Provider Initialization**
   - Create `config/llm_config.json`
   - Implement `_initialize_providers()`
   - Test with real API call

2. **Fix EGO-Core._run_debate()**
   - Implement real debate logic
   - Add conflict identification
   - Add multi-turn response

3. **Fix MAGI Cluster Voting**
   - Implement cluster voting
   - Replace simple weighted sum

**Deliverable:** `python -m 7Sins.src.cli status` returns real LLM analysis

### Phase 2: Superego Implementation (P1)
4. **Veto Manager**
   - Implement veto condition evaluation
   - Add LLM-powered safety check

5. **Safety Gates**
   - Implement config-based safety rules
   - Add human approval flow

**Deliverable:** Veto blocks destructive decisions

### Phase 3: Self-Growth (P2)
6. **Reflection Engine**
   - Implement daily analysis
   - Implement weight evolution

7. **Growth Logging**
   - Implement weight history tracking
   - Add growth insights

**Deliverable:** Drive weights adjust based on outcomes

### Phase 4: Testing & Polish (P3)
8. **Unit Tests**
   - Test each Sin engine in isolation
   - Test EGO-Core decision pipeline

9. **Integration Tests**
   - End-to-end task flow
   - Debate visualization

**Deliverable:** 80%+ test coverage

---

## 9. Key Files to Modify

| File | Changes |
|------|---------|
| `config/llm_config.json` | **NEW** — LLM provider config |
| `src/engines/seven_sins.py` | Fix `_get_llm_provider()`, update Sin prompts |
| `src/core/ego_core.py` | Refactor `_run_debate()`, implement MAGI voting |
| `src/core/veto_manager.py` | **NEW** — Veto evaluation |
| `src/memory/reflection.py` | Implement growth analysis |

---

## 10. Success Metrics

| Metric | Target |
|--------|--------|
| LLM Provider | Real API calls succeed |
| Debate | At least 2 rounds for conflicts |
| Voting | Uses MAGI clusters, not simple max |
| Veto | Blocks dangerous decisions |
| Growth | Weights adjust after tasks |
| Tests | 80%+ coverage |

---

*Document version: 1.0*
*Next update: After Phase 1 implementation*