from typing import Dict, List


class DebugInfo:
    """
    Stores and prints diagnostic information for a single classification pass.

    Usage
    -----
    Set ``debug_info.enabled = True`` (or send "enable debug mode" as input)
    to activate verbose output.  When enabled, every call to ``print_debug``
    will emit a structured report to stdout.
    """

    def __init__(self):
        self.enabled: bool = False
        self.raw_input: str = ""
        self.tokens: List[str] = []
        self.normalized_tokens: List[str] = []
        self.detected_phrases: List[str] = []
        self.category_scores: Dict[str, float] = {}
        self.selected_category: str = ""
        self.confidence: float = 0.0

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def enable(self) -> None:
        self.enabled = True
        print("\n[JARVIS] Debug mode ENABLED\n")

    def disable(self) -> None:
        self.enabled = False
        print("\n[JARVIS] Debug mode DISABLED\n")

    def toggle(self) -> None:
        if self.enabled:
            self.disable()
        else:
            self.enable()

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def print_debug(self) -> None:
        if not self.enabled:
            return

        print("\n╔══════════════════════════════════════╗")
        print("║           DEBUG MODE ACTIVE           ║")
        print("╚══════════════════════════════════════╝")
        print(f"  Raw Input        : {self.raw_input!r}")
        print(f"  Tokens           : {self.tokens}")
        print(f"  Normalized Tokens: {self.normalized_tokens}")
        print(f"  Detected Phrases : {self.detected_phrases}")
        print()
        print("  Category Scores:")
        sorted_scores = sorted(
            self.category_scores.items(), key=lambda x: x[1], reverse=True
        )
        for cat, score in sorted_scores:
            if score > 0:
                bar = "█" * int(score)
                print(f"    {cat:<25} {score:>6.2f}  {bar}")
        print()
        print(f"  Selected Category: {self.selected_category}")
        print(f"  Confidence       : {self.confidence}%")
        print("══════════════════════════════════════════\n")
