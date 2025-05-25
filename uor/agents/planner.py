"""Agent responsible for planning app creation steps."""
from __future__ import annotations

from ..async_llm_client import async_call_model


class PlannerAgent:
    """Generate a high-level plan for the requested app."""

    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    async def run(self, goal: str) -> str:
        prompt = f"Create a detailed plan to build an app that {goal}."
        return await async_call_model(self.provider, prompt)
