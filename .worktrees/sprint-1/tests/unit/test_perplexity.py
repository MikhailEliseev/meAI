# tests/unit/test_perplexity.py
import pytest
from unittest.mock import AsyncMock, patch
from meai.integrations.perplexity import PerplexityClient


@pytest.mark.asyncio
async def test_perplexity_client_initialization():
    """Test PerplexityClient can be initialized"""
    client = PerplexityClient(api_key="test-key")

    assert client.api_key == "test-key"
    assert client.base_url == "https://api.perplexity.ai"


@pytest.mark.asyncio
async def test_perplexity_research():
    """Test research method returns findings with sources"""
    client = PerplexityClient(api_key="test-key")

    # Mock API response
    mock_response = {
        "choices": [{
            "message": {
                "content": "SEO best practices include keyword research, quality content, and technical optimization.",
                "citations": [
                    "https://moz.com/beginners-guide-to-seo",
                    "https://developers.google.com/search/docs"
                ]
            }
        }]
    }

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await client.research("What are SEO best practices?")

        assert "content" in result
        assert "sources" in result
        assert len(result["sources"]) == 2
        assert "moz.com" in result["sources"][0]


@pytest.mark.asyncio
async def test_perplexity_error_handling():
    """Test error handling for API failures"""
    client = PerplexityClient(api_key="test-key")

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await client.research("test query")


@pytest.mark.asyncio
async def test_perplexity_empty_response():
    """Test handling of empty API response"""
    client = PerplexityClient(api_key="test-key")

    mock_response = {
        "choices": [{
            "message": {
                "content": "",
                "citations": []
            }
        }]
    }

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await client.research("test query")

        assert result["content"] == ""
        assert result["sources"] == []
