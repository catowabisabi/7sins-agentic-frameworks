from .core.drive_engine import DriveType, DriveEngineRegistry, DriveState
from .core.ego_core import EGOCore, TaskInput
from .engines.seven_sins import (
    GluttonyEngine, LustEngine, GreedEngine, SlothEngine,
    PrideEngine, WrathEngine, EnvyEngine,
    ErosEngine, ThanatosEngine
)
from .memory.reflection import ReflectionAgent, DecisionRecord
from .tools.terminal import TerminalExecutor, TerminalType, ExecutionResult, WSLIntegration


def create_7sins_system() -> EGOCore:
    registry = DriveEngineRegistry()
    registry.register(GluttonyEngine())
    registry.register(LustEngine())
    registry.register(GreedEngine())
    registry.register(SlothEngine())
    registry.register(PrideEngine())
    registry.register(WrathEngine())
    registry.register(EnvyEngine())
    registry.register(ErosEngine())
    registry.register(ThanatosEngine())
    return EGOCore(registry)