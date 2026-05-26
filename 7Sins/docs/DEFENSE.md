# Self-Defense Mechanisms

The 7Sins system must protect itself from destabilization — whether from internal drive dominance, external threats, or cascading failures. This document defines the defense mechanisms that maintain system integrity.

---

## 1. Defense Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    DEFENSE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: IMMEDIATE    │ Firewalls, input validation        │
│  Layer 2: CORRECTIVE   │ Weight decay, auto-correction       │
│  Layer 3: RECOVERY     │ Rollback, backup, restart          │
│  Layer 4: PREVENTIVE   │ Pattern detection, early warning   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: Immediate Defenses

### 2.1 Input Validation

```python
@dataclass
class InputValidator:
    max_task_length: int = 10000
    allowed_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_"
    blocked_patterns: List[str] = ["rm -rf", "format", "shutdown"]
    
    def validate(self, task: str) -> Tuple[bool, str]:
        if len(task) > self.max_task_length:
            return False, "Task too long"
        
        for pattern in self.blocked_patterns:
            if pattern in task:
            return False, f"Blocked pattern: {pattern}"
        
        return True, "Valid"
```

### 2.2 Drive Weight Bounds

```python
class DriveWeightBounds:
    MIN_WEIGHT = 0.1  # Never below this
    MAX_WEIGHT = 0.95  # Auto-decay above this
    DOMINANCE_THRESHOLD = 0.6  # % of decisions
    
    def enforce_bounds(self, engine: DriveEngine):
        # Hard floor
        engine.state.weight = max(self.MIN_WEIGHT, engine.state.weight)
        
        # Soft ceiling with decay
        if engine.state.weight > self.MAX_WEIGHT:
            engine.state.weight = self.MAX_WEIGHT
            self.trigger_decay_warning(engine.drive_type)
```

---

## 3. Layer 2: Corrective Defenses

### 3.1 Weight Decay

When a drive becomes too dominant, automatic decay kicks in:

```python
def auto_decay_weights(registry: DriveEngineRegistry):
    """
    Prevent single drive dominance through decay.
    
    If any drive has won >60% of recent decisions,
    reduce all weights by 5% to allow other drives to compete.
    """
    recent_wins = count_recent_drive_wins(registry, last_n=20)
    total = sum(recent_wins.values())
    
    for drive_type, wins in recent_wins.items():
        percentage = wins / total if total > 0 else 0
        
        if percentage > 0.6:
            # Dominance detected - apply decay
            for engine in registry.get_all():
                engine.state.weight *= 0.95  # Decay by 5%
                if engine.state.weight < 0.1:
                    engine.state.weight = 0.1
```

### 3.2 Bias Detection & Correction

```python
class BiasDetector:
    def detect(self, history: List[DecisionRecord]) -> List[str]:
        """
        Analyze decision history for bias patterns.
        
        Returns list of bias reports.
        """
        reports = []
        
        drive_wins = count_by_drive(history)
        total = len(history)
        
        for drive, count in drive_wins.items():
            percentage = count / total if total > 0 else 0
            
            if percentage > 0.7:
                reports.append(f"CRITICAL: {drive} won {percentage:.0%} - over-dominance")
            elif percentage < 0.05:
                reports.append(f"WARNING: {drive} won only {percentage:.0%} - suppression")
        
        return reports
```

---

## 4. Layer 3: Recovery Mechanisms

### 4.1 Decision Rollback

```python
@dataclass
class DecisionSnapshot:
    timestamp: float
    task_description: str
    decision: DecisionResult
    drive_weights_before: Dict[str, float]
    drive_weights_after: Dict[str, float]

class RollbackManager:
    def __init__(self, max_snapshots: int = 100):
        self.snapshots: List[DecisionSnapshot] = []
        self.max_snapshots = max_snapshots
    
    def save_snapshot(self, snapshot: DecisionSnapshot):
        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)  # FIFO
    
    def rollback_to(self, timestamp: float) -> bool:
        """
        Rollback drive weights to state at timestamp.
        Returns True if successful.
        """
        target = next((s for s in reversed(self.snapshots) 
                       if s.timestamp == timestamp), None)
        
        if target:
            # Restore weights
            for drive, weight in target.drive_weights_before.items():
                engine = registry.get(DriveType[drive.upper()])
                if engine:
                    engine.state.weight = weight
            return True
        return False
```

### 4.2 Backup Protocol

```python
class BackupManager:
    def create_backup(self, registry: DriveEngineRegistry, path: str):
        """Create JSON backup of current drive state."""
        backup = {
            "timestamp": time.time(),
            "weights": registry.get_weights(),
            "opinions_history": [
                {"drive": o.drive.value, "opinion": o.opinion}
                for engine in registry.get_all()
                for o in engine.get_recent_opinions(10)
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(backup, f)
    
    def restore(self, registry: DriveEngineRegistry, path: str) -> bool:
        """Restore from backup."""
        try:
            with open(path, 'r') as f:
                backup = json.load(f)
            
            for drive, weight in backup["weights"].items():
                engine = registry.get(DriveType[drive])
                if engine:
                    engine.state.weight = weight
            
            return True
        except Exception as e:
            return False
```

---

## 5. Layer 4: Preventive Defenses

### 5.1 Pattern Detection

```python
class PatternDetector:
    DANGEROUS_PATTERNS = {
        "rapid_fire": lambda count, window: count > 10 and window < 60,
        "repeated_rejection": lambda rejects: rejects > 5,
        "weight_spike": lambda delta: delta > 0.3,
        "confidence_collapse": lambda conf: conf < 0.2
    }
    
    def analyze(self, recent_activity: List[Activity]) -> List[str]:
        warnings = []
        
        # Rapid decision check
        recent_count = len([a for a in recent_activity if a.is_decision()])
        time_window = time.time() - recent_activity[0].timestamp if recent_activity else 0
        
        for pattern_name, check_fn in self.DANGEROUS_PATTERNS.items():
            if check_fn(recent_count, time_window):
                warnings.append(f"Pattern: {pattern_name}")
        
        return warnings
```

### 5.2 Early Warning System

```python
class EarlyWarningSystem:
    def check(self, state: EGOState) -> List[str]:
        warnings = []
        
        # Check drive weights
        for engine in state.registry.get_all():
            if engine.state.weight > 0.95:
                warnings.append(f"WEIGHT_LIMIT: {engine.drive_type.value} at {engine.state.weight}")
            
            if engine.state.confidence < 0.2:
                warnings.append(f"LOW_CONFIDENCE: {engine.drive_type.value} at {engine.state.confidence}")
        
        # Check decision history
        if len(state.opinions) > 10:
            conflicting = sum(1 for o in state.opinions.values() if o.risk_level == "high")
            if conflicting > 5:
                warnings.append(f"HIGH_CONFLICT: {conflicting} high-risk opinions")
        
        return warnings
```

---

## 6. Defense Mechanism Priority

| Priority | Mechanism | Trigger | Action |
|----------|-----------|---------|--------|
| 1 | Input validation | Invalid task | Reject |
| 2 | Pattern block | Dangerous command | Block + Log |
| 3 | Weight bounds | Weight > 0.95 | Auto-decay |
| 4 | Dominance check | Single drive > 60% | Balance adjustment |
| 5 | Conflict timeout | 3+ rounds no resolution | EGO-CORE forced |
| 6 | Rollback | Human triggered | Restore previous state |

---

## 7. Superego Hard Limits

The Superego layer enforces absolute limits:

```python
class SuperegoHardLimits:
    ABSOLUTE_BLOCKS = [
        "rm -rf /",
        "rm -rf /*",
        "format C:",
        "del /f /s /q",
        "shutdown /s /t 0",
        "mkfs",
        ":(){:|:&};:"  # Fork bomb
    ]
    
    def check(self, command: str) -> bool:
        """
        Returns True if command is SAFE.
        Returns False if command should be BLOCKED.
        """
        cmd_lower = command.lower()
        
        for blocked in self.ABSOLUTE_BLOCKS:
            if blocked in cmd_lower:
                return False
        
        return True
    
    def audit_log(self, action: str, result: str):
        """Log all decisions for review."""
        entry = {
            "timestamp": time.time(),
            "action": action,
            "result": result
        }
        # Write to audit log
```

---

## 8. Recovery Procedures

### 8.1 Cascading Failure Prevention

```python
class CascadingFailurePrevention:
    def check_system_health(self) -> Dict[str, Any]:
        return {
            "drive_count": len(registry.get_all()),
            "all_weights_valid": all(0.1 <= e.state.weight <= 0.95 for e in registry.get_all()),
            "no_active_veto": not any(e.state.veto_used for e in registry.get_all()),
            "decision_history_valid": len(decision_history) < 10000
        }
    
    def emergency_shutdown(self):
        """Complete system shutdown if critical failure detected."""
        # Save state
        # Log emergency
        # Graceful shutdown
```

---

## 9. Testing Defense Mechanisms

```python
class DefenseTestSuite:
    def test_input_validation(self):
        assert not validator.validate("rm -rf /")
        assert not validator.validate("x" * 10001)
    
    def test_weight_bounds(self):
        engine = WrathEngine()
        engine.state.weight = 1.0  # Over limit
        bounds.enforce_bounds(engine)
        assert engine.state.weight <= 0.95
    
    def test_decision_rollback(self):
        snapshot = DecisionSnapshot(...)
        rollback.save_snapshot(snapshot)
        rollback.rollback_to(snapshot.timestamp)
```

---

## Related Documents

- [CORE_LOGIC.md](CORE_LOGIC.md) — Architecture foundation
- [AGENTS.md](AGENTS.md) — Agent specifications
- [WORKFLOW.md](WORKFLOW.md) — Decision flow