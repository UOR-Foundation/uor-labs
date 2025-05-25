"""Asynchronous helpers for calling LLM providers."""
from __future__ import annotations

import asyncio

from .llm_client import (
    openai,
    anthropic,
    generativeai,
    _require,
    _get_env,
    MissingDependencyError,
)


async def async_call_model(provider: str, prompt: str) -> str:
    """Asynchronously send ``prompt`` to ``provider`` and return the response."""
    provider = provider.lower()

    if provider == "openai":
        _require(openai, "openai")
        openai.api_key = _get_env("OPENAI_API_KEY")
        try:  # pragma: no cover - network errors
            resp = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Failed to call OpenAI") from exc

    if provider == "anthropic":
        _require(anthropic, "anthropic")
        try:  # pragma: no cover - network errors
            client = anthropic.AsyncAnthropic(api_key=_get_env("ANTHROPIC_API_KEY"))
            resp = await client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{"role": "user", "content": prompt}],
            )
            return getattr(resp, "content", getattr(resp, "completion"))
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Failed to call Anthropic") from exc

    if provider in {"gemini", "google"}:
        _require(generativeai, "google-generativeai")
        try:  # pragma: no cover - network errors
            generativeai.configure(api_key=_get_env("GOOGLE_API_KEY"))
            model = generativeai.GenerativeModel("gemini-pro")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            return resp.text
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Failed to call Gemini") from exc

    raise ValueError(f"Unknown provider: {provider}")
