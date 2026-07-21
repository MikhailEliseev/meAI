"""Unit-тесты отзывов через Apify (замена Perplexity).

Проверяют:
- нормализацию ответов Yandex/2ГИС actor'ов
- обработку пустых результатов
- ротацию ключей при 429/402
- сборку итогового JSON в формате, совместимом с _format_reviews_block
- кэширование (повторный вызов не дёргает Apify)

Все тесты без сети — httpx мокается через monkeypatch.
"""
import json
import time

import httpx
import pytest

from app.lib import gis2_reviews, yandex_reviews
from app.tools import run_review_platforms


# --- fakes (копия паттерна из test_competitors.py) -------------------------

class _FakeResponse:
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


class _SequenceResponse:
    """AsyncClient, который выдаёт заранее заданную последовательность ответов.

    Первые N post/get вызовов возвращают заготовленные response по порядку.
    Нужно для эмуляции Apify flow: POST start → GET poll (×N) → GET dataset.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self._idx = 0
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, **kw):
        self.calls.append(("POST", url, json))
        return self._next()

    async def get(self, url, **kw):
        self.calls.append(("GET", url))
        return self._next()

    def _next(self):
        if self._idx >= len(self._responses):
            return _FakeResponse({"data": {"status": "SUCCEEDED", "defaultDatasetId": "ds_final"}}, 200)
        resp = self._responses[self._idx]
        self._idx += 1
        if isinstance(resp, Exception):
            raise resp
        return resp


def _patch_ac_httpx(monkeypatch, module, responses):
    """Подменить httpx.AsyncClient в модуле на _SequenceResponse.

    responses — список ответов (post/get). Каждый новый AsyncClient()
    продолжает с того места, где остановился предыдущий (общий счётчик),
    что важно для тестов ротации ключей, где _run_actor вызывается多次.
    """
    shared_seq = {"responses": list(responses), "idx": 0}

    class _SharedSequenceResponse(_SequenceResponse):
        def __init__(self):
            self._responses = shared_seq["responses"]
            self._idx = shared_seq["idx"]
            self.calls = []

        def _next(self):
            shared_seq["idx"] = self._idx
            return super()._next()

    def factory(*a, **kw):
        return _SharedSequenceResponse()

    monkeypatch.setattr(module.httpx, "AsyncClient", factory)
    return shared_seq


# --- Yandex нормализация ---------------------------------------------------

class TestYandexNormalize:
    def test_basic_rating_and_reviews(self):
        """Реальный формат m_mamaev/yandex-maps-places-scraper (проверено 21 июля)."""
        raw = {"totalScore": 5, "ratingCount": 562, "reviewsCount": 311, "address": "Верейская 44"}
        result = yandex_reviews._normalize(raw, "ARclinic")
        assert result is not None
        assert result["rating"] == 5.0
        assert result["reviews"] == 562  # ratingCount берём как основное
        assert result["address"] == "Верейская 44"
        assert result["source"] == "yandex_maps"

    def test_aspects_and_neurosummary(self):
        """Actor отдаёт структурированные аспекты + AI-сводку от Яндекса."""
        raw = {
            "totalScore": 4.8,
            "ratingCount": 100,
            "reviewAspects": [
                {"name": "Персонал", "count": 294},
                {"name": "Атмосфера", "count": 64},
            ],
            "neurosummary": "Отличная клиника, компетентные врачи",
            "title": "АРклиник",
        }
        result = yandex_reviews._normalize(raw, "test")
        assert len(result["aspects"]) == 2
        assert result["aspects"][0] == {"name": "Персонал", "count": 294}
        assert "Отличная клиника" in result["neuro_summary"]
        assert result["name"] == "АРклиник"

    def test_alternative_rating_field(self):
        """Если totalScore нет — пробуем rating."""
        raw = {"rating": "3.8", "ratingCount": "12", "title": "СтомСмайл"}
        result = yandex_reviews._normalize(raw, "СтомСмайл")
        assert result["rating"] == 3.8
        assert result["reviews"] == 12

    def test_no_rating_returns_none(self):
        """Без рейтинга отзыв бесполезен — возвращаем None."""
        assert yandex_reviews._normalize({"ratingCount": 5}, "test") is None
        assert yandex_reviews._normalize({}, "test") is None
        assert yandex_reviews._normalize(None, "test") is None

    def test_invalid_rating_type_returns_none(self):
        assert yandex_reviews._normalize({"totalScore": "не число"}, "test") is None


# --- 2ГИС нормализация -----------------------------------------------------

class TestGis2Normalize:
    def test_basic(self):
        """2gis-places-scraper: rating + reviewCount + reviews[].text."""
        raw = {"rating": 4.5, "reviewCount": 23, "name": "ARclinic"}
        result = gis2_reviews._normalize(raw, "ARclinic")
        assert result["rating"] == 4.5
        assert result["reviews"] == 23
        assert result["source"] == "2gis"

    def test_reviews_texts_extracted(self):
        """2ГИС actor отдаёт тексты отзывов через reviews[].text."""
        raw = {
            "rating": 4.0,
            "reviewCount": 2,
            "reviews": [
                {"text": "Хороший врач"},
                {"text": "Долгое ожидание"},
            ],
        }
        result = gis2_reviews._normalize(raw, "test")
        assert len(result["review_texts"]) == 2
        assert "Хороший врач" in result["review_texts"][0]

    def test_no_rating(self):
        assert gis2_reviews._normalize({"name": "test"}, "test") is None
        assert gis2_reviews._normalize({}, "test") is None


# --- Извлечение тем --------------------------------------------------------

class TestThemeExtraction:
    def test_positive_marker_detected(self):
        texts = ["Огромное спасибо врачу за профессионализм и внимание!"]
        praise, criticism = run_review_platforms._extract_themes(texts)
        assert len(praise) == 1
        assert "спасибо" in praise[0].lower() or "профессионал" in praise[0].lower()
        assert criticism == []

    def test_negative_marker_detected(self):
        texts = ["Ужасное отношение, грубость на ресепшене."]
        praise, criticism = run_review_platforms._extract_themes(texts)
        assert criticism == [] or len(criticism) == 1
        # "ужас" должен попасть
        if criticism:
            assert "ужас" in criticism[0].lower()

    def test_empty_returns_empty(self):
        praise, criticism = run_review_platforms._extract_themes([])
        assert praise == []
        assert criticism == []

    def test_no_markers_returns_empty(self):
        texts = ["Обычный нейтральный отзыв без ярких маркеров."]
        praise, criticism = run_review_platforms._extract_themes(texts)
        assert praise == []
        assert criticism == []


# --- Сборка итогового JSON (формат совместимый с _format_reviews_block) ----

def _patch_search(monkeypatch, yandex_ret, gis2_ret):
    """Подменить yandex_reviews.search и gis2_reviews.search на заглушки.

    Патчит атрибуты самих модулей, чтобы `from app.lib import yandex_reviews`
    внутри run_review_platforms видел подмену.
    """
    async def fake_yandex(*a, **kw):
        if isinstance(yandex_ret, Exception):
            raise yandex_ret
        return yandex_ret

    async def fake_gis2(*a, **kw):
        if isinstance(gis2_ret, Exception):
            raise gis2_ret
        return gis2_ret

    monkeypatch.setattr(yandex_reviews, "search", fake_yandex)
    monkeypatch.setattr(gis2_reviews, "search", fake_gis2)


class TestRunReviewPlatformsFormat:
    def test_both_platforms_present(self, monkeypatch):
        """Обе площадки найдены → корректный формат для форматтера."""
        yandex_mock = {"rating": 4.2, "reviews": 47, "review_texts": ["Спасибо!"], "source": "yandex_maps"}
        gis2_mock = {"rating": 4.5, "reviews": 23, "review_texts": [], "source": "2gis"}

        run_review_platforms._cache.clear()
        _patch_search(monkeypatch, yandex_mock, gis2_mock)

        import asyncio
        result_json = asyncio.run(
            run_review_platforms.handle_run_review_platforms(
                url="https://arclinic.ru",
                company_name="ARclinic",
                city="Санкт-Петербург",
            )
        )
        data = json.loads(result_json)

        # Формат совместим с _format_reviews_block:
        assert "platforms" in data
        assert data["platforms"]["yandex"]["rating"] == 4.2
        assert data["platforms"]["yandex"]["reviews"] == 47
        assert data["platforms"]["twogis"]["rating"] == 4.5
        assert data["platforms"]["prodoctorov"] == {}  # пропускаем

        assert "praise_summary" in data
        assert "criticism_summary" in data
        assert "reputation_summary" in data
        assert "4.2" in data["reputation_summary"]
        assert data["source"] == "apify"
        run_review_platforms._cache.clear()

    def test_one_platform_missing(self, monkeypatch):
        """Яндекс не нашёлся → блок строится только по 2ГИС."""
        run_review_platforms._cache.clear()
        _patch_search(
            monkeypatch,
            yandex_ret=None,
            gis2_ret={"rating": 4.0, "reviews": 5, "review_texts": [], "source": "2gis"},
        )

        import asyncio
        result_json = asyncio.run(
            run_review_platforms.handle_run_review_platforms(
                url="test.ru", company_name="Test", city="Москва"
            )
        )
        data = json.loads(result_json)
        assert data["platforms"]["yandex"] == {}
        assert data["platforms"]["twogis"]["rating"] == 4.0
        run_review_platforms._cache.clear()


# --- Кэширование -----------------------------------------------------------

class TestCache:
    def test_cache_hit_skips_apify(self, monkeypatch):
        """Повторный вызов в течение TTL не должен дёргать Apify."""
        run_review_platforms._cache.clear()

        call_count = {"n": 0}

        async def fake_yandex(*a, **kw):
            call_count["n"] += 1
            return {"rating": 4.0, "reviews": 10, "review_texts": [], "source": "yandex_maps"}

        async def fake_gis2(*a, **kw):
            return None

        monkeypatch.setattr(yandex_reviews, "search", fake_yandex)
        monkeypatch.setattr(gis2_reviews, "search", fake_gis2)

        import asyncio
        asyncio.run(
            run_review_platforms.handle_run_review_platforms(
                url="cached.ru", company_name="Cached", city="Город"
            )
        )
        asyncio.run(
            run_review_platforms.handle_run_review_platforms(
                url="cached.ru", company_name="Cached", city="Город"
            )
        )
        assert call_count["n"] == 1  # второй раз взялось из кэша
        run_review_platforms._cache.clear()


# --- Ротация ключей при 429 ------------------------------------------------

class TestKeyRotation:
    def test_429_triggers_next_key(self, monkeypatch):
        """402/429 на первом ключе → mark_exhausted → второй ключ → успех."""
        from app.lib import apify_client

        # Мок пула: 2 ключа
        class _FakePool:
            def __init__(self):
                self._keys = ["key1", "key2"]
                self._idx = 0
                self.exhausted = []

            async def get_next_key(self):
                k = self._keys[self._idx % len(self._keys)]
                self._idx += 1
                return k

            async def mark_exhausted(self, key, reason):
                self.exhausted.append((key, reason))

        fake_pool = _FakePool()
        monkeypatch.setattr(apify_client, "get_apify_pool", lambda: fake_pool)

        # Мок httpx: различаем по token в URL — key1 → 429, key2 → успех
        class _TokenAwareClient:
            def __init__(self, *a, **kw):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def post(self, url, json=None, **kw):
                if "key1" in url:
                    raise httpx.HTTPStatusError(
                        "rate limited", request=None,
                        response=_FakeResponse({"error": "rl"}, status_code=429),
                    )
                return _FakeResponse({"data": {"id": "run_ok"}}, 200)

            async def get(self, url, **kw):
                if "run_ok" in url and "status" not in url:
                    return _FakeResponse({"data": {"status": "SUCCEEDED", "defaultDatasetId": "ds1"}}, 200)
                if "datasets" in url:
                    return _FakeResponse([{"totalScore": 4.0, "ratingCount": 10}], 200)
                return _FakeResponse({"data": {"status": "SUCCEEDED"}}, 200)

        monkeypatch.setattr(yandex_reviews.httpx, "AsyncClient", _TokenAwareClient)

        import asyncio
        result = asyncio.run(yandex_reviews.search("Test", "Москва"))

        # первый ключ помечен исчерпанным
        assert len(fake_pool.exhausted) == 1
        assert fake_pool.exhausted[0] == ("key1", "rate_limited")
        # результат получен со второго ключа
        assert result is not None
        assert result["rating"] == 4.0
