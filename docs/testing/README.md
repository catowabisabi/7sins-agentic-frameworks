# 7Sins 測試體系總覽

> 繁體中文 | 測試架構版本: 1.0.0 | 建立日期: 2026-06-21

---

## 📋 概述

本項目為純 Python 後端專案（無 HTTP API Server、無 Frontend），測試體系專為以下特性設計：
- Python 庫 / CLI 工具
- SQLite 持久化
- LLM Provider 整合（七個 Sin Engine）
- 決策引擎 + 辯論機制

---

## 🗂️ 測試層級索引

| 層級 | 名稱 | 文件 | 位置 |
|------|------|------|------|
| **A** | 煙霧測試 (Smoke Tests) | [smoke-tests.md](smoke-tests.md) | `tests/smoke/` |
| **B** | 後端單元測試 (Backend Unit Tests) | [backend-tests.md](backend-tests.md) | `tests/` (現有) |
| **C** | API 合約測試 (API Contract Tests) | [api-contract-tests.md](api-contract-tests.md) | `tests/api/` |
| **D** | Mock 測試 | N/A | 無 Frontend |
| **E** | 前端非 Mock 測試 | N/A | 無 Frontend |
| **F** | 用戶流程 E2E 測試 | [user-workflow-tests.md](user-workflow-tests.md) | `tests/e2e/` |
| **G** | 外部 Provider 測試 | [provider-tests.md](provider-tests.md) | `tests/providers/` |
| **H** | 回歸測試 | [regression-tests.md](regression-tests.md) | `tests/regression/` |
| **I** | 效能/穩定性測試 | [performance-tests.md](performance-tests.md) | `tests/performance/` |
| **J** | 無障礙/UX 測試 | N/A | 無 UI |

---

## 📁 目錄結構

```
7sins/
├── docs/testing/                    # 測試文件
│   ├── README.md                    # 本文件
│   ├── smoke-tests.md               # 煙霧測試
│   ├── backend-tests.md             # 後端單元測試
│   ├── api-contract-tests.md        # API 合約測試
│   ├── user-workflow-tests.md       # 用戶流程 E2E
│   ├── provider-tests.md            # 外部 Provider 測試
│   ├── regression-tests.md          # 回歸測試
│   ├── performance-tests.md         # 效能測試
│   └── test-database-strategy.md    # 測試 DB 策略
├── tests/                          # 測試代碼
│   ├── conftest.py                 # Pytest fixtures + sys.path
│   ├── smoke/                      # 煙霧測試
│   │   └── run_smoke_tests.py
│   ├── api/                        # API 合約測試
│   │   └── test_api_contracts.py
│   ├── e2e/                        # E2E 流程測試
│   │   └── test_user_workflows.py
│   ├── providers/                  # Provider 測試
│   │   └── test_llm_providers.py
│   ├── regression/                 # 回歸測試
│   │   └── test_regression_*.py
│   ├── performance/                # 效能測試
│   │   └── test_performance_*.py
│   ├── helpers/                    # 測試輔助工具
│   │   ├── db_isolation.py
│   │   └── mock_providers.py
│   └── (existing tests/)           # 現有 173 個測試
├── runtime/logs/tests/             # 測試報告輸出
│   └── <timestamp>/
│       ├── report.md               # 本次測試報告
│       ├── console.log
│       ├── pytest.log
│       ├── db-before.json
│       ├── db-after.json
│       └── artifacts/
└── scripts/
    └── run_all_tests.sh            # 總測試入口腳本
```

---

## 🚀 快速開始

### 執行所有測試
```bash
cd /mnt/c/Users/enoma/Desktop/opencode-work/agent-works/research/7sins
bash scripts/run_all_tests.sh
```

### 執行特定層級
```bash
# 煙霧測試
python -m pytest tests/smoke/ -v

# 後端單元測試
python -m pytest tests/ -v --ignore=tests/smoke --ignore=tests/e2e

# Provider 測試
python -m pytest tests/providers/ -v

# 效能測試
python -m pytest tests/performance/ -v
```

---

## 📊 現有測試覆蓋

| 測試類別 | 檔案 | 數量 |
|----------|------|------|
| EGO-Core 單元測試 | `tests/test_ego_core.py` | ~41 |
| Veto 機制測試 | `tests/test_ego_core_veto.py` | ~9 |
| Multi-Engine Veto 測試 | `tests/test_multi_engine_veto.py` | ~7 |
| Seven Sins 引擎測試 | `tests/test_seven_sins.py` | ~50 |
| Integration 測試 | `tests/test_integration.py` | ~25 |
| Envy/Gluttony Helper 測試 | `tests/test_envy_gluttony_helpers.py` | ~16 |
| Reflection Edge Cases | `tests/test_reflection_edge_cases.py` | ~10 |
| **總計** | | **173** |

---

## 🔴 未覆蓋風險

1. **真實 LLM Provider 呼叫** — 現有測試全部使用 Mock，未覆蓋實際 MiniMax API
2. **並發決策競爭條件** — 多執行緒同時調用 `process_task` 未測試
3. **Persistence Manager 狀態一致性** — SQLite 並發寫入未測試
4. **Search Tool 真實整合** — 僅 Mock，未測試真實搜索（需要 BRAVE_SEARCH_API_KEY）
5. **LLM 回應格式漂移** — `_parse_llm_opinion` 解析失敗未測試
6. **磁碟寫滿 / 權限錯誤** — Audit log / persistence 無磁碟空間測試
7. **EGO-Core 辯論循環** — 3 輪辯論共識失敗邊界未測試

## 🟢 測試覆蓋狀態（2026-06-30 14:08 HKT）

| 層級 | 測試數 | 通過 | 失敗 | 跳過 | 狀態 |
|------|--------|------|------|------|------|
| A 煙霧測試 | 19 | 19 | 0 | 0 | ✅ |
| B 後端單元 | ~173 | ~173 | 0 | 0 | ✅ |
| C API 合約 | 20 | 20 | 0 | 0 | ✅ |
| F 用戶流程 E2E | 10 | 10 | 0 | 0 | ✅ |
| G Provider | 9 | 7 | 0 | 2 | ✅ |
| H 回歸測試 | 13 | 13 | 0 | 0 | ✅ |
| I 效能/穩定 | 6 | 6 | 0 | 0 | ✅ |
| **總計** | **250** | **248** | **0** | **2** | **99.2%** |

**被動喚醒（2026-06-26 02:05 UTC）**：
- ✅ 代碼無實質變更（僅 diary + manager state commit，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 70+ 小時）

**被動喚醒（2026-06-30 14:08 HKT / 06:08 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 230+ 小時）

**被動喚醒（2026-06-30 12:20 HKT / 04:20 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 226+ 小時）

**被動喚醒（2026-06-30 10:14 HKT / 02:14 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 218+ 小時）

**被動喚醒（2026-06-30 08:08 HKT / 00:08 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 214+ 小時）

**被動喚醒（2026-06-30 06:04 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 210+ 小時）

**被動喚醒（2026-06-30 04:07 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 206+ 小時）

**被動喚醒（2026-06-30 02:04 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 204+ 小時）

**被動喚醒（2026-06-29 18:03 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 186+ 小時）

**被動喚醒（2026-06-29 16:05 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 184+ 小時）

**被動喚醒（2026-06-29 14:05 UTC）**：
- ✅ 代碼無實質變更（僅 diary commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 182+ 小時）

**被動喚醒（2026-06-26 08:17 UTC）**：
- ✅ 代碼無實質變更（僅 diary/design review commits，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 76+ 小時）

**被動喚醒（2026-06-26 04:05 UTC）**：
- ✅ 代碼無實質變更（僅 diary commit，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 68+ 小時）

**被動喚醒（2026-06-25 18:13 UTC）**：
- ✅ 代碼無實質變更（僅 diary commit，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 52+ 小時）

**被動喚醒（2026-06-25 16:05 UTC）**：
- ✅ 代碼無實質變更（僅 diary + docs commit，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 50+ 小時）

**被動喚醒（2026-06-25 14:08 UTC）**：
- ✅ 代碼無實質變更（僅 diary commit，無 src/ 變更）
- ✅ 248 tests pass，0 fail，2 skip — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 48+ 小時）

**被動喚醒（2026-06-25 04:13 UTC）**：
- ✅ 代碼無實質變更（僅 diary/manager state commit，無 src/ 變更）
- ✅ 248 tests pass，0 fail，2 skip — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 36+ 小時）

**被動喚醒（2026-06-25 02:13 UTC）**：
- ✅ 代碼無實質變更（僅 diary/manager state commit，無 src/ 變更）
- ✅ 248 tests pass，0 fail，2 skip — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 34+ 小時）

**被動喚醒（2026-06-25 00:07 UTC）**：
- ✅ 代碼無實質變更（僅 diary commit 2026-06-24，無 src/ 變更）
- ✅ 248 tests pass，0 fail，2 skip — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 32+ 小時）

**被動喚醒（2026-06-30 16:08 HKT / 08:08 UTC）**：
- ✅ 代碼無實質變更（僅 diary × 2，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 232+ 小時）

**被動喚醒（2026-06-30 18:05 HKT / 10:05 UTC）**：
- ✅ 代碼無實質變更（diary × 2，無 src/ 變更）
- ✅ 19/19 smoke PASS — 與上次報告完全一致
- ✅ 系統狀態：穩定，進入沉澱期（持續 234+ 小時）

---

## 📝 更新日誌

|| 日期 | 版本 | 變更 ||
||------|------|------||
|| 2026-06-30 | 1.35.0 | 被動喚醒（18:05 HKT / 10:05 UTC）：代碼無實質變更（diary × 2），19/19 smoke PASS — 沉澱期確認（持續 234+ 小時） |
|| 2026-06-30 | 1.34.0 | 被動喚醒（16:08 HKT / 08:08 UTC）：代碼無實質變更（diary × 2），19/19 smoke PASS — 沉澱期確認（持續 232+ 小時） |
| 2026-06-30 | 1.33.0 | 被動喚醒（14:08 HKT / 06:08 UTC）：代碼無實質變更（diary × 2），19/19 smoke PASS — 沉澱期確認（持續 230+ 小時） |
| 2026-06-30 | 1.32.0 | 被動喚醒（12:20 HKT / 04:20 UTC）：代碼無實質變更（diary × 2），19/19 smoke PASS — 沉澱期確認（持續 226+ 小時） |
| 2026-06-30 | 1.31.0 | 被動喚醒（10:14 HKT / 02:14 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 218+ 小時） |
| 2026-06-30 | 1.30.0 | 被動喚醒（08:08 HKT / 00:08 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 214+ 小時） |
| 2026-06-30 | 1.29.0 | 被動喚醒（04:03 HKT / 20:03 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 212+ 小時） |
| 2026-06-30 | 1.28.0 | 被動喚醒（06:04 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 210+ 小時） |
| 2026-06-30 | 1.27.0 | 被動喚醒（04:07 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 206+ 小時） |
| 2026-06-30 | 1.26.0 | 被動喚醒（02:04 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 204+ 小時） |
| 2026-06-29 | 1.25.0 | 被動喚醒（18:03 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 186+ 小時） |
| 2026-06-26 | 1.24.0 | 被動喚醒（08:17 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 76+ 小時） |
| 2026-06-26 | 1.23.0 | 被動喚醒（12:05 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 80+ 小時） |
| 2026-06-26 | 1.22.0 | 被動喚醒（04:09 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 68+ 小時） |
| 2026-06-25 | 1.21.0 | 被動喚醒（18:30 UTC）：代碼無實質變更（diary + 新增 drift-patterns 文檔），19/19 smoke PASS — 沉澱期確認（持續 56+ 小時） |
| 2026-06-25 | 1.20.0 | 被動喚醒（18:13 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 52+ 小時） |
| 2026-06-25 | 1.19.0 | 被動喚醒（16:05 UTC）：代碼無實質變更（diary + docs），19/19 smoke PASS — 沉澱期確認（持續 50+ 小時） |
| 2026-06-25 | 1.18.0 | 被動喚醒（14:08 UTC）：代碼無實質變更（diary only），248/250 pass，0 fail — 沉澱期確認（持續 48+ 小時） |
| 2026-06-25 | 1.17.0 | 被動喚醒（08:19 UTC）：代碼無實質變更（diary only），248/250 pass，0 fail — 沉澱期確認（持續 42+ 小時） |
| 2026-06-25 | 1.16.0 | 被動喚醒（06:09 UTC）：代碼無實質變更（diary only），248/250 pass，0 fail — 沉澱期確認（持續 38+ 小時） |
| 2026-06-25 | 1.15.0 | 被動喚醒（04:13 UTC）：代碼無實質變更（diary only），248/250 pass，0 fail — 沉澱期確認（持續 36+ 小時） |
| 2026-06-25 | 1.14.0 | 被動喚醒（02:13 UTC）：代碼無實質變更（diary/manager state only），248/250 pass，0 fail — 沉澱期確認（持續 34+ 小時） |
| 2026-06-25 | 1.13.0 | 被動喚醒（00:07 UTC）：代碼無實質變更（diary only），248/250 pass，0 fail — 沉澱期確認（持續 32+ 小時） |
| 2026-06-24 | 1.12.0 | 被動喚醒（16:04 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 28+ 小時） |
| 2026-06-24 | 1.11.0 | 被動喚醒（14:05 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 22+ 小時） |
| 2026-06-24 | 1.10.0 | 被動喚醒（12:15 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認（持續 22+ 小時） |
| 2026-06-24 | 1.9.0 | 被動喚醒（12:06 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認 |
| 2026-06-24 | 1.8.0 | 被動喚醒（06:12 UTC）：代碼無實質變更（diary only），19/19 smoke PASS — 沉澱期確認 |
| 2026-06-23 | 1.7.0 | 被動喚醒：代碼無實質變更，248/250 pass，0 fail — 沉澱期確認 |
| 2026-06-23 | 1.6.0 | 被動喚醒：代碼無實質變更，248/250 pass，0 fail — 沉澱期確認 |
| 2026-06-23 | 1.5.0 | 被動喚醒：代碼無實質變更，248/250 pass，0 fail — 沉澱期確認 |
| 2026-06-23 | 1.4.0 | 被動喚醒：代碼無實質變更，248/250 pass，0 fail — 沉澱期確認 |
| 2026-06-23 | 1.3.0 | 被動喚醒：代碼無實質變更，248/250 pass，0 fail — 沉澱期確認 |
| 2026-06-22 | 1.2.0 | 更新覆蓋數據：248 pass / 0 fail；#66/#68/#69 重構驗證通過 |
| 2026-06-22 | 1.1.0 | 更新覆蓋數據：248 pass / 0 fail；#64 fixes 驗證 |
| 2026-06-21 | 1.0.0 | 初始建立測試體系文件 |

---

*最後更新: 2026-06-30 18:05 HKT (10:05 UTC) — 7Sins Test Engineer*
