import logging
from typing import List

from core.models import Goal
from brain import (
    Preprocessor,
    InputValidator,
    IntentClassifier,
    ConfidenceCalculator,
    RequirementsExtractor,
    TextNormalizer,
    DebugInfo,
    PHRASE_PATTERNS,
    INTERNAL_COMMAND_PHRASES,
)

logger = logging.getLogger(__name__)


class Brain:
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.validator = InputValidator()
        self.classifier = IntentClassifier()
        self.confidence_calculator = ConfidenceCalculator()
        self.extractor = RequirementsExtractor()
        self.normalizer = TextNormalizer()
        self.debug_info = DebugInfo()

    # ------------------------------------------------------------------
    # Internal-command handling
    # ------------------------------------------------------------------

    def _handle_internal_command(self, text_clean: str) -> Goal | None:
        """
        Check whether the input is an internal JARVIS command.
        Returns a Goal with category='internal_commands' if matched,
        otherwise returns None so normal classification proceeds.
        """
        for phrase in INTERNAL_COMMAND_PHRASES:
            if phrase in text_clean:
                # Execute the command side-effect
                if "enable debug" in text_clean:
                    self.debug_info.enable()
                elif "disable debug" in text_clean:
                    self.debug_info.disable()
                elif "toggle debug" in text_clean or "debug mode" in text_clean:
                    self.debug_info.toggle()
                elif "enable verbose" in text_clean:
                    self.debug_info.enable()
                elif "disable verbose" in text_clean:
                    self.debug_info.disable()
                elif "toggle verbose" in text_clean or "verbose mode" in text_clean:
                    self.debug_info.toggle()
                elif "clear memory" in text_clean or "reset memory" in text_clean:
                    logger.info("Internal command: clear memory requested")
                elif "clear history" in text_clean:
                    logger.info("Internal command: clear history requested")
                elif "show logs" in text_clean:
                    logger.info("Internal command: show logs requested")

                return Goal(
                    goal=text_clean,
                    category="internal_commands",
                    requirements=[],
                    priority="high",
                    confidence=99.0,
                    intent_summary=f"Internal command: {text_clean}",
                )
        return None

    # ------------------------------------------------------------------
    # Detected phrases helper (for debug output)
    # ------------------------------------------------------------------

    def _detect_phrases(self, text_clean: str) -> List[str]:
        found = []
        for phrase in PHRASE_PATTERNS:
            if phrase in text_clean:
                found.append(phrase)
        for phrase in INTERNAL_COMMAND_PHRASES:
            if phrase in text_clean:
                found.append(phrase)
        return found

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze_task(self, user_input: str) -> Goal:
        logger.info(f"Analyzing task: {user_input}")

        # 1. Preprocess
        text_clean, tokens = self.preprocessor.preprocess(user_input)

        # 2. Normalize (verb synonyms only — preserves content nouns)
        normalized_text = self.normalizer.normalize_text(text_clean)
        normalized_tokens = self.normalizer.normalize_tokens(tokens)

        # 3. Populate debug state
        self.debug_info.raw_input = user_input
        self.debug_info.tokens = tokens
        self.debug_info.normalized_tokens = normalized_tokens
        self.debug_info.detected_phrases = self._detect_phrases(normalized_text)

        # 4. Internal-command fast-path (before validation)
        internal_goal = self._handle_internal_command(normalized_text)
        if internal_goal:
            return internal_goal

        # 5. Validate
        is_valid, validation_msg = self.validator.validate(user_input, tokens)
        if not is_valid:
            raise ValueError(f"Unable to determine intent. {validation_msg}")

        # 6. Classify
        best_category, category_scores = self.classifier.classify(
            normalized_text, normalized_tokens
        )

        self.debug_info.category_scores = category_scores
        self.debug_info.selected_category = best_category

        # 7. Calculate confidence
        confidence = self.confidence_calculator.calculate(
            category_scores, best_category
        )
        self.debug_info.confidence = confidence
        self.debug_info.print_debug()

        # 8. Low-confidence → unknown
        if self.confidence_calculator.is_low_confidence(confidence):
            best_category = "unknown"

        # 9. Extract requirements
        requirements = self.extractor.extract(user_input, tokens)

        # 10. Generate intent summary
        intent_summary = self._generate_intent_summary(
            user_input, best_category, requirements
        )

        goal = Goal(
            goal=user_input,
            category=best_category,
            requirements=requirements,
            priority="normal",
            confidence=confidence,
            intent_summary=intent_summary,
        )

        logger.info(
            f"Goal generated: Category={goal.category}, Confidence={goal.confidence}%"
        )
        return goal

    # ------------------------------------------------------------------

    def _generate_intent_summary(
        self, user_input: str, category: str, requirements: List[str]
    ) -> str:
        category_display = category.replace("_", " ").capitalize()
        requirements_str = ", ".join(requirements[:3]) if requirements else ""
        if requirements:
            return (
                f"User wants to perform {category_display} task: {user_input}. "
                f"Key requirements: {requirements_str}"
            )
        return f"User wants to perform {category_display} task: {user_input}"


brain = Brain()
