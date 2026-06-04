from typing import Dict, List


class CategoryDefinition:
    def __init__(
        self,
        name: str,
        keywords: List[str],
        weights: Dict[str, float] = None,
        required_skills: List[str] = None,
    ):
        self.name = name
        self.keywords = keywords
        self.weights = weights or {kw: 1.0 for kw in keywords}
        self.required_skills = required_skills or []


# ---------------------------------------------------------------------------
# Phrase patterns: multi-word strings that strongly signal a category.
# Keys are lowercase phrases; values are (category_name, score) tuples.
# Phrase matches are evaluated BEFORE single-token scoring and carry higher
# weight, so they can override ambiguous single-token results.
# ---------------------------------------------------------------------------
PHRASE_PATTERNS: Dict[str, tuple] = {
    # voice_interaction and text_to_speech phrases (high weight for fast matching!)
    "speak": ("text_to_speech", 20.0),
    "speak ": ("text_to_speech", 18.0),
    "say": ("text_to_speech", 20.0),
    "say ": ("text_to_speech", 18.0),
    "read aloud": ("text_to_speech", 18.0),
    "talk": ("text_to_speech", 18.0),
    "talk ": ("text_to_speech", 18.0),
    "announce": ("text_to_speech", 18.0),
    "test speaker": ("text_to_speech", 20.0),
    "test speakers": ("text_to_speech", 20.0),
    "speaker test": ("text_to_speech", 20.0),
    "use": ("voice_interaction", 18.0),
    "use ": ("voice_interaction", 18.0),
    "switch to": ("voice_interaction", 18.0),
    "switch to ": ("voice_interaction", 18.0),
    "stop speaking": ("speech_control", 20.0),
    "stop talking": ("speech_control", 20.0),
    "mute": ("speech_control", 18.0),
    "mute voice": ("speech_control", 18.0),
    "cancel voice": ("speech_control", 18.0),
    "silence": ("speech_control", 18.0),
    "enable voice mode": ("voice_interaction", 18.0),
    "start listening": ("voice_interaction", 18.0),
    "activate microphone": ("voice_interaction", 18.0),
    "begin conversation": ("voice_interaction", 18.0),
    "talk to me": ("voice_interaction", 20.0),
    "continue conversation": ("voice_interaction", 18.0),
    "respond with voice": ("voice_interaction", 18.0),
    # software_development phrases
    "employee management system":   ("software_development", 10.0),
    "employee management":          ("software_development", 8.0),
    "inventory dashboard":          ("software_development", 8.0),
    "inventory management":         ("software_development", 8.0),
    "inventory system":             ("software_development", 8.0),
    "crm system":                   ("software_development", 8.0),
    "management system":            ("software_development", 6.0),
    "web application":              ("software_development", 8.0),
    "web app":                      ("software_development", 8.0),
    "mobile app":                   ("software_development", 8.0),
    "rest api":                     ("software_development", 8.0),
    "backend api":                  ("software_development", 8.0),
    "admin dashboard":              ("software_development", 7.0),
    "analytics dashboard":          ("software_development", 7.0),
    "sales dashboard":              ("software_development", 7.0),
    "ecommerce platform":           ("software_development", 8.0),
    "e-commerce platform":          ("software_development", 8.0),
    # design phrases
    "course poster":                ("design", 8.0),
    "ai course poster":             ("design", 9.0),
    "cybersecurity banner":         ("design", 8.0),
    "company banner":               ("design", 7.0),
    "marketing banner":             ("design", 7.0),
    "social media post":            ("design", 7.0),
    "brand identity":               ("design", 7.0),
    "modern design":                ("design", 6.0),
    "futuristic design":            ("design", 6.0),
    "premium design":               ("design", 5.0),
    # system_operations phrases
    "temporary files":              ("system_operations", 8.0),
    "temp files":                   ("system_operations", 8.0),
    "daily backup":                 ("system_operations", 8.0),
    "monitor logs":                 ("system_operations", 8.0),
    "server logs":                  ("system_operations", 7.0),
    "cron job":                     ("system_operations", 8.0),
    "disk cleanup":                 ("system_operations", 8.0),
    # communication phrases
    "send email":                   ("communication", 8.0),
    "send proposal":                ("communication", 8.0),
    "write email":                  ("communication", 7.0),
    "client proposal":              ("communication", 7.0),
    # computer_control phrases — browsers
    "open brave":               ("computer_control", 9.0),
    "open firefox":             ("computer_control", 9.0),
    "open edge":                ("computer_control", 9.0),
    "open microsoft edge":      ("computer_control", 9.0),
    "launch brave":             ("computer_control", 9.0),
    "launch firefox":           ("computer_control", 9.0),
    "launch edge":              ("computer_control", 9.0),
    # computer_control phrases — apps
    "open discord":             ("computer_control", 9.0),
    "open spotify":             ("computer_control", 9.0),
    "open telegram":            ("computer_control", 9.0),
    "open slack":               ("computer_control", 9.0),
    "open steam":               ("computer_control", 9.0),
    "open calculator":          ("computer_control", 9.0),
    "open paint":               ("computer_control", 9.0),
    "open word":                ("computer_control", 9.0),
    "open excel":               ("computer_control", 9.0),
    "open explorer":            ("computer_control", 9.0),
    "launch discord":           ("computer_control", 9.0),
    "launch spotify":           ("computer_control", 9.0),
    "launch steam":             ("computer_control", 9.0),
    # computer_control phrases — actions (existing + new)
    "scroll down":              ("computer_control", 9.0),
    "scroll up":                ("computer_control", 9.0),
    "move mouse to center":     ("computer_control", 9.0),
    "right click":              ("computer_control", 8.0),
    "double click":             ("computer_control", 8.0),
    "type hello world":         ("computer_control", 8.0),
    "press enter":              ("computer_control", 8.0),
    "open chrome":              ("computer_control", 8.0),
    "open browser":             ("computer_control", 8.0),
    "search google":            ("computer_control", 8.0),
    "open website":             ("computer_control", 8.0),
    "take screenshot":          ("computer_control", 8.0),
    "capture screen":           ("computer_control", 8.0),
    "maximize vscode":          ("computer_control", 8.0),
    "maximize window":          ("computer_control", 8.0),
    "minimize window":          ("computer_control", 8.0),
    "focus window":             ("computer_control", 8.0),
    "open notepad":             ("computer_control", 8.0),
    "open vscode":              ("computer_control", 8.0),
    "open vs code":             ("computer_control", 9.0),
    "open visual studio code":  ("computer_control", 9.0),
    "launch application":       ("computer_control", 8.0),
}


CATEGORIES: List[CategoryDefinition] = [
    # ------------------------------------------------------------------
    # software_development
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="software_development",
        keywords=[
            "code", "coding", "software", "program", "develop", "developer",
            "app", "application", "website", "web", "build", "system",
            "dashboard", "platform", "portal", "inventory", "crm",
            "backend", "frontend", "api", "database", "framework",
            "react", "python", "javascript", "typescript", "java",
            "node", "django", "flask", "fastapi", "microservice",
            "employee", "management",
        ],
        weights={
            "code":         4.0,
            "coding":       4.0,
            "software":     3.5,
            "website":      4.0,
            "app":          3.5,
            "application":  4.0,
            "dashboard":    4.0,
            "platform":     3.5,
            "portal":       3.5,
            "inventory":    4.0,
            "crm":          5.0,
            "backend":      4.0,
            "frontend":     4.0,
            "api":          4.0,
            "system":       2.5,
            "build":        2.0,
            "management":   2.0,
            "employee":     2.5,
            "react":        3.5,
            "python":       3.5,
            "javascript":   3.5,
            "typescript":   3.5,
            "django":       4.0,
            "flask":        4.0,
            "database":     3.0,
            "framework":    3.0,
        },
        required_skills=["coding_skill", "terminal_skill", "file_skill"],
    ),

    # ------------------------------------------------------------------
    # design
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="design",
        keywords=[
            "poster", "design", "canva", "graphic", "layout", "brochure",
            "flyer", "logo", "banner", "presentation", "infographic",
            "visual", "art", "branding", "creative", "modern", "futuristic",
            "marketing", "theme", "mockup", "thumbnail", "illustration",
            "typography", "color", "palette", "aesthetic",
        ],
        weights={
            "poster":       5.0,
            "brochure":     5.0,
            "flyer":        5.0,
            "banner":       5.0,
            "logo":         5.0,
            "design":       4.0,
            "canva":        4.0,
            "graphic":      4.0,
            "branding":     4.0,
            "infographic":  4.0,
            "creative":     3.0,
            "visual":       3.0,
            "marketing":    3.0,
            "modern":       2.0,
            "futuristic":   2.0,
            "theme":        2.0,
            "mockup":       4.0,
            "thumbnail":    4.0,
            "illustration": 4.0,
            "typography":   3.0,
            "presentation": 3.0,
            "layout":       3.0,
        },
        required_skills=["canva_skill", "browser_skill"],
    ),

    # ------------------------------------------------------------------
    # research
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="research",
        keywords=[
            "research", "search", "find", "information", "investigate",
            "study", "analyze", "analysis", "data", "statistics", "survey",
            "report", "compare", "review",
        ],
        weights={
            "research":    4.0,
            "investigate": 3.5,
            "analyze":     3.0,
            "analysis":    3.0,
            "search":      2.5,
            "find":        2.0,
            "statistics":  3.0,
            "survey":      3.0,
        },
        required_skills=["browser_skill"],
    ),

    # ------------------------------------------------------------------
    # automation
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="automation",
        keywords=[
            "automate", "automation", "bot", "script", "schedule",
            "workflow", "pipeline", "trigger", "recurring",
        ],
        weights={
            "automate":   4.0,
            "automation": 4.0,
            "bot":        3.5,
            "script":     3.0,
            "schedule":   3.0,
            "workflow":   3.0,
            "pipeline":   3.0,
            "trigger":    3.0,
        },
        required_skills=["coding_skill", "terminal_skill"],
    ),

    # ------------------------------------------------------------------
    # communication
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="communication",
        keywords=[
            "send", "message", "email", "chat", "call", "text", "talk",
            "communicate", "proposal", "client", "customer", "notify",
            "newsletter", "outreach",
        ],
        weights={
            "email":       4.0,
            "proposal":    4.0,
            "send":        3.0,
            "message":     3.0,
            "notify":      3.0,
            "newsletter":  3.5,
            "outreach":    3.5,
            "client":      2.5,
            "customer":    2.5,
        },
        required_skills=["gmail_skill"],
    ),

    # ------------------------------------------------------------------
    # system_operations
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="system_operations",
        keywords=[
            "backup", "restore", "server", "deploy", "maintenance",
            "cleanup", "clean", "temporary", "logs", "cron", "monitor",
            "delete", "remove", "disk", "storage", "process", "service",
            "reboot", "restart", "update", "patch", "install",
        ],
        weights={
            "backup":      5.0,
            "restore":     5.0,
            "cleanup":     5.0,
            "clean":       4.0,
            "temporary":   4.0,
            "monitor":     5.0,
            "logs":        4.0,
            "server":      5.0,
            "cron":        5.0,
            "maintenance": 5.0,
            "deploy":      4.5,
            "disk":        4.0,
            "storage":     3.5,
            "reboot":      4.0,
            "restart":     4.0,
            "update":      3.0,
            "patch":       3.5,
            "install":     3.0,
            "delete":      3.0,
            "remove":      3.0,
            "process":     2.5,
            "service":     2.5,
        },
        required_skills=["terminal_skill", "file_skill"],
    ),

    # ------------------------------------------------------------------
    # productivity
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="productivity",
        keywords=[
            "organize", "todo", "task", "note", "reminder", "calendar",
            "schedule", "plan", "agenda", "checklist",
        ],
        weights={
            "organize":  3.0,
            "todo":      3.0,
            "reminder":  3.0,
            "calendar":  3.0,
            "agenda":    3.0,
            "checklist": 3.0,
        },
        required_skills=[],
    ),

    # ------------------------------------------------------------------
    # business
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="business",
        keywords=[
            "business", "finance", "invoice", "revenue", "profit",
            "budget", "expense", "accounting", "payroll",
        ],
        weights={
            "business":   3.0,
            "invoice":    4.0,
            "finance":    3.5,
            "revenue":    3.5,
            "budget":     3.5,
            "accounting": 4.0,
            "payroll":    4.0,
        },
        required_skills=["gmail_skill", "browser_skill"],
    ),

    # ------------------------------------------------------------------
    # internal_commands  (new category)
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="internal_commands",
        keywords=[
            "debug", "verbose", "logs", "memory", "history",
            "enable", "disable", "toggle", "clear", "reset", "status",
            "config", "settings",
        ],
        weights={
            "debug":   5.0,
            "verbose": 4.0,
            "enable":  3.0,
            "disable": 3.0,
            "toggle":  3.0,
            "clear":   3.0,
            "reset":   3.0,
            "status":  2.5,
            "config":  3.0,
            "settings": 3.0,
        },
        required_skills=[],
    ),
    # ------------------------------------------------------------------
    # computer_control
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="computer_control",
        keywords=[
            # Mouse actions
            "move", "mouse", "click", "right", "double", "scroll", "drag",
            "hover", "up", "down",
            # Keyboard actions
            "type", "press", "hotkey", "shortcut", "enter", "tab",
            "save", "copy", "paste", "undo", "redo",
            # Browser names
            "chrome", "brave", "firefox", "edge", "opera", "browser",
            # App names
            "discord", "spotify", "telegram", "slack", "steam",
            "notepad", "vscode", "calculator", "paint", "word",
            "excel", "powerpoint", "outlook", "explorer",
            # Actions
            "search", "website", "refresh",
            "maximize", "minimize", "focus", "switch", "window",
            "screenshot", "capture", "screen",
            "launch", "open",
        ],
        weights={
            # Mouse — high weights since these are unambiguous control signals
            "move":        3.0,
            "mouse":       4.5,
            "click":       4.5,
            "right":       3.5,
            "double":      3.5,
            "scroll":      4.5,
            "drag":        4.0,
            "up":          2.0,
            "down":        2.0,
            # Keyboard
            "type":        4.0,
            "press":       4.5,
            "enter":       3.5,
            "tab":         3.0,
            "save":        3.0,
            "copy":        3.0,
            "paste":       3.0,
            # Browsers — very strong signals
            "chrome":      5.0,
            "brave":       5.0,
            "firefox":     5.0,
            "edge":        5.0,
            "opera":       5.0,
            "browser":     4.0,
            # Apps — strong signals
            "discord":     5.0,
            "spotify":     5.0,
            "telegram":    5.0,
            "slack":       5.0,
            "steam":       5.0,
            "notepad":     4.5,
            "vscode":      4.5,
            "calculator":  4.5,
            "paint":       4.0,
            "word":        3.5,
            "excel":       3.5,
            "powerpoint":  4.0,
            "outlook":     4.0,
            "explorer":    3.5,
            # Other
            "search":      3.0,
            "website":     3.0,
            "screenshot":  5.0,
            "capture":     4.0,
            "screen":      3.0,
            "launch":      4.0,
            "open":        3.0,
            "maximize":    3.5,
            "minimize":    3.5,
            "focus":       3.5,
            "window":      3.0,
        },
        required_skills=["computer_control_skill", "mouse_skill", "keyboard_skill"],
    ),

    # ------------------------------------------------------------------
    # text_to_speech
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="text_to_speech",
        keywords=[
            "speak", "say", "read aloud", "talk", "announce", "voice", "tts",
        ],
        weights={
            "speak":        10.0,
            "say":          10.0,
            "read aloud":   8.0,
            "announce":     8.0,
            "tts":          8.0,
        },
        required_skills=["voice_skill"],
    ),

    # ------------------------------------------------------------------
    # voice_interaction
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="voice_interaction",
        keywords=[
            "voice mode", "listening", "microphone", "conversation",
            "talk to me", "respond with voice", "begin conversation",
        ],
        weights={
            "voice mode":         10.0,
            "microphone":         9.0,
            "listening":          8.0,
            "conversation":       8.0,
            "talk to me":         8.0,
        },
        required_skills=["voice_skill"],
    ),

    # ------------------------------------------------------------------
    # speech_control
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="speech_control",
        keywords=[
            "stop speaking", "mute", "cancel voice", "silence",
            "stop talking",
        ],
        weights={
            "stop speaking":  10.0,
            "mute":           9.0,
            "silence":        9.0,
            "cancel voice":   9.0,
        },
        required_skills=["voice_skill"],
    ),

    # ------------------------------------------------------------------
    # general  (catch-all for help / questions)
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="general",
        keywords=["help", "what", "how", "explain", "tell", "show"],
        weights={
            "help":    2.0,
            "explain": 2.0,
            "tell":    1.5,
            "show":    1.5,
        },
        required_skills=[],
    ),

    # ------------------------------------------------------------------
    # unknown  (sentinel — never scored directly)
    # ------------------------------------------------------------------
    CategoryDefinition(
        name="unknown",
        keywords=[],
        weights={},
        required_skills=[],
    ),
]


# ---------------------------------------------------------------------------
# Internal-command phrase patterns (checked before normal classification)
# ---------------------------------------------------------------------------
INTERNAL_COMMAND_PHRASES: List[str] = [
    "enable debug mode",
    "disable debug mode",
    "toggle debug mode",
    "enable verbose mode",
    "disable verbose mode",
    "toggle verbose mode",
    "show logs",
    "clear memory",
    "clear history",
    "reset memory",
    "show status",
    "show config",
    "show settings",
    "debug mode",
    "verbose mode",
]


def get_category_by_name(name: str) -> CategoryDefinition:
    for category in CATEGORIES:
        if category.name == name:
            return category
    return None
