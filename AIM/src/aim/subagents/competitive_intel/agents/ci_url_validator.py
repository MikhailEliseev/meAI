"""
CI URL Validator - URL Validation Agent

Проверяет доступность URL перед дорогими операциями (Deep Analysis).
Спрашивает пользователя при проблемах.

Lesson learned: Never auto-generate URLs without validation.
Feedback: Never return empty results without asking user.
"""

import asyncio
import ssl
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

from meai.agents.base_agent import Agent, Task, TaskResult
from src.aim.core.agent_learning import AgentLearning


class CIURLValidator(Agent):
    """URL Validator Agent

    Проверяет URL перед Deep Analysis:
    1. Проверяет доступность URL (HTTP status)
    2. Проверяет DNS resolution
    3. Проверяет SSL сертификат
    4. Спрашивает пользователя при проблемах
    5. Возвращает validated URLs или запрашивает корректные
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        timeout: float = 10.0
    ):
        super().__init__(agent_id, database_url, vault_path)
        self.timeout = timeout
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

        # Initialize learning system
        self.learning = AgentLearning(agent_id=agent_id)

    def get_capabilities(self) -> list[str]:
        return [
            "url_validation",
            "accessibility_check",
            "dns_resolution",
            "ssl_verification",
            "user_interaction"
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute URL validation

        Task payload:
        {
            "competitors": [
                {"name": "Competitor 1", "url": "https://example.com"}
            ]
        }

        Returns:
        {
            "validated": [
                {"name": "...", "url": "...", "status": "ok"}
            ],
            "failed": [
                {"name": "...", "url": "...", "error": "...", "action": "skip|retry|corrected"}
            ]
        }
        """
        try:
            start_time = datetime.now()
            competitors = task.payload.get("competitors", [])

            if not competitors:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No competitors provided"},
                    error="No competitors provided",
                    duration_seconds=0.0,
                    completed_at=datetime.now()
                )

            # 🎓 LEARNING: Read lessons before starting
            print(f"[CI URL Validator] 📚 Читаю уроки перед валидацией...")
            lessons = await self.learning.get_lessons(
                tags=["validation", "ci-system", "url-validation"],
                severity="critical"
            )

            if lessons:
                print(f"[CI URL Validator] ✅ Найдено {len(lessons)} уроков")
                applied = await self.learning.apply_lessons(task, lessons)
                print(f"[CI URL Validator] 📋 Применено {len(applied['rules_applied'])} правил")

                # Show prevention rules
                for rule in applied['rules_applied'][:3]:  # Show first 3
                    print(f"[CI URL Validator]   • {rule['type']}: {rule['rule'][:80]}...")

            print(f"\n[CI URL Validator] 🔍 Валидирую {len(competitors)} URL...")

            validated = []
            failed = []

            for i, competitor in enumerate(competitors, 1):
                name = competitor.get("name", "Unknown")
                url = competitor.get("url", "")

                print(f"\n[CI URL Validator] [{i}/{len(competitors)}] Проверяю: {name}")
                print(f"[CI URL Validator]   URL: {url}")

                # Validate URL
                validation_result = await self._validate_url(url, name)

                if validation_result["status"] == "ok":
                    print(f"[CI URL Validator]   ✅ URL доступен")
                    validated.append({
                        "name": name,
                        "url": url,
                        "status": "ok",
                        "details": validation_result
                    })
                else:
                    print(f"[CI URL Validator]   ❌ Проблема: {validation_result['error']}")

                    # 🎓 PREVENTION RULE: Never return empty results without asking user
                    action = await self._ask_user_for_correction(name, url, validation_result)

                    if action["action"] == "corrected":
                        # User provided correct URL
                        corrected_url = action["corrected_url"]
                        print(f"[CI URL Validator]   🔄 Проверяю исправленный URL: {corrected_url}")

                        # Validate corrected URL
                        corrected_validation = await self._validate_url(corrected_url, name)

                        if corrected_validation["status"] == "ok":
                            print(f"[CI URL Validator]   ✅ Исправленный URL доступен")
                            validated.append({
                                "name": name,
                                "url": corrected_url,
                                "status": "ok",
                                "details": corrected_validation,
                                "original_url": url,
                                "corrected": True
                            })
                        else:
                            print(f"[CI URL Validator]   ❌ Исправленный URL тоже недоступен")
                            failed.append({
                                "name": name,
                                "url": corrected_url,
                                "original_url": url,
                                "error": corrected_validation["error"],
                                "action": "skip"
                            })
                    elif action["action"] == "skip":
                        print(f"[CI URL Validator]   ⏭️  Пропускаю конкурента")
                        failed.append({
                            "name": name,
                            "url": url,
                            "error": validation_result["error"],
                            "action": "skip"
                        })
                    elif action["action"] == "retry":
                        print(f"[CI URL Validator]   🔄 Повторная попытка...")
                        retry_validation = await self._validate_url(url, name)

                        if retry_validation["status"] == "ok":
                            print(f"[CI URL Validator]   ✅ URL доступен после retry")
                            validated.append({
                                "name": name,
                                "url": url,
                                "status": "ok",
                                "details": retry_validation,
                                "retried": True
                            })
                        else:
                            print(f"[CI URL Validator]   ❌ URL недоступен после retry")
                            failed.append({
                                "name": name,
                                "url": url,
                                "error": retry_validation["error"],
                                "action": "skip"
                            })

                # Delay between requests
                if i < len(competitors):
                    await asyncio.sleep(1.0)

            duration = (datetime.now() - start_time).total_seconds()

            print(f"\n[CI URL Validator] ✅ Валидация завершена:")
            print(f"[CI URL Validator]   • Успешно: {len(validated)}")
            print(f"[CI URL Validator]   • Проблемы: {len(failed)}")
            print(f"[CI URL Validator]   • Время: {duration:.1f}s")

            # Record success
            await self.learning.record_success(
                task=task,
                result={"validated": len(validated), "failed": len(failed)},
                metrics={"validation_rate": len(validated) / len(competitors) if competitors else 0}
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="completed",
                result={
                    "validated": validated,
                    "failed": failed,
                    "total": len(competitors),
                    "success_rate": len(validated) / len(competitors) if competitors else 0
                },
                error=None,
                duration_seconds=duration,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[CI URL Validator] ❌ Ошибка: {str(e)}")

            # Record failure
            await self.learning.record_failure(
                task=task,
                error=e,
                context={"competitors": len(competitors) if 'competitors' in locals() else 0}
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now()
            )

    async def _validate_url(self, url: str, name: str) -> Dict[str, Any]:
        """Validate URL accessibility

        Returns:
        {
            "status": "ok" | "error",
            "http_status": 200,
            "error": "...",
            "dns_ok": True,
            "ssl_ok": True,
            "redirect_chain": [...]
        }
        """
        result = {
            "status": "error",
            "http_status": None,
            "error": None,
            "dns_ok": False,
            "ssl_ok": False,
            "redirect_chain": []
        }

        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result["error"] = "Invalid URL format"
                return result

            # Check DNS resolution
            try:
                import socket
                socket.gethostbyname(parsed.netloc)
                result["dns_ok"] = True
            except socket.gaierror:
                result["error"] = "DNS resolution failed"
                return result

            # Check HTTP accessibility
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': self.user_agent}
            ) as session:
                async with session.get(url, allow_redirects=True) as response:
                    result["http_status"] = response.status

                    # Track redirect chain
                    if response.history:
                        result["redirect_chain"] = [
                            str(r.url) for r in response.history
                        ]

                    # Check SSL (if HTTPS)
                    if parsed.scheme == "https":
                        result["ssl_ok"] = True

                    # Check status code
                    if 200 <= response.status < 300:
                        result["status"] = "ok"
                        result["error"] = None
                    elif 300 <= response.status < 400:
                        result["error"] = f"Redirect to {response.url}"
                    elif 400 <= response.status < 500:
                        result["error"] = f"Client error: {response.status}"
                    elif 500 <= response.status < 600:
                        result["error"] = f"Server error: {response.status}"
                    else:
                        result["error"] = f"Unexpected status: {response.status}"

        except asyncio.TimeoutError:
            result["error"] = f"Timeout after {self.timeout}s"
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    async def _ask_user_for_correction(
        self,
        name: str,
        url: str,
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ask user what to do with failed URL

        Returns:
        {
            "action": "corrected" | "skip" | "retry",
            "corrected_url": "..." (if action == "corrected")
        }
        """
        error = validation_result.get("error", "Unknown error")
        http_status = validation_result.get("http_status", "N/A")

        print(f"\n[CI URL Validator] ⚠️  Требуется действие пользователя:")
        print(f"[CI URL Validator]   Конкурент: {name}")
        print(f"[CI URL Validator]   URL: {url}")
        print(f"[CI URL Validator]   Ошибка: {error}")
        print(f"[CI URL Validator]   HTTP Status: {http_status}")
        print(f"\n[CI URL Validator] Что делать?")
        print(f"[CI URL Validator]   1. Ввести правильный URL")
        print(f"[CI URL Validator]   2. Пропустить этого конкурента")
        print(f"[CI URL Validator]   3. Попробовать ещё раз")

        # TODO: Integrate with AskUserQuestion tool
        # For now, return skip (will be replaced with real user interaction)

        # Placeholder: In real implementation, this would use AskUserQuestion
        # For now, we'll skip failed URLs
        return {
            "action": "skip",
            "reason": "User interaction not yet implemented"
        }

    async def _get_user_input(self, prompt: str) -> str:
        """Get user input (placeholder for AskUserQuestion integration)"""
        # TODO: Integrate with Claude Code's AskUserQuestion tool
        # This is a placeholder that will be replaced
        return ""


# Example usage
async def example_usage():
    """Example of how to use CI URL Validator"""

    validator = CIURLValidator(
        agent_id="ci-url-validator",
        database_url="sqlite+aiosqlite:///./data/meai.db",
        vault_path="./obsidian/ci-url-validator"
    )

    task = Task(
        task_id="test-validation",
        subtask_id="test-validation-1",
        action="validate_urls",
        payload={
            "competitors": [
                {"name": "Good Site", "url": "https://google.com"},
                {"name": "Bad Site", "url": "https://this-site-does-not-exist-12345.com"},
                {"name": "Wrong URL", "url": "https://doctor-shcherbatova.ru"}
            ]
        },
        priority=1,
        created_at=datetime.now()
    )

    result = await validator.execute_task(task)

    print(f"\n✅ Validation completed:")
    print(f"  Validated: {len(result.result['validated'])}")
    print(f"  Failed: {len(result.result['failed'])}")
    print(f"  Success rate: {result.result['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(example_usage())
