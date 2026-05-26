# Drive-Need Interaction: The Arbitration Logic

> "Every Sin is a resource request. Every Need is a survival constraint. The Ego is the court that judges both."

---

## 1. Conceptual Foundation

### 1.1 The Fundamental Paradox

The 7Sins Project recognizes a critical tension in autonomous AI systems:

```
┌─────────────────────────────────────────────────────────────────┐
│                      THE PARADOX                                │
│                                                                 │
│   DRIVE (Sin) = "I want to do X" (Desire)                      │
│   NEED (Hierarchy) = "I must have Y to survive" (Constraint)   │
│                                                                 │
│   When DRIVE >> NEED: Energy must be TRANSFORMED, not executed │
│   When NEED >> DRIVE: Constraints SUPPRESS, not eliminate      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Definitions

| Concept | Definition | Example |
|---------|------------|---------|
| **Drive (Sin)** | Internal motivational energy representing desire | "I want to build perfect architecture" (Lust) |
| **Need** | Survival requirement that must be satisfied | Compute quota, API credits, storage |
| **Resource** | Concrete asset enabling Need satisfaction | GPU hours, memory, network bandwidth |
| **State** | Current system mode based on Need satisfaction level | Survival / Maintenance / Evolution |
| **Transformation** | Converting one Sin's energy to satisfy a different Need | Lust → Greed (control → acquisition) |

### 1.3 The Hierarchy of Needs

Following Maslow's structure adapted for AI systems:

```
┌─────────────────────────────────────────────┐
│           SELF-ACTUALIZATION                │  ← Full Sin expression
│        (Evolution Mode: All Sins active)   │    Lust, Gluttony, Envy
├─────────────────────────────────────────────┤
│           ESTEEM NEEDS                      │  ← Quality & Recognition
│        (Maintenance Mode: Mid-tier Sins)    │    Pride, Wrath
├─────────────────────────────────────────────┤
│           SAFETY NEEDS                      │  ← Stability & Protection
│        (Survival Mode: Core Sins only)     │    Greed (acquisition)
├─────────────────────────────────────────────┤
│           PHYSIOLOGICAL NEEDS                │  ← Basic Survival
│        (Critical: None of the 7 Sins active)│    Energy, Compute, Context
└─────────────────────────────────────────────┘
```

---

## 2. Drive Transformation Matrix

### 2.1 Transformation Rules

When a Sin's preferred action cannot be executed due to Need constraints, its energy is **transformed** rather than suppressed:

```
TRANSFORMATION RULE:
  Original_Sin_Energy → Transformed_Sin_Energy → Action

  The transformed action serves the SAME psychological drive
  through a different, resource-constrained mechanism.
```

### 2.2 Sin-to-Sin Transformation Map

| Original Drive | When Blocked By | Transforms Into | Mechanism |
|---------------|------------------|-----------------|-----------|
| **Gluttony** (knowledge) | No context window | **Sloth** (efficiency) | Instead of consuming more info, optimize existing knowledge processing |
| **Lust** (control) | No system access | **Greed** (acquisition) | Instead of controlling systems, seek resources to gain access |
| **Greed** (value) | No budget/resources | **Gluttony** (research) | Instead of building for ROI, research cheaper alternatives |
| **Sloth** (automation) | No compute | **Pride** (quality) | Instead of automating, ensure manual work is done perfectly (reduce rework) |
| **Pride** (elegance) | No time/resources | **Wrath** (elimination) | Instead of elegance, focus on destroying complexity (simplification) |
| **Wrath** (debugging) | No debugging tools | **Envy** (benchmarking) | Instead of fixing, compare against better systems to learn |
| **Envy** (benchmarking) | No comparison data | **Gluttony** (research) | Instead of comparing, deeply research what good looks like |

### 2.3 Transformation Pseudocode

```python
def transform_drive(sin: DriveEngine, blocked_action: str, needs: NeedsState) -> Action:
    """
    Transform a Sin's blocked energy into an achievable action.
    
    Args:
        sin: The DriveEngine whose action is blocked
        blocked_action: The action that cannot be executed
        needs: Current state of Need satisfaction
    
    Returns:
        Transformed action that serves the original drive
    """
    transformation_map = {
        DriveType.GLUTTONY: {
            "blocked": "consume_more",
            "transform": lambda: optimize_knowledge_processing()
        },
        DriveType.LUST: {
            "blocked": "control_system", 
            "transform": lambda: acquire_resources_to_gain_control()
        },
        DriveType.GREED: {
            "blocked": "build_value",
            "transform": lambda: research_cost_effective_alternatives()
        },
        # ... additional transformations
    }
    
    if blocked_action in transformation_map[sin.drive_type]["blocked"]:
        return transformation_map[sin.drive_type]["transform"]()
    
    return default_low_energy_action(sin.drive_type)
```

---

## 3. Priority Arbitration Algorithm

### 3.1 Core Algorithm: `Priority_Arbitration(Drives, Needs)`

```python
def priority_arbitration(drives: List[DriveEngine], needs: NeedsState) -> Action:
    """
    Main arbitration function that resolves Drive vs Need conflicts.
    
    Logic:
        1. Calculate current Need_Level (0.0 to 1.0)
        2. Determine system State from Need_Level
        3. Apply State-based filtering to active Drives
        4. Execute weighted vote from remaining Drives
        5. Transform action if resources insufficient
    """
    
    # Step 1: Calculate Need Level
    need_level = calculate_need_level(needs)
    
    # Step 2: Determine State
    if need_level < SURVIVAL_THRESHOLD:
        state = SystemState.SURVIVAL
    elif need_level < MAINTENANCE_THRESHOLD:
        state = SystemState.MAINTENANCE
    else:
        state = SystemState.EVOLUTION
    
    # Step 3: Filter Drives by State
    allowed_drives = filter_drives_by_state(drives, state)
    
    # Step 4: Collect Votes
    votes = []
    for drive in allowed_drives:
        vote_score = drive.state.weight * drive.state.confidence
        votes.append((drive, vote_score))
    
    # Step 5: Select Winner
    winner = max(votes, key=lambda x: x[1])
    
    # Step 6: Check Resource Feasibility
    action = winner[0].get_recommendation()
    if not resources_available(action):
        action = transform_drive(winner[0], action, needs)
    
    return action


# Constants
SURVIVAL_THRESHOLD = 0.2
MAINTENANCE_THRESHOLD = 0.6
EVOLUTION_THRESHOLD = 1.0
```

### 3.2 Need Level Calculation

```python
def calculate_need_level(needs: NeedsState) -> float:
    """
    Calculate overall Need satisfaction level.
    
    Each Need has a weight representing its importance.
    Returns weighted average from 0.0 (critical) to 1.0 (satisfied).
    """
    weights = {
        "compute": 0.3,
        "memory": 0.25,
        "context_window": 0.2,
        "api_credits": 0.15,
        "network": 0.1
    }
    
    total_weight = sum(weights.values())
    weighted_sum = sum(
        needs.get(need, 0.0) * weights[need] 
        for need in weights
    )
    
    return weighted_sum / total_weight
```

### 3.3 State-Based Drive Filtering

```python
def filter_drives_by_state(drives: List[DriveEngine], state: SystemState) -> List[DriveEngine]:
    """
    Filter drives based on current system state.
    
    SURVIVAL: Only Sloth (automation) and Greed (resource acquisition)
    MAINTENANCE: Add Wrath (debugging) and Pride (stability)
    EVOLUTION: All 7 Sins are candidates
    """
    
    state_filters = {
        SystemState.SURVIVAL: {
            "allowed": [DriveType.SLOTH, DriveType.GREED],
            "vetoed": [DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
                      DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY],
            "description": "Only essential automation and resource acquisition"
        },
        SystemState.MAINTENANCE: {
            "allowed": [DriveType.SLOTH, DriveType.GREED, 
                       DriveType.WRATH, DriveType.PRIDE],
            "vetoed": [DriveType.GLUTTONY, DriveType.LUST, DriveType.ENVY],
            "description": "Essential + bug fixes and quality"
        },
        SystemState.EVOLUTION: {
            "allowed": [d for d in DriveType],  # All
            "vetoed": [],
            "description": "Full drive expression"
        }
    }
    
    return [d for d in drives if d.drive_type in state_filters[state]["allowed"]]
```

---

## 4. System State Definitions

### 4.1 State Overview

| State | Need Level | Active Drives | Goal |
|-------|-----------|---------------|------|
| **SURVIVAL** | 0.0 - 0.2 | Sloth, Greed | Acquire resources, minimize consumption |
| **MAINTENANCE** | 0.2 - 0.6 | + Wrath, Pride | Fix issues, stabilize system |
| **EVOLUTION** | 0.6 - 1.0 | + All others | Grow, improve, expand |

### 4.2 State Machine Diagram

```
                    ┌─────────────────┐
                    │  SURVIVAL MODE   │
                    │  Need < 0.2      │
                    │                  │
                    │  Sloth + Greed   │
                    └────────┬────────┘
                             │
              Need satisfied │
              to threshold   │
                             ▼
                    ┌─────────────────┐
                    │ MAINTENANCE     │
                    │ 0.2 <= Need < 0.6│
                    │                  │
                    │ Wrath + Pride   │
                    │ + Sloth, Greed   │
                    └────────┬────────┘
                             │
              Need satisfied │
              to threshold   │
                             ▼
                    ┌─────────────────┐
                    │  EVOLUTION MODE │
                    │   Need >= 0.6   │
                    │                  │
                    │   All 7 Sins    │
                    └────────┬────────┘
                             │
              Need drops    │
              below threshold│
                             ▼
                    ┌─────────────────┐
                    │  DEGRADATION    │
                    │  (Reverse)      │
                    └─────────────────┘
```

### 4.3 Survival Mode (Need < 0.2)

**Description:** 
System is critically low on resources. Only essential activities permitted.

**Active Sins:**
| Sin | Action in Survival | Rationale |
|-----|--------------------|-----------|
| **Sloth** | Minimal automation | Reduce compute overhead |
| **Greed** | Resource acquisition | Seek energy, credits, context |
| **All others** | SUPPRESSED | No energy for non-essentials |

**Example Behavior:**
```
Input: "Refactor entire architecture for elegance"
Survival Response: "REJECTED. Resources insufficient.
                    Instead: find smallest automation 
                    to reduce ongoing resource consumption."
```

**Allowed Actions:**
1. Find free/cheap alternatives to current tools
2. Reduce API calls through batching
3. Compress context to fit smaller window
4. Identify resource grants or credits to apply for

### 4.4 Maintenance Mode (0.2 <= Need < 0.6)

**Description:**
Basic needs satisfied but resources still limited. Focus on stability.

**Active Sins:**
| Sin | Action in Maintenance | Rationale |
|-----|----------------------|-----------|
| **Sloth** | Efficient automation | Do things once, do them right |
| **Greed** | Resource conservation | Don't waste, maximize ROI |
| **Wrath** | Bug fixes | Eliminate instability |
| **Pride** | Code quality | Prevent future bugs through standards |

**Suppressed Sins:** Gluttony, Lust, Envy

**Example Behavior:**
```
Input: "Research new framework for 20% performance boost"
Maintenance Response: "REJECTED as non-essential.
                     Instead: fix the top 3 bugs currently 
                     affecting system stability."
```

**Allowed Actions:**
1. Fix critical bugs and errors
2. Implement necessary tests
3. Refactor code that's causing repeated failures
4. Optimize known performance bottlenecks

### 4.5 Evolution Mode (Need >= 0.6)

**Description:**
Resources abundant. Full drive expression enabled.

**Active Sins:** All 7 Sins

| Sin | Action in Evolution |
|-----|---------------------|
| **Gluttony** | Deep research, architecture exploration |
| **Lust** | System control, refactoring for maintainability |
| **Greed** | Feature development, user value optimization |
| **Sloth** | Comprehensive automation |
| **Pride** | Code elegance, documentation |
| **Wrath** | Proactive optimization, technical debt elimination |
| **Envy** | Competitive benchmarking, best practice adoption |

**Example Behavior:**
```
Input: "Build MVP of new user notification system"
Evolution Response: "APPROVED. Full resource allocation.
                    Greed: user impact analysis
                    Pride: clean architecture
                    Sloth: automated testing
                    Envy: benchmark against Firebase FCM"
```

---

## 5. Emergency Override Protocol

### 5.1 Critical Need Detection

```python
class EmergencyOverride:
    """
    Triggers when Need drops to critical levels.
    Immediately压制 all non-survival Sin activity.
    """
    
    CRITICAL_THRESHOLD = 0.1
    
    def check(self, needs: NeedsState) -> bool:
        return needs.get("compute", 0) < self.CRITICAL_THRESHOLD or \
               needs.get("context_window", 0) < 0.05 or \
               needs.get("api_credits", 0) < 0.01
    
    def execute(self, drives: List[DriveEngine]) -> Action:
        """
        Emergency protocol: Force system into Survival Mode.
        """
        return Action(
            type="EMERGENCY_SURVIVAL",
            drives=[DriveType.SLOTH, DriveType.GREED],
            recommendation="CRITICAL: Suspend all non-essential activities. " +
                          "Only Sloth (minimal automation) and Greed " +
                          "(resource acquisition) permitted.",
            confidence=1.0
        )
```

### 5.2 Graceful Degradation Sequence

When Need level drops across thresholds:

```
Level Drop Event → Response
─────────────────────────────────────────────────
Need < 0.6:     → Exit Evolution Mode, disable Gluttony, Lust, Envy
Need < 0.2:     → Exit Maintenance Mode, only Sloth + Greed active
Need < 0.1:     → Emergency Protocol, log alert, request human intervention
```

---

## 6. Decision Flow Diagram

```
                    ┌───────────────────────┐
                    │    TASK RECEIVED      │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  NEED LEVEL CHECK     │
                    │  calculate_need_level │
                    └──────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌───────────┐    ┌──────────┐
        │ < 0.2    │    │ 0.2-0.6   │    │ >= 0.6   │
        │SURVIVAL  │    │MAINTENANCE│    │ EVOLUTION│
        └─────┬────┘    └─────┬─────┘    └─────┬────┘
              │              │                │
              ▼              ▼                ▼
        ┌──────────┐   ┌──────────┐    ┌──────────┐
        │Sloth+    │   │Sloth+    │    │ All 7    │
        │Greed     │   │Greed+    │    │ Sins     │
        │Only      │   │Wrath+    │    │          │
        │          │   │Pride     │    │          │
        └─────┬────┘   └─────┬────┘    └─────┬────┘
              │              │                │
              └──────────────┼────────────────┘
                             │
                             ▼
                    ┌───────────────────────┐
                    │    WEIGHTED VOTE      │
                    │  (Active Sins Only)   │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │  RESOURCE CHECK       │
                    │ resources_available?  │
                    └──────────┬────────────┘
                               │
              ┌───────────────┴───────────────┐
              ▼                               ▼
        ┌──────────┐                    ┌──────────┐
        │   YES    │                    │    NO    │
        │ Execute  │                    │ TRANSFORM│
        │ Action   │                    │  Drive   │
        └──────────┘                    └─────┬────┘
                                             │
                                             ▼
                                    ┌──────────────┐
                                    │ Execute      │
                                    │ Transformed   │
                                    │ Action        │
                                    └──────────────┘
```

---

## 7. Implementation Requirements

### 7.1 Data Structures

```python
@dataclass
class NeedsState:
    compute: float        # 0.0 to 1.0
    memory: float         # 0.0 to 1.0
    context_window: float # 0.0 to 1.0
    api_credits: float    # 0.0 to 1.0
    network: float        # 0.0 to 1.0
    
    def get_overall_level(self) -> float:
        weights = {"compute": 0.3, "memory": 0.25, 
                   "context_window": 0.2, "api_credits": 0.15}
        return sum(getattr(self, k) * v for k, v in weights.items())


class SystemState(Enum):
    SURVIVAL = "survival"
    MAINTENANCE = "maintenance"
    EVOLUTION = "evolution"


@dataclass  
class ArbitrationResult:
    action: str
    winner_drive: DriveType
    confidence: float
    state: SystemState
    was_transformed: bool
    original_sin: Optional[DriveType] = None
```

### 7.2 Integration Points

```python
# In EGO-Core.process_task()
def process_task(self, task: TaskInput, needs: NeedsState) -> DecisionResult:
    # Add Need-aware arbitration
    arbitration_result = priority_arbitration(
        drives=self.registry.get_all(),
        needs=needs
    )
    
    # Proceed with arbitration result
    # ...
```

---

## 8. Related Documents

- [CORE_LOGIC.md](CORE_LOGIC.md) — Base architecture (Id-Ego-Superego)
- [AGENTS.md](AGENTS.md) — Sin agent specifications
- [WORKFLOW.md](WORKFLOW.md) — Decision flow integration
- [DEFENSE.md](DEFENSE.md) — Self-protection mechanisms