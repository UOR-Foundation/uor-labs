"""Simple assembler for the Pure UOR VM."""
from __future__ import annotations

from typing import Dict, List, Tuple

import chunks


def assemble(text: str) -> List[int]:
    """Assemble the given text into a list of encoded chunks."""
    lines = [line.split("#", 1)[0].strip() for line in text.splitlines()]
    instructions: List[Tuple[str, str | None]] = []
    labels: Dict[str, int] = {}
    pending: List[Tuple[int, str]] = []

    for line in lines:
        if not line:
            continue
        if line.endswith(":"):
            labels[line[:-1]] = len(instructions)
            continue
        parts = line.split()
        op = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else None
        instructions.append((op, arg))
        if op in {"JMP", "JZ", "JNZ"} and arg and not arg.lstrip("-+").isdigit():
            pending.append((len(instructions) - 1, arg))

    for idx, label in pending:
        if label not in labels:
            raise ValueError(f"Unknown label: {label}")
        offset = labels[label] - idx - 1
        instructions[idx] = (instructions[idx][0], str(offset))

    result: List[int] = []
    for op, arg in instructions:
        if op == "PUSH":
            if arg is None:
                raise ValueError("PUSH requires value")
            result.append(chunks.chunk_push(int(arg)))
        elif op == "ADD":
            result.append(chunks.chunk_add())
        elif op == "SUB":
            result.append(chunks.chunk_sub())
        elif op == "MUL":
            result.append(chunks.chunk_mul())
        elif op == "PRINT":
            result.append(chunks.chunk_print())
        elif op == "LOAD":
            if arg is None:
                raise ValueError("LOAD requires address")
            result.append(chunks.chunk_load(int(arg)))
        elif op == "STORE":
            if arg is None:
                raise ValueError("STORE requires address")
            result.append(chunks.chunk_store(int(arg)))
        elif op == "JMP":
            if arg is None:
                raise ValueError("JMP requires offset")
            result.append(chunks.chunk_jmp(int(arg)))
        elif op == "JZ":
            if arg is None:
                raise ValueError("JZ requires offset")
            result.append(chunks.chunk_jz(int(arg)))
        elif op == "JNZ":
            if arg is None:
                raise ValueError("JNZ requires offset")
            result.append(chunks.chunk_jnz(int(arg)))
        elif op == "BLOCK":
            if arg is None:
                raise ValueError("BLOCK requires length")
            result.append(chunks.chunk_block_start(int(arg)))
        elif op == "NTT":
            if arg is None:
                raise ValueError("NTT requires length")
            result.append(chunks.chunk_ntt(int(arg)))
        else:
            raise ValueError(f"Unknown instruction: {op}")

    return result


def assemble_file(path: str) -> List[int]:
    with open(path, "r", encoding="utf-8") as fh:
        return assemble(fh.read())

