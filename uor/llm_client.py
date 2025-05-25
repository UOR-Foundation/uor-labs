"""Unified client helpers for calling LLM providers."""
from __future__ import annotations

import os

try:
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    openai = None  # type: ignore

try:
    import anthropic  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    anthropic = None  # type: ignore

try:
    import google.generativeai as generativeai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    generativeai = None  # type: ignore


class MissingDependencyError(RuntimeError):
    """Raised when a required client library is missing."""


def _require(module: object | None, name: str) -> None:
    if module is None:
        raise MissingDependencyError(f"{name} library is not installed")


def _get_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is required")
    return value


def call_model(provider: str, prompt: str) -> str:
    """Send ``prompt`` to the given ``provider`` and return the response text."""
    provider = provider.lower()
    if provider == "openai":
        _require(openai, "openai")
        openai.api_key = _get_env("OPENAI_API_KEY")
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content
        except Exception as exc:  # pragma: no cover - network errors
            raise RuntimeError("Failed to call OpenAI") from exc

    if provider == "anthropic":
        _require(anthropic, "anthropic")
        try:
            client = anthropic.Anthropic(api_key=_get_env("ANTHROPIC_API_KEY"))
            resp = client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{"role": "user", "content": prompt}],
            )
            return getattr(resp, "content", getattr(resp, "completion"))
        except Exception as exc:  # pragma: no cover - network errors
            raise RuntimeError("Failed to call Anthropic") from exc

    if provider in {"gemini", "google"}:
        _require(generativeai, "google-generativeai")
        try:
            generativeai.configure(api_key=_get_env("GOOGLE_API_KEY"))
            model = generativeai.GenerativeModel("gemini-pro")
            resp = model.generate_content(prompt)
            return resp.text
        except Exception as exc:  # pragma: no cover - network errors
            raise RuntimeError("Failed to call Gemini") from exc

    raise ValueError(f"Unknown provider: {provider}")

