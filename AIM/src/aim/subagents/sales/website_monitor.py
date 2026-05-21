"""Website Monitor — detects changes on client websites.

Daily cron job (3:00 AM) that crawls client websites, extracts service/price
information, compares against the vault, and updates services.md when changes
are detected. Alerts the admin via Telegram.

Part of Phase 13: AI Sales Admin Agent — Sub-Phase 3.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from aim.subagents.sales.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

# Common pages to check
SERVICE_PAGES = [
    "/", "/uslugi/", "/services/", "/price/", "/prices/",
    "/ceny/", "/tseny/", "/doctors/", "/vrachi/", "/specialists/",
    "/specialisty/", "/about/", "/contacts/", "/kontakty/",
]


class WebsiteMonitor:
    """Daily monitor for client website changes.

    Crawls configured URLs, extracts structured data, compares with
    vault contents, and updates when changes are detected.
    """

    def __init__(
        self,
        knowledge: KnowledgeManager | None = None,
        admin_chat_id: str | None = None,
    ) -> None:
        self._knowledge = knowledge or KnowledgeManager()
        self._admin_chat = admin_chat_id or TELEGRAM_ADMIN_CHAT_ID

    # ── Main entry point ──────────────────────────────────────────────────

    async def run_all(self) -> dict[str, dict]:
        """Run website check for all clients that have vaults.

        Returns {client_id: change_report}.
        """
        clients = self._knowledge.list_clients()
        if not clients:
            logger.info("WebsiteMonitor: no clients to check")
            return {}

        results: dict[str, dict] = {}
        for client_id in clients:
            try:
                results[client_id] = await self.check_client(client_id)
            except Exception:
                logger.exception(f"WebsiteMonitor failed for {client_id}")
                results[client_id] = {"error": "check_failed"}

        return results

    async def check_client(self, client_id: str) -> dict:
        """Check a single client's website for changes.

        1. Read website_url from vault qualification.md
        2. Crawl service/pricing pages
        3. Extract structured data
        4. Compare with current services.md
        5. Update if changes found
        6. Notify admin
        """
        vault = self._knowledge.load_vault(client_id)
        website_url = self._extract_website_url(vault)

        if not website_url:
            logger.info(f"No website_url for {client_id}, skipping")
            return {"status": "skipped", "reason": "no_website_url"}

        logger.info(f"Checking {website_url} for {client_id}")

        # Crawl relevant pages
        pages = await self._crawl_site(website_url)

        if not pages:
            return {"status": "skipped", "reason": "no_pages_fetched"}

        # Extract structured data
        extracted = self._extract_data(pages)

        # Compare with current vault
        current_services = vault.get("services.md", "")
        changed = self._detect_changes(current_services, extracted)

        if not changed:
            logger.info(f"No changes detected for {client_id}")
            return {"status": "no_changes"}

        # Update vault
        new_services_md = self._build_services_md(extracted, website_url)
        self._knowledge.update_file(client_id, "services.md", new_services_md)

        # Alert admin
        await self._notify_admin(client_id, website_url, changed)

        logger.info(f"Changes detected for {client_id}: {list(changed.keys())}")
        return {"status": "updated", "changes": changed}

    # ── Crawling ──────────────────────────────────────────────────────────

    async def _crawl_site(self, base_url: str) -> dict[str, str]:
        """Fetch content from common service pages.

        Returns {path: html_content}.
        """
        pages: dict[str, str] = {}

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for path in SERVICE_PAGES:
                url = urljoin(base_url, path)
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.text) > 500:
                        pages[path] = resp.text
                        logger.debug(f"Fetched {url} ({len(resp.text)} chars)")
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")

        return pages

    # ── Data extraction ───────────────────────────────────────────────────

    def _extract_data(self, pages: dict[str, str]) -> dict:
        """Extract structured data from crawled pages.

        Looks for: services (headings + prices), doctors, contacts.
        """
        services: list[str] = []
        doctors: list[str] = []
        prices: list[str] = []

        for path, html in pages.items():
            soup = BeautifulSoup(html, "html.parser")

            # Remove script/style tags
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

            # Detect service-like lines (headings + price patterns)
            price_keywords = ["руб", "₽", "цена", "стоимость", "price", "cost"]
            for line in lines:
                has_price = any(pk in line.lower() for pk in price_keywords)
                is_short = 5 < len(line) < 200
                if has_price and is_short:
                    prices.append(line)
                elif is_short and any(
                    kw in line.lower()
                    for kw in ["приём", "консультация", "лечение", "операция", "диагностика", "услуг"]
                ):
                    services.append(line)

            # Detect doctor names (common Russian name patterns)
            doctor_indicators = [
                "врач", "доктор", "специалист", "хирург", "терапевт",
                "стоматолог", "косметолог", "дерматолог", "гинеколог",
                "уролог", "невролог", "отоларинголог", "офтальмолог",
            ]
            for line in lines:
                if any(di in line.lower() for di in doctor_indicators):
                    doctors.append(line)

        return {
            "services": list(set(services)),
            "prices": list(set(prices)),
            "doctors": list(set(doctors)),
            "pages_crawled": len(pages),
        }

    # ── Change detection ──────────────────────────────────────────────────

    def _detect_changes(
        self,
        current_services_md: str,
        extracted: dict,
    ) -> dict | None:
        """Compare extracted data against current vault.

        Returns dict of {category: [new_items]} or None if no changes.
        """
        changes: dict[str, list] = {}

        for category in ["services", "prices", "doctors"]:
            items = extracted.get(category, [])
            if not items:
                continue

            # Simple check: do extracted items appear in current markdown?
            new_items = [
                item for item in items
                if item[:50] not in current_services_md
            ]

            # Only report if significant number of new items
            if len(new_items) >= 2 or (
                len(new_items) == 1 and len(items) <= 3
            ):
                changes[category] = new_items[:10]

        return changes if changes else None

    # ── Output ────────────────────────────────────────────────────────────

    def _build_services_md(self, extracted: dict, website_url: str) -> str:
        """Build updated services.md from extracted data."""
        lines = [
            f"# Услуги и цены",
            f"",
            f"> Автоматически обновлено: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
            f"> Источник: {website_url}",
            f"",
        ]

        if extracted.get("services"):
            lines.append("## Услуги")
            for s in sorted(extracted["services"])[:20]:
                lines.append(f"- {s}")
            lines.append("")

        if extracted.get("prices"):
            lines.append("## Цены")
            for p in sorted(extracted["prices"])[:20]:
                lines.append(f"- {p}")
            lines.append("")

        if extracted.get("doctors"):
            lines.append("## Врачи")
            for d in sorted(extracted["doctors"])[:20]:
                lines.append(f"- {d}")
            lines.append("")

        return "\n".join(lines)

    def _extract_website_url(self, vault: dict[str, str]) -> str | None:
        """Extract website URL from qualification.md or services.md."""
        qual = vault.get("qualification.md", "")
        # Simple extraction: look for URL patterns in the vault
        import re

        for content in [qual] + list(vault.values()):
            urls = re.findall(r"https?://[^\s\)]+", content)
            if urls:
                return urls[0].rstrip(".")
        return None

    # ── Notifications ─────────────────────────────────────────────────────

    async def _notify_admin(
        self,
        client_id: str,
        website_url: str,
        changes: dict,
    ) -> None:
        """Send a Telegram notification about detected changes."""
        if not self._admin_chat or not TELEGRAM_BOT_TOKEN:
            logger.warning("Cannot notify: TELEGRAM_ADMIN_CHAT_ID or BOT_TOKEN not set")
            return

        change_lines = []
        for category, items in changes.items():
            change_lines.append(f"<b>{category}</b>: {len(items)} новых")
            for item in items[:5]:
                change_lines.append(f"  • {item[:100]}")

        message = (
            f"🔍 <b>Изменения на сайте клиента</b>\n"
            f"Клиент: <b>{client_id}</b>\n"
            f"Сайт: {website_url}\n\n"
            + "\n".join(change_lines)
            + f"\n\nservices.md обновлён в vault клиента."
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json={
                    "chat_id": int(self._admin_chat),
                    "text": message,
                    "parse_mode": "HTML",
                })
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")


# ── Cron entry point ─────────────────────────────────────────────────────────


async def run_website_monitor() -> dict:
    """Entry point for the daily cron job (3:00 AM)."""
    monitor = WebsiteMonitor()
    return await monitor.run_all()
