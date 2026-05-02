"""Setup script for Magister agents - initialize vaults and databases"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.magisters.ads_magister import AdsMagister
from meai.agents.magisters.smm_magister import SMMMagister
from meai.agents.magisters.analytics_magister import AnalyticsMagister
from meai.agents.magisters.intelligence_magister import IntelligenceMagister
from meai.events.event_bus import EventBus


def print_header(title: str):
    """Print section header"""
    print()
    print("=" * 60)
    print(f"{title}")
    print("=" * 60)


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"📋 {message}")


async def setup_magister(magister_class, name: str, event_bus: EventBus):
    """Setup a single Magister

    Args:
        magister_class: Magister class to instantiate
        name: Magister name for display
        event_bus: Event bus instance

    Returns:
        True if successful, False otherwise
    """
    try:
        print_info(f"Setting up {name}...")

        # Initialize Magister
        magister = magister_class(event_bus=event_bus)
        await magister.initialize()

        # Verify vault structure
        vault_path = magister.vault_path
        assert (vault_path / "knowledge").exists()
        assert (vault_path / "tasks").exists()
        assert (vault_path / "decisions").exists()
        assert (vault_path / "INDEX.md").exists()

        print_success(f"{name} initialized")
        print_info(f"   Vault: {vault_path}")
        print_info(f"   Domain: {magister.domain}")
        print_info(f"   Capabilities: {len(magister.get_capabilities())}")

        await magister.shutdown()
        return True

    except Exception as e:
        print_error(f"{name} failed: {e}")
        return False


async def main():
    """Setup all Magisters"""
    print()
    print("🔧 Setting up Magister Agents")
    print()

    # Initialize Event Bus
    event_bus = EventBus()
    print_success("Event Bus initialized")

    # Magisters to setup
    magisters = [
        (SEOMagister, "SEO Magister"),
        (ContentMagister, "Content Magister"),
        (AdsMagister, "Ads Magister"),
        (SMMMagister, "SMM Magister"),
        (AnalyticsMagister, "Analytics Magister"),
        (IntelligenceMagister, "Intelligence Magister"),
    ]

    print()
    print_info(f"Setting up {len(magisters)} Magisters...")
    print()

    # Setup each Magister
    success_count = 0
    failed_count = 0

    for magister_class, name in magisters:
        success = await setup_magister(magister_class, name, event_bus)
        if success:
            success_count += 1
        else:
            failed_count += 1
        print()

    # Summary
    print_header("Setup Complete")
    print()
    print(f"✅ Successfully set up: {success_count} Magisters")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} Magisters")
    print()

    # Verify Obsidian vault structure
    print_info("Obsidian vault structure:")
    obsidian_path = Path("./obsidian")
    if obsidian_path.exists():
        for magister_dir in obsidian_path.iterdir():
            if magister_dir.is_dir():
                print(f"   - {magister_dir.name}/")
                for subdir in ["knowledge", "tasks", "decisions"]:
                    subdir_path = magister_dir / subdir
                    if subdir_path.exists():
                        file_count = len(list(subdir_path.glob("*.md")))
                        print(f"     - {subdir}/ ({file_count} files)")
    else:
        print_info("   Obsidian vault will be created on first use")

    print()
    print("=" * 60)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
