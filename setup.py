"""Setup configuration for Enterprise RAG System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enterprise-rag-system",
    version="1.0.0",
    author="jeonchulho",
    description="Enterprise-grade multimodal RAG system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jeonchulho/rag-ai-project",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "langchain>=0.1.0",
        "ollama>=0.1.6",
        "pymilvus>=2.3.3",
        "redis>=5.0.1",
        "celery>=5.3.4",
        "sqlalchemy>=2.0.23",
    ],
)
