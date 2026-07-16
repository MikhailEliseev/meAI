# tests/unit/test_embeddings.py
import pytest
from meai.knowledge.embeddings import EmbeddingsModel


@pytest.mark.asyncio
async def test_embeddings_model_initialization():
    """Test EmbeddingsModel can be initialized"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")

    assert model.model_name == "BAAI/bge-m3"
    assert model.model is None  # Not loaded yet


@pytest.mark.asyncio
async def test_embeddings_model_load():
    """Test loading embeddings model"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")

    await model.load()

    assert model.model is not None
    assert model.dimension > 0


@pytest.mark.asyncio
async def test_embeddings_model_encode():
    """Test encoding text to embeddings"""
    model = EmbeddingsModel(model_name="BAAI/bge-m3")
    await model.load()

    text = "SEO best practices for 2026"
    embedding = await model.encode(text)

    assert len(embedding) == model.dimension
    assert all(isinstance(x, float) for x in embedding)
