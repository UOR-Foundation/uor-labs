Usage Examples
==============

Run the CLI::

   uor-vm program.asm

Start the development server::

   uor-server

Compile a script::

   uor-compile input.uors -o output.asm

Generate a program via LLM::

   uor-generate "print 123"

Run with the debugger::

   uor-cli debug -b 1 program.asm

Profile a program::

   uor-cli profile program.asm

Export a flamegraph::

   uor-cli flamegraph program.asm
