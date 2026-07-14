"""Unit-тесты thin-wrapper find_competitors (Phase 1 Walking Skeleton).

Проверяют только прокси-логику без сети — httpx мокается через monkeypatch.
Паттерн копируется из бэкапа app/tools/find_competitors.py:283-298.
"""
import httpx
import pytest

from app.tools import competitors


# --- helpers ---------------------------------------------------------------

class _FakeResponse:
    """Минимальный double для httpx.Response — то, что использует competitors."""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=self
            )


class _FakeAsyncClient:
    """Drop-in замена httpx.AsyncClient: POST записывается, ответ фиксирован."""

    def __init__(self, captured, response):
        self._captured = captured
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kw):
        self._captured["url"] = url
        self._captured["json"] = json
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _patch_asyncclient(monkeypatch, response):
    """Подменяет httpx.AsyncClient в модуле competitors на фейковый."""
    captured = {}

    def factory(*args, **kwargs):
        return _FakeAsyncClient(captured, response)

    monkeypatch.setattr(competitors.httpx, "AsyncClient", factory)
    return captured


# --- tests -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_proxy_calls_correct_url(monkeypatch):
    """find_competitors стучится ровно на {AIM_API_BASE}/api/competitors/find
    с телом {"url", "count"} — AIM_API_BASE переопределён на тестовый."""
    monkeypatch.setattr(competitors, "AIM_API_BASE", "http://test-aim-app:9999")
    captured = _patch_asyncclient(
        monkeypatch, _FakeResponse({"success": True, "competitors": []})
    )

    await competitors.find_competitors(url="https://clinic.ru", count=3)

    assert captured["url"] == "http://test-aim-app:9999/api/competitors/find"
    assert captured["json"] == {"url": "https://clinic.ru", "count": 3}


@pytest.mark.asyncio
async def test_proxy_returns_upstream_json_as_is(monkeypatch):
    """Прозрачный прокси: upstream-JSON возвращается без трансформации."""
    monkeypatch.setattr(competitors, "AIM_API_BASE", "http://test-aim-app:9999")
    upstream = {
        "success": True,
        "competitors": [
            {"brand_name": "Конкурент X", "rating": 4.5, "reviews_count": 88},
        ],
    }
    _patch_asyncclient(monkeypatch, _FakeResponse(upstream))

    result = await competitors.find_competitors(url="https://clinic.ru", count=3)

    assert result == upstream
    assert result["competitors"][0]["brand_name"] == "Конкурент X"


@pytest.mark.asyncio
async def test_proxy_request_error_returns_error_dict(monkeypatch):
    """При httpx.RequestError функция НЕ бросает исключение, а возвращает
    {"error": ...} (per CLAUDE.md: tool handlers never throw)."""
    monkeypatch.setattr(competitors, "AIM_API_BASE", "http://test-aim-app:9999")
    _patch_asyncclient(
        monkeypatch,
        httpx.ConnectError("connection refused"),
    )

    result = await competitors.find_competitors(url="https://clinic.ru", count=3)

    assert "error" in result
    assert "aim-app" in result["error"] or "reach" in result["error"]
    assert "detail" in result
