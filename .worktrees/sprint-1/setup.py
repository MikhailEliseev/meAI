"""Setup configuration for meAI"""

from setuptools import setup, find_packages

setup(
    name="meai",
    version="0.1.0",
    description="meAI - CEO-Architect for AIM Agency",
    author="Mikhail Eliseev",
    author_email="me@mikhaileliseev.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "pydantic>=2.0.0",
        "anthropic>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
    },
)
