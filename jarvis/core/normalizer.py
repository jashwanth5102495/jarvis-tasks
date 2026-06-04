from typing import List


class TextNormalizer:
    """
    Normalizes verb synonyms only — does NOT replace content nouns like
    'poster', 'logo', 'design' because those are needed for category scoring.
    """

    def __init__(self):
        # Only normalize ACTION verbs — never content nouns
        self.synonym_map: dict[str, str] = {
            "build":    "create",
            "develop":  "create",
            "generate": "create",
            "make":     "create",
            "produce":  "create",
            "compose":  "write",
            "draft":    "write",
            "craft":    "write",
            "setup":    "configure",
            "set up":   "configure",
        }

        # Compound nouns that should be preserved as single tokens during
        # phrase detection (used by classifier phrase patterns).
        self.compound_nouns: List[str] = [
            "employee management system",
            "employee management",
            "inventory dashboard",
            "inventory management",
            "ai course",
            "course poster",
            "cybersecurity banner",
            "company banner",
            "temporary files",
            "daily backup",
            "dark futuristic",
        ]

    def normalize_tokens(self, tokens: List[str]) -> List[str]:
        """Replace synonym verbs in token list; preserve all other tokens."""
        return [self.synonym_map.get(token, token) for token in tokens]

    def normalize_text(self, text: str) -> str:
        """
        Apply verb synonym replacement on full lowercased text.
        Preserves content nouns so category keyword matching still works.
        """
        text_lower = text.lower()
        for original, replacement in self.synonym_map.items():
            # Use word-boundary-safe replacement (space-padded)
            text_lower = text_lower.replace(f" {original} ", f" {replacement} ")
            if text_lower.startswith(original + " "):
                text_lower = replacement + text_lower[len(original):]
        return text_lower
