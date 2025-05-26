# Pure UOR Labs

This repository implements a modular "Pure UOR" virtual machine.  Programs are
encoded as products of prime powers with checksums for integrity.  The VM is
Turing complete thanks to arithmetic, memory access and branching opcodes.

## Installation

Install the package via `pip` to get the `uor-cli` command:

```bash
pip install uor-labs
```

You can then run `uor-cli` from anywhere.

## Instruction Set

| Instruction | Description               |
|-------------|---------------------------|
| `PUSH n`       | Push integer `n`                |
| `ADD`          | Pop two values, push sum        |
| `SUB`          | Pop two values, push diff       |
| `MUL`          | Pop two values, push prod       |
| `LOAD a`       | Push value at memory `a`        |
| `STORE a`      | Store value into `a`            |
| `JMP o`        | Jump by offset `o`              |
| `JZ o`         | Jump if zero                    |
| `JNZ o`        | Jump if non‑zero                |
| `PRINT`        | Pop value and output            |
| `BLOCK n`      | Run next `n` chunks in new VM   |
| `NTT n`        | NTT roundtrip next `n` chunks   |
| `CALL o`       | Call subroutine at offset `o`   |
| `RET`          | Return from subroutine          |
| `ALLOC n`      | Allocate `n` units of memory    |
| `FREE a`       | Free memory at address `a`      |
| `INPUT`        | Read value from input queue     |
| `OUTPUT`       | Write top of stack to output    |
| `NET_SEND`     | Send network packet             |
| `NET_RECV`     | Receive network packet          |
| `THREAD_START` | Spawn new thread                |
| `THREAD_JOIN`  | Join spawned thread             |
| `DIV`          | Pop two values, push quotient   |
| `MOD`          | Pop two values, push remainder  |
| `AND`          | Bitwise AND on two values       |
| `OR`           | Bitwise OR on two values        |
| `XOR`          | Bitwise XOR on two values       |
| `SHL`          | Shift left                      |
| `SHR`          | Shift right                     |
| `NEG`          | Negate top of stack             |
| `FMUL`         | Multiply two floats             |
| `FDIV`         | Divide two floats               |
| `F2I`          | Float to integer conversion     |
| `I2F`          | Integer to float conversion     |
| `SYSCALL`      | Perform host system call        |
| `INT`          | Trigger software interrupt      |
| `HALT`         | Stop execution                  |
| `NOP`          | No operation                    |
| `HASH`         | Hash top of stack               |
| `SIGN`         | Sign value with key             |
| `VERIFY`       | Verify signature                |
| `RNG`          | Push random value               |
| `BRK`          | Emit literal ``BRK``            |
| `TRACE`        | Output current stack value      |
| `CHECKPOINT`   | Save VM state through backend   |

Negative offsets for jumps and `CALL` are encoded using a special `NEG_FLAG` prime.
Memory is an unbounded dictionary of integer addresses.

## Assembler and CLI

`uor-cli` offers several commands:

```bash
uor-cli assemble program.asm            # assemble to chunks
uor-cli assemble -o program.uor foo.asm # write chunks to file
uor-cli assemble < foo.asm              # read source from stdin
uor-cli run program.asm                 # assemble and execute
uor-cli run program.uor                 # run pre-encoded program
uor-cli run < program.asm               # assemble from stdin and run
uor-cli ipfs-add program.asm            # store encoded program via IPFS
uor-cli ipfs-run QmCID                  # run program fetched from IPFS
uor-cli generate --provider openai "your prompt"  # create program with an LLM
uor-cli profile program.asm             # run with profiler and print metrics
uor-cli flamegraph program.asm          # output flamegraph data
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

Integration tests covering full programs are located under
`tests/integration`. Run them with the same command to verify end-to-end
behaviour.

## Debugging

The `DebugVM` subclass provides interactive debugging features. Set
breakpoints and watchpoints or trace every instruction using the
`uor-cli debug` command.  The legacy `BRK` and `TRACE` opcodes still work
inside programs and will emit ``BRK`` and the current stack value.

Example:

```bash
uor-cli debug -b 2 -w 0 program.asm
```


## Optional IPFS Support

The module `uor.ipfs_storage` provides helpers for storing and retrieving
programs via [IPFS](https://ipfs.tech/). To use it you must install the optional
dependency and have an IPFS daemon running locally:

```bash
pip install -r requirements.txt
ipfs daemon &
```

### Canonical Addressing

`uor.addressing` introduces a canonical storage system based on 512‑bit prime
digests. Objects are hashed with SHA‑512 and mapped to the nearest prime to
create deterministic addresses. A lightweight distributed hash table manages the
mapping from addresses to IPFS CIDs while providing an LRU cache for frequent
lookups. Namespaces like `org.uor.stdlib.math` resolve to their canonical
address so different VMs can reference and retrieve identical objects.

See `examples/canonical_demo.py` for a short example.

## LLM API Keys

The upcoming LLM helpers require API credentials. Set the following environment
variables for the providers you want to use:

```bash
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export GOOGLE_API_KEY=your-gemini-key
```


## Asynchronous LLM Helper

Use `uor.async_llm_client.async_call_model` when coordinating multiple agents concurrently. It mirrors `llm_client.call_model` but returns a coroutine that can be awaited.

## Agent Factory

Specialized agents (planner, coder and tester) live under `uor.agents`. The `AppFactory` orchestrates them to create new apps and store the result via IPFS. Run this process through the CLI:

```bash
uor-cli factory "your goal"            # uses OpenAI by default
```

Pass `--provider` to select another LLM backend.

## API Server

A small Flask server exposes HTTP endpoints for assembling, running and generating programs.
Start it with:

```bash
python3 server.py
```

Available routes:

- `POST /assemble` – body `{ "text": "..." }` returns `{"chunks": [...]}`
- `POST /run` – body with `"text"` or `"chunks"` executes the program and returns `{"output": "..."}`
- `POST /generate` – body `{ "prompt": "...", "provider": "openai" }` calls the selected LLM, assembles the result, stores it via IPFS and returns `{"cid": "..."}`.

The server relies on the same environment variables as `llm_client` for API keys.

## Universal Number

`UniversalNumber` represents integers using prime and geometric coordinates. It
caches prime factorizations and reference frames for fast reuse.  Methods like
`getGradedComponents`, `innerProduct` and `coherenceNorm` provide simple
geometric operations on these numbers.

### Universal CLI

The `universal` subcommand exposes basic operations:

```bash
uor-cli universal create 4        # build a number and print VM output
uor-cli universal dwt signal.txt  # apply DWT to a signal
uor-cli universal denoise img.raw # denoise data using transforms
uor-cli universal benchmark       # measure operation speed
```
