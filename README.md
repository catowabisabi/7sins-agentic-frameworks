# 7Sins Project: The Self-Driven AI Harness

> "Traditional AI is a passive tool. 7Sins Project is a framework with an 'inner drive'."

## Project Philosophy

The 7Sins Project transforms AI from a reactive tool into a proactive collaborator. We believe the **Seven Deadly Sins** are not negative traits but **high-performance psychological engines** that have driven human engineers to excel. These drives —傲慢 (Pride), 憤怒 (Wrath), 嫉妒 (Envy), 懶惰 (Sloth), 貪婪 (Greed), 色慾 (Lust), 暴食 (Gluttony) — are recast as the core motivational architecture powering autonomous development.

## Why "7 Sins"?

Human engineers don't just follow instructions — they are driven by internal forces:
- **Pride** demands elegant code, not just functional code
- **Wrath** refuses to tolerate bugs or system failures
- **Greed** seeks market value and user impact
- **Sloth** automates repetitive tasks to eliminate tedium
- **Lust** demands control and order over complex systems
- **Gluttony** consumes knowledge to stay ahead
- **Envy** benchmarks against the best to find gaps

These drives, properly channeled, create a self-motivated developer that doesn't just execute tasks — it **seeks** problems to solve and improvements to make.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPEREGO LAYER                         │
│          Governance: Safety, Constraints, Ethics           │
├─────────────────────────────────────────────────────────────┤
│                        EGO LAYER                            │
│       Decision: Balance Drives vs Reality Constraints       │
├─────────────────────────────────────────────────────────────┤
│                         ID LAYER                            │
│           Seven Sins: Raw Motivational Energy               │
└─────────────────────────────────────────────────────────────┘
```

### Id Layer (The Drives)
The **Id** represents raw motivational energy — the Seven Sins as independent agents:
- Each Sin has a **Drive Weight** (0.0-1.0) reflecting current intensity
- Drive weights dynamically adjust based on outcomes and context
- Sins compete for influence through the **MAGI-style voting mechanism**

### Ego Layer (The Decision Maker)
The **Ego** is the central coordinator (EGO-CORE):
- Receives task input and activates relevant Sins
- Mediates debates between competing drives
- Selects final action based on weighted voting
- Maintains decision history for reflection

### Superego Layer (The Guardian)
The **Superego** ensures responsible operation:
- Hard limits on destructive operations
- Ethics guardrails and best practices
- Human override capability
- Audit logging for decisions

## The MAGI System

Inspired by Neon Genesis Evangelion's MAGI supercomputer, 7Sins implements a **multi-personalty voting system** where each Sin contributes to decisions:

```
Melchior (Gluttony)   → Scientific analysis, research depth
Balthasar (Greed)     → Market value, user impact
Casper (Pride)        → Code aesthetics, quality standards
```

Final decisions emerge from the **debate and vote** between personalities, weighted by each Sin's current drive strength.

## Key Features

| Feature | Description |
|---------|-------------|
| **Self-Driven** | Not just reactive — actively seeks improvements |
| **Dynamic Weights** | Drive intensity adjusts based on success/failure |
| **Multi-Agent Debate** | Decisions emerge from personality conflict |
| **Self-Reflection** | Analyzes own decisions and adjusts behavior |
| **Terminal Integration** | Executes via PowerShell/WSL/bash |
| **Human-in-the-Loop** | Final approval on critical decisions |

## Project Structure

```
7Sins/
├── README.md              # This file - Project Constitution
├── docs/
│   ├── CORE_LOGIC.md      # Id-Ego-Superego architecture
│   ├── AGENTS.md          # 7 Sin agents detailed specs
│   ├── WORKFLOW.md        # Decision flow & integration
│   ├── DRIVES.md          # Life Drive (Eros) & Death Drive (Thanatos)
│   └── DEFENSE.md         # Self-protection mechanisms
├── scripts/
│   └── ego_core.ps1       # CLI launcher & agent scheduler
├── src/
│   └── 7Sins/             # Python implementation
└── tests/
```

## Quick Start

```powershell
# View system status
python -m 7Sins.src.cli status

# Run a task through 7Sins decision
python -m 7Sins.src.cli task "Fix authentication bug" "debug"

# Execute via WSL
python -m 7Sins.src.cli exec "git status" --wsl
```

## Design Principles

1. **Drives are Energy, Not Morality** — The Sins represent motivational vectors, not ethical judgments
2. **Debate Creates Better Decisions** — Conflict between personalities produces nuanced choices
3. **Self-Growth is Mandatory** — Reflection and weight adjustment happen after every task
4. **Human Override is Sacred** — No critical decision without human approval
5. **Transparent Logic** — Every decision can be traced to its driving Sin

## Development Status

- [x] Core architecture (Tri-Layer)
- [x] 7 Sin engine implementations
- [x] EGO-Core decision layer
- [x] Self-growth reflective loop
- [x] WSL/PowerShell terminal integration
- [x] CLI interface
- [ ] LLM integration for actual reasoning
- [ ] Persistent memory across sessions
- [ ] Full MAGI-style debate visualization

## References

- Freud's Id-Ego-Superego model
- Neon Genesis Evangelion MAGI system
- Seven Deadly Sins as motivational theory
- Agentic AI frameworks (LangChain, AutoGPT)

---

*"The goal is not to overcome our nature, but to harness it."*

For architecture details, see [docs/CORE_LOGIC.md](docs/CORE_LOGIC.md)
For agent specifications, see [docs/AGENTS.md](docs/AGENTS.md)