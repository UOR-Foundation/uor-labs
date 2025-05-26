#!/usr/bin/env python3
"""Command line interface for the Pure UOR VM.

The tool can assemble text programs into numeric chunks or execute an
assembly file directly.  If a ``.uor`` file is given, its numbers are
loaded and executed through the VM.
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import sys

from uor import ipfs_storage, llm_client
from uor.agents.factory import AppFactory

from vm import VM
from uor.debug import DebugVM
from decoder import decode
import chunks
import assembler
import time


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


def cmd_debug(args: argparse.Namespace) -> int:
    """Run a program under the DebugVM."""
    if args.source is None:
        text = sys.stdin.read()
        chunks_list = assembler.assemble(text)
    elif args.source.endswith('.uor'):
        with open(args.source, 'r', encoding='utf-8') as fh:
            chunks_list = [int(x) for x in fh.read().split() if x]
    else:
        chunks_list = assembler.assemble_file(args.source)

    vm = DebugVM()
    for bp in args.breakpoints:
        vm.add_breakpoint(bp)
    for wp in args.watchpoints:
        vm.add_watchpoint(wp)
    if args.trace:
        vm.enable_tracing()
    output = ''.join(vm.execute(decode(chunks_list)))
    print(output)
    return 0


def cmd_ipfs_add(args: argparse.Namespace) -> int:
    """Assemble ``source`` and store the encoded program via IPFS."""
    if args.source:
        if args.source.endswith('.uor'):
            with open(args.source, 'r', encoding='utf-8') as fh:
                chunks_list = [int(x) for x in fh.read().split() if x]
        else:
            chunks_list = assembler.assemble_file(args.source)
    else:
        text = sys.stdin.read()
        chunks_list = assembler.assemble(text)
    data = '\n'.join(str(x) for x in chunks_list).encode('utf-8')
    cid = ipfs_storage.add_data(data)
    print(cid)
    return 0


def cmd_ipfs_run(args: argparse.Namespace) -> int:
    """Fetch a program by CID from IPFS and execute it."""
    raw = ipfs_storage.get_data(args.cid)
    chunks_list = [int(x) for x in raw.decode('utf-8').split() if x]
    vm = VM()
    output = ''.join(vm.execute(decode(chunks_list)))
    print(output)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate a program via an LLM and store it in IPFS."""
    asm = llm_client.call_model(args.provider, args.prompt)
    chunks_list = assembler.assemble(asm)
    data = '\n'.join(str(x) for x in chunks_list).encode('utf-8')
    cid = ipfs_storage.add_data(data)
    print(cid)
    return 0


async def cmd_factory(args: argparse.Namespace) -> int:
    """Build an app via specialized agents and store it in IPFS."""
    factory = AppFactory(provider=args.provider)
    cid = await factory.build_app(args.goal)
    print(cid)
    return 0


def _execute_prog(chunks_list: list[int]) -> str:
    """Helper to run a small program and capture output."""
    vm = VM()
    return "".join(vm.execute(decode(chunks_list)))


def cmd_universal_create(args: argparse.Namespace) -> int:
    """Create a universal number and print the VM output."""
    prog = [
        chunks.chunk_un_create(int(args.value)),
        chunks.chunk_print(),
    ]
    out = _execute_prog(prog)
    print(out)
    return 0


def cmd_universal_dwt(args: argparse.Namespace) -> int:
    """Run a DWT on the provided signal file."""
    with open(args.signal_file, "r", encoding="utf-8") as fh:
        values = [int(x) for x in fh.read().split() if x]
    prog = [chunks.chunk_push(v) for v in values]
    prog.append(chunks.chunk_un_dwt())
    prog.append(chunks.chunk_print())
    out = _execute_prog(prog)
    print(out)
    return 0


def cmd_universal_denoise(args: argparse.Namespace) -> int:
    """Denoise an image using universal operations."""
    with open(args.image_file, "r", encoding="utf-8") as fh:
        values = [int(x) for x in fh.read().split() if x]
    prog = [chunks.chunk_push(v) for v in values]
    prog.append(chunks.chunk_un_dwt())
    prog.append(chunks.chunk_un_trans())
    prog.append(chunks.chunk_print())
    out = _execute_prog(prog)
    print(out)
    return 0


def cmd_universal_benchmark(args: argparse.Namespace) -> int:
    """Benchmark universal operations."""
    prog = [chunks.chunk_un_create(1)]
    decoded = decode(prog)
    vm = VM()
    start = time.time()
    vm.execute(decoded)
    elapsed = time.time() - start
    print(f"{elapsed:.6f}")
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

    pd = sub.add_parser('debug', help='run program with debugger')
    pd.add_argument('source', nargs='?', help='assembly or .uor file, defaults to stdin')
    pd.add_argument('-b', '--break', dest='breakpoints', action='append', type=int, default=[], help='set breakpoint at instruction index')
    pd.add_argument('-w', '--watch', dest='watchpoints', action='append', type=int, default=[], help='watch memory address')
    pd.add_argument('-t', '--trace', action='store_true', help='trace instructions')
    pd.set_defaults(func=cmd_debug)

    pi = sub.add_parser('ipfs-add', help='assemble program and store via IPFS')
    pi.add_argument('source', nargs='?', help='assembly or .uor file, defaults to stdin')
    pi.set_defaults(func=cmd_ipfs_add)

    px = sub.add_parser('ipfs-run', help='run program from IPFS CID')
    px.add_argument('cid', help='content identifier to fetch')
    px.set_defaults(func=cmd_ipfs_run)

    pg = sub.add_parser('generate', help='generate program via an LLM')
    pg.add_argument('--provider', default='openai',
                    choices=['openai', 'anthropic', 'gemini'],
                    help='LLM provider to use')
    pg.add_argument('prompt', help='prompt describing the program')
    pg.set_defaults(func=cmd_generate)

    pf = sub.add_parser('factory', help='build app using specialized agents')
    pf.add_argument('--provider', default='openai',
                    choices=['openai', 'anthropic', 'gemini'],
                    help='LLM provider to use')
    pf.add_argument('goal', help='high level goal for the app')
    pf.set_defaults(func=cmd_factory)

    un = sub.add_parser('universal', help='universal number helpers')
    un_sub = un.add_subparsers(dest='u_cmd', required=True)

    uc = un_sub.add_parser('create', help='create universal number')
    uc.add_argument('value', type=int)
    uc.set_defaults(func=cmd_universal_create)

    ud = un_sub.add_parser('dwt', help='apply DWT to signal')
    ud.add_argument('signal_file')
    ud.set_defaults(func=cmd_universal_dwt)

    une = un_sub.add_parser('denoise', help='denoise image using universal ops')
    une.add_argument('image_file')
    une.set_defaults(func=cmd_universal_denoise)

    ub = un_sub.add_parser('benchmark', help='benchmark universal ops')
    ub.set_defaults(func=cmd_universal_benchmark)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    if inspect.iscoroutine(result):
        return asyncio.run(result)
    return result


if __name__ == '__main__':
    sys.exit(main())

