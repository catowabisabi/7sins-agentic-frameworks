<#
.SYNOPSIS
    7Sins Project - EGO-Core Launcher and Agent Scheduler

.DESCRIPTION
    PowerShell CLI tool for launching and managing the 7Sins self-driven agent system.
    Provides interface for task execution, status monitoring, and system control.

.NOTES
    Version: 1.0.0
    Author: 7Sins Project Team
    Purpose: Self-driven AI harness with psychological drive theory
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("status", "task", "exec", "init", "backup", "restore", "help")]
    [string]$Command = "help",
    
    [Parameter(Mandatory=$false)]
    [string]$TaskDescription = "",
    
    [Parameter(Mandatory=$false)]
    [string]$TaskType = "general",
    
    [Parameter(Mandatory=$false)]
    [switch]$UseWSL,
    
    [Parameter(Mandatory=$false)]
    [string]$BackupPath = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Configuration
$Script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$Script:SrcPath = Join-Path $Script:ProjectRoot "src"
$Script:ConfigPath = Join-Path $Script:ProjectRoot "config"
$Script:LogsPath = Join-Path $Script:ProjectRoot "logs"

# Colors for output
$Colors = @{
    "Header" = "Cyan"
    "Success" = "Green"
    "Warning" = "Yellow"
    "Error" = "Red"
    "Info" = "White"
    "DriveActive" = "Magenta"
    "DriveInactive" = "DarkGray"
}

function Write-7SinsOutput {
    param(
        [string]$Message,
        [string]$Color = "Info"
    )
    $host.UI.RawUI.ForegroundColor = $Colors[$Color]
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = "White"
}

function Show-Header {
    Write-7SinsOutput "========================================" "Header"
    Write-7SinsOutput "    7Sins Project - Self-Driven AI" "Header"
    Write-7SinsOutput "========================================" "Header"
    Write-Output ""
}

function Show-Help {
    Show-Header
    Write-7SinsOutput "USAGE:" "Header"
    Write-Output "  7Sins.ps1 -Command <cmd> [options]"
    Write-Output ""
    Write-7SinsOutput "COMMANDS:" "Header"
    Write-Output "  status              Show drive weights and system status"
    Write-Output "  task <desc> [type]  Run a task through 7Sins decision system"
    Write-Output "  exec <cmd> [--wsl]   Execute terminal command"
    Write-Output "  init                Initialize 7Sins system"
    Write-Output "  backup [path]       Create system backup"
    Write-Output "  restore <path>      Restore from backup"
    Write-Output "  help                Show this help message"
    Write-Output ""
    Write-7SinsOutput "EXAMPLES:" "Header"
    Write-Output "  .\ego_core.ps1 -Command status"
    Write-Output "  .\ego_core.ps1 -Command task -TaskDescription 'Fix auth bug' -TaskType 'debug'"
    Write-Output "  .\ego_core.ps1 -Command exec -TaskDescription 'git status' -UseWSL"
}

function Show-Status {
    Show-Header
    Write-7SinsOutput "Drive Status:" "Header"
    Write-Output ""
    
    $drives = @(
        @{Name="GLUTTONY"; Weight=0.7; Role="Knowledge Harvester"},
        @{Name="LUST"; Weight=0.6; Role="System Controller"},
        @{Name="GREED"; Weight=0.8; Role="Value Maximizer"},
        @{Name="SLOTH"; Weight=0.7; Role="Efficiency Engine"},
        @{Name="PRIDE"; Weight=0.6; Role="Quality Guardian"},
        @{Name="WRATH"; Weight=0.8; Role="Error Eliminator"},
        @{Name="ENVY"; Weight=0.5; Role="Benchmark Analyst"}
    )
    
    foreach ($drive in $drives) {
        $barCount = [int]($drive.Weight * 10)
        $bar = "█" * $barCount + "░" * (10 - $barCount)
        Write-Output "  $($drive.Name.PadRight(10)) [$bar] $($drive.Weight.ToString('F2')) - $($drive.Role)"
    }
    
    Write-Output ""
    Write-7SinsOutput "System Health: READY" "Success"
    Write-Output "Last Decision: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

function Invoke-Task {
    param(
        [string]$Description,
        [string]$Type
    )
    
    Show-Header
    Write-7SinsOutput "Processing Task..." "Header"
    Write-Output ""
    Write-Output "  Description: $Description"
    Write-Output "  Type: $Type"
    Write-Output ""
    
    # Simulate drive activation
    $relevantDrives = @()
    switch -Regex ($Type) {
        "bug|error|fix" { $relevantDrives += "WRATH"; $relevantDrives += "PRIDE" }
        "feature|user|growth" { $relevantDrives += "GREED"; $relevantDrives += "PRIDE" }
        "research|analyze" { $relevantDrives += "GLUTTONY"; $relevantDrives += "ENVY" }
        "refactor|auto" { $relevantDrives += "SLOTH"; $relevantDrives += "PRIDE" }
        default { $relevantDrives = @("GREED", "GLUTTONY", "PRIDE") }
    }
    
    Write-7SinsOutput "Activated Drives: $($relevantDrives -join ', ')" "Info"
    Write-Output ""
    
    # Simulate decision
    $winner = $relevantDrives | Get-Random
    $confidence = (Get-Random -Minimum 60 -Maximum 95) / 100
    
    Write-7SinsOutput "Decision:" "Success"
    Write-Output "  Winner: $winner"
    Write-Output "  Confidence: $($confidence.ToString('P0'))"
    Write-Output "  Recommendation: Execute task with $winner dominance"
    
    # Log decision
    $logEntry = @{
        Timestamp = (Get-Date).ToString('o')
        Task = $Description
        Type = $Type
        Winner = $winner
        Confidence = $confidence
    } | ConvertTo-Json
    
    $logFile = Join-Path $LogsPath "decisions_$(Get-Date -Format 'yyyyMMdd').json"
    Add-Content -Path $logFile -Value $logEntry
}

function Invoke-Execute {
    param(
        [string]$Command,
        [bool]$UseWSL
    )
    
    Show-Header
    Write-7SinsOutput "Executing Command..." "Header"
    Write-Output ""
    Write-Output "  Command: $Command"
    Write-Output "  Terminal: $(if($UseWSL){'WSL Bash'}else{'PowerShell'})"
    Write-Output ""
    
    try {
        if ($UseWSL) {
            $result = bash -c $Command 2>&1
            $exitCode = $LASTEXITCODE
        } else {
            $result = Invoke-Expression $Command 2>&1
            $exitCode = $?
        }
        
        Write-7SinsOutput "Output:" "Info"
        Write-Output $result
        Write-Output ""
        Write-7SinsOutput "Exit Code: $exitCode" $(if($exitCode -eq 0){'Success'}else{'Error'})
    }
    catch {
        Write-7SinsOutput "Error: $_" "Error"
    }
}

function Initialize-System {
    Show-Header
    Write-7SinsOutput "Initializing 7Sins System..." "Header"
    
    # Create directories
    $dirs = @($LogsPath, $ConfigPath)
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-7SinsOutput "Created: $dir" "Success"
        }
    }
    
    # Create default config
    $configFile = Join-Path $ConfigPath "default.json"
    $defaultConfig = @{
        max_debate_rounds = 3
        confidence_threshold = 0.6
        human_override_weight = 1.5
        terminal_default = "powershell"
        safe_mode = $true
    } | ConvertTo-Json
    
    Set-Content -Path $configFile -Value $defaultConfig
    Write-7SinsOutput "Config created: $configFile" "Success"
    
    Write-Output ""
    Write-7SinsOutput "7Sins System initialized successfully!" "Success"
}

function New-Backup {
    param([string]$Path)
    
    Show-Header
    Write-7SinsOutput "Creating Backup..." "Header"
    
    $backupPath = if ($Path) { $Path } else { Join-Path $ProjectRoot "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip" }
    
    try {
        Compress-Archive -Path "$Script:ProjectRoot\*" -DestinationPath $backupPath -Force
        Write-7SinsOutput "Backup created: $backupPath" "Success"
    }
    catch {
        Write-7SinsOutput "Backup failed: $_" "Error"
    }
}

function Restore-Backup {
    param([string]$Path)
    
    Show-Header
    Write-7SinsOutput "Restoring from Backup: $Path" "Header"
    
    if (-not (Test-Path $Path)) {
        Write-7SinsOutput "Backup file not found: $Path" "Error"
        return
    }
    
    try {
        Expand-Archive -Path $Path -DestinationPath $Script:ProjectRoot -Force
        Write-7SinsOutput "Restore completed successfully!" "Success"
    }
    catch {
        Write-7SinsOutput "Restore failed: $_" "Error"
    }
}

# Main execution
switch ($Command) {
    "status" { Show-Status }
    "task" { 
        if (-not $TaskDescription) {
            Write-7SinsOutput "Task description required" "Error"
            Show-Help
            exit 1
        }
        Invoke-Task -Description $TaskDescription -Type $TaskType 
    }
    "exec" {
        if (-not $TaskDescription) {
            Write-7SinsOutput "Command required" "Error"
            Show-Help
            exit 1
        }
        Invoke-Execute -Command $TaskDescription -UseWSL $UseWSL
    }
    "init" { Initialize-System }
    "backup" { New-Backup -Path $BackupPath }
    "restore" { 
        if (-not $BackupPath) {
            Write-7SinsOutput "Backup path required" "Error"
            Show-Help
            exit 1
        }
        Restore-Backup -Path $BackupPath
    }
    "help" { Show-Help }
    default {
        Write-7SinsOutput "Unknown command: $Command" "Error"
        Show-Help
        exit 1
    }
}