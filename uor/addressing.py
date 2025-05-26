from __future__ import annotations

"""Canonical addressing utilities based on 512-bit prime digests."""

import hashlib
from typing import Dict, Optional

from . import ipfs_storage
from .cache import InstructionCache
import primes


def _nearest_prime(n: int) -> int:
    """Return the smallest prime >= ``n`` using Miller-Rabin."""
    if n % 2 == 0:
        n += 1
    while True:
        if primes.miller_rabin(n):
            return n
        n += 2


def canonical_address(data: bytes) -> int:
    """Return a 512-bit prime digest for ``data``."""
    digest = hashlib.sha512(data).digest()
    num = int.from_bytes(digest, "big")
    return _nearest_prime(num)


class DHT:
    """Simple distributed hash table mapping addresses to IPFS CIDs."""

    def __init__(self, nodes: int = 3, cache_size: int = 64) -> None:
        self.tables = [{} for _ in range(max(1, nodes))]
        self.cache = InstructionCache(max_size=cache_size)
        self.namespaces: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Node selection helpers
    # ------------------------------------------------------------------
    def _select_table(self, addr: int) -> Dict[int, Dict[str, str]]:
        return self.tables[addr % len(self.tables)]

    # ------------------------------------------------------------------
    # Store and retrieve
    # ------------------------------------------------------------------
    def store(self, namespace: str, data: bytes) -> int:
        addr = canonical_address(data)
        cid = ipfs_storage.add_data(data)
        table = self._select_table(addr)
        existing = table.get(addr)
        if existing and existing.get("cid") != cid:
            # collision, search next free prime
            next_addr = _nearest_prime(addr + 2)
            addr = next_addr
            table = self._select_table(addr)
        table[addr] = {"namespace": namespace, "cid": cid}
        self.namespaces[namespace] = addr
        self.cache.put(addr, data)
        return addr

    def retrieve(self, addr: int) -> bytes:
        cached = self.cache.get(addr)
        if cached is not None:
            return cached
        table = self._select_table(addr)
        entry = table.get(addr)
        if not entry:
            raise KeyError("Address not found")
        data = ipfs_storage.get_data(entry["cid"])
        self.cache.put(addr, data)
        return data

    def resolve(self, namespace: str) -> Optional[int]:
        return self.namespaces.get(namespace)
