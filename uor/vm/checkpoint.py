"""Checkpoint helpers for the VM."""
from __future__ import annotations

import json
import os
import time
from typing import List, Dict, Tuple

from .. import ipfs_storage

try:
    import boto3  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    boto3 = None


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def serialize_state(stack: List[int], mem: Dict[int, int], ip: int) -> bytes:
    """Serialize ``stack``, ``mem`` and ``ip`` to bytes."""
    data = {"stack": stack, "mem": mem, "ip": ip}
    return json.dumps(data).encode("utf-8")


def deserialize_state(data: bytes) -> Tuple[List[int], Dict[int, int], int]:
    """Deserialize bytes into VM state."""
    obj = json.loads(data.decode("utf-8"))
    mem = {int(k): int(v) for k, v in obj.get("mem", {}).items()}
    stack = [int(v) for v in obj.get("stack", [])]
    ip = int(obj.get("ip", 0))
    return stack, mem, ip


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------

class FileBackend:
    """Store checkpoints as local files."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save(self, name: str, data: bytes) -> str:
        path = os.path.join(self.directory, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def load(self, identifier: str) -> bytes:
        with open(identifier, "rb") as fh:
            return fh.read()


class IPFSBackend:
    """Store checkpoints in IPFS."""

    def save(self, name: str, data: bytes) -> str:  # name unused
        return ipfs_storage.add_data(data)

    def load(self, identifier: str) -> bytes:
        return ipfs_storage.get_data(identifier)


class S3Backend:
    """Store checkpoints in an S3 bucket."""

    def __init__(self, bucket: str) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 is not installed")
        self.bucket = bucket
        self.client = boto3.client("s3")

    def save(self, name: str, data: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=name, Body=data)
        return name

    def load(self, identifier: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=identifier)
        body = obj["Body"].read()
        return body


# ---------------------------------------------------------------------------
# Auto-checkpoint policies
# ---------------------------------------------------------------------------

class BasePolicy:
    """Base class for checkpoint policies."""

    def should_checkpoint(self, vm) -> bool:  # pragma: no cover - interface
        raise NotImplementedError


class TimePolicy(BasePolicy):
    """Checkpoint every ``interval`` seconds."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._last = time.time()

    def should_checkpoint(self, vm) -> bool:
        now = time.time()
        if now - self._last >= self.interval:
            self._last = now
            return True
        return False


class InstructionCountPolicy(BasePolicy):
    """Checkpoint every ``count`` executed instructions."""

    def __init__(self, count: int) -> None:
        self.count = count
        self._counter = 0

    def should_checkpoint(self, vm) -> bool:
        self._counter += 1
        if self._counter >= self.count:
            self._counter = 0
            return True
        return False


class MemoryPolicy(BasePolicy):
    """Checkpoint when memory usage reaches ``threshold`` entries."""

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold

    def should_checkpoint(self, vm) -> bool:
        return len(vm.mem) >= self.threshold

