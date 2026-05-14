#!/usr/bin/env python3
"""Environment configuration validation script.

Validates that all required environment variables are properly configured
before running the AIM agency system.

Usage:
    python scripts/validate_env.py [--check-connectivity]

Options:
    --check-connectivity    Test API connectivity (requires valid credentials)
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


class EnvValidator:
    """Environment configuration validator."""

    def __init__(self, check_connectivity: bool = False):
        """Initialize validator.

        Args:
            check_connectivity: Whether to test API connectivity
        """
        self.check_connectivity = check_connectivity
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def validate_required_var(
        self,
        var_name: str,
        description: str,
        validator: callable | None = None,
    ) -> str | None:
        """Validate required environment variable.

        Args:
            var_name: Environment variable name
            description: Human-readable description
            validator: Optional validation function

        Returns:
            Variable value if valid, None otherwise
        """
        value = os.getenv(var_name)

        if not value:
            self.errors.append(f"{var_name} is not set ({description})")
            print_error(f"{var_name}: Not set")
            return None

        if validator:
            try:
                validator(value)
            except ValueError as e:
                self.errors.append(f"{var_name}: {e}")
                print_error(f"{var_name}: {e}")
                return None

        print_success(f"{var_name}: Set")
        return value

    def validate_optional_var(
        self,
        var_name: str,
        description: str,
        validator: callable | None = None,
    ) -> str | None:
        """Validate optional environment variable.

        Args:
            var_name: Environment variable name
            description: Human-readable description
            validator: Optional validation function

        Returns:
            Variable value if valid, None otherwise
        """
        value = os.getenv(var_name)

        if not value:
            self.warnings.append(f"{var_name} is not set ({description})")
            print_warning(f"{var_name}: Not set (optional)")
            return None

        if validator:
            try:
                validator(value)
            except ValueError as e:
                self.warnings.append(f"{var_name}: {e}")
                print_warning(f"{var_name}: {e}")
                return None

        print_success(f"{var_name}: Set")
        return value

    def validate_file_path(self, path: str) -> None:
        """Validate file path exists.

        Args:
            path: File path to validate

        Raises:
            ValueError: If file does not exist
        """
        if not Path(path).exists():
            raise ValueError(f"File not found: {path}")

    def validate_positive_int(self, value: str) -> None:
        """Validate positive integer.

        Args:
            value: Value to validate

        Raises:
            ValueError: If value is not a positive integer
        """
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            raise ValueError("Must be a positive integer")

    def validate_positive_float(self, value: str) -> None:
        """Validate positive float.

        Args:
            value: Value to validate

        Raises:
            ValueError: If value is not a positive float
        """
        try:
            float_value = float(value)
            if float_value <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            raise ValueError("Must be a positive number")

    def validate_boolean(self, value: str) -> None:
        """Validate boolean value.

        Args:
            value: Value to validate

        Raises:
            ValueError: If value is not a valid boolean
        """
        if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
            raise ValueError("Must be true/false, yes/no, or 1/0")

    def validate_url(self, value: str) -> None:
        """Validate URL format.

        Args:
            value: URL to validate

        Raises:
            ValueError: If URL format is invalid
        """
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(value):
            raise ValueError("Invalid URL format")

    async def check_ga4_connectivity(self, property_id: str, credentials_file: str) -> bool:
        """Test GA4 API connectivity.

        Args:
            property_id: GA4 property ID
            credentials_file: Path to service account JSON

        Returns:
            True if connection successful, False otherwise
        """
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                credentials_file
            )
            client = BetaAnalyticsDataClient(credentials=credentials)

            # Simple test request
            from google.analytics.data_v1beta.types import (
                DateRange,
                Dimension,
                Metric,
                RunReportRequest,
            )

            request = RunReportRequest(
                property=f"properties/{property_id}",
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="sessions")],
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            )

            response = client.run_report(request)
            print_success("GA4 API: Connection successful")
            return True

        except Exception as e:
            print_error(f"GA4 API: Connection failed - {e}")
            return False

    async def check_semrush_connectivity(self, api_key: str) -> bool:
        """Test SEMrush API connectivity.

        Args:
            api_key: SEMrush API key

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.semrush.com/",
                    params={
                        "type": "phrase_all",
                        "key": api_key,
                        "phrase": "test",
                        "database": "us",
                        "export_columns": "Ph,Nq",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    print_success("SEMrush API: Connection successful")
                    return True
                else:
                    print_error(f"SEMrush API: HTTP {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"SEMrush API: Connection failed - {e}")
            return False

    async def check_ahrefs_connectivity(self, api_key: str) -> bool:
        """Test Ahrefs API connectivity.

        Args:
            api_key: Ahrefs API key

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.ahrefs.com/v3/site-explorer/overview",
                    params={
                        "target": "ahrefs.com",
                        "mode": "domain",
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    print_success("Ahrefs API: Connection successful")
                    return True
                else:
                    print_error(f"Ahrefs API: HTTP {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"Ahrefs API: Connection failed - {e}")
            return False

    async def validate_all(self) -> bool:
        """Validate all environment variables.

        Returns:
            True if all required variables are valid, False otherwise
        """
        print_header("AIM Agency - Environment Configuration Validation")

        # GA4 Configuration
        print_header("Google Analytics 4 (GA4)")
        ga4_property_id = self.validate_required_var(
            "GA4_PROPERTY_ID",
            "GA4 property ID",
            self.validate_positive_int,
        )
        ga4_service_account_file = self.validate_optional_var(
            "GA4_SERVICE_ACCOUNT_FILE",
            "Path to service account JSON",
            self.validate_file_path,
        )
        ga4_service_account_json = self.validate_optional_var(
            "GA4_SERVICE_ACCOUNT_JSON",
            "Service account JSON (for cloud deployments)",
        )

        if not ga4_service_account_file and not ga4_service_account_json:
            self.errors.append(
                "Either GA4_SERVICE_ACCOUNT_FILE or GA4_SERVICE_ACCOUNT_JSON must be set"
            )
            print_error("GA4 credentials: Neither file nor JSON provided")

        # Yandex Metrica Configuration
        print_header("Yandex Metrica")
        yandex_counter_id = self.validate_optional_var(
            "YANDEX_METRICA_COUNTER_ID",
            "Yandex Metrica counter ID",
            self.validate_positive_int,
        )
        yandex_access_token = self.validate_optional_var(
            "YANDEX_METRICA_ACCESS_TOKEN",
            "Yandex OAuth access token",
        )

        # SEMrush Configuration
        print_header("SEMrush API")
        semrush_api_key = self.validate_required_var(
            "SEMRUSH_API_KEY",
            "SEMrush API key",
        )

        # Ahrefs Configuration
        print_header("Ahrefs API (Optional)")
        ahrefs_api_key = self.validate_optional_var(
            "AHREFS_API_KEY",
            "Ahrefs API key (fallback)",
        )

        # HH API Configuration
        print_header("HH API")
        hh_access_token = self.validate_optional_var(
            "HH_ACCESS_TOKEN",
            "HH API access token",
        )

        # PageSpeed Insights Configuration
        print_header("PageSpeed Insights API")
        pagespeed_api_key = self.validate_optional_var(
            "PAGESPEED_API_KEY",
            "PageSpeed Insights API key",
        )

        # Rate Limiting Configuration
        print_header("Rate Limiting")
        self.validate_optional_var(
            "GA4_RATE_LIMIT_CAPACITY",
            "GA4 rate limit capacity",
            self.validate_positive_int,
        )
        self.validate_optional_var(
            "GA4_RATE_LIMIT_REFILL",
            "GA4 rate limit refill",
            self.validate_positive_float,
        )

        # Cache Configuration
        print_header("Cache")
        self.validate_optional_var(
            "CACHE_TTL",
            "Cache TTL in seconds",
            self.validate_positive_int,
        )
        cache_backend = self.validate_optional_var(
            "CACHE_BACKEND",
            "Cache backend (memory, redis)",
        )
        if cache_backend and cache_backend not in ("memory", "redis"):
            self.warnings.append("CACHE_BACKEND: Must be 'memory' or 'redis'")
            print_warning("CACHE_BACKEND: Invalid value (must be memory or redis)")

        # Budget Configuration
        print_header("Budget and Cost Control")
        self.validate_optional_var(
            "MAX_COST_USD",
            "Maximum cost per API request",
            self.validate_positive_float,
        )
        self.validate_optional_var(
            "MIN_KEYWORDS",
            "Minimum keywords to return",
            self.validate_positive_int,
        )
        self.validate_optional_var(
            "MIN_VOLUME",
            "Minimum search volume filter",
            self.validate_positive_int,
        )

        # Database Configuration
        print_header("Database")
        database_url = self.validate_required_var(
            "DATABASE_URL",
            "Database connection URL",
        )
        if database_url and not database_url.startswith(("sqlite", "postgresql")):
            self.warnings.append("DATABASE_URL: Only SQLite and PostgreSQL are supported")
            print_warning("DATABASE_URL: Unsupported database type")

        # Obsidian Configuration
        print_header("Obsidian Vault")
        obsidian_base_path = self.validate_required_var(
            "OBSIDIAN_BASE_PATH",
            "Base path for Obsidian vaults",
        )
        if obsidian_base_path:
            obsidian_path = Path(obsidian_base_path)
            if not obsidian_path.exists():
                self.warnings.append(f"OBSIDIAN_BASE_PATH: Directory does not exist: {obsidian_base_path}")
                print_warning(f"OBSIDIAN_BASE_PATH: Directory does not exist (will be created)")

        # Feature Flags
        print_header("Feature Flags")
        self.validate_optional_var(
            "ENABLE_GA4",
            "Enable GA4 integration",
            self.validate_boolean,
        )
        self.validate_optional_var(
            "ENABLE_YANDEX_METRICA",
            "Enable Yandex Metrica integration",
            self.validate_boolean,
        )
        self.validate_optional_var(
            "ENABLE_SEMRUSH",
            "Enable SEMrush integration",
            self.validate_boolean,
        )
        self.validate_optional_var(
            "ENABLE_AHREFS",
            "Enable Ahrefs integration",
            self.validate_boolean,
        )

        # Environment Configuration
        print_header("Environment")
        environment = self.validate_optional_var(
            "ENVIRONMENT",
            "Environment (development, staging, production)",
        )
        if environment and environment not in ("development", "staging", "production"):
            self.warnings.append("ENVIRONMENT: Must be development, staging, or production")
            print_warning("ENVIRONMENT: Invalid value")

        # Security Configuration
        print_header("Security")
        secret_key = self.validate_required_var(
            "SECRET_KEY",
            "Secret key for session encryption",
        )
        if secret_key and len(secret_key) < 32:
            self.warnings.append("SECRET_KEY: Should be at least 32 characters")
            print_warning("SECRET_KEY: Too short (should be at least 32 characters)")

        # API Connectivity Tests
        if self.check_connectivity:
            print_header("API Connectivity Tests")

            if ga4_property_id and ga4_service_account_file:
                await self.check_ga4_connectivity(ga4_property_id, ga4_service_account_file)

            if semrush_api_key:
                await self.check_semrush_connectivity(semrush_api_key)

            if ahrefs_api_key:
                await self.check_ahrefs_connectivity(ahrefs_api_key)

        # Summary
        print_header("Validation Summary")

        if self.errors:
            print_error(f"Found {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print_warning(f"Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if not self.errors and not self.warnings:
            print_success("All configuration checks passed!")
            print()

        if self.errors:
            print_error("Configuration validation failed. Please fix the errors above.")
            print_info("See .env.example for configuration examples and documentation.")
            return False
        else:
            print_success("Configuration validation passed!")
            if self.warnings:
                print_warning("Some optional features are not configured.")
            return True


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    check_connectivity = "--check-connectivity" in sys.argv

    # Load .env file
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print_error(f".env file not found: {env_file}")
        print_info("Copy .env.example to .env and configure your API keys.")
        return 1

    load_dotenv(env_file)

    # Validate configuration
    validator = EnvValidator(check_connectivity=check_connectivity)
    success = await validator.validate_all()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
