"""Agent for validating generated assembly code."""
from __future__ import annotations

from ..async_llm_client import async_call_model


class TesterAgent:
    """Review assembly code and suggest improvements."""

    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    async def run(self, assembly: str) -> str:
        prompt = "Review this UOR assembly for errors and provide the corrected version:\n" + assembly
        return await async_call_model(self.provider, prompt)
