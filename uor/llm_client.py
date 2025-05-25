"""Unified LLM client helpers."""
from __future__ import annotations

import os


def call_model(provider: str, prompt: str) -> str:
    """Call the selected model with ``prompt`` and return the text response."""
    provider = provider.lower()
    if provider == "openai":
        import openai
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        openai.api_key = key
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content.strip()
    if provider == "anthropic":
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(model="claude-3-haiku-20240307", messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text.strip()
    if provider == "gemini":
        import google.generativeai as genai
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-pro")
        resp = model.generate_content(prompt)
        return resp.text.strip()
    raise ValueError(f"Unknown provider: {provider}")
