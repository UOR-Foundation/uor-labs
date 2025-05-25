#!/usr/bin/env python3
"""Command line interface for the Pure UOR VM.

The tool can assemble text programs into numeric chunks or execute an
assembly file directly.  If a ``.uor`` file is given, its numbers are
loaded and executed through the VM.
"""
from __future__ import annotations

import argparse
import sys

from vm import VM
from decoder import decode
import chunks
import assembler


def cmd_assemble(args: argparse.Namespace) -> int:
    """Assemble a program and optionally write the chunks to a file."""
    if args.source:
        with open(args.source, "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    program = assembler.assemble(text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write("\n".join(str(ck) for ck in program) + "\n")
    else:
        for ck in program:
            print(ck)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a program, assembling it first if needed."""
    if args.source is None:
        text = sys.stdin.read()
        chunks_list = assembler.assemble(text)
    elif args.source.endswith('.uor'):
        with open(args.source, 'r', encoding='utf-8') as fh:
            chunks_list = [int(x) for x in fh.read().split() if x]
    else:
        chunks_list = assembler.assemble_file(args.source)
    vm = VM()
    output = ''.join(vm.execute(decode(chunks_list)))
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pure UOR VM utilities")
    sub = p.add_subparsers(dest='cmd', required=True)

    pa = sub.add_parser('assemble', help='assemble program')
    pa.add_argument('source', nargs='?', help='assembly file, defaults to stdin')
    pa.add_argument('-o', '--output', help='write encoded program to file')
    pa.set_defaults(func=cmd_assemble)

    pr = sub.add_parser('run', help='assemble and run program')
    pr.add_argument('source', nargs='?', help='source .asm or encoded .uor file; reads assembly from stdin if omitted')
    pr.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

