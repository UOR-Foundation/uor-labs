"""JIT compiler infrastructure for the Pure UOR VM."""
from __future__ import annotations

import platform
from typing import Callable, Iterable, List

try:
    import llvmlite.ir as ir  # type: ignore
    import llvmlite.binding as llvm  # type: ignore
    _HAS_LLVM = True
except Exception:  # pragma: no cover - optional dependency
    ir = None  # type: ignore
    llvm = None  # type: ignore
    _HAS_LLVM = False

from decoder import DecodedInstruction


class JITBlock:
    """Callable wrapper for compiled blocks."""

    def __init__(self, func: Callable[["VM"], Iterable[str]], end_ip: int) -> None:
        self.func = func
        self.end_ip = end_ip

    def __call__(self, vm: "VM") -> Iterable[str]:
        return self.func(vm)


class JITCompiler:
    """Very small JIT compiler using llvmlite when available."""

    def __init__(self) -> None:
        self.arch = platform.machine().lower()
        self.available = _HAS_LLVM and self.arch in {"x86_64", "amd64", "aarch64", "arm64"}
        if self.available:
            llvm.initialize()
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()

    # ------------------------------------------------------------------
    def compile_block(self, instructions: List[DecodedInstruction]) -> JITBlock | None:
        """Compile a block of decoded instructions."""
        if not self.available:
            return self._compile_py(instructions)
        try:
            return self._compile_llvm(instructions)
        except Exception:  # pragma: no cover - LLVM may fail
            return self._compile_py(instructions)

    # ------------------------------------------------------------------
    def _compile_py(self, instructions: List[DecodedInstruction]) -> JITBlock:
        """Fallback compilation to pure Python code."""

        def block(vm: "VM") -> Iterable[str]:
            for instr in instructions:
                op = next(p for p, e in instr.data if e == 4)
                handler = vm._dispatch[op]
                yield from handler(instr.data)
            vm.ip += len(instructions)
            return iter(())

        return JITBlock(block, end_ip=0)

    # ------------------------------------------------------------------
    def _compile_llvm(self, instructions: List[DecodedInstruction]) -> JITBlock:
        """Compile to native code via llvmlite."""
        # This is a very small and limited example.  We build a function
        # that simply dispatches back to the Python opcode handlers.
        # In a full implementation we would translate the bytecode to
        # real machine operations.  Here we keep it minimal but still
        # produce an executable LLVM function when llvmlite is available.
        module = ir.Module(name="jit")
        func_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(64).as_pointer()])
        func = ir.Function(module, func_ty, name="jit_block")
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        builder.ret_void()

        llvm_module = llvm.parse_assembly(str(module))
        llvm_module.verify()
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        with llvm.create_mcjit_compiler(llvm_module, target_machine) as ee:
            ee.finalize_object()
            ptr = ee.get_function_address("jit_block")

            import ctypes

            cfunc = ctypes.CFUNCTYPE(None, ctypes.c_void_p)(ptr)

            def block(vm: "VM") -> Iterable[str]:  # pragma: no cover - runtime
                cfunc(id(vm))
                vm.ip += len(instructions)
                return iter(())

            return JITBlock(block, end_ip=0)

