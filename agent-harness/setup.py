"""Setup for cli-anything-nodepad — CLI harness for the nodepad spatial research tool."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-nodepad",
    version="0.1.0",
    description="CLI harness for nodepad — spatial AI-augmented research tool",
    author="cli-anything",
    url="https://nodepad.space",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    python_requires=">=3.11",
    install_requires=[
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-nodepad=cli_anything.nodepad.nodepad_cli:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
