import chunks
from decoder import decode
from vm import VM


def test_instruction_counter():
    prog = [
        chunks.chunk_push(1),
        chunks.chunk_print(),
    ]
    vm = VM()
    list(vm.execute(decode(prog)))
    assert vm._counter.get(0) == 1
    assert vm._counter.get(1) == 1
    if not vm._jit.available:
        assert vm._compiled == {}
