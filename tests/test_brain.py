"""
JARVIS v0.3 — Brain Intelligence Layer Test Suite
==================================================
Covers:
  - Semantic classification (design, software_development, system_operations,
    communication, research, automation, internal_commands)
  - Confidence scoring (realistic range, never 100 %)
  - Phrase detection
  - Verb synonym normalisation
  - Debug mode toggle
  - Internal command routing
  - Input validation (gibberish rejection)
  - Requirements extraction
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.brain import Brain
from brain.validator import InputValidator
from brain.normalizer import TextNormalizer
from brain.classifier import IntentClassifier
from brain.confidence import ConfidenceCalculator
from brain.preprocessing import Preprocessor

# Use a fresh Brain instance per test run so debug state doesn't bleed
_brain = Brain()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def classify(text: str) -> str:
    """Return the category string for a given input."""
    goal = _brain.analyze_task(text)
    return goal.category


def confidence(text: str) -> float:
    """Return the confidence score for a given input."""
    goal = _brain.analyze_task(text)
    return goal.confidence


PASS = "✅ PASS"
FAIL = "❌ FAIL"

_results = {"pass": 0, "fail": 0}


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        _results["pass"] += 1
        print(f"  ✓ PASS  {label}")
    else:
        _results["fail"] += 1
        print(f"  ✗ FAIL  {label}" + (f"  [{detail}]" if detail else ""))


# ──────────────────────────────────────────────────────────────────────────────
# 1. Design classification
# ──────────────────────────────────────────────────────────────────────────────

def test_design_classification():
    print("\n── 1. Design Classification ──────────────────────────────────────")
    cases = [
        "Create brochure",
        "Create poster",
        "Make futuristic logo",
        "Create premium AI course poster with modern design",
        "Design a company banner",
        "Build a cybersecurity banner",
        "Make a marketing flyer",
        "Generate a brand identity",
        "Create a social media post",
        "Design a modern infographic",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "design",
              f"expected design, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. Software development classification
# ──────────────────────────────────────────────────────────────────────────────

def test_software_development_classification():
    print("\n── 2. Software Development Classification ────────────────────────")
    cases = [
        "Build website",
        "Build employee management system",
        "Make inventory dashboard",
        "Create a CRM platform",
        "Develop a REST API",
        "Build a web application",
        "Create a mobile app",
        "Develop a backend API",
        "Build an admin dashboard",
        "Create an ecommerce platform",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "software_development",
              f"expected software_development, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. System operations classification
# ──────────────────────────────────────────────────────────────────────────────

def test_system_operations_classification():
    print("\n── 3. System Operations Classification ───────────────────────────")
    cases = [
        "Clean temporary files",
        "Monitor logs",
        "Schedule daily backup",
        "Deploy server update",
        "Restart the service",
        "Run disk cleanup",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "system_operations",
              f"expected system_operations, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 4. Communication classification
# ──────────────────────────────────────────────────────────────────────────────

def test_communication_classification():
    print("\n── 4. Communication Classification ───────────────────────────────")
    cases = [
        "Send proposal",
        "Send email to client",
        "Write a newsletter",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "communication",
              f"expected communication, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 4.5. Computer Control Classification
# ──────────────────────────────────────────────────────────────────────────────

def test_computer_control_classification():
    print("\n── 4.5. Computer Control Classification ───────────────────────────")
    cases = [
        "Move mouse",
        "Move mouse to center",
        "Right click",
        "Double click",
        "Type hello world",
        "Press enter",
        "Open Chrome",
        "Open browser",
        "Search google",
        "Open website",
        "Take screenshot",
        "Capture screen",
        "Maximize window",
        "Minimize window",
        "Focus window",
        "Open notepad",
        "Open VS Code",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "computer_control",
              f"expected computer_control, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Internal commands
# ──────────────────────────────────────────────────────────────────────────────

def test_internal_commands():
    print("\n── 5. Internal Commands ──────────────────────────────────────────")
    cases = [
        "Enable debug mode",
        "Disable debug mode",
        "Toggle debug mode",
        "Show logs",
        "Clear memory",
        "Enable verbose mode",
    ]
    for text in cases:
        result = classify(text)
        check(f'"{text}" → {result}', result == "internal_commands",
              f"expected internal_commands, got {result}")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Confidence scoring
# ──────────────────────────────────────────────────────────────────────────────

def test_confidence_scoring():
    print("\n── 6. Confidence Scoring ─────────────────────────────────────────")
    cases = [
        "Build website",
        "Monitor logs",
        "Clean temporary files",
        "Create brochure",
        "Send proposal",
    ]
    for text in cases:
        c = confidence(text)
        check(
            f'"{text}" confidence={c}% (must be 30–95)',
            30.0 <= c <= 95.0,
            f"out of range: {c}",
        )
        check(
            f'"{text}" confidence ≠ 100%',
            c < 100.0,
            f"got 100%",
        )


# ──────────────────────────────────────────────────────────────────────────────
# 7. Phrase detection
# ──────────────────────────────────────────────────────────────────────────────

def test_phrase_detection():
    print("\n── 7. Phrase Detection ───────────────────────────────────────────")
    preprocessor = Preprocessor()
    normalizer = TextNormalizer()
    classifier = IntentClassifier()

    phrase_cases = [
        ("Make inventory dashboard", "software_development"),
        ("Build employee management system", "software_development"),
        ("Create AI course poster", "design"),
        ("Design cybersecurity banner", "design"),
        ("Clean temporary files", "system_operations"),
        ("Schedule daily backup", "system_operations"),
        ("Open Chrome", "computer_control"),
        ("Move mouse to center", "computer_control"),
        ("Take screenshot", "computer_control"),
        ("Open notepad", "computer_control"),
    ]
    for text, expected_cat in phrase_cases:
        text_clean, tokens = preprocessor.preprocess(text)
        norm_text = normalizer.normalize_text(text_clean)
        norm_tokens = normalizer.normalize_tokens(tokens)
        best_cat, scores = classifier.classify(norm_text, norm_tokens)
        check(
            f'Phrase "{text}" → {best_cat}',
            best_cat == expected_cat,
            f"expected {expected_cat}, got {best_cat}",
        )


# ──────────────────────────────────────────────────────────────────────────────
# 8. Synonym normalisation
# ──────────────────────────────────────────────────────────────────────────────

def test_synonym_normalisation():
    print("\n── 8. Synonym Normalisation ──────────────────────────────────────")
    normalizer = TextNormalizer()

    verb_cases = [
        (["build", "website"], ["create", "website"]),
        (["develop", "app"], ["create", "app"]),
        (["generate", "report"], ["create", "report"]),
        (["make", "poster"], ["create", "poster"]),
        (["compose", "email"], ["write", "email"]),
        (["draft", "proposal"], ["write", "proposal"]),
    ]
    for tokens, expected in verb_cases:
        result = normalizer.normalize_tokens(tokens)
        check(
            f"normalize_tokens({tokens}) → {result}",
            result == expected,
            f"expected {expected}",
        )

    # Content nouns must NOT be altered
    preserved = ["poster", "logo", "brochure", "banner", "design", "dashboard"]
    for noun in preserved:
        result = normalizer.normalize_tokens([noun])
        check(
            f"Content noun '{noun}' preserved",
            result == [noun],
            f"was changed to {result}",
        )


# ──────────────────────────────────────────────────────────────────────────────
# 9. Debug mode toggle
# ──────────────────────────────────────────────────────────────────────────────

def test_debug_mode():
    print("\n── 9. Debug Mode Toggle ──────────────────────────────────────────")
    b = Brain()

    check("Debug starts disabled", not b.debug_info.enabled)

    b.debug_info.enable()
    check("enable() sets enabled=True", b.debug_info.enabled)

    b.debug_info.disable()
    check("disable() sets enabled=False", not b.debug_info.enabled)

    b.debug_info.toggle()
    check("toggle() flips to True", b.debug_info.enabled)

    b.debug_info.toggle()
    check("toggle() flips back to False", not b.debug_info.enabled)

    # Sending "Enable debug mode" as input should activate debug
    b2 = Brain()
    goal = b2.analyze_task("Enable debug mode")
    check(
        '"Enable debug mode" → internal_commands',
        goal.category == "internal_commands",
    )
    check("debug_info.enabled is True after command", b2.debug_info.enabled)


# ──────────────────────────────────────────────────────────────────────────────
# 10. Input validation
# ──────────────────────────────────────────────────────────────────────────────

def test_validation():
    print("\n── 10. Input Validation ──────────────────────────────────────────")
    validator = InputValidator()
    preprocessor = Preprocessor()

    invalid_cases = [
        "asdfghjkl",
        "zzzzz",
        "123456",
        "qwerty",
        "!!!",
    ]
    for text in invalid_cases:
        _, tokens = preprocessor.preprocess(text)
        is_valid, _ = validator.validate(text, tokens)
        check(f'"{text}" rejected as invalid', not is_valid)

    valid_cases = [
        "Create poster",
        "Build website",
        "Send email",
    ]
    for text in valid_cases:
        _, tokens = preprocessor.preprocess(text)
        is_valid, _ = validator.validate(text, tokens)
        check(f'"{text}" accepted as valid', is_valid)


# ──────────────────────────────────────────────────────────────────────────────
# 11. Requirements extraction
# ──────────────────────────────────────────────────────────────────────────────

def test_requirements_extraction():
    print("\n── 11. Requirements Extraction ───────────────────────────────────")
    b = Brain()

    cases = [
        (
            "Create premium AI course poster with modern design",
            ["premium AI course", "modern design", "poster"],
        ),
        (
            "Build employee management system",
            ["employee management system"],
        ),
        (
            "Make inventory dashboard",
            ["inventory dashboard"],
        ),
        (
            "Design cybersecurity banner",
            ["cybersecurity banner"],
        ),
    ]
    for text, must_contain in cases:
        goal = b.analyze_task(text)
        extracted_lower = [r.lower() for r in goal.requirements]
        for expected in must_contain:
            check(
                f'"{text}" contains requirement "{expected}"',
                expected.lower() in extracted_lower,
                f"extracted: {goal.requirements}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# 12. Confidence calculator unit tests
# ──────────────────────────────────────────────────────────────────────────────

def test_confidence_calculator():
    print("\n── 12. Confidence Calculator ─────────────────────────────────────")
    calc = ConfidenceCalculator()

    # Single dominant category → high but not 100 %
    scores_dominant = {
        "design": 20.0,
        "software_development": 0.0,
        "system_operations": 0.0,
        "unknown": 0.0,
    }
    c = calc.calculate(scores_dominant, "design")
    check(f"Dominant score → {c}% (must be ≤ 95)", c <= 95.0)
    check(f"Dominant score → {c}% (must be ≥ 30)", c >= 30.0)

    # Two equal categories → ambiguity penalty applied
    scores_tied = {
        "design": 10.0,
        "software_development": 10.0,
        "system_operations": 0.0,
        "unknown": 0.0,
    }
    c_tied = calc.calculate(scores_tied, "design")
    check(f"Tied scores → {c_tied}% (must be < 70)", c_tied < 70.0)

    # Zero scores → floor is now 30.0%
    scores_zero = {"design": 0.0, "software_development": 0.0, "unknown": 0.0}
    c_zero = calc.calculate(scores_zero, "design")
    check("Zero scores → floor 30.0%", c_zero == 30.0)
    
    # Also check LOW_CONFIDENCE_THRESHOLD is 40.0
    check("LOW_CONFIDENCE_THRESHOLD is 40.0", calc.LOW_CONFIDENCE_THRESHOLD == 40.0)

    # is_low_confidence
    check("39.9 is low confidence", calc.is_low_confidence(39.9))
    check("40.0 is NOT low confidence", not calc.is_low_confidence(40.0))
    check("80.0 is NOT low confidence", not calc.is_low_confidence(80.0))


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def test_computer_control_workflow_generator():
    print("\n── 13. Computer Control Workflow Generator ───────────────────────")
    from brain import control_workflow_generator

    workflow_cases = [
        "Open Chrome and search latest AI models",
        "Open notepad and type hello world",
        "Take screenshot",
        "Move mouse to center",
        "Right click",
        "Press enter",
        "Open VS Code",
    ]

    for text in workflow_cases:
        actions = control_workflow_generator.generate_from_input(text, "computer_control", [])
        check(f'"{text}" → {len(actions)} actions', len(actions) > 0)


if __name__ == "__main__":
    test_design_classification()
    test_software_development_classification()
    test_system_operations_classification()
    test_communication_classification()
    test_computer_control_classification()
    test_internal_commands()
    test_confidence_scoring()
    test_phrase_detection()
    test_synonym_normalisation()
    test_debug_mode()
    test_validation()
    test_requirements_extraction()
    test_confidence_calculator()
    test_computer_control_workflow_generator()

    total = _results["pass"] + _results["fail"]
    print(f"\n{'═' * 60}")
    print(f"  Results: {_results['pass']}/{total} passed"
          f"  ({_results['fail']} failed)")
    print(f"{'═' * 60}\n")

    if _results["fail"] > 0:
        sys.exit(1)
