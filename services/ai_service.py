"""AI provider abstraction for intent extraction."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


class AIServiceError(Exception):
    """Raised when AI provider interaction fails."""


@dataclass(slots=True)
class AIService:
    """Thin wrapper around OpenAI Chat Completions API."""

    api_key: str | None = None
    model: str | None = None
    timeout_seconds: int = 8

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        self.model = self.model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def interpret_search_intent(self, *, query: str) -> dict[str, Any]:
        """Extract structured filters from a natural-language query."""
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente que interpreta búsquedas de usuarios en un marketplace. "
                        "Convierte la consulta en filtros estructurados. "
                        "Devuelve JSON válido con: category (string), "
                        "price_range (low|medium|high), distance (near|medium|far)."
                    ),
                },
                {
                    "role": "user",
                    "content": f'Consulta: "{query}"',
                },
            ],
            "response_format": {"type": "json_object"},
        }
        return self._chat_completion(payload=payload)

    def _chat_completion(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("OPENAI_API_KEY is not configured")

        req = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                parsed_response = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AIServiceError("OpenAI request failed") from exc

        try:
            content = parsed_response["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIServiceError("Invalid OpenAI response format") from exc
