"""Command line compiler for the toy language."""

from __future__ import annotations

import argparse
import sys

from .lexer import Lexer
from .parser import Parser
from .codegen import CodeGenerator

import assembler
import decoder
from vm import VM


def _compile_source(text: str, *, print_tokens: bool = False, print_ast: bool = False,
                    opt_level: int = 0, debug: bool = False) -> str:
    """Compile ``text`` to assembly and return it as a string."""

    lexer = Lexer(text)
    tokens = list(lexer.tokenize())
    if print_tokens:
        for tok in tokens:
            print(tok)

    parser = Parser(tokens)
    ast = parser.parse()
    if print_ast:
        print(ast)

    gen = CodeGenerator()
    program = gen.generate(ast)
    asm = program.as_text()

    if debug:
        asm = "; debug\n" + asm

    # ``opt_level`` currently unused but accepted for future extensions
    _ = opt_level

    return asm


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compile UOR script to assembly")
    p.add_argument("source", help="input .uors file")
    p.add_argument("-o", "--output", help="write assembly to file")
    p.add_argument("--opt", type=int, default=0, help="optimization level")
    p.add_argument("--debug", action="store_true", help="include debug information")
    p.add_argument("--tokens", action="store_true", help="print tokens")
    p.add_argument("--ast", action="store_true", help="print parsed AST")
    p.add_argument("--run", action="store_true", help="execute after compilation")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    with open(args.source, "r", encoding="utf-8") as fh:
        text = fh.read()

    asm = _compile_source(
        text,
        print_tokens=args.tokens,
        print_ast=args.ast,
        opt_level=args.opt,
        debug=args.debug,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(asm + "\n")
    else:
        print(asm)

    if args.run:
        program = assembler.assemble(asm)
        vm = VM()
        output = "".join(vm.execute(decoder.decode(program)))
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

