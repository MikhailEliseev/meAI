"""Client Knowledge Manager — per-client vault isolation for Hermes.

Each client gets a vault directory with:
- services.md — prices and service descriptions
- faq.md — frequently asked questions
- tone_of_voice.md — communication style rules
- escalation_rules.md — custom escalation triggers
- qualification.md — lead qualification criteria

At conversation start, the vault is loaded and injected into the Hermes
system prompt, so the agent responds with client-specific knowledge.

Part of Phase 13: AI Sales Admin Agent — Sub-Phase 3.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE = Path(__file__).resolve().parents[5] / "hermes" / "knowledge" / "clients"

VAULT_FILES = [
    "services.md",
    "faq.md",
    "tone_of_voice.md",
    "escalation_rules.md",
    "qualification.md",
]

TEMPLATE_VAULT: dict[str, str] = {
    "services.md": (
        "# Услуги и цены\n\n"
        "> Заполните услуги и цены клиента.\n"
        "> Формат: услуга — цена, описание в одну строку.\n\n"
        "| Услуга | Цена | Описание |\n"
        "|--------|------|----------|\n"
        "| Пример услуги | 10 000 ₽ | Краткое описание |\n"
    ),
    "faq.md": (
        "# Частые вопросы\n\n"
        "> Заполните частые вопросы и ответы.\n\n"
        "### В: Пример вопроса?\n"
        "**О:** Пример ответа.\n"
    ),
    "tone_of_voice.md": (
        "# Тон общения\n\n"
        "> Укажите стиль общения клиента.\n\n"
        "- **Формальность:** professional / friendly / casual\n"
        "- **Язык:** ru\n"
        "- **Медицинские термины:** patient_friendly / professional\n"
        "- **Запрещённые темы:** (укажите темы, которые нельзя обсуждать)\n"
    ),
    "escalation_rules.md": (
        "# Правила эскалации\n\n"
        "> Настройте клиент-специфичные правила эскалации.\n\n"
        "- **Менеджер для эскалаций:** (имя)\n"
        "- **Telegram менеджера:** @username\n"
        "- **Email менеджера:** example@mail.ru\n"
        "- **Рабочие часы:** 09:00–21:00 МСК\n"
        "- **Критические темы:** (темы, требующие немедленной эскалации)\n"
    ),
    "qualification.md": (
        "# Критерии квалификации\n\n"
        "> Настройте критерии для квалификации лидов.\n\n"
        "- **Высокоценные специальности:** (перечислить)\n"
        "- **Минимальный бюджет:** (сумма в ₽)\n"
        "- **Целевые услуги:** (перечислить)\n"
        "- **Города присутствия:** (перечислить)\n"
        "- **Стоп-факторы:** (что disqualifies лид сразу)\n"
    ),
}


class KnowledgeManager:
    """Manages per-client vaults for the Sales Admin Agent.

    Loads client-specific knowledge (services, FAQ, tone of voice,
    escalation rules, qualification criteria) and formats it for
    injection into Hermes system prompts.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        self._base = base_path or KNOWLEDGE_BASE
        self._cache: dict[str, dict[str, str]] = {}

    # ── Vault lifecycle ───────────────────────────────────────────────────

    def ensure_vault(self, client_id: str) -> Path:
        """Create a client vault from template if it doesn't exist.

        Returns the vault directory path.
        """
        vault_dir = self._base / client_id
        vault_dir.mkdir(parents=True, exist_ok=True)

        for filename, template_content in TEMPLATE_VAULT.items():
            file_path = vault_dir / filename
            if not file_path.exists():
                file_path.write_text(template_content)
                logger.info(f"Created {file_path}")

        return vault_dir

    def vault_exists(self, client_id: str) -> bool:
        """Check if a client vault directory exists."""
        return (self._base / client_id).is_dir()

    # ── Loading ───────────────────────────────────────────────────────────

    def load_vault(self, client_id: str, use_cache: bool = True) -> dict[str, str]:
        """Load all vault files for a client.

        Returns {filename: content} dict. Missing files are silently skipped.
        """
        if use_cache and client_id in self._cache:
            return self._cache[client_id]

        vault_dir = self._base / client_id
        if not vault_dir.is_dir():
            logger.warning(f"Vault not found: {vault_dir} — using defaults")
            self.ensure_vault(client_id)

        loaded: dict[str, str] = {}
        for filename in VAULT_FILES:
            file_path = vault_dir / filename
            if file_path.exists():
                content = file_path.read_text().strip()
                if content:
                    loaded[filename] = content

        if use_cache:
            self._cache[client_id] = loaded

        logger.info(f"Loaded vault for {client_id}: {list(loaded.keys())}")
        return loaded

    def invalidate_cache(self, client_id: str | None = None) -> None:
        """Clear the vault cache for a client or all clients."""
        if client_id:
            self._cache.pop(client_id, None)
        else:
            self._cache.clear()

    # ── Prompt formatting ─────────────────────────────────────────────────

    def format_for_prompt(
        self,
        client_id: str,
        sections: list[str] | None = None,
    ) -> str:
        """Load and format a client vault for injection into a system prompt.

        Args:
            client_id: The client identifier.
            sections: Which vault files to include. None = all.

        Returns:
            Formatted markdown string ready for system prompt insertion.
        """
        vault = self.load_vault(client_id)

        if not vault:
            return ""

        parts: list[str] = [f"## ЗНАНИЯ КЛИЕНТА ({client_id})"]

        include = set(sections or VAULT_FILES)

        section_order = [
            ("services.md", "### Услуги и цены"),
            ("faq.md", "### Частые вопросы"),
            ("tone_of_voice.md", "### Тон общения"),
            ("escalation_rules.md", "### Правила эскалации"),
            ("qualification.md", "### Критерии квалификации"),
        ]

        for filename, heading in section_order:
            if filename in include and filename in vault:
                parts.append(heading)
                parts.append(vault[filename])
                parts.append("")

        # Only return if we have more than just the header
        if len(parts) == 1:
            return ""

        return "\n".join(parts)

    # ── CRUD helpers for API ─────────────────────────────────────────────

    def update_file(self, client_id: str, filename: str, content: str) -> Path:
        """Write a single vault file. Creates vault dir if needed."""
        if filename not in VAULT_FILES:
            raise ValueError(f"Unknown vault file: {filename}. Must be one of {VAULT_FILES}")

        self.ensure_vault(client_id)
        file_path = self._base / client_id / filename
        file_path.write_text(content)
        self.invalidate_cache(client_id)
        logger.info(f"Updated {file_path}")
        return file_path

    def read_file(self, client_id: str, filename: str) -> str | None:
        """Read a single vault file. Returns None if not found."""
        file_path = self._base / client_id / filename
        if file_path.exists():
            return file_path.read_text()
        return None

    def list_clients(self) -> list[str]:
        """List all client IDs that have vault directories."""
        if not self._base.is_dir():
            return []
        return [
            d.name
            for d in self._base.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]


# Singleton for the hermes package to import
knowledge_manager = KnowledgeManager()
