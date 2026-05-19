from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="elsevier-mcp-server",
    version="1.0.0",
    author="Yasufumi Nakata",
    description="MCP Server for Elsevier Academic APIs (Scopus, SciVal, Abstract Retrieval)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yasufumi-nakata/Elsevier_MCP",
    packages=find_packages(),
    py_modules=["elsevier_mcp_complete"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="elsevier scopus scival academic research mcp cursor ai",
    project_urls={
        "Bug Reports": "https://github.com/yasufumi-nakata/Elsevier_MCP/issues",
        "Source": "https://github.com/yasufumi-nakata/Elsevier_MCP",
        "Documentation": "https://github.com/yasufumi-nakata/Elsevier_MCP#readme",
        "Elsevier Developer": "https://dev.elsevier.com/",
    },
    entry_points={
        "console_scripts": [
            "elsevier-mcp-server=elsevier_mcp_complete:main",
        ],
    },
)
