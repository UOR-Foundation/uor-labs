UOR-Script Standard Library
===========================

The standard library provides common utilities implemented in UOR-Script and
assembly.  Modules are stored under ``uor/stdlib`` and can be used by the
compiler or referenced directly by their canonical address when running inside
the VM.

Modules
-------

* ``math.uors`` – arithmetic helpers and number theory functions
* ``math_advanced.asm`` – VM primitives for trigonometry and other heavy
actions
* ``io.uors`` – console and file I/O abstractions
* ``io_primitives.asm`` – assembly helpers for I/O and networking
* ``collections.uors`` – coherent list, map and set implementations
* ``iterator.asm`` – basic iterator protocol
* ``crypto.uors`` – hashing and signature helpers
* ``crypto_primitives.asm`` – cryptographic VM primitives
* ``memory.asm`` – memory management utilities
* ``loader.asm`` – module loading and caching logic
* ``test.uors`` – minimal testing helpers

Examples are provided in ``examples/stdlib_examples.uors`` showcasing basic
usage of the library objects.
