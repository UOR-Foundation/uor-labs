class UORException(Exception):
    """Base class for exceptions raised by the UOR VM."""
    def __init__(self, message: str, ip: int | None = None) -> None:
        super().__init__(message)
        self.ip = ip

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.ip is not None:
            return f"[{self.ip}] {super().__str__()}"
        return super().__str__()

class DivisionByZeroError(UORException):
    """Raised when a division by zero occurs."""

class MemoryAccessError(UORException):
    """Raised on invalid memory access or allocation failure."""

class StackOverflowError(UORException):
    """Raised when the VM stack exceeds its allowed size."""

class InvalidOpcodeError(UORException):
    """Raised when an unknown opcode is encountered."""

class ChecksumError(UORException):
    """Raised when an instruction checksum is invalid."""

class StackUnderflowError(UORException):
    """Raised when popping from an empty stack."""

class SegmentationFaultError(UORException):
    """Raised when the instruction pointer becomes invalid."""
