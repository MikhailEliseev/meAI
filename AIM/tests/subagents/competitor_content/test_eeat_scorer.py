"""
Unit tests for E-E-A-T Scorer.

Tests medical YMYL content scoring for Experience, Expertise, Authoritativeness, Trustworthiness.
"""

from datetime import datetime, timedelta

import pytest

from AIM.src.aim.subagents.competitor_content.eeat_scorer import EEATScorer


class TestEEATScorer:
    """Test E-E-A-T Scorer functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        scorer = EEATScorer()

        assert scorer.min_word_count == 300
        assert scorer.freshness_months == 12
        assert scorer.min_update_percentage == 0.20

    def test_initialization_custom(self):
        """Test custom initialization."""
        scorer = EEATScorer(
            min_word_count=500, freshness_months=6, min_update_percentage=0.30
        )

        assert scorer.min_word_count == 500
        assert scorer.freshness_months == 6
        assert scorer.min_update_percentage == 0.30

    def test_score_basic_structure(self):
        """Test basic score structure."""
        scorer = EEATScorer()

        html = "<html><body><p>Медицинская статья о лечении.</p></body></html>"
        text = "Медицинская статья о лечении."

        result = scorer.score(html, text, "https://example.com")

        assert "overall_score" in result
        assert "compliance" in result
        assert "experience" in result
        assert "expertise" in result
        assert "authoritativeness" in result
        assert "trustworthiness" in result
        assert "recommendations" in result

        assert 0.0 <= result["overall_score"] <= 100.0
        assert result["compliance"] in ["excellent", "good", "fair", "poor"]

    def test_experience_scoring_case_studies(self):
        """Test experience scoring with case studies."""
        scorer = EEATScorer()

        html = "<html><body><p>Случай из практики: пациент 45 лет с диагнозом...</p></body></html>"
        text = "Случай из практики: пациент 45 лет с диагнозом. Результаты лечения показали улучшение на 80%."

        result = scorer.score(html, text, "https://example.com")

        assert result["experience"]["score"] > 0
        assert len(result["experience"]["signals"]) > 0

    def test_experience_scoring_personal_language(self):
        """Test experience scoring with personal language."""
        scorer = EEATScorer()

        # Need >5 instances of personal language to trigger signal
        html = "<html><body><p>Наши пациенты получают качественное лечение. Мы используем современные методы. Наша клиника работает 10 лет. Мы гордимся нашими результатами. Наши врачи имеют большой опыт. Мы помогаем нашим пациентам.</p></body></html>"
        text = "Наши пациенты получают качественное лечение. Мы используем современные методы. Наша клиника работает 10 лет. Мы гордимся нашими результатами. Наши врачи имеют большой опыт. Мы помогаем нашим пациентам."

        result = scorer.score(html, text, "https://example.com")

        assert result["experience"]["score"] > 0
        signals = result["experience"]["signals"]
        assert any("Personal experience" in s for s in signals)

    def test_expertise_scoring_credentials(self):
        """Test expertise scoring with medical credentials."""
        scorer = EEATScorer()

        html = "<html><body><p>Автор: Иванов И.И., врач-хирург, кандидат медицинских наук</p></body></html>"
        text = "Автор: Иванов И.И., врач-хирург, кандидат медицинских наук. Специализация: пластическая хирургия."

        result = scorer.score(html, text, "https://example.com")

        assert result["expertise"]["score"] > 0
        signals = result["expertise"]["signals"]
        assert any("credentials" in s.lower() for s in signals)

    def test_expertise_scoring_medical_terminology(self):
        """Test expertise scoring with medical terminology."""
        scorer = EEATScorer()

        # Need >10 medical terms to trigger signal
        html = "<html><body><p>Диагностика и лечение заболевание. Терапия включает профилактику и реабилитацию. Хирургия и анестезия необходимы для лечение патология. Диагностика помогает в профилактике заболевание. Терапия и реабилитация важны для лечение. Симптомы заболевание требуют диагностика и лечение патология.</p></body></html>"
        text = "Диагностика и лечение заболевание. Терапия включает профилактику и реабилитацию. Хирургия и анестезия необходимы для лечение патология. Диагностика помогает в профилактике заболевание. Терапия и реабилитация важны для лечение. Симптомы заболевание требуют диагностика и лечение патология."

        result = scorer.score(html, text, "https://example.com")

        assert result["expertise"]["score"] > 0
        signals = result["expertise"]["signals"]
        assert any("terminology" in s.lower() for s in signals)

    def test_expertise_scoring_author_bio(self):
        """Test expertise scoring with author bio section."""
        scorer = EEATScorer()

        html = """
        <html>
        <body>
            <p>Медицинская статья</p>
            <div class="author-bio">
                <p>Автор: Доктор Петров, врач высшей категории</p>
            </div>
        </body>
        </html>
        """
        text = "Медицинская статья. Автор: Доктор Петров, врач высшей категории."

        result = scorer.score(html, text, "https://example.com")

        assert result["expertise"]["score"] > 0
        signals = result["expertise"]["signals"]
        assert any("bio" in s.lower() for s in signals)

    def test_authoritativeness_scoring_citations(self):
        """Test authoritativeness scoring with authoritative citations."""
        scorer = EEATScorer()

        html = """
        <html>
        <body>
            <p>Исследование показало <a href="https://pubmed.ncbi.nlm.nih.gov/12345">результаты</a></p>
            <p>По данным <a href="https://who.int/article">ВОЗ</a></p>
        </body>
        </html>
        """
        text = "Исследование показало результаты. По данным ВОЗ."

        result = scorer.score(html, text, "https://example.com")

        assert result["authoritativeness"]["score"] > 0
        signals = result["authoritativeness"]["signals"]
        assert any("citations" in s.lower() for s in signals)

    def test_authoritativeness_scoring_awards(self):
        """Test authoritativeness scoring with awards and certifications."""
        scorer = EEATScorer()

        html = "<html><body><p>Клиника имеет сертификат качества и лицензию Минздрава. Награждена премией.</p></body></html>"
        text = "Клиника имеет сертификат качества и лицензию Минздрава. Награждена премией."

        result = scorer.score(html, text, "https://example.com")

        assert result["authoritativeness"]["score"] > 0
        signals = result["authoritativeness"]["signals"]
        assert any("certifications" in s.lower() for s in signals)

    def test_trustworthiness_scoring_freshness(self):
        """Test trustworthiness scoring with content freshness."""
        scorer = EEATScorer()

        html = "<html><body><p>Медицинская статья. Обновлено недавно.</p></body></html>"
        text = "Медицинская статья. Обновлено недавно."

        # Recent update (3 months ago)
        updated_date = datetime.now() - timedelta(days=90)

        result = scorer.score(
            html, text, "https://example.com", updated_date=updated_date
        )

        assert result["trustworthiness"]["score"] > 0
        signals = result["trustworthiness"]["signals"]
        assert any("updated" in s.lower() for s in signals)

    def test_trustworthiness_scoring_old_content(self):
        """Test trustworthiness scoring with old content."""
        scorer = EEATScorer()

        html = "<html><body><p>Медицинская статья.</p></body></html>"
        text = "Медицинская статья."

        # Old update (3 years ago)
        updated_date = datetime.now() - timedelta(days=1095)

        result = scorer.score(
            html, text, "https://example.com", updated_date=updated_date
        )

        # Should have lower trustworthiness score
        assert result["trustworthiness"]["score"] < 50

    def test_trustworthiness_scoring_contact_info(self):
        """Test trustworthiness scoring with contact information."""
        scorer = EEATScorer()

        html = "<html><body><p>Контакты: телефон +7 (495) 123-45-67, email info@clinic.ru, адрес: Москва</p></body></html>"
        text = "Контакты: телефон +7 (495) 123-45-67, email info@clinic.ru, адрес: Москва"

        result = scorer.score(html, text, "https://example.com")

        assert result["trustworthiness"]["score"] > 0
        signals = result["trustworthiness"]["signals"]
        assert any("contact" in s.lower() for s in signals)

    def test_trustworthiness_scoring_privacy_policy(self):
        """Test trustworthiness scoring with privacy policy."""
        scorer = EEATScorer()

        html = "<html><body><p>Политика конфиденциальности. Пользовательское соглашение.</p></body></html>"
        text = "Политика конфиденциальности. Пользовательское соглашение."

        result = scorer.score(html, text, "https://example.com")

        assert result["trustworthiness"]["score"] > 0
        signals = result["trustworthiness"]["signals"]
        assert any("privacy" in s.lower() for s in signals)

    def test_trustworthiness_scoring_medical_disclaimer(self):
        """Test trustworthiness scoring with medical disclaimer."""
        scorer = EEATScorer()

        html = "<html><body><p>Информация не является медицинской консультацией. Обратитесь к специалисту.</p></body></html>"
        text = "Информация не является медицинской консультацией. Обратитесь к специалисту."

        result = scorer.score(html, text, "https://example.com")

        assert result["trustworthiness"]["score"] > 0
        signals = result["trustworthiness"]["signals"]
        assert any("disclaimer" in s.lower() for s in signals)

    def test_trustworthiness_scoring_references(self):
        """Test trustworthiness scoring with references."""
        scorer = EEATScorer()

        html = """
        <html>
        <body>
            <p>Исследование показало</p>
            <cite>Источник: Медицинский журнал, 2024</cite>
            <blockquote>Цитата из исследования</blockquote>
        </body>
        </html>
        """
        text = "Исследование показало. Источник: Медицинский журнал, 2024. Цитата из исследования."

        result = scorer.score(html, text, "https://example.com")

        assert result["trustworthiness"]["score"] > 0
        signals = result["trustworthiness"]["signals"]
        assert any("references" in s.lower() or "citations" in s.lower() for s in signals)

    def test_compliance_excellent(self):
        """Test compliance level determination - excellent."""
        scorer = EEATScorer()

        # High-quality medical content
        html = """
        <html itemscope itemtype="http://schema.org/MedicalOrganization">
        <body>
            <div class="author-bio">
                <p>Автор: Доктор Иванов, врач-хирург, кандидат медицинских наук</p>
            </div>
            <p>Случай из практики: пациент 45 лет. Результаты лечения: улучшение на 85%.</p>
            <p>Диагностика и лечение заболеваний. Терапия включает профилактику.</p>
            <p>Исследование <a href="https://pubmed.ncbi.nlm.nih.gov/12345">опубликовано</a></p>
            <p>Сертификат качества. Лицензия Минздрава.</p>
            <p>Обновлено: 2024-04-01. Контакты: телефон, email, адрес.</p>
            <p>Политика конфиденциальности. Не является медицинской консультацией.</p>
            <cite>Источник: Медицинский журнал</cite>
        </body>
        </html>
        """
        text = """
        Автор: Доктор Иванов, врач-хирург, кандидат медицинских наук.
        Случай из практики: пациент 45 лет. Результаты лечения: улучшение на 85%.
        Диагностика и лечение заболеваний. Терапия включает профилактику.
        Исследование опубликовано. Сертификат качества. Лицензия Минздрава.
        Обновлено: 2024-04-01. Контакты: телефон, email, адрес.
        Политика конфиденциальности. Не является медицинской консультацией.
        Источник: Медицинский журнал.
        """

        updated_date = datetime.now() - timedelta(days=30)
        result = scorer.score(
            html, text, "https://example.com", updated_date=updated_date
        )

        # Should have high overall score
        assert result["overall_score"] >= 60
        assert result["compliance"] in ["good", "excellent"]

    def test_compliance_poor(self):
        """Test compliance level determination - poor."""
        scorer = EEATScorer()

        # Low-quality content
        html = "<html><body><p>Короткая статья без деталей.</p></body></html>"
        text = "Короткая статья без деталей."

        result = scorer.score(html, text, "https://example.com")

        # Should have low overall score
        assert result["overall_score"] < 40
        assert result["compliance"] == "poor"

    def test_recommendations_generation(self):
        """Test recommendations generation based on scores."""
        scorer = EEATScorer()

        html = "<html><body><p>Простая статья.</p></body></html>"
        text = "Простая статья."

        result = scorer.score(html, text, "https://example.com")

        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        # Should have recommendations for improvement
        assert any("case studies" in r.lower() for r in result["recommendations"])

    def test_schema_org_detection(self):
        """Test schema.org markup detection."""
        scorer = EEATScorer()

        html = """
        <html itemscope itemtype="http://schema.org/MedicalOrganization">
        <body>
            <p>Медицинская организация</p>
        </body>
        </html>
        """
        text = "Медицинская организация"

        result = scorer.score(html, text, "https://example.com")

        # Should detect schema markup
        expertise_signals = result["expertise"]["signals"]
        trust_signals = result["trustworthiness"]["signals"]

        assert any("schema" in s.lower() for s in expertise_signals + trust_signals)

    def test_weighted_scoring(self):
        """Test weighted scoring (Expertise and Trustworthiness are most important for medical YMYL)."""
        scorer = EEATScorer()

        # Content with high expertise and trustworthiness
        html = """
        <html>
        <body>
            <p>Автор: Доктор Петров, врач высшей категории, кандидат медицинских наук</p>
            <p>Диагностика и лечение заболеваний. Терапия и профилактика.</p>
            <p>Обновлено недавно. Контакты: телефон, email.</p>
            <p>Политика конфиденциальности. Не является медицинской консультацией.</p>
        </body>
        </html>
        """
        text = """
        Автор: Доктор Петров, врач высшей категории, кандидат медицинских наук.
        Диагностика и лечение заболеваний. Терапия и профилактика.
        Обновлено недавно. Контакты: телефон, email.
        Политика конфиденциальности. Не является медицинской консультацией.
        """

        updated_date = datetime.now() - timedelta(days=60)
        result = scorer.score(
            html, text, "https://example.com", updated_date=updated_date
        )

        # Expertise and trustworthiness should contribute more to overall score
        # (35% + 30% = 65% of total weight)
        assert result["expertise"]["score"] > 0
        assert result["trustworthiness"]["score"] > 0
