"""Simple API helpers for assembling and running programs."""
from __future__ import annotations

from typing import Iterable

import assembler
import decoder
from vm import VM


class ProgramInputError(Exception):
    """Raised when the provided program text is invalid."""


def run_program(text: str) -> str:
    """Assemble and execute ``text`` and return the VM output.

    Parameters
    ----------
    text:
        Assembly program to run.

    Returns
    -------
    str
        Output produced by executing the program.

    Raises
    ------
    TypeError
        If ``text`` is not a string.
    ValueError
        If assembly fails due to invalid instructions or labels.
    """
    if not isinstance(text, str):
        raise TypeError("Program text must be a string")

    program = assembler.assemble(text)
    decoded = decoder.decode(program)
    vm = VM()
    return "".join(vm.execute(decoded))
