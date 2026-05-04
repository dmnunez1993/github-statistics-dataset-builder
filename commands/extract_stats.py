#!/usr/bin/env python3
"""Runnable entry point for the GitHub statistics extractor.

Usage (without installing the package):
    uv run commands/extract_stats.py <repos_dir> --output <file.csv> [--email addr@example.com ...]

Usage (after `uv sync` / `pip install -e .`):
    github-stats <repos_dir> --output <file.csv> [--email addr@example.com ...]
    github-stats emails <repos_dir>
"""
from github_stats.cli import run

if __name__ == "__main__":
    run()
