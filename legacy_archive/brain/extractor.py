"""
extractor.py
============
RequirementsExtractor — extracts meaningful entities from user input.

For computer_control goals the requirements list should contain
the target app name or object (e.g. "brave", "discord") NOT
raw action verbs or UI noise words like "enter", "click", "screen".

Filtering rules
---------------
- Action verbs ("scroll", "click", "press", "type", "open") are excluded
  unless they are part of a longer meaningful compound.
- Generic UI terms ("enter", "tab", "screen", "window") are excluded
  from the standalone noun list.
- Meaningful entities (app names, project names, real objects) are kept.
"""

from typing import List


# Words that are action verbs / UI terms and should NOT appear as requirements
_UI_NOISE: set = {
    "enter", "tab", "space", "escape", "esc", "backspace", "delete",
    "screen", "display", "desktop", "cursor", "pointer",
    "click", "scroll", "press", "type", "move", "drag", "hover",
    "open", "close", "launch", "start", "run", "focus",
    "maximize", "minimize", "resize", "show", "hide",
    "search", "find", "go", "navigate", "refresh",
    "copy", "paste", "cut", "undo", "redo",
    "text", "key", "button", "icon",
    "mouse", "keyboard",
}


class RequirementsExtractor:
    """
    Extracts meaningful requirements from user input.

    Strategy (priority order)
    1. Compound / multi-word entities — extracted as single units.
    2. Adjective / style modifiers — only for design/software contexts.
    3. Standalone meaningful noun keywords — excluding UI noise words.
    """

    def __init__(self):
        # Multi-word entities — checked first, longest match wins
        self.compound_entities: List[str] = [
            # Software / project entities
            "premium AI course",
            "AI course",
            "employee management system",
            "employee management",
            "inventory management system",
            "inventory management",
            "inventory dashboard",
            "cybersecurity banner",
            "company banner",
            "marketing banner",
            "modern design",
            "futuristic design",
            "dark futuristic",
            "temporary files",
            "daily backup",
            "rest api",
            "backend api",
            "admin dashboard",
            "analytics dashboard",
            "sales dashboard",
            "ecommerce platform",
            "social media post",
            "brand identity",
            # App names (multi-word)
            "google chrome",
            "visual studio code",
            "vs code",
            "microsoft edge",
            "brave browser",
        ]

        # Adjective / style modifiers (design/software context only)
        self.modifiers: List[str] = [
            "premium", "modern", "futuristic", "dark", "light", "simple",
            "complex", "professional", "elegant", "minimal", "colorful",
            "monochrome", "advanced", "basic", "custom", "automated",
            "real-time", "interactive",
        ]

        # Core noun keywords — meaningful entities ONLY, no UI noise
        self.noun_keywords: List[str] = [
            # Web / software artifacts
            "website", "poster", "brochure", "system", "app", "application",
            "design", "proposal", "email", "backup", "logo", "banner",
            "dashboard", "platform", "portal", "inventory", "crm",
            "api", "database", "script", "bot", "workflow", "report",
            "invoice", "presentation", "infographic", "flyer", "thumbnail",
            "mockup", "illustration",
            # App names (single-word) — meaningful to extract
            "chrome", "brave", "firefox", "edge", "opera",
            "discord", "telegram", "slack", "spotify", "steam",
            "notepad", "vscode", "photoshop", "figma",
            "word", "excel", "powerpoint", "outlook",
            "calculator", "paint",
        ]

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract(self, text: str, tokens: List[str]) -> List[str]:
        requirements: List[str] = []
        text_lower = text.lower()

        # ── Step 1: compound entities (longest first) ──────────────────────
        sorted_compounds = sorted(self.compound_entities, key=len, reverse=True)
        matched_spans: List[tuple] = []
        for entity in sorted_compounds:
            idx = text_lower.find(entity.lower())
            if idx != -1:
                span = (idx, idx + len(entity))
                if not any(s <= idx < e or s < idx + len(entity) <= e
                           for s, e in matched_spans):
                    requirements.append(entity)
                    matched_spans.append(span)

        # ── Step 2: modifiers (only for design/software goals) ─────────────
        for modifier in self.modifiers:
            if modifier.lower() in text_lower:
                if not self._already_covered(modifier, requirements):
                    requirements.append(modifier)

        # ── Step 3: standalone meaningful nouns (no UI noise) ─────────────
        for keyword in self.noun_keywords:
            kw_lower = keyword.lower()
            if kw_lower in _UI_NOISE:
                continue                          # skip noise words
            if kw_lower in text_lower:
                if not self._already_covered(kw_lower, requirements):
                    requirements.append(keyword)

        # ── Deduplicate and sort ──────────────────────────────────────────
        unique: List[str] = []
        seen: set = set()
        for req in requirements:
            key = req.lower()
            if key not in seen:
                seen.add(key)
                unique.append(req)

        unique.sort(key=str.lower)
        return unique

    def _already_covered(self, term: str, existing: List[str]) -> bool:
        term_lower = term.lower()
        for req in existing:
            if term_lower in req.lower():
                return True
        return False
