"""Demonstrate running a program through the high level API."""
from uor.api import run_program

PROGRAM = """
PUSH 1
PUSH 2
ADD
PRINT
"""

if __name__ == "__main__":
    print(run_program(PROGRAM))
