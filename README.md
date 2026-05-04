# GitHub Statistics Dataset Builder

Extract commit-level statistics from a directory of local git repositories and write a [Polars](https://pola.rs/)-compatible CSV dataset.

## Features

- Scans every git repository inside a given directory
- Extracts per-commit metrics: lines added/removed, files changed, date, author, message
- Flags merge commits so merge request activity can be counted from the dataset
- Detects programming languages touched in each commit from file extensions (~80 languages), grouping unknown files as `Other`
- Adds per-language changed-file and line-count summaries for each commit
- Lists all author emails found across local repositories
- Privacy filter: restrict output to a specific set of author emails
- Outputs a single CSV file ready for use with Polars (or any other data tool)

## Output columns

| Column | Type | Description |
|---|---|---|
| `commit_hash` | `String` | Full Git commit SHA |
| `is_merge_commit` | `Int64` | `1` when the commit has more than one parent, otherwise `0` |
| `parent_count` | `Int64` | Number of parent commits |
| `author_name` | `String` | Git author display name |
| `author_email` | `String` | Git author email |
| `commit_date` | `String` | ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SS+00:00`) |
| `lines_added` | `Int64` | Lines inserted in the commit |
| `lines_removed` | `Int64` | Lines deleted in the commit |
| `files_changed` | `Int64` | Number of files modified |
| `languages` | `String` | Pipe-separated languages detected (e.g. `Python\|TypeScript\|Other`) |
| `language_file_counts` | `String` | JSON object of changed-file counts by language (e.g. `{"Python":2}`) |
| `language_lines_added` | `String` | JSON object of inserted-line counts by language |
| `language_lines_removed` | `String` | JSON object of deleted-line counts by language |

## Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or any PEP 517 build tool

## Installation

```bash
git clone https://github.com/your-org/github-statistics-dataset-builder.git
cd github-statistics-dataset-builder
uv sync
```

This creates a `.venv` and installs all dependencies including `gitpython`, `polars`, and `typer`.

## Usage

### As a CLI command (after `uv sync`)

```bash
uv run github-stats REPOS_DIR --output OUTPUT.csv [--email EMAIL ...]
```

List all author emails found in repositories under a folder:

```bash
uv run github-stats emails REPOS_DIR
```

### As a standalone script

```bash
uv run commands/extract_stats.py REPOS_DIR --output OUTPUT.csv [--email EMAIL ...]
uv run commands/extract_stats.py emails REPOS_DIR
```

### Arguments and options

| Argument / Option | Required | Description |
|---|---|---|
| `REPOS_DIR` | yes | Root directory to search recursively for git repositories |
| `--output / -o` | yes | Destination CSV file path |
| `--email / -e` | no | Author email to include. Repeat for multiple authors. Omit to include all. |

### Examples

Analyse all commits from two authors across all repos in `~/projects/`:

```bash
uv run github-stats ~/projects/ \
  --output commits.csv \
  --email alice@example.com \
  --email bob@example.com
```

Analyse all commits (no privacy filter):

```bash
uv run github-stats ~/projects/ --output commits.csv
```

Show every author email available for filtering:

```bash
uv run github-stats emails ~/projects/
```

Load the result with Polars:

```python
import polars as pl

df = pl.read_csv("commits.csv", try_parse_dates=True)
print(df.head())
```

## Project structure

```
pyproject.toml
commands/
  extract_stats.py       # Standalone runnable entry point
src/github_stats/
  __init__.py
  cli.py                 # Typer CLI (registered as `github-stats`)
  extractor.py           # GitPython-based commit extraction logic
  languages.py           # File extension → language name mapping
```

## Language detection

Languages are inferred from the file extensions of every file touched in a commit. ~80 languages and formats are supported out of the box (Python, TypeScript, Go, Rust, Java, SQL, Dockerfile, and more). The `languages` column contains a pipe-separated (`|`) list of unique languages sorted alphabetically, making it straightforward to filter or explode in Polars:

```python
df.with_columns(
    pl.col("languages").str.split("|").alias("language_list")
).explode("language_list")
```

> **Note:** Language detection is extension-based and does not filter vendored or auto-generated files. For most commit-level analysis this is sufficient; for linguist-level accuracy, consider integrating [PyGments](https://pygments.org/) or [go-enry](https://github.com/go-enry/go-enry) as a post-processing step.
