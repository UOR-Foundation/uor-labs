"""Prompt templates and loader utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class PromptTemplate:
    """Simple prompt template with optional examples."""

    text: str
    examples: list[dict[str, str]] = field(default_factory=list)

    def add_example(self, input: str, output: str) -> None:
        """Add an input/output example to the template."""
        self.examples.append({"input": input, "output": output})

    def render(self, **params: Any) -> str:
        """Render the template with ``params`` and included examples."""
        prompt = self.text.format(**params)
        if self.examples:
            parts = [prompt, "\nExamples:"]
            for ex in self.examples:
                parts.append(f"Input: {ex['input']}\nOutput: {ex['output']}")
            prompt = "\n".join(parts)
        return prompt


_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _load_raw(path: Path) -> dict[str, Any]:
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError:  # pragma: no cover - optional
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_template(data: dict[str, Any]) -> None:
    if not isinstance(data.get("prompt"), str):
        raise ValueError("template must contain 'prompt' string")
    examples = data.get("examples")
    if examples is None:
        return
    if not isinstance(examples, list):
        raise ValueError("'examples' must be a list")
    for ex in examples:
        if not isinstance(ex, dict) or "input" not in ex or "output" not in ex:
            raise ValueError("each example must have 'input' and 'output'")


def load_template(name: str) -> PromptTemplate:
    """Load a prompt template by ``name`` from the templates directory."""
    path = Path(name)
    if not path.suffix:
        for ext in (".yaml", ".yml", ".json"):
            cand = _TEMPLATES_DIR / f"{name}{ext}"
            if cand.exists():
                path = cand
                break
        else:
            raise FileNotFoundError(f"Template {name!r} not found")
    else:
        path = _TEMPLATES_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Template {name!r} not found")

    data = _load_raw(path)
    _validate_template(data)
    tmpl = PromptTemplate(data["prompt"], data.get("examples", []))
    return tmpl
