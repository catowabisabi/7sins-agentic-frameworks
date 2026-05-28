from typing import Optional
import time
import sys

from .core.drive_engine import DriveEngineRegistry
from .core.ego_core import EGOCore, TaskInput
from .engines.seven_sins import (
    GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
    PrideEngine, WrathEngine, EnvyEngine
)
from .memory.reflection import ReflectionAgent, DecisionRecord
from .tools.terminal import TerminalExecutor, TerminalType


class SevenSinsCLI:
    
    def __init__(self):
        self.ego_core = self._create_system()
        self.reflector = ReflectionAgent()
    
    def _create_system(self) -> EGOCore:
        registry = DriveEngineRegistry()
        registry.register(GluttonyEngine())
        registry.register(LustEngine())
        registry.register(GreedEngine())
        registry.register(SlothEngine())
        registry.register(PrideEngine())
        registry.register(WrathEngine())
        registry.register(EnvyEngine())
        return EGOCore(registry)
    
    def run_task(self, description: str, task_type: str, context: Optional[dict] = None):
        task = TaskInput(
            description=description,
            task_type=task_type,
            context=context or {}
        )
        
        result = self.ego_core.process_task(task)
        
        record = DecisionRecord(
            task_id=f"task_{id(result)}",
            task_description=description,
            winning_drive=str(result.selected_drives[0][0]) if result.selected_drives else "unknown",
            drive_weights={str(d): w for d, w in result.selected_drives},
            outcome="success",
            outcome_confidence=result.confidence,
            timestamp=time.time()
        )
        self.reflector.record_decision(record)
        
        print(f"\n=== 7Sins Decision ===")
        print(f"Task: {description}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Winner: {result.selected_drives[0] if result.selected_drives else 'None'}")
        
        return result
    
    def status(self):
        weights = self.ego_core.registry.get_weights()
        print("\n=== 7Sins Drive Status ===")
        for drive, weight in weights.items():
            bar = "█" * int(weight * 10) + "░" * (10 - int(weight * 10))
            print(f"  {drive.upper():10} [{bar}] {weight:.2f}")
        
        print("\n=== Recent Reflection ===")
        print(self.reflector.get_self_criticism())
    
    def exec_terminal(self, command: str, use_wsl: bool = False):
        terminal_type = TerminalType.WSL_BASH if use_wsl else TerminalType.POWERSHELL
        executor = TerminalExecutor(terminal_type)
        result = executor.execute(command)
        
        print(f"\n=== Terminal ({terminal_type.value}) ===")
        print(f"Command: {command}")
        print(f"Exit code: {result.exit_code}")
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        
        return result


def main():
    cli = SevenSinsCLI()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            cli.status()
        elif command == "task" and len(sys.argv) > 2:
            description = sys.argv[2]
            task_type = sys.argv[3] if len(sys.argv) > 3 else "general"
            cli.run_task(description, task_type)
        elif command == "exec" and len(sys.argv) > 2:
            command_to_run = sys.argv[2]
            use_wsl = "--wsl" in sys.argv
            cli.exec_terminal(command_to_run, use_wsl)
        else:
            print("Usage:")
            print("  7sins status              - Show drive weights and reflection")
            print("  7sins task <desc> [type]  - Run a task")
            print("  7sins exec <cmd> [--wsl]   - Execute terminal command")
    else:
        print("7Sins Project - Self-Driven LLM Agent Harness")
        print("Type '7sins status' to see drive weights")


if __name__ == "__main__":
    main()