# Workflow: Decision Flow & Terminal Integration

This document defines how tasks flow through the 7Sins system, from input to execution, and how the system integrates with PowerShell and WSL environments.

---

## 1. Decision Workflow

### 1.1 Full Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      TASK INPUT                                  │
│   "Fix authentication bug in production"                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EGO-CORE: PARSING                            │
│   - Extract task type: bug, error, debug                        │
│   - Identify constraints: no break existing features            │
│   - Determine relevant drives                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 EGO-CORE: CONSULTATION                           │
│   Activate relevant Sins based on task type:                     │
│   → Wrath (weight: 0.8, confidence: 0.95)                        │
│   → Pride (weight: 0.6, confidence: 0.7)                         │
│   → Sloth (weight: 0.4, confidence: 0.5)                         │
│   → Others suppressed                                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EGO-CORE: DEBATE (MAGI)                        │
│   Round 1: Opening positions                                     │
│   → Wrath: "Fix immediately, zero tolerance"                     │
│   → Pride: "Fix properly with tests"                            │
│   → Sloth: "Create regression test first"                       │
│                                                                 │
│   Round 2: Challenge/response                                    │
│   → Wrath vs Pride: Speed vs Quality                            │
│                                                                 │
│   Round 3: Vote registration                                     │
│   → Wrath: 0.95 × 0.8 = 0.76                                    │
│   → Pride: 0.70 × 0.6 = 0.42                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EGO-CORE: RESOLUTION                            │
│   Winner: Wrath (0.76 > 0.42)                                    │
│   Decision: "Immediate hotfix with expedited review"            │
│   Confidence: 0.85                                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SUPEREGO: CONSTRAINT CHECK                      │
│   ✓ No destructive commands without backup                     │
│   ✓ Quality gates active                                        │
│   ✓ Human override available                                    │
│   → Proceed to execution                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION (Terminal)                         │
│   PowerShell: git stash && git checkout hotfix/                 │
│   WSL: ./scripts/deploy.sh --hotfix                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  REFLECTION: LEARNING                            │
│   Record decision to history                                     │
│   Analyze outcome                                                │
│   Adjust weights if needed                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Task Types & Drive Activation

### 2.1 Task Type Mapping

| Task Type | Primary Drive | Secondary Drives | Suppressed |
|-----------|---------------|------------------|------------|
| `bug` `fix` `error` | Wrath | Pride, Sloth | Greed, Envy |
| `feature` `user` `growth` | Greed | Pride, Gluttony | Wrath, Sloth |
| `research` `analyze` `architecture` | Gluttony | Pride, Lust | Wrath, Greed |
| `refactor` `automation` `tool` | Sloth | Pride, Lust | Wrath, Envy |
| `review` `quality` `standard` | Pride | Gluttony, Envy | Sloth, Greed |
| `benchmark` `compare` `competitor` | Envy | Gluttony, Pride | Sloth, Lust |
| `control` `priority` `system` | Lust | Pride, Greed | Sloth, Envy |

### 2.2 Drive Weight Calculation

```
Effective Influence = Base Weight × Context Modifier × Task Match Score

Example:
Task: "Fix critical production bug"
Wrath base_weight = 0.8
Context modifier (error keywords) = 1.2
Task match (bug keywords) = 0.95

Effective influence = 0.8 × 1.2 × 0.95 = 0.912
```

---

## 3. Terminal Integration

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    7Sins System                            │
│                                                             │
│   ┌─────────────┐      ┌─────────────────┐                 │
│   │   EGO-CORE  │─────→│ TerminalExecutor │                 │
│   │  (Decision) │      └────────┬──────────┘                 │
│   └─────────────┘               │                           │
│                                ▼                           │
│                    ┌───────────────────────┐               │
│                    │  SafeExecutor Wrapper │               │
│                    └───────────┬───────────┘               │
│                                │                           │
│         ┌──────────────────────┼──────────────────────┐    │
│         ▼                      ▼                      ▼    │
│   ┌────────────┐       ┌────────────┐        ┌──────────┐ │
│   │ PowerShell │       │  WSL Bash  │        │   CMD    │ │
│   └────────────┘       └────────────┘        └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Command Execution

```python
class TerminalExecutor:
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        # For WSL
        if self.terminal_type == TerminalType.WSL_BASH:
            result = subprocess.run(["wsl", "bash", "-c", command], ...)
        
        # For PowerShell
        elif self.terminal_type == TerminalType.POWERSHELL:
            result = subprocess.run(["powershell", "-Command", command], ...)
```

### 3.3 Safety Constraints

The Superego layer enforces these safety rules:

| Command Pattern | Action | Reason |
|-----------------|--------|--------|
| `rm -rf /` | BLOCKED | Destructive |
| `format` | BLOCKED | Data loss |
| `del /f /s` | BLOCKED | Windows destructive |
| `shutdown` | BLOCKED | System change |
| `git push --force` | WARN + LOG | History destruction |
| `del` without confirmation | WARN | Potential data loss |

### 3.4 WSL Integration

```powershell
# Check WSL availability
wsl --status

# Run bash command through WSL
wsl bash -c "cd ~/projects && ./deploy.sh"

# Access Windows files from WSL
cd /mnt/c/Users/enoma/Desktop/7
```

---

## 4. Human-in-the-Loop

### 4.1 Escalation Triggers

| Condition | Action |
|-----------|--------|
| Drive weight > 0.95 (over-dominant) | Human notification |
| Same conflict 3+ times | Human mediation |
| Execution involves destructive commands | Human approval |
| Decision confidence < 0.5 | Human review |
| System failure after decision | Human intervention |

### 4.2 Approval Flow

```
Decision Made → Check Escalation Triggers →
  If triggered: "Awaiting human approval..."
  If not: Execute immediately

Human Response:
  - "approve" → Execute
  - "reject" → Log and abort
  - "modify" → Adjust and re-evaluate
```

---

## 5. Workflow Configuration

### 5.1 config/workflow.yaml

```yaml
workflow:
  max_debate_rounds: 3
  confidence_threshold: 0.6
  human_override_weight: 1.5  # Human decision always wins
  
  terminal:
    default: powershell
    timeout_seconds: 30
    safe_mode: true
    
  escalation:
    dominant_drive_threshold: 0.95
    repeated_conflict_limit: 3
    low_confidence_threshold: 0.5
    
  reflection:
    auto_enabled: true
    daily_review_time: "08:00"
    bias_detection_threshold: 0.6
```

---

## 6. CLI Commands

### 6.1 Status Command

```bash
python -m 7Sins.src.cli status

# Output:
# === 7Sins Drive Status ===
#   GLUTTONY    [██████░░░░] 0.70
#   LUST        [█████░░░░░] 0.60
#   GREED       [████████░░] 0.80
#   SLOTH       [███████░░░] 0.70
#   PRIDE       [█████░░░░░] 0.60
#   WRATH       [████████░░] 0.80
#   ENVY        [████░░░░░░] 0.50
#
# === Recent Reflection ===
# Dominant drive: Wrath (45% of last 20 decisions)
# No significant biases detected
```

### 6.2 Task Command

```bash
python -m 7Sins.src.cli task "Analyze App Alpha 2-3 star reviews" "market"

# Output:
# === 7Sins Decision ===
# Task: Analyze App Alpha 2-3 star reviews
# Recommendation: Deploy Gluttony for market research, 
#                Greed for value gap analysis
# Confidence: 0.78
# Winner: (DriveType.GREED, 0.80)
```

### 6.3 Exec Command

```bash
# PowerShell
python -m 7Sins.src.cli exec "Get-Process | Select-Object Name, CPU"

# WSL
python -m 7Sins.src.cli exec "htop" --wsl
```

---

## 7. Error Handling

### 7.1 Error Types & Recovery

| Error | Recovery Action |
|-------|-----------------|
| Terminal timeout | Retry with longer timeout, log warning |
| Command not found | Suggest alternative, log to reflection |
| Permission denied | Request elevation, log security event |
| WSL not available | Fallback to PowerShell, notify user |
| Drive conflict deadlock | EGO-CORE forced decision, log conflict |

---

## Related Documents

- [AGENTS.md](AGENTS.md) — Agent specifications
- [CORE_LOGIC.md](CORE_LOGIC.md) — Architecture foundation
- [DEFENSE.md](DEFENSE.md) — Safety and protection mechanisms