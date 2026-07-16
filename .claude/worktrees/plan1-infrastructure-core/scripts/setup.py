#!/usr/bin/env python3
"""Setup script for meAI University Infrastructure

Initializes:
- Database tables
- Qdrant collections
- Embeddings model
- Directory structure
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.storage.database import Database
from meai.knowledge.qdrant_client import QdrantClient
from meai.knowledge.embeddings import EmbeddingsModel
from meai.knowledge.fallback_storage import FallbackStorage
from meai.events.event_bus import EventBus

from qdrant_client.models import Distance


async def setup_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")

    directories = [
        "data",
        "obsidian",
        "obsidian/researcher",
        "obsidian/teacher",
        "obsidian/operator",
        "logs",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")


async def setup_database():
    """Initialize database tables"""
    print("\n💾 Initializing database...")

    db = Database("sqlite+aiosqlite:///./data/meai.db")
    await db.connect()

    # Event Bus tables
    event_bus = EventBus("sqlite+aiosqlite:///./data/meai.db")
    await event_bus.initialize()

    print("  ✓ Database tables created")

    await event_bus.close()
    await db.disconnect()


async def setup_fallback_storage():
    """Initialize fallback storage"""
    print("\n💿 Initializing fallback storage...")

    fallback = FallbackStorage("sqlite+aiosqlite:///./data/fallback.db")
    await fallback.initialize()

    print("  ✓ Fallback storage ready")

    await fallback.shutdown()


async def setup_qdrant(skip_qdrant: bool = False):
    """Initialize Qdrant collections"""
    if skip_qdrant:
        print("\n⏭️  Skipping Qdrant setup (use --skip-qdrant flag)")
        return

    print("\n🔍 Initializing Qdrant collections...")

    try:
        qdrant = QdrantClient(url="http://localhost:6333")
        await qdrant.connect()

        collections = [
            "seo_knowledge",
            "content_knowledge",
            "ads_knowledge",
            "general_knowledge",
        ]

        for collection in collections:
            if not await qdrant.collection_exists(collection):
                await qdrant.create_collection(
                    collection_name=collection,
                    vector_size=1024,  # bge-m3 dimension
                    distance=Distance.COSINE,
                )
                print(f"  ✓ Created collection: {collection}")
            else:
                print(f"  ⚠️  Collection already exists: {collection}")

        await qdrant.disconnect()
        print("  ✓ Qdrant collections ready")

    except Exception as e:
        print(f"  ⚠️  Qdrant not available: {e}")
        print("  ℹ️  System will use SQLite fallback storage")


async def setup_embeddings(skip_download: bool = False):
    """Load embeddings model"""
    if skip_download:
        print("\n⏭️  Skipping embeddings download (use --skip-download flag)")
        return

    print("\n🤖 Loading embeddings model (bge-m3)...")
    print("  ⏳ This may take a few minutes on first run (~2GB download)...")

    try:
        embeddings = EmbeddingsModel(model_name="BAAI/bge-m3")
        await embeddings.load()

        # Test encoding
        test_vector = await embeddings.encode("test")
        print(f"  ✓ Model loaded (dimension: {len(test_vector)})")

    except Exception as e:
        print(f"  ⚠️  Failed to load embeddings: {e}")
        print("  ℹ️  You can download manually later")


async def main():
    """Run setup"""
    import argparse

    parser = argparse.ArgumentParser(description="Setup meAI University Infrastructure")
    parser.add_argument("--skip-qdrant", action="store_true", help="Skip Qdrant setup")
    parser.add_argument("--skip-download", action="store_true", help="Skip embeddings download")
    args = parser.parse_args()

    print("🚀 meAI University Infrastructure Setup")
    print("=" * 50)

    try:
        await setup_directories()
        await setup_database()
        await setup_fallback_storage()
        await setup_qdrant(skip_qdrant=args.skip_qdrant)
        await setup_embeddings(skip_download=args.skip_download)

        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("  1. Start Qdrant (if not running): docker run -p 6333:6333 qdrant/qdrant")
        print("  2. Run tests: pytest tests/")
        print("  3. Start using the system!")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
