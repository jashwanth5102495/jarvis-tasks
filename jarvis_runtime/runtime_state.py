
from enum import Enum, auto


class RuntimeState(Enum):
    STARTING = auto()
    ACTIVE = auto()
    PAUSED = auto()
    RECOVERING = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()


_current_state = RuntimeState.STARTING


def get_state() -> RuntimeState:
    global _current_state
    return _current_state


def set_state(new_state: RuntimeState):
    global _current_state
    _current_state = new_state
    print(f"[JARVIS Runtime] State changed to {new_state.name}")
