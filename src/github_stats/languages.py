from __future__ import annotations

from collections import Counter
from pathlib import Path

UNKNOWN_LANGUAGE = "Other"

# Maps lowercase file extensions to canonical language names.
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".jsx": "JSX",
    ".tsx": "TSX",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".cs": "C#",
    ".fs": "F#",
    ".fsx": "F#",
    ".vb": "Visual Basic",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C/C++ Header",
    ".hxx": "C/C++ Header",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".rb": "Ruby",
    ".php": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".lua": "Lua",
    ".r": "R",
    ".jl": "Julia",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",
    ".nim": "Nim",
    ".cr": "Crystal",
    ".zig": "Zig",
    ".dart": "Dart",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".styl": "Stylus",
    ".sql": "SQL",
    ".tf": "HCL",
    ".hcl": "HCL",
    ".json": "JSON",
    ".jsonc": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".mdx": "MDX",
    ".rst": "reStructuredText",
    ".tex": "LaTeX",
    ".ipynb": "Jupyter Notebook",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".thrift": "Thrift",
}

# Filenames (basename, case-insensitive) that map to a language regardless of extension.
FILENAME_TO_LANGUAGE: dict[str, str] = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
    "gemfile": "Ruby",
    "rakefile": "Ruby",
    "cmakelists.txt": "CMake",
}


def get_language_for_file(filename: str) -> str:
    """Return the language for a given file path."""
    basename = Path(filename).name.lower()
    if basename in FILENAME_TO_LANGUAGE:
        return FILENAME_TO_LANGUAGE[basename]
    ext = Path(filename).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, UNKNOWN_LANGUAGE)


def get_languages_from_files(filenames: list[str]) -> list[str]:
    """Return a sorted, deduplicated list of languages from a list of file paths."""
    languages: set[str] = set()
    for filename in filenames:
        languages.add(get_language_for_file(filename))
    return sorted(languages)


def get_language_counts_from_files(filenames: list[str]) -> dict[str, int]:
    """Return changed-file counts grouped by detected language."""
    counts: Counter[str] = Counter()
    for filename in filenames:
        counts[get_language_for_file(filename)] += 1
    return dict(sorted(counts.items()))
