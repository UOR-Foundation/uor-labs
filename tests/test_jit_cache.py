import chunks
from decoder import decode
from vm import VM


def test_jit_cache_ttl():
    prog = decode([chunks.chunk_push(1), chunks.chunk_print()])
    vm = VM()
    vm._jit.available = True
    vm.jit_threshold = 1
    vm._jit.ttl = 0.0
    list(vm.execute(prog))
    first = vm._compiled.get(0)
    assert first is not None
    list(vm.execute(prog))
    second = vm._compiled.get(0)
    assert second is not None
    assert second is not first
    assert vm._jit.blocks_compiled >= 2

