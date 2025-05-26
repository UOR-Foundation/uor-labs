"""Orchestrator that coordinates specialized agents to produce an app."""
from __future__ import annotations

from .planner import PlannerAgent
from .coder import CoderAgent
from .tester import TesterAgent
import assembler
from .. import ipfs_storage


class AppFactory:
    """Create apps using planner, coder and tester agents."""

    def __init__(self, provider: str = "openai") -> None:
        self.planner = PlannerAgent(provider)
        self.coder = CoderAgent(provider)
        self.tester = TesterAgent(provider)

    async def build_app(self, goal: str) -> str:
        """Generate an app for ``goal`` and return its IPFS CID."""
        plan = await self.planner.run(goal)
        code = await self.coder.run(plan)
        checked = await self.tester.run(code)
        chunks_list = assembler.assemble(checked)
        data = "\n".join(str(x) for x in chunks_list).encode("utf-8")
        return await ipfs_storage.async_add_data(data)
