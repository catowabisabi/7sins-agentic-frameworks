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
    
    BLOCKED_COMMANDS = frozenset([
        "rm", "del", "format", "shutdown", "reboot", "mkfs", "dd",
    "fdisk", "parted", "sfdisk"
    ])
    
    def __init__(self, executor: TerminalExecutor):
        self.executor = executor
    
    def _tokenize(self, command: str) -> List[str]:
        if not command:
            return []
        return command.strip().split()
    
    def _check_dangerous_flags(self, tokens: List[str]) -> bool:
        for token in tokens:
            if token in ("-rf", "-rF", "-R", "-f", "--force"):
                return True
            if token.startswith("/") and token.lower() in ("/s", "/f", "/q", "/force"):
                return True
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in ("-r", "-R"):
                if i + 1 < len(tokens) and tokens[i + 1] in ("-f", "--force"):
                    return True
            elif t == "-f":
                if i > 0 and tokens[i - 1] in ("-r", "-R"):
                    return True
            i += 1
        return False
    
    def is_safe(self, command: str) -> bool:
        tokens = self._tokenize(command)
        if not tokens:
            return True
        
        base_cmd = tokens[0].lower()
        if base_cmd in self.BLOCKED_COMMANDS:
            return False
        
        if self._check_dangerous_flags(tokens):
            return False
        
        return True
    
    def execute_safe(self, command: str, timeout: int = 30) -> ExecutionResult:
        if not self.is_safe(command):
            tokens = self._tokenize(command)
            base = tokens[0] if tokens else "unknown"
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command '{base}' is blocked for safety",
                exit_code=-1,
                terminal_type=self.executor.terminal_type,
                command=command
            )
        return self.executor.execute(command, timeout)
