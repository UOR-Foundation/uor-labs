# Pure UOR Labs

This repository implements a modular "Pure UOR" virtual machine.  Programs are
encoded as products of prime powers with checksums for integrity.  The VM is
Turing complete thanks to arithmetic, memory access and branching opcodes.

## Instruction Set

| Instruction | Description               |
|-------------|---------------------------|
| `PUSH n`    | Push integer `n`          |
| `ADD`       | Pop two values, push sum  |
| `SUB`       | Pop two values, push diff |
| `MUL`       | Pop two values, push prod |
| `LOAD a`    | Push value at memory `a`  |
| `STORE a`   | Store value into `a`      |
| `JMP o`     | Jump by offset `o`        |
| `JZ o`      | Jump if zero              |
| `JNZ o`     | Jump if non‑zero          |
| `PRINT`     | Pop value and output      |
| `BLOCK n`   | Run next `n` chunks in new VM |
| `NTT n`     | NTT roundtrip next `n` chunks |

Negative jump offsets are encoded using a special `NEG_FLAG` prime.  Memory is
an unbounded dictionary of integer addresses.

## Assembler and CLI

`uor-cli.py` offers two commands:

```bash
python3 uor-cli.py assemble program.asm   # assemble to chunks
python3 uor-cli.py run program.asm        # assemble and execute
python3 uor-cli.py run program.uor        # run pre-encoded program
```

Assembly files consist of one instruction per line with optional labels and
`#` comments.  Offsets for jumps can reference labels and will be translated to
relative jumps automatically.

## Examples

Two sample programs are provided in the `examples/` directory.  `countdown.asm`
implements a simple loop that prints `321`.  `block_demo.asm` demonstrates the
`BLOCK` opcode by executing a small block which prints `HI`.

## Tests

Unit tests reside in `tests/`.  Run them with:

```bash
python3 -m unittest discover -v
```

