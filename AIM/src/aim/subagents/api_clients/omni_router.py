"""
Omni-Router для API интеграций

КРИТИЧНО: Прослойка для ротации моделей и провайдеров.
Позволяет подключать множество моделей и ротировать их вручную.
Fallback при падении одного провайдера.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import httpx
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class ProviderStatus(str, Enum):
    """Статус провайдера"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


class Provider:
    """Провайдер API"""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        priority: int = 0,
        timeout: int = 30,
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.priority = priority
        self.timeout = timeout

        # Статус и метрики
        self.status = ProviderStatus.ACTIVE
        self.failure_count = 0
        self.success_count = 0
        self.last_failure: Optional[datetime] = None
        self.last_success: Optional[datetime] = None

        # HTTP клиент
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Инициализация HTTP клиента"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    async def close(self) -> None:
        """Закрытие HTTP клиента"""
        if self.client:
            await self.client.aclose()

    def mark_success(self) -> None:
        """Отметить успешный запрос"""
        self.success_count += 1
        self.last_success = datetime.now()

        # Восстановление после деградации
        if self.status == ProviderStatus.DEGRADED:
            if self.success_count >= 3:
                self.status = ProviderStatus.ACTIVE
                self.failure_count = 0
                logger.info(
                    "provider_recovered",
                    provider=self.name,
                    success_count=self.success_count,
                )

    def mark_failure(self) -> None:
        """Отметить неудачный запрос"""
        self.failure_count += 1
        self.last_failure = datetime.now()

        # Деградация после 3 ошибок
        if self.failure_count >= 3 and self.status == ProviderStatus.ACTIVE:
            self.status = ProviderStatus.DEGRADED
            logger.warning(
                "provider_degraded",
                provider=self.name,
                failure_count=self.failure_count,
            )

        # Отключение после 5 ошибок
        if self.failure_count >= 5:
            self.status = ProviderStatus.FAILED
            logger.error(
                "provider_failed",
                provider=self.name,
                failure_count=self.failure_count,
            )

    def is_available(self) -> bool:
        """Проверка доступности провайдера"""
        if self.status in [ProviderStatus.FAILED, ProviderStatus.DISABLED]:
            return False

        # Cooldown после последней ошибки (1 минута)
        if self.last_failure:
            cooldown = timedelta(minutes=1)
            if datetime.now() - self.last_failure < cooldown:
                return False

        return True


class OmniRouter:
    """
    Omni-Router для API интеграций

    Функции:
    - Ротация между провайдерами
    - Fallback при падении
    - Ручное управление приоритетами
    - Мониторинг статуса
    """

    def __init__(self):
        self.providers: Dict[str, Provider] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Инициализация всех провайдеров"""
        for provider in self.providers.values():
            await provider.initialize()
        self._initialized = True
        logger.info("omni_router_initialized", providers=list(self.providers.keys()))

    async def close(self) -> None:
        """Закрытие всех провайдеров"""
        for provider in self.providers.values():
            await provider.close()
        logger.info("omni_router_closed")

    def add_provider(
        self,
        name: str,
        base_url: str,
        api_key: str,
        priority: int = 0,
        timeout: int = 30,
    ) -> None:
        """
        Добавить провайдера

        Args:
            name: Имя провайдера (например, "semrush", "ahrefs")
            base_url: Базовый URL API
            api_key: API ключ
            priority: Приоритет (выше = используется первым)
            timeout: Таймаут запросов в секундах
        """
        provider = Provider(
            name=name,
            base_url=base_url,
            api_key=api_key,
            priority=priority,
            timeout=timeout,
        )
        self.providers[name] = provider
        logger.info("provider_added", name=name, priority=priority)

    def remove_provider(self, name: str) -> None:
        """Удалить провайдера"""
        if name in self.providers:
            del self.providers[name]
            logger.info("provider_removed", name=name)

    def set_priority(self, name: str, priority: int) -> None:
        """Установить приоритет провайдера (ручная ротация)"""
        if name in self.providers:
            self.providers[name].priority = priority
            logger.info("provider_priority_changed", name=name, priority=priority)

    def disable_provider(self, name: str) -> None:
        """Отключить провайдера вручную"""
        if name in self.providers:
            self.providers[name].status = ProviderStatus.DISABLED
            logger.info("provider_disabled", name=name)

    def enable_provider(self, name: str) -> None:
        """Включить провайдера вручную"""
        if name in self.providers:
            self.providers[name].status = ProviderStatus.ACTIVE
            self.providers[name].failure_count = 0
            logger.info("provider_enabled", name=name)

    def get_available_providers(self) -> List[Provider]:
        """Получить список доступных провайдеров (отсортированных по приоритету)"""
        available = [p for p in self.providers.values() if p.is_available()]
        return sorted(available, key=lambda p: p.priority, reverse=True)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        preferred_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Выполнить запрос с автоматическим fallback

        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Endpoint API
            params: Query параметры
            json: JSON body
            preferred_provider: Предпочтительный провайдер (если доступен)

        Returns:
            Ответ API

        Raises:
            RuntimeError: Если все провайдеры недоступны
        """
        if not self._initialized:
            await self.initialize()

        # Получить список провайдеров
        providers = self.get_available_providers()

        # Попытаться использовать предпочтительного провайдера
        if preferred_provider and preferred_provider in self.providers:
            pref = self.providers[preferred_provider]
            if pref.is_available():
                providers.insert(0, pref)

        if not providers:
            raise RuntimeError("No available providers")

        # Попытки с fallback
        last_error = None
        for provider in providers:
            try:
                logger.info(
                    "attempting_request",
                    provider=provider.name,
                    method=method,
                    endpoint=endpoint,
                )

                response = await provider.client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json,
                )
                response.raise_for_status()

                provider.mark_success()
                logger.info(
                    "request_success",
                    provider=provider.name,
                    status_code=response.status_code,
                )

                return response.json()

            except Exception as e:
                provider.mark_failure()
                last_error = e
                logger.warning(
                    "request_failed",
                    provider=provider.name,
                    error=str(e),
                )
                continue

        # Все провайдеры упали
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def get_status(self) -> Dict[str, Any]:
        """Получить статус всех провайдеров"""
        return {
            name: {
                "status": provider.status.value,
                "priority": provider.priority,
                "success_count": provider.success_count,
                "failure_count": provider.failure_count,
                "last_success": provider.last_success.isoformat() if provider.last_success else None,
                "last_failure": provider.last_failure.isoformat() if provider.last_failure else None,
            }
            for name, provider in self.providers.items()
        }
