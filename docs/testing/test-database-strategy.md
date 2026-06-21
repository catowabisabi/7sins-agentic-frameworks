# 7Sins 測試資料庫策略

> 繁體中文 | 版本: 1.0.0 | 建立日期: 2026-06-21

---

## 🎯 目標

確保測試使用的資料庫完全隔離，不可污染正式或開發中的資料庫。

---

## 📍 現有資料庫位置

| DB 名稱 | 路徑 | 用途 |
|---------|------|------|
| `persistence.db` | `7Sins_manager_state/persistence.db` | 決策日誌、Drive Weight 演化 |
| `manager.db` | `7Sins_manager_state/manager.db` | Manager 狀態 |

---

## 🛡️ 隔離策略

### 原則

1. **測試決不使用正式 DB path** — 所有測試使用 `tempfile.mkdtemp()` 建立獨立目錄
2. **使用 `:memory:` SQLite** — 單執行緒記憶體資料庫，測試完成後自動釋放
3. **隔離 fixture** — 每個 test function 獲得乾淨的 DB state
4. **失敗保留 snapshot** — 測試失敗時，DB path 輸出到 report

### 實現方式

```python
# tests/helpers/db_isolation.py
import tempfile
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator, Tuple

@contextmanager
def isolated_test_db() -> Generator[Tuple[str, sqlite3.Connection], None, None]:
    """
    Creates an isolated temporary SQLite database for each test.
    
    Yields:
        Tuple of (db_path, connection)
    
    On test failure:
        - db_path is preserved in test artifacts
        - connection is NOT closed to allow inspection
    
    On test success:
        - connection is closed
        - temp directory is cleaned up
    """
    temp_dir = tempfile.mkdtemp(prefix="7sins_test_db_")
    db_path = os.path.join(temp_dir, "test_isolated.db")
    
    conn = sqlite3.connect(db_path)
    
    # Initialize schema (same as production)
    _init_test_schema(conn)
    
    try:
        yield db_path, conn
    except Exception:
        # On failure, preserve the DB for inspection
        print(f"TEST DB PRESERVED AT: {db_path}")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass  # Already closed or broken


def _init_test_schema(conn: sqlite3.Connection):
    """Initialize test DB with same schema as production."""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_description TEXT,
            winning_drive TEXT,
            confidence REAL,
            eros_weight REAL,
            thanatos_weight REAL,
            weight_snapshot TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            drive_name TEXT NOT NULL,
            new_weight REAL NOT NULL,
            delta REAL NOT NULL
        )
    """)
    
    conn.commit()
```

---

## 🔧 Patch 策略（測試時）

### 方式 1：Monkey-patch `PersistenceManager._db_path`

```python
import tests.helpers.db_isolation as db_iso
from src.memory.persistence import PersistenceManager

def test_decision_logging(tmp_path):
    """Test that decisions are logged to isolated DB."""
    test_db = tmp_path / "test.db"
    
    # Patch the singleton's db path
    original_path = PersistenceManager._db_path
    PersistenceManager._db_path = str(test_db)
    
    # Reset singleton for test
    PersistenceManager._instance = None
    
    try:
        pm = PersistenceManager()
        # ... run test ...
    finally:
        PersistenceManager._db_path = original_path
        PersistenceManager._instance = None
```

### 方式 2：Environment Variable Override

```python
# 在 conftest.py 中
import os
import tempfile

@pytest.fixture(scope="session", autouse=True)
def isolate_persistence_for_tests():
    """Session-level: redirect all DB operations to temp location."""
    temp_dir = tempfile.mkdtemp(prefix="7sins_test_session_")
    os.environ["7SINS_TEST_DB_DIR"] = temp_dir
    yield
    # Cleanup after all tests
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
```

---

## 📊 測試 DB Schema 版本追蹤

每個測試報告需記錄：

```json
{
  "test_db": {
    "path": "/tmp/7sins_test_db_xxx/test_isolated.db",
    "schema_version": "1.0.0",
    "tables": {
      "decision_log": { "row_count": 0 },
      "weight_history": { "row_count": 0 }
    }
  }
}
```

---

## ✅ 測試前 / 測試後檢查清單

### 測試前
- [ ] DB path 已設為 temp location
- [ ] Schema migration 已執行
- [ ] 無殘留數據

### 測試後
- [ ] decision_log table 有正確行數
- [ ] weight_history table 有記錄（如有 weight change）
- [ ] 如失敗，DB snapshot 已保存

---

## 🚨 禁止事項

1. ❌ 不可直接使用 `7Sins_manager_state/persistence.db`
2. ❌ 不可假設 DB 為 `:memory:` 而不清理連接
3. ❌ 不可在多個 test function 間共享同一個 DB connection（SQLite 單執行緒）
4. ❌ 不可在 fixture 中 commit 並期望其他 test 可見

---

## 📝 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-21 | 1.0.0 | 初始建立 |

*最後更新: 2026-06-21*
