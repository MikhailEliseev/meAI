#!/usr/bin/env python3
"""
Production Environment Validation Script

Validates all environment variables, API keys, database, and system requirements
before deployment.

Usage:
    python scripts/validate_environment.py
    python scripts/validate_environment.py --fix  # Auto-fix issues where possible
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValidationResult:
    """Validation result with status and details"""

    def __init__(self, name: str, passed: bool, message: str, severity: str = "error"):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity  # error, warning, info

    def __repr__(self):
        status = "✅" if self.passed else ("⚠️" if self.severity == "warning" else "❌")
        return f"{status} {self.name}: {self.message}"


class EnvironmentValidator:
    """Validates production environment configuration"""

    def __init__(self, env_file: str = ".env.production", fix: bool = False):
        self.env_file = Path(env_file)
        self.fix = fix
        self.results: List[ValidationResult] = []
        self.env_vars: Dict[str, str] = {}

    def load_env(self) -> bool:
        """Load environment variables from file"""
        if not self.env_file.exists():
            self.results.append(ValidationResult(
                "Environment File",
                False,
                f"File not found: {self.env_file}"
            ))
            return False

        try:
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.env_vars[key.strip()] = value.strip()

            self.results.append(ValidationResult(
                "Environment File",
                True,
                f"Loaded {len(self.env_vars)} variables from {self.env_file}"
            ))
            return True
        except Exception as e:
            self.results.append(ValidationResult(
                "Environment File",
                False,
                f"Failed to load: {e}"
            ))
            return False

    def validate_required_vars(self) -> None:
        """Validate required environment variables"""
        required = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "SECRET_KEY": None,  # Any non-empty value
            "DATABASE_URL": "sqlite+aiosqlite",
        }

        for var, expected in required.items():
            value = self.env_vars.get(var, "")

            if not value:
                self.results.append(ValidationResult(
                    f"Required Variable: {var}",
                    False,
                    f"Missing or empty"
                ))
            elif expected and expected not in value:
                self.results.append(ValidationResult(
                    f"Required Variable: {var}",
                    False,
                    f"Expected '{expected}' in value, got '{value}'"
                ))
            else:
                self.results.append(ValidationResult(
                    f"Required Variable: {var}",
                    True,
                    f"Valid: {value[:50]}..." if len(value) > 50 else f"Valid: {value}"
                ))

    def validate_api_keys(self) -> None:
        """Validate API keys configuration"""
        api_keys = {
            "GOOGLE_ANALYTICS_KEY": ("Google Analytics", True),
            "YANDEX_METRICA_CLIENT_ID": ("Yandex Metrica Client ID", True),
            "YANDEX_METRICA_CLIENT_SECRET": ("Yandex Metrica Secret", True),
            "YANDEX_DIRECT_TOKEN": ("Yandex Direct", True),
            "SEMRUSH_API_KEY": ("SEMrush", False),  # Optional
            "AHREFS_API_KEY": ("Ahrefs", False),  # Optional
        }

        for var, (name, required) in api_keys.items():
            value = self.env_vars.get(var, "")

            if not value:
                severity = "error" if required else "warning"
                self.results.append(ValidationResult(
                    f"API Key: {name}",
                    not required,
                    "Missing or empty" + (" (optional)" if not required else ""),
                    severity
                ))
            else:
                # Check if it's a file path (for service accounts)
                if value.startswith('/') or value.startswith('./'):
                    if Path(value).exists():
                        self.results.append(ValidationResult(
                            f"API Key: {name}",
                            True,
                            f"Service account file exists: {value}"
                        ))
                    else:
                        self.results.append(ValidationResult(
                            f"API Key: {name}",
                            False,
                            f"Service account file not found: {value}"
                        ))
                else:
                    # Regular API key
                    masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                    self.results.append(ValidationResult(
                        f"API Key: {name}",
                        True,
                        f"Configured: {masked}"
                    ))

    async def validate_database(self) -> None:
        """Validate database connection and schema"""
        db_url = self.env_vars.get("DATABASE_URL", "")

        if not db_url:
            self.results.append(ValidationResult(
                "Database",
                False,
                "DATABASE_URL not configured"
            ))
            return

        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            engine = create_async_engine(db_url, echo=False)

            async with engine.begin() as conn:
                # Check tables exist
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                tables = [row[0] for row in result]

                required_tables = ["tasks", "metrics", "api_costs"]
                missing = [t for t in required_tables if t not in tables]

                if missing:
                    self.results.append(ValidationResult(
                        "Database Schema",
                        False,
                        f"Missing tables: {', '.join(missing)}"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Database Schema",
                        True,
                        f"All required tables exist: {', '.join(required_tables)}"
                    ))

            await engine.dispose()

            self.results.append(ValidationResult(
                "Database Connection",
                True,
                f"Connected successfully: {db_url.split('///')[1] if '///' in db_url else db_url}"
            ))

        except Exception as e:
            self.results.append(ValidationResult(
                "Database",
                False,
                f"Connection failed: {e}"
            ))

    def validate_limits(self) -> None:
        """Validate API limits and budget configuration"""
        limits = {
            "MAX_COST_USD": (float, 0.1, 100.0),
            "MIN_KEYWORDS": (int, 10, 1000),
            "MIN_VOLUME": (int, 0, 10000),
            "RATE_LIMIT_CAPACITY": (int, 1, 100),
            "RATE_LIMIT_REFILL": (float, 0.1, 10.0),
        }

        for var, (type_func, min_val, max_val) in limits.items():
            value = self.env_vars.get(var, "")

            if not value:
                self.results.append(ValidationResult(
                    f"Limit: {var}",
                    False,
                    "Missing or empty",
                    "warning"
                ))
                continue

            try:
                num_value = type_func(value)
                if min_val <= num_value <= max_val:
                    self.results.append(ValidationResult(
                        f"Limit: {var}",
                        True,
                        f"Valid: {num_value}"
                    ))
                else:
                    self.results.append(ValidationResult(
                        f"Limit: {var}",
                        False,
                        f"Out of range [{min_val}, {max_val}]: {num_value}",
                        "warning"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    f"Limit: {var}",
                    False,
                    f"Invalid {type_func.__name__}: {value}",
                    "warning"
                ))

    def validate_security(self) -> None:
        """Validate security configuration"""
        # Check SECRET_KEY strength
        secret_key = self.env_vars.get("SECRET_KEY", "")
        if len(secret_key) < 32:
            self.results.append(ValidationResult(
                "Security: SECRET_KEY",
                False,
                f"Too short ({len(secret_key)} chars, minimum 32)"
            ))
        else:
            self.results.append(ValidationResult(
                "Security: SECRET_KEY",
                True,
                f"Strong ({len(secret_key)} chars)"
            ))

        # Check DEBUG is false
        debug = self.env_vars.get("DEBUG", "").lower()
        if debug == "false":
            self.results.append(ValidationResult(
                "Security: DEBUG",
                True,
                "Disabled (production mode)"
            ))
        else:
            self.results.append(ValidationResult(
                "Security: DEBUG",
                False,
                f"Enabled in production: {debug}"
            ))

        # Check file permissions
        if self.env_file.exists():
            stat = self.env_file.stat()
            mode = oct(stat.st_mode)[-3:]
            if mode == "600":
                self.results.append(ValidationResult(
                    "Security: File Permissions",
                    True,
                    f"Restrictive: {mode}"
                ))
            else:
                self.results.append(ValidationResult(
                    "Security: File Permissions",
                    False,
                    f"Too permissive: {mode} (should be 600)",
                    "warning"
                ))

    async def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print(f"🔍 Validating production environment: {self.env_file}\n")

        if not self.load_env():
            return False

        self.validate_required_vars()
        self.validate_api_keys()
        await self.validate_database()
        self.validate_limits()
        self.validate_security()

        return True

    def print_results(self) -> Tuple[int, int, int]:
        """Print validation results and return counts"""
        errors = []
        warnings = []
        passed = []

        for result in self.results:
            if not result.passed:
                if result.severity == "warning":
                    warnings.append(result)
                else:
                    errors.append(result)
            else:
                passed.append(result)

        print("\n" + "="*70)
        print("VALIDATION RESULTS")
        print("="*70 + "\n")

        if passed:
            print("✅ PASSED:")
            for r in passed:
                print(f"   {r}")
            print()

        if warnings:
            print("⚠️  WARNINGS:")
            for r in warnings:
                print(f"   {r}")
            print()

        if errors:
            print("❌ ERRORS:")
            for r in errors:
                print(f"   {r}")
            print()

        print("="*70)
        print(f"Summary: {len(passed)} passed, {len(warnings)} warnings, {len(errors)} errors")
        print("="*70 + "\n")

        return len(passed), len(warnings), len(errors)


async def main():
    """Main validation entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate production environment")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("--env", default=".env.production", help="Environment file path")
    args = parser.parse_args()

    validator = EnvironmentValidator(env_file=args.env, fix=args.fix)

    success = await validator.run_all_validations()

    if not success:
        print("❌ Validation failed to complete")
        sys.exit(1)

    passed, warnings, errors = validator.print_results()

    if errors > 0:
        print("❌ Environment validation FAILED")
        print(f"   Fix {errors} error(s) before deploying to production")
        sys.exit(1)
    elif warnings > 0:
        print("⚠️  Environment validation PASSED with warnings")
        print(f"   Consider fixing {warnings} warning(s) for optimal configuration")
        sys.exit(0)
    else:
        print("✅ Environment validation PASSED")
        print("   System is ready for production deployment")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
