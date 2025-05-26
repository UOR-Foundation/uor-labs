from __future__ import annotations

import random
from typing import List

import chunks


def random_instruction() -> int:
    """Return a random instruction chunk."""
    ops = [
        lambda: chunks.chunk_push(random.randint(0, 10)),
        chunks.chunk_add,
        chunks.chunk_sub,
        chunks.chunk_mul,
        lambda: chunks.chunk_load(random.randint(0, 3)),
        lambda: chunks.chunk_store(random.randint(0, 3)),
        chunks.chunk_print,
    ]
    op = random.choice(ops)
    return op() if callable(op) else op()


def random_program(length: int = 5) -> List[int]:
    """Generate a random program of ``length`` instructions."""
    return [random_instruction() for _ in range(length)]

__all__ = ["random_program"]
