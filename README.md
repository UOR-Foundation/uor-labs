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

`uor-cli.py` offers several commands:

```bash
python3 uor-cli.py assemble program.asm            # assemble to chunks
python3 uor-cli.py assemble -o program.uor foo.asm # write chunks to file
python3 uor-cli.py assemble < foo.asm              # read source from stdin
python3 uor-cli.py run program.asm                 # assemble and execute
python3 uor-cli.py run program.uor                 # run pre-encoded program
python3 uor-cli.py run < program.asm               # assemble from stdin and run
python3 uor-cli.py ipfs-add program.asm            # store encoded program via IPFS
python3 uor-cli.py ipfs-run QmCID                  # run program fetched from IPFS
python3 uor-cli.py generate --provider openai "your prompt"  # create program with an LLM
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


## Optional IPFS Support

The module `uor.ipfs_storage` provides helpers for storing and retrieving
programs via [IPFS](https://ipfs.tech/). To use it you must install the optional
dependency and have an IPFS daemon running locally:

```bash
pip install -r requirements.txt
ipfs daemon &
```

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
python3 uor-cli.py factory "your goal"            # uses OpenAI by default
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
