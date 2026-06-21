# 7Sins API 合約測試 (API Contract Tests)

> 繁體中文 | 層級: C | 建立日期: 2026-06-21

---

## 🎯 目的

測試 Python Module-Level API 合約，確保公開介面的輸入輸出符合預期。此專案無 HTTP API Server，但需確保 Python API 的 dataclass、enum、function signatures 保持穩定。

---

## ⚡ 執行命令

```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
python -m pytest tests/api/ -v
```

---

## 📋 API 合約層級

### C.1 DriveType Enum 合約

```python
def test_drive_type_enum_values():
    """All expected DriveType values must exist."""
    from src.core.drive_engine import DriveType
    
    expected = {
        "GLUTTONY", "LUST", "GREED", "SLOTH",
        "PRIDE", "WRATH", "ENVY", "EROS", "THANATOS"
    }
    actual = {e.name for e in DriveType}
    assert expected == actual, f"Missing: {expected - actual}"


def test_drive_type_seven_sins_count():
    """Exactly 7 main Sins (excluding EROS/THANATOS life drives)."""
    from src.core.drive_engine import DriveType
    
    seven = {
        DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
        DriveType.SLOTH, DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY
    }
    assert len(seven) == 7
```

### C.2 DecisionPhase Enum 合約

```python
def test_decision_phase_values():
    """All decision phases must be defined."""
    from src.core.ego_core import DecisionPhase
    
    expected_phases = {"PARSING", "CONSULTATION", "DEBATE", "VOTING", "EXECUTION", "REFLECTION"}
    actual = {p.name for p in DecisionPhase}
    assert expected_phases == actual


def test_decision_phase_count():
    """Must have exactly 6 phases."""
    from src.core.ego_core import DecisionPhase
    assert len(DecisionPhase) == 6
```

### C.3 TaskInput 合約

```python
def test_task_input_required_fields():
    """TaskInput must have description and task_type as required fields."""
    from src.core.ego_core import TaskInput
    import inspect
    
    sig = inspect.signature(TaskInput)
    params = list(sig.parameters.keys())
    
    assert "description" in params
    assert "task_type" in params


def test_task_input_defaults():
    """TaskInput default values must be correct."""
    from src.core.ego_core import TaskInput
    
    task = TaskInput(description="test", task_type="debug")
    assert task.constraints == []
    assert task.context == {}
    assert task.priority == 0.5
```

### C.4 DecisionResult 合約

```python
def test_decision_result_required_fields():
    """DecisionResult must have all required fields."""
    from src.core.ego_core import DecisionResult
    import inspect
    
    sig = inspect.signature(DecisionResult)
    params = list(sig.parameters.keys())
    
    required = ["recommendation", "selected_drives", "confidence", "phase", "reasoning"]
    for field in required:
        assert field in params, f"Missing field: {field}"


def test_decision_result_types():
    """DecisionResult field types must be correct."""
    from src.core.ego_core import DecisionResult, DecisionPhase
    from src.core.drive_engine import DriveType
    
    result = DecisionResult(
        recommendation="Run tests",
        selected_drives=[(DriveType.WRATH, 0.5)],
        confidence=0.85,
        phase=DecisionPhase.EXECUTION,
        reasoning="Wrath wins"
    )
    
    assert isinstance(result.recommendation, str)
    assert isinstance(result.selected_drives, list)
    assert isinstance(result.confidence, float)
    assert isinstance(result.phase, DecisionPhase)
    assert isinstance(result.reasoning, str)
```

### C.5 DriveOpinion 合約

```python
def test_drive_opinion_fields():
    """DriveOpinion must have all required fields."""
    from src.core.drive_engine import DriveOpinion, DriveType
    
    opinion = DriveOpinion(
        drive=DriveType.WRATH,
        opinion="This is risky",
        confidence=0.9,
        recommendation="Abort",
        risk_level="high"
    )
    
    assert opinion.drive == DriveType.WRATH
    assert opinion.confidence == 0.9
    assert opinion.risk_level in {"low", "medium", "high"}
```

### C.6 EGOState 合約

```python
def test_ego_state_defaults():
    """EGOState default phase must be PARSING."""
    from src.core.ego_core import EGOState, DecisionPhase
    
    state = EGOState()
    assert state.phase == DecisionPhase.PARSING
    assert state.active_drives == []
    assert state.opinions == {}
    assert state.votes == {}


def test_ego_state_mutable():
    """EGOState must allow state changes."""
    from src.core.ego_core import EGOState, DecisionPhase
    from src.core.drive_engine import DriveType, DriveOpinion
    
    state = EGOState()
    state.phase = DecisionPhase.CONSULTATION
    state.opinions[DriveType.WRATH] = DriveOpinion(
        drive=DriveType.WRATH,
        opinion="risky",
        confidence=0.9,
        recommendation="abort",
        risk_level="high"
    )
    
    assert state.phase == DecisionPhase.CONSULTATION
    assert DriveType.WRATH in state.opinions
```

### C.7 DriveEngineRegistry API 合約

```python
def test_registry_methods():
    """Registry must have all required methods."""
    from src.core.drive_engine import DriveEngineRegistry
    
    registry = DriveEngineRegistry()
    
    assert hasattr(registry, "register")
    assert hasattr(registry, "get")
    assert hasattr(registry, "get_all")
    assert hasattr(registry, "get_by_task_type")
    assert hasattr(registry, "reset_all")
    assert hasattr(registry, "get_weights")
    assert hasattr(registry, "normalize_weights")
    assert hasattr(registry, "record_decision_outcome")


def test_registry_register_and_retrieve():
    """Registry register/get round-trip."""
    from src.core.drive_engine import DriveEngineRegistry, DriveType
    from src.engines.seven_sins import PrideEngine
    
    registry = DriveEngineRegistry()
    engine = PrideEngine()
    registry.register(engine)
    
    retrieved = registry.get(engine.drive_type)
    assert retrieved is engine
    assert retrieved.drive_type == DriveType.PRIDE


def test_registry_get_all():
    """Registry get_all returns all registered engines."""
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import PrideEngine, WrathEngine
    
    registry = DriveEngineRegistry()
    registry.register(PrideEngine())
    registry.register(WrathEngine())
    
    all_engines = registry.get_all()
    assert len(all_engines) == 2
```

### C.8 PersistenceManager API 合約

```python
def test_persistence_manager_methods():
    """PersistenceManager must have required methods."""
    from src.memory.persistence import PersistenceManager
    
    pm = PersistenceManager()
    
    assert hasattr(pm, "log_decision")
    assert hasattr(pm, "log_weight_change")
    assert hasattr(pm, "get_decision_logs")
    assert hasattr(pm, "get_weight_history")
```

---

## 📊 輸出位置

| 輸出 | 位置 |
|------|------|
| pytest 標準輸出 | stdout |
| 報告 | `runtime/logs/tests/<timestamp>/api-contract-report.md` |

---

## ✅ Pass / Fail 標準

| 條件 | 結果 |
|------|------|
| 所有 API 合約測試通過 | **PASS** |
| 任何 1 項失敗 | **FAIL** |

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
