"""
test_cases.py
=============
All structured test case definitions for the JARVIS QA framework.

Each test case is a dict with:
  input              : str   — raw user input
  expected_category  : str   — expected classification result
  min_confidence     : float — minimum acceptable confidence %
  expected_reqs      : list  — substrings that MUST appear in requirements
                               (empty list = no requirement check)
  should_reject      : bool  — True if input should raise ValueError (invalid)
  tags               : list  — labels for grouping / filtering
"""

from typing import List, Dict, Any

TestCase = Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# 1. DESIGN
# ─────────────────────────────────────────────────────────────────────────────
DESIGN_CASES: List[TestCase] = [
    {
        "input": "Create brochure",
        "expected_category": "design",
        "min_confidence": 70,
        "expected_reqs": ["brochure"],
        "should_reject": False,
        "tags": ["design", "core"],
    },
    {
        "input": "Create poster",
        "expected_category": "design",
        "min_confidence": 70,
        "expected_reqs": ["poster"],
        "should_reject": False,
        "tags": ["design", "core"],
    },
    {
        "input": "Make futuristic logo",
        "expected_category": "design",
        "min_confidence": 65,
        "expected_reqs": ["logo"],
        "should_reject": False,
        "tags": ["design", "synonym"],
    },
    {
        "input": "Create premium AI course poster with modern design",
        "expected_category": "design",
        "min_confidence": 70,
        "expected_reqs": ["poster", "premium AI course", "modern design"],
        "should_reject": False,
        "tags": ["design", "phrase", "requirements"],
    },
    {
        "input": "Design a company banner",
        "expected_category": "design",
        "min_confidence": 70,
        "expected_reqs": ["banner"],
        "should_reject": False,
        "tags": ["design", "core"],
    },
    {
        "input": "Build a cybersecurity banner",
        "expected_category": "design",
        "min_confidence": 65,
        "expected_reqs": ["cybersecurity banner"],
        "should_reject": False,
        "tags": ["design", "phrase"],
    },
    {
        "input": "Make a marketing flyer",
        "expected_category": "design",
        "min_confidence": 65,
        "expected_reqs": ["flyer"],
        "should_reject": False,
        "tags": ["design", "synonym"],
    },
    {
        "input": "Generate a brand identity",
        "expected_category": "design",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["design", "synonym"],
    },
    {
        "input": "Design a modern infographic",
        "expected_category": "design",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["design"],
    },
    {
        "input": "Create a social media post",
        "expected_category": "design",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["design", "phrase"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. SOFTWARE DEVELOPMENT
# ─────────────────────────────────────────────────────────────────────────────
SOFTWARE_CASES: List[TestCase] = [
    {
        "input": "Build website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": ["website"],
        "should_reject": False,
        "tags": ["software", "core"],
    },
    {
        "input": "Build employee management system",
        "expected_category": "software_development",
        "min_confidence": 75,
        "expected_reqs": ["employee management system"],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Make inventory dashboard",
        "expected_category": "software_development",
        "min_confidence": 75,
        "expected_reqs": ["inventory dashboard"],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Generate CRM platform",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "synonym"],
    },
    {
        "input": "Develop a REST API",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Build a web application",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Create a mobile app",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software"],
    },
    {
        "input": "Build an admin dashboard",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Create an ecommerce platform",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "phrase"],
    },
    {
        "input": "Generate admin portal",
        "expected_category": "software_development",
        "min_confidence": 65,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["software", "synonym"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. SYSTEM OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_OPS_CASES: List[TestCase] = [
    {
        "input": "Clean temporary files",
        "expected_category": "system_operations",
        "min_confidence": 75,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops", "phrase"],
    },
    {
        "input": "Monitor server logs",
        "expected_category": "system_operations",
        "min_confidence": 75,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops", "phrase"],
    },
    {
        "input": "Schedule daily backup",
        "expected_category": "system_operations",
        "min_confidence": 75,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops", "phrase"],
    },
    {
        "input": "Deploy server update",
        "expected_category": "system_operations",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops"],
    },
    {
        "input": "Restart the service",
        "expected_category": "system_operations",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops"],
    },
    {
        "input": "Run disk cleanup",
        "expected_category": "system_operations",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["system_ops"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. COMMUNICATION
# ─────────────────────────────────────────────────────────────────────────────
COMMUNICATION_CASES: List[TestCase] = [
    {
        "input": "Send proposal to client",
        "expected_category": "communication",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["communication", "phrase"],
    },
    {
        "input": "Send email to client",
        "expected_category": "communication",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["communication"],
    },
    {
        "input": "Write a newsletter",
        "expected_category": "communication",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["communication"],
    },
    {
        "input": "Draft internship email",
        "expected_category": "communication",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["communication", "synonym"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 5. RESEARCH
# ─────────────────────────────────────────────────────────────────────────────
RESEARCH_CASES: List[TestCase] = [
    {
        "input": "Research AI models",
        "expected_category": "research",
        "min_confidence": 65,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["research"],
    },
    {
        "input": "Analyze competitors",
        "expected_category": "research",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["research"],
    },
    {
        "input": "Find market statistics",
        "expected_category": "research",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["research"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 6. AUTOMATION
# ─────────────────────────────────────────────────────────────────────────────
AUTOMATION_CASES: List[TestCase] = [
    {
        "input": "Automate daily report generation",
        "expected_category": "automation",
        "min_confidence": 65,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["automation"],
    },
    {
        "input": "Create a workflow bot",
        "expected_category": "automation",
        "min_confidence": 60,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["automation"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 7. INTERNAL COMMANDS
# ─────────────────────────────────────────────────────────────────────────────
INTERNAL_COMMAND_CASES: List[TestCase] = [
    {
        "input": "Enable debug mode",
        "expected_category": "internal_commands",
        "min_confidence": 90,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["internal", "debug"],
    },
    {
        "input": "Disable debug mode",
        "expected_category": "internal_commands",
        "min_confidence": 90,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["internal", "debug"],
    },
    {
        "input": "Show logs",
        "expected_category": "internal_commands",
        "min_confidence": 90,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["internal"],
    },
    {
        "input": "Clear memory",
        "expected_category": "internal_commands",
        "min_confidence": 90,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["internal"],
    },
    {
        "input": "Toggle verbose mode",
        "expected_category": "internal_commands",
        "min_confidence": 90,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["internal"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 8. INVALID / GIBBERISH (should_reject = True)
# ─────────────────────────────────────────────────────────────────────────────
INVALID_CASES: List[TestCase] = [
    {
        "input": "asdfghjkl",
        "expected_category": "unknown",
        "min_confidence": 0,
        "expected_reqs": [],
        "should_reject": True,
        "tags": ["invalid", "gibberish"],
    },
    {
        "input": "123456789",
        "expected_category": "unknown",
        "min_confidence": 0,
        "expected_reqs": [],
        "should_reject": True,
        "tags": ["invalid", "numbers"],
    },
    {
        "input": "zzzzzzzzz",
        "expected_category": "unknown",
        "min_confidence": 0,
        "expected_reqs": [],
        "should_reject": True,
        "tags": ["invalid", "repetition"],
    },
    {
        "input": "qwerty",
        "expected_category": "unknown",
        "min_confidence": 0,
        "expected_reqs": [],
        "should_reject": True,
        "tags": ["invalid", "keyboard"],
    },
    {
        "input": "!!!###$$$",
        "expected_category": "unknown",
        "min_confidence": 0,
        "expected_reqs": [],
        "should_reject": True,
        "tags": ["invalid", "symbols"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 9. SYNONYM NORMALISATION (same category regardless of verb)
# ─────────────────────────────────────────────────────────────────────────────
SYNONYM_CASES: List[TestCase] = [
    {
        "input": "Build website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["synonym", "software"],
    },
    {
        "input": "Create website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["synonym", "software"],
    },
    {
        "input": "Develop website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["synonym", "software"],
    },
    {
        "input": "Generate website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["synonym", "software"],
    },
    {
        "input": "Make website",
        "expected_category": "software_development",
        "min_confidence": 70,
        "expected_reqs": [],
        "should_reject": False,
        "tags": ["synonym", "software"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 10. STRESS TESTS (rapid-fire mixed inputs)
# ─────────────────────────────────────────────────────────────────────────────
STRESS_CASES: List[TestCase] = [
    {"input": "Create logo",                          "expected_category": "design",                "min_confidence": 65, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Generate flyer",                       "expected_category": "design",                "min_confidence": 65, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Build CRM",                            "expected_category": "software_development",  "min_confidence": 65, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Monitor logs",                         "expected_category": "system_operations",     "min_confidence": 70, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Enable debug mode",                    "expected_category": "internal_commands",     "min_confidence": 90, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Create AI course poster",              "expected_category": "design",                "min_confidence": 70, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Analyze competitors",                  "expected_category": "research",              "min_confidence": 60, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Draft internship email",               "expected_category": "communication",         "min_confidence": 60, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "asdfghjkl",                            "expected_category": "unknown",               "min_confidence": 0,  "expected_reqs": [], "should_reject": True,  "tags": ["stress"]},
    {"input": "Clean temporary files",                "expected_category": "system_operations",     "min_confidence": 75, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Generate admin portal",                "expected_category": "software_development",  "min_confidence": 65, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Design cybersecurity banner",          "expected_category": "design",                "min_confidence": 70, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Send proposal to client",              "expected_category": "communication",         "min_confidence": 70, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Schedule daily backup",                "expected_category": "system_operations",     "min_confidence": 75, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
    {"input": "Build employee management system",     "expected_category": "software_development",  "min_confidence": 75, "expected_reqs": [], "should_reject": False, "tags": ["stress"]},
]


# ─────────────────────────────────────────────────────────────────────────────
# Master list — all suites combined
# ─────────────────────────────────────────────────────────────────────────────
ALL_TEST_CASES: List[TestCase] = (
    DESIGN_CASES
    + SOFTWARE_CASES
    + SYSTEM_OPS_CASES
    + COMMUNICATION_CASES
    + RESEARCH_CASES
    + AUTOMATION_CASES
    + INTERNAL_COMMAND_CASES
    + INVALID_CASES
    + SYNONYM_CASES
    + STRESS_CASES
)

# Suite registry for selective runs
SUITES = {
    "design":           DESIGN_CASES,
    "software":         SOFTWARE_CASES,
    "system_ops":       SYSTEM_OPS_CASES,
    "communication":    COMMUNICATION_CASES,
    "research":         RESEARCH_CASES,
    "automation":       AUTOMATION_CASES,
    "internal":         INTERNAL_COMMAND_CASES,
    "invalid":          INVALID_CASES,
    "synonym":          SYNONYM_CASES,
    "stress":           STRESS_CASES,
    "all":              ALL_TEST_CASES,
}
