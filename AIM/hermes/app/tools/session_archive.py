"""session_archive — Persistent session data storage.

Три функции для сохранения и загрузки данных пайплайна на диск.
Используется engine.py, agent_wrapper.py, generate_html_report.py.

Данные хранятся в SESSIONS_ROOT/{session_hash}/data/*.json + metadata.json.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

SESSIONS_ROOT = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")


def _session_dir(session_id: str) -> Path:
    """Путь к директории сессии."""
    return Path(SESSIONS_ROOT) / session_id


def _data_dir(session_id: str) -> Path:
    """Путь к data/ внутри сессии."""
    return _session_dir(session_id) / "data"


def save_tool_output(session_id: str, key: str, value: dict) -> str:
    """Сохранить выходные данные инструмента как {key}.json.

    Атомарная запись: пишем во временный файл → os.rename().

    Args:
        session_id: ID сессии (hash).
        key: Ключ данных (например, "PHASE_1_TECH_AUDIT").
        value: Данные для сохранения (dict).

    Returns:
        Путь к сохранённому файлу.
    """
    data_dir = _data_dir(session_id)
    data_dir.mkdir(parents=True, exist_ok=True)

    filepath = data_dir / f"{key}.json"

    # Ensure parent directories exist (e.g. data/TECH AUDIT/)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
        safe_key = key.replace("/", "_").replace(" ", "_")
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json", prefix=f".{safe_key}_", dir=str(data_dir)
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2, default=str)

        os.rename(tmp_path, str(filepath))
        logger.debug("session_archive: saved %s/%s.json (%d keys)", session_id[:12], key, len(value))
        return str(filepath)
    except Exception as e:
        logger.error("session_archive: failed to save %s/%s.json: %s", session_id[:12], key, e)
        raise


def upsert_metadata(session_id: str, **kwargs) -> str:
    """Сохранить/обновить metadata.json (merge с существующим).

    Args:
        session_id: ID сессии.
        **kwargs: Данные для сохранения в metadata.

    Returns:
        Путь к сохранённому файлу.
    """
    sess_dir = _session_dir(session_id)
    sess_dir.mkdir(parents=True, exist_ok=True)

    filepath = sess_dir / "metadata.json"

    # Загружаем существующие метаданные, если есть
    existing = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}

    # Merge
    existing.update(kwargs)

    # Атомарная запись
    try:
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json", prefix=".metadata_", dir=str(sess_dir)
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2, default=str)

        os.rename(tmp_path, str(filepath))
        logger.debug("session_archive: metadata saved for %s", session_id[:12])
        return str(filepath)
    except Exception as e:
        logger.error("session_archive: failed to save metadata for %s: %s", session_id[:12], e)
        raise


def load_all_data(session_hash: str) -> dict:
    """Загрузить все .json из data/ + metadata.json в один dict.

    Args:
        session_hash: Хеш сессии (session_id).

    Returns:
        Словарь со всеми данными: {key: value, ..., "metadata": {...}}.
    """
    data_dir = _data_dir(session_hash)
    result = {}

    # Загружаем все .json из data/
    if data_dir.exists():
        for json_file in sorted(data_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                key = json_file.stem  # filename without .json
                result[key] = data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("session_archive: failed to load %s: %s", json_file, e)

    # Загружаем metadata.json
    metadata_path = _session_dir(session_hash) / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                result["metadata"] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("session_archive: failed to load metadata: %s", e)

    logger.info("session_archive: loaded %d keys for session %s", len(result), session_hash[:12])
    return result
