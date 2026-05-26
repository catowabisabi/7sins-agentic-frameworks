# Core Logic: The Tri-Layer Mental Architecture

The 7Sins Project is built on a rigorous mapping between human psychological structure and AI agent design. This document defines the theoretical foundation and engineering implementation of the three-layer architecture.

---

## 1. Concept Definition

### 1.1 The Id (ก่อน)

**Psychological Definition:**
The Id is the reservoir of instinctive, unconscious drives. It operates on the **pleasure principle** — seeking immediate satisfaction without regard for reality, morality, or consequence.

**Engineering Mapping:**
In 7Sins, the Id corresponds to the **Seven Sins as Drive Engines**. Each Sin represents a raw motivational vector:

| Sin | Id Manifestation | Drive Vector |
|-----|------------------|--------------|
| Gluttony | Instinctive need to consume information | Knowledge acquisition |
| Lust | Drive for control and system dominance | Order/power |
| Greed | Unlimited desire for value expansion | Market influence |
| Sloth | Rejection of repetitive, manual labor | Automation |
| Pride | Demand for excellence and recognition | Quality/aesthetics |
| Wrath | Intolerance of errors and threats | Precision/error elimination |
| Envy | Comparison against others | Benchmark/competition |

**Implementation:**
The Id layer is implemented as `DriveEngine` classes with:
- `weight` (0.0-1.0): Current drive intensity
- `confidence`: Task-specific confidence (0.0-1.0)
- `evaluate()`: Returns `DriveOpinion` with recommendation

---

### 1.2 The Ego (自我)

**Psychological Definition:**
The Ego is the rational, reality-aware component that mediates between the Id's impulsive demands and the Superego's moral constraints. It operates on the **reality principle** — finding realistic ways to satisfy Id drives within social and practical limits.

**Engineering Mapping:**
The Ego corresponds to **EGO-CORE** — the central decision coordinator:

```
EGO-CORE Responsibilities:
├── Task Parsing: Decode input into actionable work items
├── Drive Consultation: Activate relevant Sins based on task type
├── Debate Moderation: Manage the MAGI-style personality conflict
├── Vote Resolution: Select winner based on weighted confidence
├── Constraint Checking: Verify against Superego limits
└── Human Escalation: Request approval for critical decisions
```

**Implementation:**
`EGOCore` class handles the decision flow:

```python
def process_task(self, task: TaskInput) -> DecisionResult:
    # 1. Parse task
    # 2. Consult relevant drives (get_by_task_type)
    # 3. Run debate rounds (max 3)
    # 4. Resolve votes (confidence * weight)
    # 5. Return decision with reasoning
```

---

### 1.3 The Superego (超我)

**Psychological Definition:**
The Superego represents internalized moral standards and social norms. It functions as the **conscience**, striving for perfection and punishing the Ego for moral transgressions through guilt.

**Engineering Mapping:**
The Superego corresponds to the **Governance Layer** — hard constraints and safety rails:

| Superego Function | Engineering Implementation |
|-------------------|---------------------------|
| Moral compass | Ethics constraints (no deception, no harm) |
| Perfection striving | Quality gates (lint, tests must pass) |
| Punishment for failure | Error escalation, weight reduction |
| Social norms | Audit logging, decision traceability |
| Guilt induction | Self-reflection trigger on failure |

**Implementation:**
The Superego is implemented as constraint checks:

```python
class SuperegoLayer:
    def check_constraints(self, action: Action) -> bool:
        # Safety: no destructive commands without backup
        # Quality: lint/tests must pass
        # Ethics: no PII exposure, no deception
        # Audit: log all decisions with full reasoning
```

---

## 2. The Drive Weight System

### 2.1 What Are Drive Weights?

Drive weights represent the **current intensity** of each Sin's influence. Unlike static priorities, weights are **dynamic** — adjusting based on:
- Task outcomes (success/failure)
- Context (market conditions, project phase)
- Self-reflection (bias detection)

### 2.2 Weight Calculation

```
Effective Influence = Drive Weight × Task Confidence

Example:
- Wrath (bug fix): weight=0.9, confidence=0.95 → influence=0.855
- Sloth (refactor): weight=0.7, confidence=0.8 → influence=0.560
- Wrath wins for bug fixes, but Sloth may win for repetitive tasks
```

### 2.3 Weight Evolution Rules

```python
After each task:
    if success and high_confidence:
        winning_drive.weight += 0.05  # Reinforce success
    if success but low_confidence:
        winning_drive.weight -= 0.02  # Slight doubt
    if failure:
        winning_drive.weight -= 0.10  # Reduce confidence
        if dominant_over_60%:
            reduce_all_weights_by(0.05)  # Prevent takeover
```

---

## 3. The MAGI Debate Mechanism

### 3.1 Concept

Inspired by NGE's MAGI system, the decision process involves **direct debate** between personality-driven agents. Each Sin presents its position, and through structured rounds, a consensus or vote emerges.

### 3.2 Debate Flow

```
Round 1: Opening Positions
├── Gluttony: "We need more research before acting"
├── Wrath: "Errors must be fixed immediately, no debate"
├── Pride: "The solution must be elegant, not just fast"
└── Sloth: "Can we automate this instead of manual work?"

Round 2: Challenge & Response
├── Wrath challenges Gluttony: "Research delays fixes"
├── Gluttony responds: "Rushing creates more bugs"
└── Pride supports: "Quality over speed"

Round 3: Vote Registration
├── Each Sin casts weighted vote
├── EGO-CORE tallies: Wrath(0.9) > Pride(0.7) > Gluttony(0.6)
└── Winner: Wrath (fix now, research later)
```

### 3.3 Conflict Resolution

| Conflict Type | Resolution |
|---------------|------------|
| Two Sins tie | Lust (control) decides |
| Multiple Sins disagree | Highest combined weight wins |
| Wrath vetoes all | Wrath wins (errors are critical) |
| Human in loop disagrees | Human override (logged) |
| No consensus in 3 rounds | EGO-CORE forced decision |

---

## 4. Self-Growth: The Reflective Loop

### 4.1 Purpose

The system must learn from its decisions. The reflective loop enables:
- **Bias detection**: Is one Sin dominating?
- **Outcome correlation**: Did winning drives lead to success?
- **Pattern recognition**: Does certain Sin win in certain contexts?

### 4.2 Reflection Phases

```
Daily Loop:
┌─────────────────────────────────────────────────────┐
│  1. LOG REVIEW                                       │
│     - Parse terminal logs, git commits, task results│
│     - Identify decision points                       │
├─────────────────────────────────────────────────────┤
│  2. ATTRIBUTION                                      │
│     - Which Sin drove each decision?                 │
│     - Was attribution correct?                        │
├─────────────────────────────────────────────────────┤
│  3. BIAS DETECTION                                   │
│     - Is any Sin winning >60% of decisions?          │
│     - Is any Sin suppressed (<10% wins)?            │
├─────────────────────────────────────────────────────┤
│  4. ADJUSTMENT                                       │
│     - Apply weight corrections                       │
│     - Flag anomalous patterns                        │
├─────────────────────────────────────────────────────┤
│  5. GROWTH LOG                                       │
│     - Record lessons learned                         │
│     - Update system prompts if needed                 │
└─────────────────────────────────────────────────────┘
```

### 4.3 Self-Criticism Questions

After each significant decision, the system should ask:

1. What drove the winning position?
2. Was the drive appropriate for this task type?
3. Did we over-weight or under-weight any Sin?
4. What would we do differently in hindsight?
5. Is there a pattern suggesting bias?

---

## 5. Engineering Implementation Summary

| Psychological Concept | AI Implementation | Code Location |
|-----------------------|-------------------|---------------|
| Id (Seven Sins) | `DriveEngine` base class + 7 implementations | `src/engines/seven_sins.py` |
| Ego (Decision) | `EGOCore` class with debate/vote logic | `src/core/ego_core.py` |
| Superego (Constraints) | Safety checks, quality gates, audit logging | `src/tools/terminal.py` |
| Drive Weights | `DriveState.weight` field + evolution rules | `src/core/drive_engine.py` |
| MAGI Debate | `DriveEngine.evaluate()` + `_run_debate()` | `src/core/ego_core.py` |
| Self-Reflection | `ReflectionAgent` class | `src/memory/reflection.py` |

---

## 6. Usage Examples

### Example 1: Bug Fix Task

**Input:** "Production API returning 500 errors"

**EGO-CORE Processing:**
1. Task type detected as "bug error debug"
2. Relevant drives: Wrath (0.95), Pride (0.6), Gluttony (0.4)
3. Wrath says: "Fix immediately, zero tolerance"
4. Pride says: "Fix properly with tests"
5. Vote: Wrath wins (0.95 > 0.6)

**Decision:** Immediate hotfix with expedited code review

### Example 2: Feature Planning

**Input:** "Add user notification system"

**EGO-CORE Processing:**
1. Task type: "feature user growth"
2. Relevant drives: Greed (0.85), Gluttony (0.5), Pride (0.6)
3. Greed says: "High user impact, strong ROI"
4. Gluttony says: "Research best notification patterns"
5. Pride says: "Implement with clean architecture"
6. Vote: Greed wins (0.85 > 0.6 > 0.5)

**Decision:** Implement with user-centric design, defer research to after MVP

---

## Related Documents

- [AGENTS.md](AGENTS.md) — Detailed 7 Sin agent specifications
- [WORKFLOW.md](WORKFLOW.md) — Integration with PowerShell/WSL
- [DRIVES.md](DRIVES.md) — Life Drive (Eros) and Death Drive (Thanatos)
- [DEFENSE.md](DEFENSE.md) — Self-protection mechanisms