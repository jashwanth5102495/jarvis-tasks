from typing import List, Tuple
from jarvis.computer_control.cc_models import ControlAction, ControllerType, ActionRisk


def _get_screen_center() -> Tuple[int, int]:
    try:
        import pyautogui
        w, h = pyautogui.size()
        return w // 2, h // 2
    except Exception:
        return 960, 540  # fallback to 1080p center


class ControlWorkflowGenerator:
    """
    Generates structured computer control workflows (lists of ControlAction)
    based on natural language input, detected intent, and extracted requirements.
    """

    def generate_from_input(self, user_input: str, category: str, requirements: List[str]) -> List[ControlAction]:
        """
        Main entry point to generate a control workflow.
        """
        input_lower = user_input.lower()

        # Check for specific predefined workflows first
        if "open chrome" in input_lower and "search" in input_lower:
            # Extract query from input (after "search")
            query = self._extract_query(user_input)
            return self._workflow_open_chrome_and_search(query)
        elif "open notepad" in input_lower and "type" in input_lower:
            content = self._extract_text_to_type(user_input)
            return self._workflow_open_notepad_and_type(content)
        elif "take screenshot" in input_lower or "capture screen" in input_lower:
            return self._workflow_screenshot()
        elif "open vscode" in input_lower or "open visual studio code" in input_lower or "open vs code" in input_lower:
            return self._workflow_open_app("vscode")
        elif "open notepad" in input_lower:
            return self._workflow_open_app("notepad")
        elif "open chrome" in input_lower:
            return self._workflow_open_app("chrome")
        elif "open" in input_lower and "vscode" in input_lower:
            return self._workflow_open_app("vscode")
        elif "open" in input_lower and "notepad" in input_lower:
            return self._workflow_open_app("notepad")
        elif "open" in input_lower and "chrome" in input_lower:
            return self._workflow_open_app("chrome")

        # Fallback: build workflow from keywords
        actions: List[ControlAction] = []

        if "move mouse" in input_lower:
            if "center" in input_lower:
                center_x, center_y = _get_screen_center()
                actions.append(
                    ControlAction(
                        controller=ControllerType.MOUSE,
                        action="move_to",
                        params={"x": center_x, "y": center_y},
                        risk=ActionRisk.MEDIUM,
                        description="Move mouse to center of screen",
                    )
                )
        if "click" in input_lower:
            if "right" in input_lower:
                actions.append(
                    ControlAction(
                        controller=ControllerType.MOUSE,
                        action="right_click",
                        params={},
                        risk=ActionRisk.HIGH,
                        description="Right-click",
                    )
                )
            elif "double" in input_lower:
                actions.append(
                    ControlAction(
                        controller=ControllerType.MOUSE,
                        action="double_click",
                        params={},
                        risk=ActionRisk.HIGH,
                        description="Double-click",
                    )
                )
            else:
                actions.append(
                    ControlAction(
                        controller=ControllerType.MOUSE,
                        action="click",
                        params={},
                        risk=ActionRisk.HIGH,
                        description="Click",
                    )
                )
        if "type" in input_lower:
            text = self._extract_text_to_type(user_input)
            if text:
                actions.append(
                    ControlAction(
                        controller=ControllerType.KEYBOARD,
                        action="type_text",
                        params={"text": text},
                        risk=ActionRisk.HIGH,
                        description=f"Type: {text[:50]}",
                    )
                )
        if "press enter" in input_lower:
            actions.append(
                ControlAction(
                    controller=ControllerType.KEYBOARD,
                    action="press",
                    params={"key": "enter"},
                    risk=ActionRisk.MEDIUM,
                    description="Press Enter",
                )
            )
        if "maximize" in input_lower:
            actions.append(
                ControlAction(
                    controller=ControllerType.WINDOW,
                    action="maximize_window",
                    params={},
                    risk=ActionRisk.MEDIUM,
                    description="Maximize window",
                )
            )
        if "minimize" in input_lower:
            actions.append(
                ControlAction(
                    controller=ControllerType.WINDOW,
                    action="minimize_window",
                    params={},
                    risk=ActionRisk.MEDIUM,
                    description="Minimize window",
                )
            )

        return actions if actions else []

    # ---------------------------------------------------------------
    # Predefined workflow builders
    # ---------------------------------------------------------------

    def _workflow_open_chrome_and_search(self, query: str) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": "chrome"},
                risk=ActionRisk.HIGH,
                description="Open Chrome",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": "chrome", "timeout_s": 8},
                risk=ActionRisk.SAFE,
                description="Wait for Chrome",
            ),
            ControlAction(
                controller=ControllerType.BROWSER,
                action="search_google",
                params={"query": query},
                risk=ActionRisk.HIGH,
                description=f"Search Google: {query}",
            ),
        ]

    def _workflow_open_notepad_and_type(self, content: str) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": "notepad"},
                risk=ActionRisk.HIGH,
                description="Open Notepad",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": "notepad", "timeout_s": 6},
                risk=ActionRisk.SAFE,
                description="Wait for Notepad",
            ),
            ControlAction(
                controller=ControllerType.KEYBOARD,
                action="type_text",
                params={"text": content, "interval": 0.03},
                risk=ActionRisk.HIGH,
                description="Type text into Notepad",
            ),
        ]

    def _workflow_screenshot(self) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.SCREENSHOT,
                action="capture_screen",
                params={"suffix": "jarvis"},
                risk=ActionRisk.SAFE,
                description="Take screenshot",
            ),
        ]

    def _workflow_open_app(self, app_name: str) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": app_name},
                risk=ActionRisk.HIGH,
                description=f"Open {app_name}",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": app_name, "timeout_s": 8},
                risk=ActionRisk.SAFE,
                description=f"Wait for {app_name}",
            ),
        ]

    # ---------------------------------------------------------------
    # Helper methods for extraction
    # ---------------------------------------------------------------

    def _extract_query(self, user_input: str) -> str:
        """Extract search query from input like "search latest AI models"."""
        parts = user_input.lower().split("search", 1)
        if len(parts) > 1:
            return parts[1].strip()
        return ""

    def _extract_text_to_type(self, user_input: str) -> str:
        """Extract text after "type" in input like "type hello world"."""
        parts = user_input.lower().split("type", 1)
        if len(parts) > 1:
            return parts[1].strip()
        return ""


# Module-level singleton
control_workflow_generator = ControlWorkflowGenerator()
