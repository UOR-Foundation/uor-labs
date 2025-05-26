from __future__ import annotations

import argparse
from uor_cli import cmd_generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a UOR program via an LLM")
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "anthropic", "gemini"],
        help="LLM provider to use",
    )
    parser.add_argument("prompt", help="prompt describing the program")
    args = parser.parse_args(argv)
    return cmd_generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
