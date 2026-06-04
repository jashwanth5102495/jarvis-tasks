
"""
test_runtime.py
===============
Unit tests for JARVIS runtime system components.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.runtime_state import runtime_state, RuntimeStatus


def test_runtime_state_initialization():
    assert runtime_state.current_status == RuntimeStatus.IDLE
    assert runtime_state.is_running is True
    print("[OK] Test 1: Initialization passed")


def test_toggle_pause():
    old_status = runtime_state.current_status
    toggled = runtime_state.toggle_pause()
    assert toggled is True
    assert runtime_state.current_status == RuntimeStatus.PAUSED
    toggled2 = runtime_state.toggle_pause()
    assert toggled2 is True
    assert runtime_state.current_status != RuntimeStatus.PAUSED
    print("[OK] Test 2: Toggle pause/resume passed")


def test_set_status():
    runtime_state.set_status(RuntimeStatus.LISTENING)
    assert runtime_state.current_status == RuntimeStatus.LISTENING
    runtime_state.set_status(RuntimeStatus.IDLE)
    print("[OK] Test 3: Set status passed")


def test_status_change_callbacks():
    callback_called = False
    last_old = None
    last_new = None

    def test_callback(old, new):
        nonlocal callback_called, last_old, last_new
        callback_called = True
        last_old = old
        last_new = new

    runtime_state.register_status_change_callback(test_callback)
    runtime_state.set_status(RuntimeStatus.SPEAKING)
    assert callback_called is True
    assert last_new == RuntimeStatus.SPEAKING
    print("[OK] Test 4: Status change callbacks passed")
    # Reset to idle to clean up
    runtime_state.set_status(RuntimeStatus.IDLE)


if __name__ == "__main__":
    print("Running JARVIS Runtime System Tests...\n")
    test_runtime_state_initialization()
    test_toggle_pause()
    test_set_status()
    test_status_change_callbacks()
    print("\n[OK] All runtime tests passed!")



