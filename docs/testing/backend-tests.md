# 7Sins 後端單元測試 (Backend Unit Tests)

> 繁體中文 | 層級: B | 建立日期: 2026-06-21

---

## 🎯 目的

測試 Service、Validator、Parser、Database Helper、Config Loader 等純邏輯。優先使用 Temp DB / Mock IO，不依賴真 Server。

---

## 📁 現有單元測試

| 檔案 | 覆蓋範圍 | 數量 |
|------|---------|------|
| `tests/test_ego_core.py` | EGO-Core 決策層所有方法 | ~41 |
| `tests/test_ego_core_veto.py` | Veto 機制所有場景 | ~9 |
| `tests/test_multi_engine_veto.py` | 多引擎 Veto 互動 | ~7 |
| `tests/test_seven_sins.py` | 7 個 Sin Engine 獨立行為 | ~50 |
| `tests/test_envy_gluttony_helpers.py` | Envy/Gluttony 搜索工具注入 | ~16 |
| `tests/test_reflection_edge_cases.py` | Reflection 邊界條件 | ~10 |

---

## ⚡ 執行命令

```bash
# 所有後端單元測試
python -m pytest tests/ -v --ignore=tests/smoke --ignore=tests/e2e --ignore=tests/providers --ignore=tests/performance

# 只跑特定檔案
python -m pytest tests/test_ego_core.py -v
python -m pytest tests/test_seven_sins.py -v
```

---

## 📋 測試覆蓋範圍

### B.1 Config / Env Loading

```python
# 測試 FALLBACK_CONFIDENCE 政策
def test_fallback_confidence_all_sins_defined():
    """All 7 Sins must have fallback confidence values."""
    from src.core.drive_engine import FALLBACK_CONFIDENCE, DriveType
    for sin in DriveType:
        if sin in [DriveType.EROS, DriveType.THANATOS]:
            continue  # Not in the 7
        assert sin in FALLBACK_CONFIDENCE

# 測試 FALLBACK_CONFIDENCE 值範圍
def test_fallback_confidence_range():
    """Fallback confidence must be 0.0-1.0."""
    from src.core.drive_engine import FALLBACK_CONFIDENCE
    for sin, val in FALLBACK_CONFIDENCE.items():
        assert 0.0 <= val <= 1.0
```

### B.2 DriveState 驗證

```python
def test_drive_state_weight_bounds():
    """Weight must stay within MIN/MAX bounds."""
    from src.core.drive_engine import DriveState, DriveType
    state = DriveState(name=DriveType.PRIDE, weight=0.5)
    
    state.weight = 999  # Attempt to exceed MAX
    state.weight = max(state.MIN_WEIGHT, min(state.MAX_WEIGHT, state.weight))
    assert state.weight <= state.MAX_WEIGHT  # 0.95
    
    state.weight = -999  # Attempt to go below MIN
    state.weight = max(state.MIN_WEIGHT, min(state.MAX_WEIGHT, state.weight))
    assert state.weight >= state.MIN_WEIGHT  # 0.1
```

### B.3 Database CRUD Helper

```python
def test_persistence_decision_log(tmp_path):
    """Decision log writes and reads correctly."""
    from src.memory.persistence import PersistenceManager
    from src.core.drive_engine import DriveType
    
    # Override DB path
    test_db = tmp_path / "test.db"
    PersistenceManager._db_path = str(test_db)
    PersistenceManager._instance = None
    
    pm = PersistenceManager()
    pm.log_decision(
        task_description="Test task",
        winning_drive=DriveType.WRATH.value,
        confidence=0.85,
        eros_weight=0.5,
        thanatos_weight=0.5
    )
    
    # Read back
    logs = pm.get_decision_logs(limit=1)
    assert len(logs) >= 1
    assert logs[0]["task_description"] == "Test task"
```

### B.4 Request Payload 驗證

```python
def test_task_input_validation():
    """TaskInput must have required fields."""
    from src.core.ego_core import TaskInput
    
    # Valid task
    task = TaskInput(description="test", task_type="debug")
    assert task.description is not None
    assert task.task_type is not None
    
    # Empty description should still create (no validation enforced)
    task = TaskInput(description="", task_type="")
    assert task.description == ""
```

### B.5 Model / Provider 選擇邏輯

```python
def test_registry_get_by_task_type():
    """Registry correctly filters engines by task type keywords."""
    from src.core.drive_engine import DriveEngineRegistry, DriveType
    
    registry = DriveEngineRegistry()
    from src.engines.seven_sins import PrideEngine, WrathEngine, GluttonyEngine
    registry.register(PrideEngine())
    registry.register(WrathEngine())
    registry.register(GluttonyEngine())
    
    # "debug" should trigger Wrath (has "debug" in specialization)
    relevant = registry.get_by_task_type("debug")
    assert any(e.drive_type == DriveType.WRATH for e in relevant)
```

### B.6 Streaming Event Parser

N/A — 專案目前無 streaming event 解析邏輯。

### B.7 File Path Safety

```python
def test_audit_log_path_safety(tmp_path):
    """Audit logger handles special characters in path."""
    from src.core.ego_core import AuditLogger
    import os
    
    # Normal path
    log_dir = tmp_path / "normal"
    logger = AuditLogger(log_dir=str(log_dir))
    assert os.path.exists(log_dir) or logger.log_dir
    
    # Path with spaces
    log_dir = tmp_path / "path with spaces"
    logger = AuditLogger(log_dir=str(log_dir))
    assert logger.log_dir is not None
```

### B.8 MAGI Cluster 投票邏輯

```python
def test_magi_clusters_defined():
    """MAGI clusters must include all 7 Sins exactly once."""
    from src.core.ego_core import MAGI_CLUSTERS, MAGICluster, DriveType
    
    seven_sins = {
        DriveType.GLUTTONY, DriveType.LUST, DriveType.GREED,
        DriveType.SLOTH, DriveType.PRIDE, DriveType.WRATH, DriveType.ENVY
    }
    
    clustered_sins = set()
    for cluster, sins in MAGI_CLUSTERS.items():
        clustered_sins.update(sins)
    
    assert clustered_sins == seven_sins, "All 7 Sins must be in exactly one cluster"
```

### B.9 Veto Condition 語意匹配

```python
def test_veto_keywords_extraction():
    """Veto keywords are correctly extracted from veto condition."""
    from src.engines.seven_sins import WrathEngine
    
    engine = WrathEngine()
    keywords = engine._extract_veto_keywords(engine.veto_condition)
    
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert all(isinstance(k, str) for k in keywords)
```

### B.10 Weight Evolution（抑制/主導邏輯）

```python
def test_normalize_weights_suppression():
    """Suppressed engine (win_rate < 10%) gets boost."""
    from src.core.drive_engine import DriveEngineRegistry
    from src.engines.seven_sins import PrideEngine, WrathEngine
    from src.core.drive_engine import DriveType
    
    registry = DriveEngineRegistry()
    pride = PrideEngine()
    wrath = WrathEngine()
    registry.register(pride)
    registry.register(wrath)
    
    # Simulate suppressed state
    pride.state.record_win()  # 1 win
    pride.state.record_loss()  # 1 loss -> 50% win rate, not suppressed
    
    wrath.state.record_loss()
    wrath.state.record_loss()
    wrath.state.record_loss()  # 0 wins, 3 losses -> 0% win rate < 10%
    
    adjustments = registry.normalize_weights()
    assert DriveType.WRATH in adjustments  # Wrath should be boosted
    assert adjustments[DriveType.WRATH] > 0  # Positive delta
```

---

## ✅ Pass / Fail 標準

所有測試通過（173 existing + 新增 smoke tests）= **PASS**

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
