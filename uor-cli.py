#!/usr/bin/env python3
"""Command line interface for the Pure UOR VM."""
from __future__ import annotations

import argparse
import sys

from vm import VM
import chunks
import assembler


def cmd_assemble(args: argparse.Namespace) -> int:
    program = assembler.assemble_file(args.source)
    for ck in program:
        print(ck)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.source.endswith('.uor'):
        with open(args.source, 'r', encoding='utf-8') as fh:
            chunks_list = [int(x) for x in fh.read().split() if x]
    else:
        chunks_list = assembler.assemble_file(args.source)
    vm = VM()
    output = ''.join(vm.execute(chunks_list))
    print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pure UOR VM utilities")
    sub = p.add_subparsers(dest='cmd', required=True)

    pa = sub.add_parser('assemble', help='assemble program')
    pa.add_argument('source')
    pa.set_defaults(func=cmd_assemble)

    pr = sub.add_parser('run', help='assemble and run program')
    pr.add_argument('source')
    pr.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

