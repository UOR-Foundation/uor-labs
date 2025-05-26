"""LLM provider abstractions."""
from __future__ import annotations

import abc
import asyncio
import os
import json
import hashlib
from typing import AsyncGenerator, Any

try:
    import openai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    openai = None  # type: ignore

try:
    import anthropic  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    anthropic = None  # type: ignore

try:
    import google.generativeai as generativeai  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    generativeai = None  # type: ignore

try:
    import ollama  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    ollama = None  # type: ignore

try:
    import huggingface_hub  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    huggingface_hub = None  # type: ignore


_cache: dict[str, str] = {}


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class LLMProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    default_model: str = ""
    price_per_1k_tokens: float = 0.0
    max_retries: int = 3

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.default_model
        self.total_cost = 0.0

    # --- public API -----------------------------------------------------
    async def generate_code(self, prompt: str) -> str:
        return await self._call(prompt, purpose="generate")

    async def explain_code(self, code: str) -> str:
        prompt = f"Explain the following code:\n{code}"
        return await self._call(prompt, purpose="explain")

    async def optimize_code(self, code: str) -> str:
        prompt = f"Optimize the following code:\n{code}"
        return await self._call(prompt, purpose="optimize")

    async def fix_errors(self, code: str, errors: str) -> str:
        prompt = f"Fix the following errors in the code:\n{errors}\nCode:\n{code}"
        return await self._call(prompt, purpose="fix")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        async for chunk in self._stream_call(prompt):
            yield chunk

    # --- internal helpers ----------------------------------------------
    async def _call(self, prompt: str, *, purpose: str) -> str:
        key = self._cache_key(prompt, purpose)
        if key in _cache:
            return _cache[key]

        for attempt in range(self.max_retries):
            try:
                resp = await self._send_request(prompt)
                _cache[key] = resp
                self._update_cost(prompt, resp)
                return resp
            except Exception:
                if attempt >= self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    async def _stream_call(self, prompt: str) -> AsyncGenerator[str, None]:
        key = self._cache_key(prompt, "stream")
        if key in _cache:
            yield _cache[key]
            return
        acc = []
        for attempt in range(self.max_retries):
            try:
                async for chunk in self._send_request_stream(prompt):
                    acc.append(chunk)
                    yield chunk
                resp = "".join(acc)
                _cache[key] = resp
                self._update_cost(prompt, resp)
                return
            except Exception:
                if attempt >= self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    def _cache_key(self, prompt: str, purpose: str) -> str:
        m = hashlib.sha256()
        m.update(self.__class__.__name__.encode())
        m.update(purpose.encode())
        m.update(self.model.encode())
        m.update(prompt.encode())
        return m.hexdigest()

    def _update_cost(self, prompt: str, resp: str) -> None:
        tokens = _approx_tokens(prompt) + _approx_tokens(resp)
        self.total_cost += tokens / 1000 * self.price_per_1k_tokens

    # --- provider specific ---------------------------------------------
    @abc.abstractmethod
    async def _send_request(self, prompt: str) -> str:
        raise NotImplementedError

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        # default: fall back to non-streaming
        yield await self._send_request(prompt)


# ----------------------------------------------------------------------
# Provider implementations
# ----------------------------------------------------------------------


class OpenAIProvider(LLMProvider):
    default_model = "gpt-3.5-turbo"
    price_per_1k_tokens = 0.001

    async def _send_request(self, prompt: str) -> str:
        if openai is None:  # pragma: no cover - optional dependency
            raise RuntimeError("openai library is not installed")
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        if not openai.api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        resp = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if openai is None:  # pragma: no cover - optional
            raise RuntimeError("openai library is not installed")
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        if not openai.api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        stream = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            text = chunk.choices[0].delta.get("content", "")
            if text:
                yield text


class AnthropicProvider(LLMProvider):
    default_model = "claude-3-opus-20240229"
    price_per_1k_tokens = 0.002

    async def _send_request(self, prompt: str) -> str:
        if anthropic is None:  # pragma: no cover - optional
            raise RuntimeError("anthropic library is not installed")
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        resp = await client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return getattr(resp, "content", getattr(resp, "completion"))

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if anthropic is None:  # pragma: no cover - optional
            raise RuntimeError("anthropic library is not installed")
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        stream = await client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            text = getattr(chunk, "content", getattr(chunk, "completion", ""))
            if text:
                yield text


class GeminiProvider(LLMProvider):
    default_model = "gemini-pro"
    price_per_1k_tokens = 0.001

    async def _send_request(self, prompt: str) -> str:
        if generativeai is None:  # pragma: no cover - optional
            raise RuntimeError("google-generativeai library is not installed")
        generativeai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = generativeai.GenerativeModel(self.model)
        resp = await asyncio.to_thread(model.generate_content, prompt)
        return resp.text

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if generativeai is None:  # pragma: no cover - optional
            raise RuntimeError("google-generativeai library is not installed")
        generativeai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        model = generativeai.GenerativeModel(self.model)
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            yield chunk.text


class OllamaProvider(LLMProvider):
    default_model = "llama2"
    price_per_1k_tokens = 0.0

    async def _send_request(self, prompt: str) -> str:
        if ollama is None:  # pragma: no cover - optional
            raise RuntimeError("ollama library is not installed")
        resp = await ollama.acomplete(model=self.model, prompt=prompt)
        return resp["choices"][0]["message"]["content"]

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if ollama is None:  # pragma: no cover - optional
            raise RuntimeError("ollama library is not installed")
        async for chunk in ollama.astream(model=self.model, prompt=prompt):
            text = chunk.get("message", {}).get("content")
            if text:
                yield text


class HuggingFaceProvider(LLMProvider):
    default_model = "HuggingFaceH4/starchat-alpha"
    price_per_1k_tokens = 0.0

    def __init__(self, model: str | None = None, token: str | None = None) -> None:
        super().__init__(model)
        self.token = token or os.getenv("HF_API_TOKEN", "")

    async def _send_request(self, prompt: str) -> str:
        if huggingface_hub is None:  # pragma: no cover - optional
            raise RuntimeError("huggingface-hub library is not installed")
        client = huggingface_hub.InferenceClient(token=self.token)
        resp = await client.text_generation(prompt, model=self.model)
        return resp

    async def _send_request_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        if huggingface_hub is None:  # pragma: no cover - optional
            raise RuntimeError("huggingface-hub library is not installed")
        client = huggingface_hub.InferenceClient(token=self.token)
        async for chunk in client.text_generation(prompt, model=self.model, stream=True):
            yield chunk

