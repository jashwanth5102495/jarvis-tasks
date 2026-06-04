import math
from typing import Dict


class ConfidenceCalculator:
    """
    Produces realistic, calibrated confidence scores in the range [20, 95].

    Algorithm
    ---------
    1. Softmax over all non-unknown category scores to get a probability
       distribution.  This naturally prevents 100 % when multiple categories
       have non-zero scores.
    2. Scale the softmax probability of the winning category to [0, 95].
    3. Apply an ambiguity penalty when the runner-up score is close to the
       winner (reduces confidence for genuinely ambiguous inputs).
    4. Floor at 20 % so the system never reports 0 % for a valid match.

    Thresholds
    ----------
    MIN_CONFIDENCE : inputs whose confidence falls below this are flagged as
                     low-confidence and may be reclassified as "unknown".
                     Set to 25 so that clear single-category inputs always
                     pass, while truly ambiguous ones are rejected.
    """

    MIN_CONFIDENCE: float = 30.0
    # Lowered from 40 → 30 so short but valid desktop commands
    # ("scroll down", "click", "open chrome") are not rejected.
    LOW_CONFIDENCE_THRESHOLD: float = 30.0
    MAX_CONFIDENCE: float = 95.0
    SOFTMAX_TEMPERATURE: float = 1.0   # lower → sharper; higher → flatter
    AMBIGUITY_PENALTY_RATIO: float = 0.80  # if runner-up ≥ 80 % of winner → penalise

    def calculate(
        self,
        category_scores: Dict[str, float],
        best_category: str,
    ) -> float:
        # Exclude the sentinel "unknown" bucket
        scores = {k: v for k, v in category_scores.items() if k != "unknown"}

        if not scores:
            return self.MIN_CONFIDENCE

        best_score = scores.get(best_category, 0.0)

        if best_score <= 0:
            return self.MIN_CONFIDENCE

        # ── Softmax ───────────────────────────────────────────────────────
        # Shift by max for numerical stability
        max_score = max(scores.values())
        exp_scores = {
            k: math.exp((v - max_score) / self.SOFTMAX_TEMPERATURE)
            for k, v in scores.items()
        }
        total_exp = sum(exp_scores.values())
        softmax_prob = exp_scores[best_category] / total_exp  # in (0, 1]

        # Scale to [0, MAX_CONFIDENCE]
        confidence = softmax_prob * self.MAX_CONFIDENCE

        # ── Ambiguity penalty ─────────────────────────────────────────────
        other_scores = [v for k, v in scores.items() if k != best_category]
        if other_scores:
            runner_up = max(other_scores)
            if runner_up > 0 and (runner_up / best_score) >= self.AMBIGUITY_PENALTY_RATIO:
                # Reduce confidence proportionally to how close the runner-up is
                penalty_factor = 1.0 - 0.15 * (runner_up / best_score)
                confidence *= max(penalty_factor, 0.6)

        # ── Clamp ─────────────────────────────────────────────────────────
        confidence = max(self.MIN_CONFIDENCE, min(confidence, self.MAX_CONFIDENCE))

        return round(confidence, 1)

    def is_low_confidence(self, confidence: float) -> bool:
        return confidence < self.LOW_CONFIDENCE_THRESHOLD
