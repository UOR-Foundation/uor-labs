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
        if op in {"JMP", "JZ", "JNZ", "CALL"} and arg and not arg.lstrip("-+").isdigit():
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
        elif op == "DIV":
            result.append(chunks.chunk_div())
        elif op == "MOD":
            result.append(chunks.chunk_mod())
        elif op == "AND":
            result.append(chunks.chunk_and())
        elif op == "OR":
            result.append(chunks.chunk_or())
        elif op == "XOR":
            result.append(chunks.chunk_xor())
        elif op == "SHL":
            result.append(chunks.chunk_shl())
        elif op == "SHR":
            result.append(chunks.chunk_shr())
        elif op == "NEG":
            result.append(chunks.chunk_neg())
        elif op == "FMUL":
            result.append(chunks.chunk_fmul())
        elif op == "FDIV":
            result.append(chunks.chunk_fdiv())
        elif op == "F2I":
            result.append(chunks.chunk_f2i())
        elif op == "I2F":
            result.append(chunks.chunk_i2f())
        elif op == "SYSCALL":
            result.append(chunks.chunk_syscall())
        elif op == "INT":
            result.append(chunks.chunk_int())
        elif op == "HALT":
            result.append(chunks.chunk_halt())
        elif op == "NOP":
            result.append(chunks.chunk_nop())
        elif op == "HASH":
            result.append(chunks.chunk_hash())
        elif op == "SIGN":
            result.append(chunks.chunk_sign())
        elif op == "VERIFY":
            result.append(chunks.chunk_verify())
        elif op == "RNG":
            result.append(chunks.chunk_rng())
        elif op == "BRK":
            result.append(chunks.chunk_brk())
        elif op == "TRACE":
            result.append(chunks.chunk_trace())
        elif op == "DEBUG":
            result.append(chunks.chunk_debug())
        elif op == "ATOMIC":
            result.append(chunks.chunk_atomic())
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
        elif op == "CALL":
            if arg is None:
                raise ValueError("CALL requires offset")
            result.append(chunks.chunk_call(int(arg)))
        elif op == "RET":
            result.append(chunks.chunk_ret())
        elif op == "ALLOC":
            if arg is None:
                raise ValueError("ALLOC requires size")
            result.append(chunks.chunk_alloc(int(arg)))
        elif op == "FREE":
            if arg is None:
                raise ValueError("FREE requires address")
            result.append(chunks.chunk_free(int(arg)))
        elif op == "INPUT":
            result.append(chunks.chunk_input())
        elif op == "OUTPUT":
            result.append(chunks.chunk_output())
        elif op == "NET_SEND":
            result.append(chunks.chunk_net_send())
        elif op == "NET_RECV":
            result.append(chunks.chunk_net_recv())
        elif op == "THREAD_START":
            result.append(chunks.chunk_thread_start())
        elif op == "THREAD_JOIN":
            result.append(chunks.chunk_thread_join())
        elif op == "BLOCK":
            if arg is None:
                raise ValueError("BLOCK requires length")
            result.append(chunks.chunk_block_start(int(arg)))
        elif op == "NTT":
            if arg is None:
                raise ValueError("NTT requires length")
            result.append(chunks.chunk_ntt(int(arg)))
        elif op == "UN_CREATE":
            if arg is None:
                raise ValueError("UN_CREATE requires value")
            result.append(chunks.chunk_un_create(int(arg)))
        elif op == "UN_GRADE":
            if arg is None:
                raise ValueError("UN_GRADE requires value")
            result.append(chunks.chunk_un_grade(int(arg)))
        elif op == "UN_INNER":
            result.append(chunks.chunk_un_inner())
        elif op == "UN_NORM":
            result.append(chunks.chunk_un_norm())
        elif op == "UN_TRANS":
            result.append(chunks.chunk_un_trans())
        elif op == "UN_DWT":
            result.append(chunks.chunk_un_dwt())
        elif op == "CHECKPOINT":
            result.append(chunks.chunk_checkpoint())
        else:
            raise ValueError(f"Unknown instruction: {op}")

    return result


def assemble_file(path: str) -> List[int]:
    with open(path, "r", encoding="utf-8") as fh:
        return assemble(fh.read())

