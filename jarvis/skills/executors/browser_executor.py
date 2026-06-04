"""
browser_executor.py
===================
BrowserExecutor — lightweight web interaction.

This is intentionally minimal for Milestone 2.
No Playwright, no Selenium, no autonomous clicking.

Supported actions
-----------------
open_url      : open a URL in the system default browser
search        : perform a web search (opens browser with query)
fetch_page    : fetch page content via requests + BeautifulSoup
fetch_snippet : fetch and return a short text snippet from a URL

Future compatibility
--------------------
The class is designed so that Playwright / Selenium can be plugged in
as additional action handlers in Milestone 3 without changing the interface.
"""

from __future__ import annotations

import logging
import webbrowser
from typing import Optional
from urllib.parse import quote_plus

from jarvis.execution.execution_context import ExecutionContext, RiskLevel
from jarvis.skills.base import BaseExecutor

logger = logging.getLogger(__name__)

_SEARCH_BASE = "https://www.google.com/search?q="
_REQUEST_TIMEOUT = 15   # seconds


class BrowserExecutor(BaseExecutor):

    SUPPORTED_ACTIONS = [
        "open_url",
        "search",
        "fetch_page",
        "fetch_snippet",
    ]

    ACTION_RISK_MAP = {
        "open_url":      RiskLevel.MEDIUM,
        "search":        RiskLevel.MEDIUM,
        "fetch_page":    RiskLevel.MEDIUM,
        "fetch_snippet": RiskLevel.MEDIUM,
    }

    # ── Action handlers ────────────────────────────────────────────────────────

    def _action_open_url(self, ctx: ExecutionContext) -> str:
        url = ctx.params.get("url", "")
        self._validate_url(url)
        webbrowser.open(url)
        logger.info(f"BrowserExecutor: opened {url}")
        return f"Opened in browser: {url}"

    def _action_search(self, ctx: ExecutionContext) -> str:
        query = ctx.params.get("query", "")
        if not query:
            raise ValueError("Search query cannot be empty.")
        url = _SEARCH_BASE + quote_plus(query)
        webbrowser.open(url)
        logger.info(f"BrowserExecutor: search opened for {query!r}")
        return f"Search opened: {query!r}"

    def _action_fetch_page(self, ctx: ExecutionContext) -> str:
        url = ctx.params.get("url", "")
        self._validate_url(url)
        return self._fetch(url, max_chars=3000)

    def _action_fetch_snippet(self, ctx: ExecutionContext) -> str:
        url = ctx.params.get("url", "")
        self._validate_url(url)
        return self._fetch(url, max_chars=500)

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _validate_url(url: str) -> None:
        if not url:
            raise ValueError("URL cannot be empty.")
        if not url.startswith(("https://", "http://")):
            raise ValueError(f"URL must start with https:// or http://: {url!r}")

    @staticmethod
    def _fetch(url: str, max_chars: int = 3000) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return (
                f"[BrowserExecutor] requests/beautifulsoup4 not installed. "
                f"Run: pip install requests beautifulsoup4"
            )

        try:
            headers = {"User-Agent": "JARVIS/0.3 (research assistant)"}
            resp    = requests.get(url, timeout=_REQUEST_TIMEOUT, headers=headers)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script/style noise
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = " ".join(text.split())   # collapse whitespace
            snippet = text[:max_chars]
            if len(text) > max_chars:
                snippet += "…"

            logger.info(f"BrowserExecutor: fetched {url} ({len(text)} chars)")
            return snippet

        except Exception as exc:
            raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
