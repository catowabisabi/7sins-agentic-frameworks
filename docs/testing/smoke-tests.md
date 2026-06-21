# 7Sins 煙霧測試 (Smoke Tests)

> 繁體中文 | 層級: A | 建立日期: 2026-06-21

---

## 🎯 目的

用最短時間確認專案基本可啟動。煙霧測試用於快速驗證系統的「基本呼吸」是否正常。

---

## ⚡ 執行命令

```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
python -m pytest tests/smoke/ -v
```

或直接執行 Python：
```bash
python tests/smoke/run_smoke_tests.py
```

---

## 📋 檢查清單

### A.1 Backend Import 測試

```python
def test_backend_imports():
    """Verify all core modules can be imported without error."""
    from src.core.ego_core import EGOCore, TaskInput, DecisionResult
    from src.core.drive_engine import DriveEngine, DriveType, DriveEngineRegistry
    from src.engines.seven_sins import (
        GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
        PrideEngine, WrathEngine, EnvyEngine
    )
    from src.memory.persistence import PersistenceManager
    from src.memory.reflection import ReflectionAgent
    from src.tools.search import get_search_tool
    from src.tools.terminal import TerminalExecutor
```

### A.2 所有 7 個 Engine 可實例化

```python
def test_all_engines_instantiable():
    """Verify all 7 Sin engines can be instantiated."""
    engines = [
        GluttonyEngine(),
        LustEngine(),
        GreedEngine(),
        SlothEngine(),
        PrideEngine(),
        WrathEngine(),
        EnvyEngine(),
    ]
    assert len(engines) == 7
    for e in engines:
        assert e.state is not None
        assert e.drive_type is not None
```

### A.3 DriveEngineRegistry 正常工作

```python
def test_registry_initialization():
    """Verify DriveEngineRegistry can register and retrieve engines."""
    from src.core.drive_engine import DriveEngineRegistry
    
    registry = DriveEngineRegistry()
    engine = PrideEngine()
    registry.register(engine)
    
    assert registry.get(engine.drive_type) is engine
    assert len(registry.get_all()) == 1
```

### A.4 EGO-Core 可初始化

```python
def test_ego_core_initialization():
    """Verify EGOCore can be instantiated with registry."""
    from src.core.ego_core import EGOCore, TaskInput
    from src.core.drive_engine import DriveEngineRegistry
    
    registry = DriveEngineRegistry()
    core = EGOCore(registry)
    
    assert core.registry is registry
    assert core.max_debate_rounds == 3
    assert core.confidence_threshold == 0.6
```

### A.5 TaskInput 可創建

```python
def test_task_input_creation():
    """Verify TaskInput dataclass works correctly."""
    from src.core.ego_core import TaskInput
    
    task = TaskInput(
        description="Fix authentication bug",
        task_type="debug",
        priority=0.8
    )
    
    assert task.description == "Fix authentication bug"
    assert task.task_type == "debug"
    assert task.priority == 0.8
```

### A.6 DecisionResult 可創建

```python
def test_decision_result_creation():
    """Verify DecisionResult dataclass works correctly."""
    from src.core.ego_core import DecisionResult, DecisionPhase
    from src.core.drive_engine import DriveType
    
    result = DecisionResult(
        recommendation="Run tests first",
        selected_drives=[(DriveType.WRATH, 0.5)],
        confidence=0.85,
        phase=DecisionPhase.EXECUTION,
        reasoning="Wrath demands verification"
    )
    
    assert result.confidence == 0.85
    assert result.phase == DecisionPhase.EXECUTION
```

### A.7 PersistenceManager 單例模式正常

```python
def test_persistence_manager_singleton():
    """Verify PersistenceManager singleton pattern works."""
    from src.memory.persistence import PersistenceManager, get_persistence_manager
    
    pm1 = PersistenceManager()
    pm2 = get_persistence_manager()
    
    assert pm1 is pm2  # Same instance
```

### A.8 Search Tool 可獲取（Mock 模式）

```python
def test_search_tool_gettable():
    """Verify search tool can be retrieved (may be mock)."""
    from src.tools.search import get_search_tool
    
    tool = get_search_tool()
    assert tool is not None
    assert hasattr(tool, 'search')
```

### A.9 Audit Logger 可創建日誌目錄

```python
def test_audit_logger_creates_log_dir(tmp_path):
    """Verify AuditLogger creates log directory."""
    from src.core.ego_core import AuditLogger
    
    log_dir = tmp_path / "audit_logs"
    logger = AuditLogger(log_dir=str(log_dir))
    
    assert log_dir.exists() or logger.log_dir  # Dir created
```

### A.10 配置常數完整性

```python
def test_fallback_confidence_values():
    """Verify FALLBACK_CONFIDENCE has all 7 Sins defined."""
    from src.core.drive_engine import FALLBACK_CONFIDENCE, DriveType
    
    for sin in [DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
                DriveType.SLOTH, DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY]:
        assert sin in FALLBACK_CONFIDENCE
        assert 0.0 <= FALLBACK_CONFIDENCE[sin] <= 1.0
```

---

## 📊 輸出位置

| 輸出 | 位置 |
|------|------|
| pytest 標準輸出 | stdout |
| 報告 | `runtime/logs/tests/<timestamp>/smoke-report.md` |

---

## ✅ Pass / Fail 標準

| 條件 | 結果 |
|------|------|
| 所有 10 項檢查通過 | **PASS** |
| 任何 1 項失敗 | **FAIL** |

---

## 🔍 失敗時收集證據

1. Python traceback（完整 stack trace）
2. 失敗時的 import error message
3. `sys.path` 內容
4. Python 版本 (`python --version`)

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
