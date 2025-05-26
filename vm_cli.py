from __future__ import annotations

import argparse
from uor_cli import cmd_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a UOR program")
    parser.add_argument(
        "source",
        nargs="?",
        help="source .asm or encoded .uor file; reads assembly from stdin if omitted",
    )
    args = parser.parse_args(argv)
    return cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
