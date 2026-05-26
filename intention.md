# 7Sins Project Intention

## 用戶目標
完成 7Sins 框架，使其成為真正可用的 Self-Driven AI Agent。

## 核心需求
1. **LLM 整合** — 7 個 Sin Engine 需要 LLM 進行 actual reasoning
2. **Web Search 能力** — 令 Agent 多啲上網搵料（Gluttony 作為牽頭引擎）
3. **Benchmark 分析** — Envy 引擎需要搜索競品最佳實踐
4. **真正嘅驅動決策** —唔係 static rule，而係 LLM-powered 推理

## 缺失組件 (TODO Priority)

### P0 - 核心缺失
1. **LLM Provider 整合**
   - 支援 OpenAI / Anthropic / Local LLM
   - 統一接口，可配置

2. **Web Search 集成**
   - 為 Gluttony 提供實際 research 能力
   - Brave Search / SerpAPI / Tavily 等等

3. **實際 Drive Engine 實現**
   - 當前只有 abstract configs，需要 LLM-powered evaluate()
   - 每個 Sin 要能夠調用 LLM 进行推理

### P1 - 功能完善
4. **Eros/Thanatos 基礎驅動**
   - 實現 Life Drive / Death Drive
   - 與 7 Sins 互動

5. **Superego 約束執行**
   - 實現 Safety checks
   - Quality gates

6. **持久化記憶**
   - Decision history
   - Drive weight evolution
   - Self-growth log

### P2 - 測試驗證
7. **整合測試**
   - 端到端測試案例演示
   - 各 Engine 工作正常
   
8. **文檔完成**
   - Quick start guide
   - API reference

##技術方向的共識
- 語言: Python 3.10+
- LLM: 可配置 (MiniMax/M2.7 API default)
- Web Search: Brave Search API (free tier)
- 持久化: SQLite
- Terminal集成: WSL/PowerShell

## 成功標準
- Agent 能夠獨立執行 research 任務（使用 web search）
- EGO-CORE 能夠根據 Sin 驅動做決策
- Drive weights 能夠根據 outcomes 調整

---
*Created: 2026-05-26*
*Foundation: SPEC.md + 7Sins docs*
