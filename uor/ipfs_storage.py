"""Utility helpers for storing programs in IPFS."""
from __future__ import annotations

import asyncio

try:
    import ipfshttpclient  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency not installed
    ipfshttpclient = None


def _require_client() -> None:
    if ipfshttpclient is None:
        raise RuntimeError("ipfshttpclient is not installed")


def add_data(data: bytes) -> str:
    """Add ``data`` to IPFS and return its CID."""
    _require_client()
    try:
        with ipfshttpclient.connect() as client:  # type: ignore[attr-defined]
            return client.add_bytes(data)
    except Exception as exc:  # ipfshttpclient errors are broad
        raise RuntimeError("Failed to add data to IPFS") from exc


def get_data(cid: str) -> bytes:
    """Retrieve data from IPFS by ``cid``."""
    _require_client()
    try:
        with ipfshttpclient.connect() as client:  # type: ignore[attr-defined]
            return client.cat(cid)
    except Exception as exc:
        raise RuntimeError("Failed to fetch data from IPFS") from exc


async def async_add_data(data: bytes) -> str:
    """Asynchronously add ``data`` to IPFS and return its CID."""
    return await asyncio.to_thread(add_data, data)


async def async_get_data(cid: str) -> bytes:
    """Asynchronously retrieve data from IPFS by ``cid``."""
    return await asyncio.to_thread(get_data, cid)
