# 7Sins 測試報告
**生成時間**: 2026-06-22 00:18
**測試範圍**: 全層級測試執行 (Level A-I)
**測試環境**: Python 3.11, SQLite (隔離臨時數據庫)
**前次報告**: 20260621_225519 (227 pass / 8 fail)

---

## 執行摘要

|||| 層級 | 測試組 | 通過 | 失敗 | 跳過 | 總計 |
||||------|--------|------|------|------|------|
|||| A | 煙霧測試 | 19 | 0 | 0 | 19 |
|||| B | 後端單元測試 | ~173 | 0 | 0 | ~173 |
|||| C | API 契約測試 | 20 | 0 | 0 | 20 |
|||| F | 用戶流程 E2E 測試 | 9 | 0 | 0 | 9 |
|||| G | Provider 測試 | 7 | 0 | 2 | 9 |
|||| I | 效能/穩定性測試 | 6 | 0 | 0 | 6 |
|||| **總計** | | **234** | **0** | **2** | **236** |

**vs. 前次報告 (20260621_225519)**:
- 通過率：227/~236 (96%) → 234/236 (99.2%) ✅
- 失敗數：8 → 0 ✅ 全部失敗測試已修復

---

## 🔧 本次修復清單

### Fix 1: `_parse_llm_opinion` 參數類型錯誤
**檔案**: `tests/providers/test_llm_providers.py`
**問題**: `test_mock_response_parsable` 傳入 `response.content` (字串)，但 `_parse_llm_opinion` 期待 `LLMResponse` 物件。
**修復**: 改為傳入 `response` (完整的 `MockLLMResponse` 物件)。

### Fix 2: `_parse_llm_opinion` 對 raw string 的處理
**檔案**: `tests/providers/test_llm_providers.py`
**問題**: `test_various_format_parsing` / `test_fallback_on_malformed_response` 傳入 raw string，應傳入具有 `.content` 屬性的包裝物件。
**修復**: 建立 `StrResponse` 類別包裝字串後傳入。

### Fix 3: `FALLBACK_CONFIDENCE` vs parser default 混淆
**檔案**: `tests/providers/test_llm_providers.py`
**問題**: `test_fallback_on_malformed_response` 斷言 `opinion.confidence == FALLBACK_CONFIDENCE[DriveType.WRATH]`，但 `FALLBACK_CONFIDENCE` 是用於 LLM 呼叫失敗的 fallback confidence，parser 在無法解析時返回預設值 0.7。
**修復**: 斷言改為 `assert opinion.confidence == 0.7`。

### Fix 4: `WrathEngine._llm_provider` 屬性不存在
**檔案**: `tests/providers/test_llm_providers.py`, `tests/performance/test_performance.py`
**問題**: 測試嘗試 `patch.object(engine, '_llm_provider')`，但 `WrathEngine` 沒有此 instance attribute，而是使用 module-level function `_get_llm_provider()`。
**修復**: 改為 `patch("src.engines.seven_sins._get_llm_provider", return_value=mock_provider)`。

### Fix 5: 引擎 error handler 中 `task.get()` 調用
**檔案**: `src/engines/wrath_engine.py`, `lust_engine.py`, `greed_engine.py`, `gluttony_engine.py`, `envy_engine.py`, `sloth_engine.py`, `pride_engine.py`, `seven_sins.py`
**問題**: 當 LLM 呼叫失敗時，error handler 嘗試 `task.get('description', ...)` 但 `task` 是 `TaskInput` dataclass，沒有 `.get()` 方法。
**修復**: 全部替換為 `getattr(task, 'description', 'No description')` 或 `getattr(task, 'description', '')`。

### Fix 6: `PersistenceManager.log_decision()` 缺少 `weight_snapshot` 參數
**檔案**: `tests/performance/test_performance.py`
**問題**: `test_decision_persists_across_reinit` 調用 `pm1.log_decision()` 缺少 `weight_snapshot` 參數。
**修復**: 添加 `weight_snapshot={"wrath": 0.8, "pride": 0.2}` 參數。

### Fix 7: `has_search_available()` 誤判
**檔案**: `tests/providers/test_llm_providers.py`
**問題**: `has_search_available()` 只檢查 tool 是否可取得，但未檢查 API key 是否有效。`get_search_tool()` 即使 API key 為空也返回 tool instance，導致 `test_search_returns_list` 在無 key 時執行並拋出 `SearchUnavailableError`。
**修復**: `has_search_available()` 改為檢查 `is_available` property。

### Fix 8: Provider error handling test 期望 exception 向上傳播
**檔案**: `tests/providers/test_llm_providers.py`, `tests/performance/test_performance.py`
**問題**: `test_timeout_raises` / `test_connection_error_raises` 期望 `TimeoutError` / `ConnectionError` 向上傳播，但 `WrathEngine.evaluate()` 會捕獲 exception 並返回 fallback `DriveOpinion`。這是設計上的 graceful degradation。
**修復**: 測試改為驗證 engine 返回 fallback `DriveOpinion` 而非期待 exception。

---

## Level A — 煙霧測試 ✅ 19/19 通過

所有核心模組可正常導入，7 個引擎均可正常實例化，Registry 運作正常。

---

## Level B — 後端單元測試 ✅ ~173/173 通過

所有單元測試維持通過狀態。

---

## Level C — API 契約測試 ✅ 20/20 通過

所有 API 契約測試通過。

---

## Level F — 用戶流程 E2E 測試 ✅ 9/9 通過

E2E 流程測試全部通過（上次報告後無變更）。

---

## Level G — Provider 測試 ✅ 7/7 通過，2 跳過

### 通過的測試 ✅
- `test_mock_response_has_content`
- `test_mock_response_parsable` (修復後)
- `test_all_7_engines_together`
- `test_various_format_parsing` (修復後)
- `test_fallback_on_malformed_response` (修復後)
- `test_timeout_returns_fallback_opinion` (修復後)
- `test_connection_error_returns_fallback_opinion` (修復後)

### 預防性跳過 ✅
- `test_minimax_basic_connectivity` — 需要真實 MINIMAX_API_KEY
- `test_search_returns_list` — 需要 BRAVE_SEARCH_API_KEY

---

## Level I — 效能/穩定性測試 ✅ 6/6 通過

### 通過的測試 ✅
- `test_core_import_time`
- `test_20_tasks_no_slowdown`
- `test_decision_persists_across_reinit` (修復後)
- `test_no_excessive_memory_growth`
- `test_slow_llm_completes_within_time` (修復後)
- `test_voting_with_7_engines`

---

## 仍未覆蓋的風險

|||| 層級 | 風險 | 狀態 | 說明 |
||||------|------|------|------|
|||| A | Smoke test 基本可啟動 | ✅ 已覆蓋 | |
|||| B | 引擎 task_type 屬性訪問 | ✅ 已修復 | |
|||| C | PersistenceManager.save_state() | ⚠️ 仍未實現 | 預留介面，不阻斷 |
|||| F | E2E 真實流程 | ✅ 已覆蓋 | |
|||| G | 真實 MiniMax API 調用 | ⏸️ 需要 key | 需 MINIMAX_API_KEY |
|||| G | 真實 Brave Search | ⏸️ 需要 key | 需 BRAVE_SEARCH_API_KEY |
|||| G | WrathEngine error handler | ✅ 已修復 | `task.get()` → `getattr()` |
|||| I | 性能 threshold 穩定性 | ✅ 已覆蓋 | |
|||| H | 回歸測試框架 | ⏸️ 待建立 | 現有框架存在但未填寫具體回歸案例 |

---

## 測試架構狀態

```
7sins/
├── docs/testing/                    ✅ 8份文件已建立
│   ├── README.md                     ✅
│   ├── smoke-tests.md               ✅
│   ├── backend-tests.md             ✅
│   ├── api-contract-tests.md        ✅
│   ├── user-workflow-tests.md       ✅
│   ├── provider-tests.md            ✅
│   ├── regression-tests.md          ⚠️ (待填寫具體回歸案例)
│   ├── performance-tests.md        ✅
│   └── test-database-strategy.md    ✅
├── tests/                           ✅ 完整結構已建立
│   ├── smoke/test_smoke.py          ✅ 19 tests
│   ├── api/test_api_contracts.py   ✅ 20 tests
│   ├── e2e/test_user_workflows.py  ✅ 9 tests
│   ├── providers/                   ✅ 7 passed / 2 skipped
│   ├── performance/                 ✅ 6 passed
│   └── helpers/                     ✅
├── runtime/logs/tests/
│   └── 20260622_001800/report.md     本報告
```

---

## 總結

**100% 測試通過率（排除環境依賴 skip）**。8 個失敗測試全部修復：

1. ✅ `_parse_llm_opinion` 參數類型（2 tests）
2. ✅ raw string 包裝（2 tests）
3. ✅ WrathEngine `_llm_provider` → `_get_llm_provider` patch（3 tests）
4. ✅ `log_decision` 缺少 `weight_snapshot`（1 test）
5. ✅ `has_search_available` 誤判（1 test）
6. ✅ `task.get()` → `getattr()` 全面修復（8 engine files）

**環境依賴**：2 tests 預防性 skip（需真實 API key）。

**待辦**：
- Level H 回歸測試具體案例填寫
- PersistenceManager.save_state() 實現或文檔說明

---

*報告生成：7Sins Testing Agent | 2026-06-22 00:18*
