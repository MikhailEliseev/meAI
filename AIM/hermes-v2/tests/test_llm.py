"""Unit-тесты LLM-клиента (Phase 2).

Мокают openai.AsyncClient — проверяют что системный промпт подставляется
и токены стримятся. Реальная сеть не нужна.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import llm


class _FakeChunk:
    """Фейковый chunk из openai streaming response."""

    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].delta.content = content


def _make_fake_stream(tokens):
    """Создаёт async-iterable фейковых chunks."""
    chunks = [_FakeChunk(t) for t in tokens]

    class _Stream:
        def __init__(self):
            self._i = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._i >= len(chunks):
                raise StopAsyncIteration
            c = chunks[self._i]
            self._i += 1
            return c

    return _Stream()


def _patch_client(monkeypatch, tokens=None, capture=None):
    """Подменяет get_client() фейковым клиентом с мок- streaming."""
    fake_client = MagicMock()

    async def fake_create(**kwargs):
        if capture is not None:
            capture["messages"] = kwargs["messages"]
        return _make_fake_stream(tokens or [])

    fake_client.chat.completions.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(llm, "get_client", lambda: fake_client)
    return fake_client


@pytest.mark.asyncio
async def test_system_prompt_prepended(monkeypatch):
    """stream_chat подаёт в client messages[0] = system с SYSTEM_PROMPT."""
    captured = {}
    _patch_client(monkeypatch, tokens=["ok"], capture=captured)

    collected = [t async for t in llm.stream_chat([{"role": "user", "content": "привет"}])]

    assert captured["messages"][0]["role"] == "system"
    assert "Гермес" in captured["messages"][0]["content"]
    assert captured["messages"][0]["content"] == llm.SYSTEM_PROMPT
    # история пользователя после промпта
    assert captured["messages"][1] == {"role": "user", "content": "привет"}
    assert collected == ["ok"]


@pytest.mark.asyncio
async def test_stream_yields_tokens(monkeypatch):
    """Streaming yields токены по порядку."""
    _patch_client(monkeypatch, tokens=["При", "вет"])

    collected = [t async for t in llm.stream_chat([{"role": "user", "content": "x"}])]

    assert collected == ["При", "вет"]


@pytest.mark.asyncio
async def test_stream_handles_empty_delta(monkeypatch):
    """chunk с delta.content=None (role/reasoning chunk) пропускается без ошибки."""
    # None между реальными токенами — частый случай в openai streaming
    _patch_client(monkeypatch, tokens=[None, "A", None, "B"])

    collected = [t async for t in llm.stream_chat([{"role": "user", "content": "x"}])]

    # None не попали в вывод
    assert collected == ["A", "B"]
