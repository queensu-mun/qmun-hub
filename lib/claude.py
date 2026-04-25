"""Anthropic client wrapper with prompt caching + cost computation.

Models locked: never use Opus in prod — too expensive for this app's budget envelope.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"

# Per-million-token USD pricing. Update if Anthropic shifts pricing.
PRICING = {
    HAIKU: {
        "input": 1.00,
        "input_cached": 0.10,
        "input_cache_write": 1.25,
        "output": 5.00,
    },
    SONNET: {
        "input": 3.00,
        "input_cached": 0.30,
        "input_cache_write": 3.75,
        "output": 15.00,
    },
}

# Cache control requires a minimum block length (~1024 tokens). Below this it's a no-op.
CACHE_MIN_CHARS = 4000


class Tier(str, Enum):
    CHEAP = HAIKU
    SMART = SONNET


@dataclass
class CallResult:
    text: str
    input_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    output_tokens: int
    cost_usd: float
    model: str


@lru_cache(maxsize=1)
def _api_key() -> str:
    """Read Anthropic key from env var, then Streamlit secrets, then secrets.toml directly."""
    if env := os.environ.get("ANTHROPIC_API_KEY"):
        return env
    try:
        import streamlit as st
        return st.secrets["anthropic"]["api_key"]
    except Exception:
        pass
    secrets_path = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib  # 3.11+
        except ModuleNotFoundError:
            try:
                import tomli as tomllib  # type: ignore
            except ModuleNotFoundError:
                import toml
                return toml.load(secrets_path)["anthropic"]["api_key"]
        with secrets_path.open("rb") as f:
            return tomllib.load(f)["anthropic"]["api_key"]
    raise RuntimeError("No Anthropic API key found in env, Streamlit secrets, or secrets.toml")


def _client() -> Anthropic:
    return Anthropic(api_key=_api_key())


def compute_cost(
    model: str,
    input_tokens: int,
    cached_input_tokens: int,
    cache_write_tokens: int,
    output_tokens: int,
) -> float:
    p = PRICING[model]
    fresh_input = max(0, input_tokens - cached_input_tokens - cache_write_tokens)
    return (
        fresh_input * p["input"]
        + cached_input_tokens * p["input_cached"]
        + cache_write_tokens * p["input_cache_write"]
        + output_tokens * p["output"]
    ) / 1_000_000


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def chat(
    messages: list[dict],
    *,
    tier: Tier = Tier.CHEAP,
    system: str | None = None,
    cache_system: bool = True,
    max_tokens: int = 1024,
    temperature: float = 1.0,
) -> CallResult:
    """Call Claude with optional prompt caching on the system prompt.

    When cache_system=True and system prompt is long enough, sends it as a
    cache_control=ephemeral block so subsequent calls within ~5min hit cache.
    """
    client = _client()
    model = tier.value

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }

    if system:
        if cache_system and len(system) >= CACHE_MIN_CHARS:
            kwargs["system"] = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        else:
            kwargs["system"] = system

    response = client.messages.create(**kwargs)

    text = "".join(getattr(b, "text", "") for b in response.content)

    usage = response.usage
    input_tokens = usage.input_tokens
    cached_input_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0
    output_tokens = usage.output_tokens

    cost = compute_cost(
        model, input_tokens, cached_input_tokens, cache_write_tokens, output_tokens
    )

    return CallResult(
        text=text,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_write_tokens=cache_write_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        model=model,
    )


def stream_chat(
    messages: list[dict],
    *,
    tier: Tier = Tier.CHEAP,
    system: str | None = None,
    cache_system: bool = True,
    max_tokens: int = 1024,
    temperature: float = 1.0,
):
    """Yield (text_delta, final_result_or_none) — final_result has token counts + cost."""
    client = _client()
    model = tier.value

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        if cache_system and len(system) >= CACHE_MIN_CHARS:
            kwargs["system"] = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        else:
            kwargs["system"] = system

    full_text = ""
    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                delta = event.delta.text
                full_text += delta
                yield delta, None
        final = stream.get_final_message()

    usage = final.usage
    input_tokens = usage.input_tokens
    cached_input_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0
    output_tokens = usage.output_tokens
    cost = compute_cost(model, input_tokens, cached_input_tokens, cache_write_tokens, output_tokens)

    yield "", CallResult(
        text=full_text,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_write_tokens=cache_write_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        model=model,
    )
