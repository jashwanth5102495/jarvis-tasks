from typing import Dict, List, Tuple

from .categories import (
    CATEGORIES,
    CategoryDefinition,
    PHRASE_PATTERNS,
    INTERNAL_COMMAND_PHRASES,
)


class IntentClassifier:
    """
    Semantic intent classifier with three scoring layers:

    1. Internal-command fast-path  — checked first via exact phrase match.
    2. Phrase-pattern scoring      — multi-word patterns carry higher weight.
    3. Single-token keyword scoring — weighted keyword lookup per category.

    The final category is the one with the highest cumulative score.
    """

    def __init__(self):
        self.categories = CATEGORIES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(
        self, text_clean: str, tokens: List[str]
    ) -> Tuple[str, Dict[str, float]]:
        """
        Returns (best_category_name, category_scores_dict).

        text_clean  : lowercased, punctuation-stripped input text
        tokens      : filtered token list (stop-words removed, verbs normalised)
        """
        category_scores: Dict[str, float] = {
            cat.name: 0.0 for cat in self.categories
        }

        # ── Layer 0: internal-command fast-path ──────────────────────────
        for phrase in INTERNAL_COMMAND_PHRASES:
            if phrase in text_clean:
                category_scores["internal_commands"] += 15.0
                # Still continue scoring so debug output is complete

        # ── Layer 1: phrase-pattern scoring ──────────────────────────────
        for phrase, (cat_name, score) in PHRASE_PATTERNS.items():
            if phrase in text_clean:
                category_scores[cat_name] += score

        # ── Layer 2: single-token keyword scoring ─────────────────────────
        for token in tokens:
            for category in self.categories:
                if category.name == "unknown":
                    continue
                for keyword in category.keywords:
                    if " " not in keyword and token == keyword.lower():
                        weight = category.weights.get(keyword, 1.0)
                        category_scores[category.name] += weight

        # ── Layer 3: multi-word keywords in category definitions ──────────
        # (handles any compound keywords defined directly in CategoryDefinition)
        for category in self.categories:
            if category.name == "unknown":
                continue
            for keyword in category.keywords:
                if " " in keyword and keyword.lower() in text_clean:
                    weight = category.weights.get(keyword, 1.0)
                    category_scores[category.name] += weight

        # ── Select best category ──────────────────────────────────────────
        temp_scores = {
            k: v for k, v in category_scores.items() if k != "unknown"
        }

        if not temp_scores or max(temp_scores.values()) == 0:
            return "unknown", category_scores

        best_category = max(temp_scores, key=temp_scores.__getitem__)
        return best_category, category_scores
