# Life Drive (Eros) & Death Drive (Thanatos)

Beyond the Seven Sins, the 7Sins Project incorporates Freudian drive theory — specifically the dual existence of **Eros** (life drive) and **Thanatos** (death drive). These represent fundamental motivational forces that operate at a level below the individual Sins.

---

## 1. Concept Definition

### 1.1 Eros (Life Drive / ชีวิต)

**Freudian Definition:**
Eros is the life drive — the force that seeks to preserve, protect, and create. It encompasses all drives aimed at survival, pleasure, and reproduction. In psychological terms, Eros manifests as the drive to **build, connect, and grow**.

**Engineering Mapping:**
In 7Sins, Eros represents the **creation and growth vector**:

| Eros Manifestation | 7Sins Application |
|--------------------|--------------------|
| Survival instinct | System stability, backup, recovery |
| Pleasure seeking | User satisfaction, positive outcomes |
| Reproduction/creation | Code generation, feature creation |
| Connection/bonding | Integration, dependency management |
| Growth | Continuous improvement, learning |

**Eros-Dominant Scenarios:**
- Building new features
- Connecting systems/apis
- Improving user experience
- Creating documentation
- Establishing backups and recovery

### 1.2 Thanatos (Death Drive / ความตาย)

**Freudian Definition:**
Thanatos is the death drive — the force that seeks to return to an inorganic state. It manifests as aggression, destruction, and ultimately dissolution. In psychological terms, Thanatos seeks **reduction of tension through destruction**.

**Engineering Mapping:**
In 7Sins, Thanatos represents the **deconstruction and elimination vector**:

| Thanatos Manifestation | 7Sins Application |
|------------------------|-------------------|
| Destruction impulse | Deleting dead code, cleanup |
| Aggression | Aggressive refactoring, debt elimination |
| Return to zero | Simplification, reduction to essentials |
| Entropy acceptance | Accepting technical debt resolution |
| Controlled demolition | Planned deprecation, migration |

**Thanatos-Dominant Scenarios:**
- Removing obsolete features
- Aggressive debt paydown
- Deleting over-engineered code
- Simplifying architectures
- Deprecating legacy systems

---

## 2. Drive Interaction Model

### 2.1 The Balance

Eros and Thanatos are not opposites but **complementary forces**:

```
                    CREATION
                       ↑
         ┌─────────────┼─────────────┐
         │                         │
      EROS                      THANATOS
    (Build)                    (Destroy)
         │                         │
         └─────────────┬─────────────┘
                       ↓
                   BALANCE
                   (Evolution)
```

**Example: Refactoring Decision**
- Eros says: "Keep this code, it works and has tests"
- Thanatos says: "Delete it, it's overcomplicated and hard to maintain"
- Resolution: "Rewrite in simplified form" — both drives satisfied

### 2.2 Drive Dominance by Context

| Context | Primary Drive | Secondary Drive |
|---------|--------------|----------------|
| Feature development | Eros | Thanatos (delete old) |
| Technical debt | Thanatos | Eros (preserve function) |
| Architecture evolution | Balance | Dynamic |
| Bug fixing | Thanatos (eliminate) | Eros (preserve stability) |
| Performance optimization | Thanatos (remove inefficiency) | Eros (preserve function) |

---

## 3. Implementation

### 3.1 Drive State

```python
@dataclass
class FundamentalDriveState:
    eros_weight: float = 0.5  # 0.0 to 1.0
    thanatos_weight: float = 0.5  # 0.0 to 1.0
    dominance_threshold: float = 0.7  # Above this = dominant
    
    def get_current_dominance(self) -> str:
        if abs(self.eros_weight - self.thanatos_weight) < 0.1:
            return "BALANCED"
        return "EROS" if self.eros_weight > self._thanatos_weight else "THANATOS"
    
    def adjust(self, event_type: str):
        if event_type in ["create", "build", "connect", "grow"]:
            self.eros_weight = min(1.0, self.eros_weight + 0.05)
            self.thanatos_weight = max(0.1, self.thanatos_weight - 0.03)
        elif event_type in ["delete", "remove", "cleanup", "destroy"]:
            self.thanatos_weight = min(1.0, self.thanatos_weight + 0.05)
            self.eros_weight = max(0.1, self.eros_weight - 0.03)
```

### 3.2 Decision Influence

```python
def influence_decision(self, sin_vote: float, context: str) -> float:
    """
    Adjust Sin vote based on fundamental drive context.
    
    If Thanatos is dominant, destruction-oriented votes get boost.
    If Eros is dominant, creation-oriented votes get boost.
    """
    drive_balance = self.state.eros_weight - self.state.thanatos_weight
    
    if context in ["delete", "remove", "cleanup"]:
        return sin_vote * (1.0 + drive_balance * 0.3)
    elif context in ["create", "build", "new"]:
        return sin_vote * (1.0 - drive_balance * 0.3)
    
    return sin_vote
```

---

## 4. Eros-Specific Behaviors

### 4.1 Creation Triggers

When Eros is dominant, the system favors:

```python
EROS_MANIFESTATIONS = {
    "feature_creation": {
        "trigger": ["new", "add", "create", "implement"],
        "drive_bias": +0.2,
        "sin_affinity": ["Pride", "Greed"]
    },
    "connection_building": {
        "trigger": ["integrate", "connect", "link", "api"],
        "drive_bias": +0.15,
        "sin_affinity": ["Lust", "Gluttony"]
    },
    "protection": {
        "trigger": ["backup", "recover", "safeguard"],
        "drive_bias": +0.25,
        "sin_affinity": ["Pride", "Wrath"]
    }
}
```

### 4.2 Eros Evaluation Template

```
[EROS ANALYSIS]
Creation potential: {creation_score}
User value addition: {value_score}
System growth: {growth_score}
Recommendation: {build_or_not}
Eros confidence: {eros_confidence}
```

---

## 5. Thanatos-Specific Behaviors

### 5.1 Destruction Triggers

When Thanatos is dominant, the system favors:

```python
THANATOS_MANIFESTATIONS = {
    "code_cleanup": {
        "trigger": ["delete", "remove", "cleanup", "refactor"],
        "drive_bias": +0.3,
        "sin_affinity": ["Wrath", "Sloth"]
    },
    "simplification": {
        "trigger": ["simplify", "reduce", "streamline"],
        "drive_bias": +0.25,
        "sin_affinity": ["Pride", "Sloth"]
    },
    "deprecation": {
        "trigger": ["deprecate", "archive", "end-of-life"],
        "drive_bias": +0.2,
        "sin_affinity": ["Envy", "Lust"]
    }
}
```

### 5.2 Thanatos Evaluation Template

```
[THANATOS ANALYSIS]
Destruction benefit: {destruction_score}
Complexity reduction: {reduction_score}
Technical debt elimination: {debt_score}
Recommendation: {destroy_or_preserve}
Thanatos confidence: {thanatos_confidence}
```

---

## 6. Conflict Resolution Between Drives

### 6.1 Eros vs Thanatos Scenarios

**Scenario 1: Legacy Code Cleanup**
- Eros says: "Keep working code, modify incrementally"
- Thanatos says: "Full rewrite, eliminate debt"
- Resolution: Incremental rewrite with feature flags

**Scenario 2: New Feature vs System Stability**
- Eros says: "Add feature to grow user base"
- Thanatos says: "Don't complicate, stay stable"
- Resolution: MVP feature with minimal footprint

**Scenario 3: Performance vs Quality**
- Eros says: "Optimize for user experience"
- Thanatos says: "Simplify to reduce maintenance"
- Resolution: Measure-based optimization, not premature

### 6.2 Resolution Mechanism

```python
def resolve_eros_thanatos_conflict(eros_vote: float, thanatos_vote: float) -> str:
    net_direction = eros_vote - thanatos_vote
    
    if abs(net_direction) < 0.2:
        return "BALANCED_APPROACH"  # Hybrid solution
    elif net_direction > 0:
        return "EROS_PRIMARY"  # Build-focused
    else:
        return "THANATOS_PRIMARY"  # Destroy-focused
```

---

## 7. Daily Drive Balance Review

The system should track and report drive balance daily:

```python
def daily_drive_report(self) -> str:
    """
    Generate daily report on Eros/Thanatos balance.
    """
    dominance = self.state.get_current_dominance()
    
    report = f"""
=== DAILY DRIVE BALANCE ===
Eros (Life):   {self.state.eros_weight:.2f}
Thanatos (Death): {self.state.thanatos_weight:.2f}
Dominance: {dominance}

Recent Eros events: {self.count_eros_events()}
Recent Thanatos events: {self.count_thanatos_events()}

Recommendation: {'Favor building' if dominance == 'EROS' else 'Favor cleanup' if dominance == 'THANATOS' else 'Balanced approach'}
"""
    return report
```

---

## 8. Integration with Seven Sins

| Sin | Eros Affinity | Thanatos Affinity |
|-----|---------------|-------------------|
| Gluttony | Research deepens | Cutting knowledge gaps |
| Lust | System control | Breaking over-engineering |
| Greed | Value creation | Eliminating waste |
| Sloth | Automation | Removing redundancy |
| Pride | Quality craftsmanship | Destroying mediocrity |
| Wrath | Error elimination | Aggressive cleanup |
| Envy | Best practice learning | Removing inferior patterns |

---

## Related Documents

- [AGENTS.md](AGENTS.md) — Sin agent specifications
- [CORE_LOGIC.md](CORE_LOGIC.md) — Architecture foundation
- [WORKFLOW.md](WORKFLOW.md) — Decision flow
- [DEFENSE.md](DEFENSE.md) — Self-protection mechanisms