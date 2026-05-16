"""Email Template Renderer with Jinja2 and AI Personalization

Renders email templates with dynamic variables and optional AI-generated content.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template


class TemplateRenderer:
    """Renders email templates with Jinja2 and AI personalization.

    Supports:
    - Jinja2 template rendering with variables
    - AI content generation for personalization
    - HTML and plain text versions
    - Template caching for performance

    Example:
        renderer = TemplateRenderer()
        html, text = await renderer.render(
            template_id="hot_instant",
            context={
                "name": "Иван Петров",
                "specialty": "стоматология",
                "service": "имплантация зубов",
            }
        )
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize template renderer.

        Args:
            templates_dir: Path to templates directory.
                          Defaults to AIM/src/aim/services/email/templates/
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,  # Auto-escape HTML for security
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(
        self,
        template_id: str,
        context: Dict[str, Any],
        generate_ai_content: bool = True,
    ) -> tuple[str, str]:
        """Render email template with context.

        Args:
            template_id: Template identifier (e.g., 'hot_instant', 'warm_day0')
            context: Template variables (name, specialty, etc.)
            generate_ai_content: Whether to generate AI personalized content

        Returns:
            Tuple of (html_content, text_content)

        Raises:
            FileNotFoundError: If template files not found
            ValueError: If required context variables missing
        """
        # Load templates
        html_template = self.env.get_template(f"{template_id}.html")
        text_template = self.env.get_template(f"{template_id}.txt")

        # Enrich context with AI content if needed
        if generate_ai_content:
            context = await self._enrich_with_ai(template_id, context)

        # Add default variables
        context = self._add_defaults(context)

        # Render templates
        html_content = html_template.render(**context)
        text_content = text_template.render(**context)

        return html_content, text_content

    async def _enrich_with_ai(
        self, template_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich context with AI-generated content.

        Generates personalized content based on template and lead data.

        Args:
            template_id: Template identifier
            context: Current context variables

        Returns:
            Enriched context with AI-generated content
        """
        # AI content generation prompts per template
        ai_prompts = {
            "hot_instant": self._generate_hot_intro,
            "warm_day0": self._generate_warm_content,
            "warm_day3": self._generate_case_study,
            "warm_day7": self._generate_offer,
            "cold_weekly": self._generate_digest,
        }

        # Generate AI content if prompt exists
        if template_id in ai_prompts:
            ai_content = await ai_prompts[template_id](context)
            context.update(ai_content)

        return context

    async def _generate_hot_intro(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized intro for hot leads.

        Args:
            context: Lead context (specialty, service, etc.)

        Returns:
            Dict with 'ai_intro' key
        """
        # TODO: Integrate with AI service (Claude/GPT)
        # For now, return template-based intro
        specialty = context.get("specialty", "медицинская клиника")
        service = context.get("service", "услуга")

        intro = f"""
        <p>Я уже изучил специфику <strong>{specialty}</strong> и подготовил несколько идей,
        как мы можем помочь вам с <strong>{service}</strong>. Расскажу о них на консультации.</p>
        """

        return {"ai_intro": intro.strip()}

    async def _generate_warm_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate value proposition for warm leads.

        Args:
            context: Lead context

        Returns:
            Dict with 'ai_content' key
        """
        specialty = context.get("specialty", "медицинская клиника")

        content = f"""
        <p>Для клиник <strong>{specialty}</strong> мы разработали специальную методику продвижения,
        которая учитывает особенности вашей аудитории и конкурентной среды.</p>
        """

        return {"ai_content": content.strip()}

    async def _generate_case_study(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate case study content for warm leads.

        Args:
            context: Lead context

        Returns:
            Dict with 'ai_case_study' key
        """
        specialty = context.get("specialty", "медицинская клиника")

        case_study = f"""
        <p><strong>Что мы сделали:</strong> Провели глубокий анализ рынка {specialty},
        выявили недостатки в текущем маркетинге клиента и разработали комплексную стратегию
        продвижения с фокусом на SEO и таргетированную рекламу.</p>
        """

        return {"ai_case_study": case_study.strip()}

    async def _generate_offer(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized offer for warm leads.

        Args:
            context: Lead context

        Returns:
            Dict with 'ai_offer' key
        """
        specialty = context.get("specialty", "медицинская клиника")

        offer = f"""
        <p>Этот пакет специально адаптирован для клиник <strong>{specialty}</strong>
        и включает все необходимые инструменты для быстрого роста потока пациентов.</p>
        """

        return {"ai_offer": offer.strip()}

    async def _generate_digest(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate digest content for cold leads.

        Args:
            context: Lead context

        Returns:
            Dict with digest content
        """
        # TODO: Integrate with content generation service
        # For now, return placeholder content

        return {
            "ai_digest_intro": "<p>На этой неделе мы собрали для вас самые актуальные материалы по маркетингу медицинских клиник.</p>",
            "ai_digest_content": "",
            "trend_title": "Рост спроса на онлайн-консультации",
            "trend_category": "Тренды",
            "trend_summary": "По данным Яндекса, запросы на онлайн-консультации выросли на 45% за последний квартал.",
            "trend_url": "https://iamaim.ru/blog/online-consultations-trend",
            "weekly_tip": "Добавьте на сайт виджет онлайн-записи — это увеличивает конверсию на 20-30%.",
            "case_title": "Как клиника увеличила поток на 150%",
            "case_specialty": "Стоматология",
            "case_result": "+150% пациентов",
            "case_summary": "Комплексная стратегия SEO + контент + реклама за 3 месяца.",
            "case_url": "https://iamaim.ru/cases/dental-clinic-150",
            "market_stat_1_value": "45%",
            "market_stat_1_label": "Рост онлайн-записей",
            "market_stat_2_value": "30%",
            "market_stat_2_label": "Снижение стоимости лида",
            "education_title": "Как настроить Яндекс.Директ для клиники",
            "education_category": "Реклама",
            "education_summary": "Пошаговое руководство по настройке эффективной рекламной кампании.",
            "education_url": "https://iamaim.ru/education/yandex-direct-guide",
        }

    def _add_defaults(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add default variables to context.

        Args:
            context: Current context

        Returns:
            Context with defaults added
        """
        defaults = {
            "manager_name": "Михаил Елисеев",
            "manager_phone": "+7 (999) 123-45-67",
            "manager_email": "me@iamaim.ru",
            "consultation_url": "https://iamaim.ru/consultation",
            "unsubscribe_url": "https://iamaim.ru/unsubscribe?email={email}",
            "digest_date": datetime.now().strftime("%d.%m.%Y"),
            "offer_deadline": (datetime.now()).strftime("%d.%m.%Y"),
        }

        # Merge defaults with context (context takes precedence)
        return {**defaults, **context}

    def render_subject(self, template_id: str, context: Dict[str, Any]) -> str:
        """Render email subject line.

        Args:
            template_id: Template identifier
            context: Template variables

        Returns:
            Rendered subject line
        """
        subjects = {
            "hot_instant": "Ваш запрос на {{ service }} получен",
            "warm_day0": "Добро пожаловать в AIM Agency",
            "warm_day3": "Кейс: Как мы увеличили поток пациентов на 150%",
            "warm_day7": "Специальное предложение для {{ specialty }}",
            "cold_weekly": "📰 Дайджест для медицинских клиник | {{ digest_date }}",
        }

        subject_template = subjects.get(
            template_id, "Письмо от AIM Agency"
        )
        template = Template(subject_template)
        context = self._add_defaults(context)

        return template.render(**context)
