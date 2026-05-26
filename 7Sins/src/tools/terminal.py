"""
7Sins Project - Terminal Integration
WSL and PowerShell execution tools
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import os


class TerminalType(Enum):
    POWERSHELL = "powershell"
    WSL_BASH = "wsl_bash"
    CMD = "cmd"


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    terminal_type: TerminalType
    command: str


class TerminalExecutor:
    
    def __init__(self, terminal_type: TerminalType = TerminalType.POWERSHELL):
        self.terminal_type = terminal_type
    
    def execute(self, command: str, timeout: int = 30) -> ExecutionResult:
        try:
            if self.terminal_type == TerminalType.WSL_BASH:
                result = subprocess.run(
                    ["wsl", "bash", "-c", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            elif self.terminal_type == TerminalType.POWERSHELL:
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    ["cmd", "/c", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                terminal_type=self.terminal_type,
                command=command
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                exit_code=-1,
                terminal_type=self.terminal_type,
                command=command
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                terminal_type=self.terminal_type,
                command=command
            )
    
    def execute_multi(self, commands: List[str]) -> List[ExecutionResult]:
        return [self.execute(cmd) for cmd in commands]


class WSLIntegration:
    
    def __init__(self):
        self.bash_executor = TerminalExecutor(TerminalType.WSL_BASH)
        self.ps_executor = TerminalExecutor(TerminalType.POWERSHELL)
    
    def run_bash(self, command: str, timeout: int = 30) -> ExecutionResult:
        return self.bash_executor.execute(command, timeout)
    
    def run_powershell(self, command: str, timeout: int = 30) -> ExecutionResult:
        return self.ps_executor.execute(command, timeout)
    
    def get_system_info(self) -> Dict[str, str]:
        info = {}
        result = self.run_bash("uname -a")
        info["linux_info"] = result.stdout if result.success else "N/A"
        result = self.run_powershell("$PSVersionTable.PSVersion")
        info["pwsh_version"] = result.stdout if result.success else "N/A"
        return info
    
    def check_wsl_available(self) -> bool:
        result = self.run_bash("wsl --status")
        return result.success


class SafeExecutor:
    
    def __init__(self, executor: TerminalExecutor):
        self.executor = executor
        self.safe_commands = ["git", "ls", "cat", "head", "tail", "grep", "find"]
        self.dangerous_commands = ["rm", "del", "format", "shutdown", "reboot"]
    
    def is_safe(self, command: str) -> bool:
        cmd_lower = command.lower().split()[0] if command else ""
        if cmd_lower in self.dangerous_commands:
            return False
        return True
    
    def execute_safe(self, command: str, timeout: int = 30) -> ExecutionResult:
        if not self.is_safe(command):
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command '{command.split()[0]}' is blocked for safety",
                exit_code=-1,
                terminal_type=self.executor.terminal_type,
                command=command
            )
        return self.executor.execute(command, timeout)