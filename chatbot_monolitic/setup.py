"""
Setup para instalar chatbot_core como paquete
"""
from setuptools import setup, find_packages

setup(
    name="chatbot-core",
    version="2.1",
    description="Librería modular para ChatBot con NLP, Storage, LLM Fallback",
    author="ChatBot Team",
    author_email="team@chatbot.dev",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "sentence-transformers>=2.0.0",
    ],
    extras_require={
        "api": ["fastapi>=0.104.0", "uvicorn[standard]>=0.24.0"],
        "llm": ["openai>=1.0.0", "requests>=2.31.0"],
        "dev": ["pytest>=7.0", "black>=22.0", "flake8>=4.0"],
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
