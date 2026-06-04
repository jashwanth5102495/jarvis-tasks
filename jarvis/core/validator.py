import re
from typing import Tuple, List


class InputValidator:
    MIN_INPUT_LENGTH = 3
    MIN_ALPHANUMERIC_RATIO = 0.6
    # Lowered to 1 so single-token desktop commands ("click", "screenshot")
    # are not rejected before the classifier can score them.
    MIN_MEANINGFUL_TOKENS = 1
    REPETITION_THRESHOLD = 0.75
    GIBBERISH_PATTERNS = [
        # True keyboard row mashing — must be ONLY from one row AND 4+ chars with no vowels
        # Old pattern was too aggressive and rejected real words like "click", "scroll", "brave"
        r"^[0-9]+$",        # All numbers
        r"^(.)\1{3,}$",     # 4+ identical characters in a row (zzzz, aaaa)
    ]

    # Known keyboard-mash sequences that are NOT real words
    _KEYBOARD_MASH = {
        "qwerty", "asdf", "asdfgh", "qwertyuiop", "asdfghjkl",
        "zxcvbn", "qazwsx", "asdfjkl", "zxcvbnm", "qweasd",
    }

    def validate(self, text: str, tokens: List[str]) -> Tuple[bool, str]:
        text_stripped = text.strip()

        # 1. Check minimum length
        if len(text_stripped) < self.MIN_INPUT_LENGTH:
            return False, "Input too short"

        # 2. Check gibberish patterns
        text_lower = text_stripped.lower()
        for pattern in self.GIBBERISH_PATTERNS:
            if re.fullmatch(pattern, text_lower):
                return False, "Input appears to be gibberish"

        # 2b. Check known keyboard-mash sequences
        if text_lower in self._KEYBOARD_MASH:
            return False, "Input appears to be gibberish"

        # 3. Check alphanumeric ratio
        alnum_count = sum(1 for c in text_stripped if c.isalnum() or c.isspace())
        alnum_ratio = alnum_count / max(len(text_stripped), 1)
        if alnum_ratio < self.MIN_ALPHANUMERIC_RATIO:
            return False, "Input appears to be random characters"

        # 4. Check for highly repetitive input
        if self._is_highly_repetitive(text_stripped):
            return False, "Input is repetitive"

        # 5. Check meaningful tokens count (1 is enough for desktop commands)
        if len(tokens) < self.MIN_MEANINGFUL_TOKENS:
            return False, "Not enough meaningful information"

        return True, ""

    def _is_highly_repetitive(self, text: str) -> bool:
        if len(text) < 5:
            return False

        char_counts = {}
        for c in text.lower():
            if c.isalnum():
                char_counts[c] = char_counts.get(c, 0) + 1

        if not char_counts:
            return True

        max_count = max(char_counts.values())
        total_alnum = sum(char_counts.values())
        repetition_ratio = max_count / max(total_alnum, 1)

        return repetition_ratio >= self.REPETITION_THRESHOLD
