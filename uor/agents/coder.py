"""Agent that turns a plan into UOR assembly code."""
from __future__ import annotations

from ..async_llm_client import async_call_model


class CoderAgent:
    """Generate code implementing the planned app."""

    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    async def run(self, plan: str) -> str:
        prompt = "Write UOR assembly that implements the following plan:\n" + plan
        return await async_call_model(self.provider, prompt)
