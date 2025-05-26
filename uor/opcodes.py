"""Opcode definitions for UniversalNumber operations."""
from __future__ import annotations

from enum import Enum, auto


class UNOpcodes(Enum):
    """Opcodes for UniversalNumber instructions."""

    UN_CREATE = auto()
    UN_GRADE = auto()
    UN_INNER = auto()
    UN_NORM = auto()
    UN_TRANS = auto()
    UN_DWT = auto()


__all__ = ["UNOpcodes"]
