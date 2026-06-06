"""
Tests for NLP Extractor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.aim.services.document_processing.nlp_extractor import NLPExtractor


@pytest.fixture
def nlp_extractor():
    """Create NLP extractor instance"""
    with patch("src.aim.services.document_processing.nlp_extractor.spacy.load") as mock_load:
        with patch("src.aim.services.document_processing.nlp_extractor.Matcher") as mock_matcher:
            # Mock spaCy model
            mock_nlp = MagicMock()
            mock_vocab = MagicMock()
            mock_vocab.strings = {"EMAIL": 1, "PHONE": 2, "WEBSITE": 3}
            mock_nlp.vocab = mock_vocab
            mock_load.return_value = mock_nlp

            # Mock matcher instance
            mock_matcher_instance = MagicMock()
            mock_matcher.return_value = mock_matcher_instance

            extractor = NLPExtractor(model="en_core_web_sm")
            extractor.matcher = mock_matcher_instance
            return extractor


@pytest.fixture
def sample_text():
    """Sample document text"""
    return """
    Dental Clinic "Smile Plus"
    Location: Moscow, Russia
    Specialty: Cosmetic Dentistry

    Contact Information:
    Email: info@smileplus.ru
    Phone: +7 (495) 123-45-67
    Website: https://smileplus.ru

    Analytics:
    Google Analytics: UA-123456-1
    Yandex Metrica: 12345678
    Access: analytics@smileplus.ru

    Advertising:
    Google Ads: 123-456-7890
    Yandex Direct: 9876543210
    Access: ads@smileplus.ru
    """


class TestNLPExtractor:
    """Test NLP extractor"""

    @pytest.mark.asyncio
    async def test_init_with_model(self):
        """Test initialization with spaCy model"""
        with patch("src.aim.services.document_processing.nlp_extractor.spacy.load") as mock_load:
            with patch("src.aim.services.document_processing.nlp_extractor.Matcher"):
                mock_nlp = MagicMock()
                mock_vocab = MagicMock()
                mock_nlp.vocab = mock_vocab
                mock_load.return_value = mock_nlp

                extractor = NLPExtractor(model="en_core_web_sm")

                mock_load.assert_called_once_with("en_core_web_sm")
                assert extractor.nlp == mock_nlp

    @pytest.mark.asyncio
    async def test_init_fallback_to_blank(self):
        """Test fallback to blank model when model not found"""
        with patch("src.aim.services.document_processing.nlp_extractor.spacy.load") as mock_load:
            with patch("src.aim.services.document_processing.nlp_extractor.spacy.blank") as mock_blank:
                with patch("src.aim.services.document_processing.nlp_extractor.Matcher"):
                    mock_load.side_effect = OSError("Model not found")
                    mock_blank_nlp = MagicMock()
                    mock_vocab = MagicMock()
                    mock_blank_nlp.vocab = mock_vocab
                    mock_blank.return_value = mock_blank_nlp

                    extractor = NLPExtractor(model="en_core_web_sm")

                    mock_blank.assert_called_once_with("en")
                    assert extractor.nlp == mock_blank_nlp

    @pytest.mark.asyncio
    async def test_extract_practice_info_complete(self, nlp_extractor, sample_text):
        """Test extraction of complete practice information"""
        # Mock spaCy doc with entities
        mock_doc = MagicMock()
        mock_doc.ents = [
            MagicMock(label_="ORG", text="Smile Plus"),
            MagicMock(label_="GPE", text="Moscow"),
        ]
        nlp_extractor.nlp.return_value = mock_doc

        # Mock matcher to return empty (no pattern matches)
        nlp_extractor.matcher.return_value = []

        result = await nlp_extractor.extract_practice_info(sample_text)

        assert "practice_name" in result
        assert "location" in result
        assert "specialty" in result
        assert "emails" in result
        assert "phones" in result
        assert "websites" in result
        assert "confidence" in result

        # Should extract organization and location
        assert result["practice_name"] == "Smile Plus"
        assert result["location"] == "Moscow"

    @pytest.mark.asyncio
    async def test_extract_practice_info_partial(self, nlp_extractor):
        """Test extraction with partial information"""
        text = "Clinic in Moscow"

        mock_doc = MagicMock()
        mock_doc.ents = [
            MagicMock(label_="GPE", text="Moscow"),
        ]
        nlp_extractor.nlp.return_value = mock_doc
        nlp_extractor.matcher.return_value = []

        result = await nlp_extractor.extract_practice_info(text)

        assert result["practice_name"] is None
        assert result["location"] == "Moscow"
        # Specialty might be detected from "Clinic" word
        assert result["emails"] == []
        assert result["phones"] == []
        assert result["websites"] == []

        # Confidence should be lower with missing fields
        assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_extract_practice_info_specialty_detection(self, nlp_extractor):
        """Test specialty detection from text"""
        text = "We specialize in periodontics and gum treatment"

        mock_doc = MagicMock()
        mock_doc.ents = []
        nlp_extractor.nlp.return_value = mock_doc
        nlp_extractor.matcher.return_value = []

        result = await nlp_extractor.extract_practice_info(text)

        # Should detect "periodontics" from the specialty list
        assert result["specialty"] == "Periodontics"

    @pytest.mark.asyncio
    async def test_extract_analytics_access_google(self, nlp_extractor):
        """Test Google Analytics extraction"""
        text = """
        Google Analytics: UA-123456-1
        GA4: G-ABCDEFGHIJ
        Access: analytics@example.com
        """

        result = await nlp_extractor.extract_analytics_access(text)

        assert "google_analytics" in result
        assert len(result["google_analytics"]["property_ids"]) == 2
        assert "UA-123456-1" in result["google_analytics"]["property_ids"]
        assert "G-ABCDEFGHIJ" in result["google_analytics"]["property_ids"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_extract_analytics_access_yandex(self, nlp_extractor):
        """Test Yandex Metrica extraction"""
        text = """
        Yandex Metrica: 12345678
        Access: metrica@example.com
        """

        result = await nlp_extractor.extract_analytics_access(text)

        assert "yandex_metrica" in result
        assert len(result["yandex_metrica"]["counter_ids"]) == 1
        assert "12345678" in result["yandex_metrica"]["counter_ids"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_extract_analytics_access_empty(self, nlp_extractor):
        """Test analytics extraction with no data"""
        text = "No analytics information here"

        result = await nlp_extractor.extract_analytics_access(text)

        assert result["google_analytics"]["property_ids"] == []
        assert result["yandex_metrica"]["counter_ids"] == []
        assert result["confidence"] == 0

    @pytest.mark.asyncio
    async def test_extract_ad_accounts_google(self, nlp_extractor):
        """Test Google Ads extraction"""
        text = """
        Google Ads: 123-456-7890
        AdWords access: ads@example.com
        """

        result = await nlp_extractor.extract_ad_accounts(text)

        assert "google_ads" in result
        assert len(result["google_ads"]["account_ids"]) == 1
        assert "123-456-7890" in result["google_ads"]["account_ids"]
        assert len(result["google_ads"]["access_emails"]) > 0
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_extract_ad_accounts_yandex(self, nlp_extractor):
        """Test Yandex Direct extraction"""
        text = """
        Yandex Direct: 1234567890
        Access: direct@example.com
        """

        result = await nlp_extractor.extract_ad_accounts(text)

        assert "yandex_direct" in result
        assert len(result["yandex_direct"]["client_ids"]) == 1
        assert "1234567890" in result["yandex_direct"]["client_ids"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_extract_ad_accounts_empty(self, nlp_extractor):
        """Test ad accounts extraction with no data"""
        text = "No advertising information here"

        result = await nlp_extractor.extract_ad_accounts(text)

        assert result["google_ads"]["account_ids"] == []
        assert result["yandex_direct"]["client_ids"] == []
        assert result["confidence"] == 0

    @pytest.mark.asyncio
    async def test_extract_all_complete(self, nlp_extractor, sample_text):
        """Test extraction of all information"""
        # Mock practice info
        mock_doc = MagicMock()
        mock_doc.ents = [
            MagicMock(label_="ORG", text="Smile Plus"),
            MagicMock(label_="GPE", text="Moscow"),
        ]
        nlp_extractor.nlp.return_value = mock_doc
        nlp_extractor.matcher.return_value = []

        result = await nlp_extractor.extract_all(sample_text)

        assert "practice_info" in result
        assert "analytics_access" in result
        assert "ad_accounts" in result
        assert "overall_confidence" in result

        # Overall confidence is weighted average
        assert 0 <= result["overall_confidence"] <= 1

    @pytest.mark.asyncio
    async def test_extract_all_confidence_calculation(self, nlp_extractor):
        """Test overall confidence calculation"""
        text = "Minimal information"

        mock_doc = MagicMock()
        mock_doc.ents = []
        nlp_extractor.nlp.return_value = mock_doc
        nlp_extractor.matcher.return_value = []

        result = await nlp_extractor.extract_all(text)

        # Calculate expected confidence
        practice_conf = result["practice_info"]["confidence"]
        analytics_conf = result["analytics_access"]["confidence"]
        ads_conf = result["ad_accounts"]["confidence"]

        expected = practice_conf * 0.4 + analytics_conf * 0.3 + ads_conf * 0.3

        assert abs(result["overall_confidence"] - expected) < 0.01

