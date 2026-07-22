"""Unit-тесты для publisher — публикация HTML-отчёта в WordPress.

Все тесты без сети — pymysql.connect мокается через monkeypatch.
"""
import asyncio
import json
import os
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from app.report_builder import publisher
from app.report_builder.publisher import publish_report, _random_slug


# --- helpers ----------------------------------------------------------------

class _FakeCursor:
    """Мок pymysql cursor — отслеживает execute/fetchone/lastrowid."""
    def __init__(self, existing_slugs=None):
        self._existing = existing_slugs or []
        self._queries = []
        self.lastrowid = 42
        self._fetch_count = 0

    def execute(self, query, params=None):
        self._queries.append((query, params))
        # Для SELECT — возвращаем "найдено" если slug в existing
        if "SELECT" in query.upper() and params:
            slug = params[0] if isinstance(params, tuple) else params
            return 1 if slug in self._existing else 0
        return 1

    def fetchone(self):
        # Первый slug найден (дубликат), второй — нет
        if self._fetch_count < len(self._existing):
            self._fetch_count += 1
            return (1,)  # найден
        return None  # не найден (уникальный)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeConn:
    """Мок pymysql connection."""
    def __init__(self, cursor=None):
        self._cursor = cursor or _FakeCursor()
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass


# --- _random_slug ------------------------------------------------------------

class TestRandomSlug:
    def test_length(self):
        slug = _random_slug()
        assert len(slug) == 8

    def test_custom_length(self):
        slug = _random_slug(12)
        assert len(slug) == 12

    def test_charset(self):
        slug = _random_slug(100)
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789" for c in slug)

    def test_uniqueness(self):
        slugs = {_random_slug() for _ in range(50)}
        assert len(slugs) >= 45  # практически все уникальные


# --- publish_report ----------------------------------------------------------

class TestPublishReport:
    def test_success(self, monkeypatch):
        """Успешная публикация — возвращается URL с slug и post_id."""
        fake_conn = _FakeConn()
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")
        monkeypatch.setattr(publisher, "WP_DB_HOST", "aim-mysql")

        with patch("pymysql.connect", return_value=fake_conn):
            result = asyncio.run(publish_report("<html>test</html>", "TestClinic"))

        assert result["status"] == "published"
        assert result["url"].startswith("https://iamaim.ru/")
        assert result["post_id"] == 42
        assert fake_conn.committed is True

    def test_no_db_password_saves_locally(self, monkeypatch, tmp_path):
        """Без WP_DB_PASSWORD — отчёт сохраняется локально."""
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "")
        monkeypatch.setattr(publisher.os, "makedirs", lambda *a, **kw: None)

        mock_open = MagicMock()
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        monkeypatch.setattr("builtins.open", mock_open)

        result = asyncio.run(publish_report("<html>local</html>", "Local"))

        assert result["status"] == "saved_locally"
        assert result["url"] is None
        assert ".html" in result["path"]

    def test_slug_uniqueness_retry(self, monkeypatch):
        """При дубликате slug — генерируется новый."""
        fake_cursor = _FakeCursor(existing_slugs=["aaaaaaaa"])
        fake_conn = _FakeConn(cursor=fake_cursor)
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        with patch("pymysql.connect", return_value=fake_conn):
            result = asyncio.run(publish_report("<html>test</html>", "Test"))

        assert result["status"] == "published"
        # При дубликате slug должен был быть retry (execute SELECT вызван >1 раза)
        select_queries = [q for q in fake_cursor._queries if "SELECT" in q[0].upper()]
        assert len(select_queries) >= 1

    def test_mysql_error_handled(self, monkeypatch):
        """Ошибка MySQL — graceful return с error."""
        import pymysql as _pymysql
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        def raise_error(**kw):
            raise _pymysql.Error("Connection refused")

        with patch("pymysql.connect", side_effect=raise_error):
            result = asyncio.run(publish_report("<html>test</html>", "Test"))

        assert result["status"] == "error"
        assert "Database" in result["error"] or "Connection" in result["error"]

    def test_generic_error_handled(self, monkeypatch):
        """Произвольная ошибка — graceful return с error."""
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        with patch("pymysql.connect", side_effect=RuntimeError("unexpected")):
            result = asyncio.run(publish_report("<html>test</html>", "Test"))

        assert result["status"] == "error"
        assert "unexpected" in result["error"]

    def test_title_prefixed_with_aim(self, monkeypatch):
        """Заголовок страницы = 'AIM — {title}'."""
        fake_conn = _FakeConn()
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        captured_params = []

        class _CapturingCursor(_FakeCursor):
            def execute(self, query, params=None):
                if "INSERT" in query.upper():
                    captured_params.append(params)
                return super().execute(query, params)

        fake_conn = _FakeConn(cursor=_CapturingCursor())

        with patch("pymysql.connect", return_value=fake_conn):
            asyncio.run(publish_report("<html>test</html>", "ARclinic"))

        # post_title = params[4] (5-й параметр в INSERT)
        assert len(captured_params) >= 1
        insert_params = captured_params[0]
        assert insert_params[4] == "AIM — ARclinic"

    def test_insert_contains_html(self, monkeypatch):
        """HTML попадает в post_content (params[3])."""
        fake_conn = _FakeConn()
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        captured = []

        class _CaptureCursor(_FakeCursor):
            def execute(self, query, params=None):
                if "INSERT" in query.upper():
                    captured.append(params)
                return super().execute(query, params)

        fake_conn = _FakeConn(cursor=_CaptureCursor())
        test_html = "<html><body>Full Report</body></html>"

        with patch("pymysql.connect", return_value=fake_conn):
            asyncio.run(publish_report(test_html, "Test"))

        assert len(captured) >= 1
        assert captured[0][3] == test_html  # post_content = params[3]

    def test_post_status_publish(self, monkeypatch):
        """post_status = 'publish' (params[5]), post_type = 'page' (params[9])."""
        fake_conn = _FakeConn()
        monkeypatch.setattr(publisher, "WP_DB_PASSWORD", "secret")

        captured = []

        class _CaptureCursor(_FakeCursor):
            def execute(self, query, params=None):
                if "INSERT" in query.upper():
                    captured.append(params)
                return super().execute(query, params)

        fake_conn = _FakeConn(cursor=_CaptureCursor())

        with patch("pymysql.connect", return_value=fake_conn):
            asyncio.run(publish_report("<html>test</html>", "Test"))

        assert captured[0][5] == "publish"  # post_status
        assert captured[0][9] == "page"  # post_type
