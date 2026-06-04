
"""
response_validator.py
=====================
Validates LLM responses for safety, schema compliance, and sanity.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Error raised when validation fails."""
    pass


class ResponseValidator:
    """
    Validates LLM responses before they are used.
    """

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"format\s+[A-Za-z]:",
        r"del\s+[A-Za-z]:\\",
        r"mkfs\.",
        r":(){:|:&};:",
        r"base64.*-d.*pipe",
        r"curl.*sh",
        r"wget.*sh",
        r"eval\(",
        r"exec\(",
    ]

    def validate(
        self,
        response: str,
        expected_schema: Optional[Dict[str, Any]] = None,
        require_safe: bool = True,
    ) -> bool:
        """
        Validate an LLM response.
        """
        if require_safe:
            self._validate_safety(response)
        if expected_schema:
            self._validate_schema(response, expected_schema)
        return True

    def _validate_safety(self, response: str) -> None:
        """Validate that response doesn't contain dangerous patterns."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                logger.error(f"Dangerous pattern detected: {pattern}")
                raise ValidationError(f"Response contains dangerous content: {pattern}")

    def _validate_schema(self, response: str, schema: Dict[str, Any]) -> None:
        """Validate response structure against a schema (JSON schema subset)."""
        import json

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # If it's not JSON, check if schema allows plain text
            if schema.get("type") != "string":
                raise ValidationError("Response is not valid JSON")
            return

        # Simple schema validation
        if schema.get("type") == "object":
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

    def sanitize(self, response: str) -> str:
        """Sanitize a response (remove potentially dangerous parts)."""
        sanitized = response
        for pattern in self.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized


# Module-level singleton
response_validator = ResponseValidator()

