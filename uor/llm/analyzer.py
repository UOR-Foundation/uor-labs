"""Static code analysis helpers with optional LLM integration."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, Set, List, AsyncGenerator

from .providers import LLMProvider


@dataclass
class CFG:
    """Simple control flow graph representation."""

    edges: Dict[int, Set[int]] = field(default_factory=dict)
    nodes: Dict[int, ast.stmt] = field(default_factory=dict)


class _MetricsVisitor(ast.NodeVisitor):
    """Collect metrics and variable usage information."""

    def __init__(self) -> None:
        self.variables_defined: Set[str] = set()
        self.variables_used: Set[str] = set()
        self.loops: List[int] = []
        self.complexity: int = 1

    # ---- node handlers -------------------------------------------------
    def visit_Name(self, node: ast.Name) -> None:  # pragma: no cover - trivial
        if isinstance(node.ctx, ast.Store):
            self.variables_defined.add(node.id)
        else:
            self.variables_used.add(node.id)

    def visit_For(self, node: ast.For) -> None:
        self.loops.append(node.lineno)
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.loops.append(node.lineno)
        self.complexity += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # pragma: no cover - simple
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class CodeAnalyzer:
    """Analyze Python code to build a CFG and compute metrics."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.tree = ast.parse(code)
        self.cfg = self._build_cfg()
        visitor = _MetricsVisitor()
        visitor.visit(self.tree)
        self.variables_defined = visitor.variables_defined
        self.variables_used = visitor.variables_used
        self.loops = visitor.loops
        self.complexity = visitor.complexity

    # ---- analysis helpers ---------------------------------------------
    def _build_cfg(self) -> CFG:
        cfg = CFG()
        statements: List[ast.stmt] = []

        def _flatten(stmts: List[ast.stmt]) -> None:
            for stmt in stmts:
                statements.append(stmt)
                body = getattr(stmt, "body", None)
                if isinstance(body, list):
                    _flatten(body)
                orelse = getattr(stmt, "orelse", None)
                if isinstance(orelse, list):
                    _flatten(orelse)
        _flatten(self.tree.body)

        for i, stmt in enumerate(statements):
            line = stmt.lineno
            cfg.nodes[line] = stmt
            if i + 1 < len(statements):
                next_line = statements[i + 1].lineno
                cfg.edges.setdefault(line, set()).add(next_line)
            if isinstance(stmt, (ast.For, ast.While)) and stmt.body:
                last = stmt.body[-1].lineno
                cfg.edges.setdefault(last, set()).add(line)
        return cfg

    # ---- LLM helpers --------------------------------------------------
    async def explain(self, provider: LLMProvider) -> str:
        """Return an explanation of the analyzed code via ``provider``."""
        return await provider.explain_code(self.code)

    async def compare(self, other_code: str, provider: LLMProvider) -> str:
        """Compare ``self.code`` to ``other_code`` using ``provider``."""
        prompt = (
            "Compare the following code snippets:\n"
            f"A:\n{self.code}\nB:\n{other_code}"
        )
        # _call is used internally by providers
        return await provider._call(prompt, purpose="compare")

    async def ask(self, question: str, provider: LLMProvider) -> str:
        """Ask ``provider`` a question about ``self.code``."""
        prompt = f"{question}\nCode:\n{self.code}"
        return await provider._call(prompt, purpose="qa")

    async def stream_qa(self, question: str, provider: LLMProvider) -> AsyncGenerator[str, None]:
        """Stream an answer from ``provider`` for ``question`` about the code."""
        prompt = f"{question}\nCode:\n{self.code}"
        async for chunk in provider.stream(prompt):
            yield chunk
