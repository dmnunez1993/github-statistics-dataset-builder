from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from .extractor import collect_all_emails, extract_all_repos

_OUTPUT_COLS = [
    "commit_hash",
    "is_merge_commit",
    "parent_count",
    "commit_date",
    "lines_added",
    "lines_removed",
    "files_changed",
    "languages",
    "language_file_counts",
    "language_lines_added",
    "language_lines_removed",
]
_DEDUP_COLS = ["commit_hash"]

app = typer.Typer(
    help=(
        "Extract commit statistics from a directory of git repositories "
        "and write a Polars-compatible CSV dataset."
    ),
    no_args_is_help=True,
)


def _extract(
    repos_dir: Path,
    output: Path,
    emails: list[str] | None = None,
    exclude: list[str] | None = None,
) -> None:
    email_set = set(emails) if emails else None
    exclude_set = set(exclude) if exclude else None
    email_info = (
        f" (filtering to {len(email_set)} email(s))" if email_set else ""
    )
    exclude_info = (
        f" (excluding {len(exclude_set)} repo(s))" if exclude_set else ""
    )
    typer.echo(f"Scanning repositories in '{repos_dir}'{email_info}{exclude_info}...")

    records = extract_all_repos(repos_dir, email_set, exclude_set)

    if not records:
        typer.echo("No matching commits found.", err=True)
        raise typer.Exit(code=1)

    df = pl.DataFrame(records)
    df = df.select(_OUTPUT_COLS)

    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists():
        existing = pl.read_csv(output)
        existing_keys = set(
            zip(*[existing[c].to_list() for c in _DEDUP_COLS])
        )
        df = df.filter(
            pl.struct(_DEDUP_COLS).map_elements(
                lambda row: tuple(row[c] for c in _DEDUP_COLS) not in existing_keys,
                return_dtype=pl.Boolean,
            )
        )
        if df.is_empty():
            typer.echo("No new commits to append — output is already up to date.")
            raise typer.Exit(code=0)
        combined = pl.concat([existing, df])
        combined.write_csv(output)
        typer.echo(f"Appended {len(df)} new commit(s) to '{output}'.")
    else:
        df.write_csv(output)
        typer.echo(f"Saved {len(df)} commit(s) to '{output}'.")


@app.command("extract")
def extract_command(
    repos_dir: Annotated[
        Path,
        typer.Argument(
            help="Path to the directory that contains the git repositories to analyse.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Destination CSV file path.",
            writable=True,
            resolve_path=True,
        ),
    ],
    emails: Annotated[
        list[str] | None,
        typer.Option(
            "--email",
            "-e",
            help=(
                "Author email to include in the dataset. "
                "Can be repeated to allow multiple authors. "
                "Omit to include every author."
            ),
        ),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            "-x",
            help=(
                "Repository name (directory basename) to exclude. "
                "Can be repeated to exclude multiple repositories."
            ),
        ),
    ] = None,
) -> None:
    _extract(repos_dir, output, emails, exclude)


@app.command("emails")
def list_emails(
    repos_dir: Annotated[
        Path,
        typer.Argument(
            help="Path to the directory that contains the git repositories to scan.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """Show all unique author emails found in repositories under REPOS_DIR."""
    typer.echo(f"Scanning repositories in '{repos_dir}' for author emails...")
    emails = collect_all_emails(repos_dir)

    if not emails:
        typer.echo("No author emails found.", err=True)
        raise typer.Exit(code=1)

    for email in sorted(emails):
        typer.echo(email)


def run() -> None:
    """CLI entry point.

    Preserve the original root extraction form:
        github-stats REPOS_DIR --output OUTPUT.csv

    while also allowing subcommands:
        github-stats emails REPOS_DIR
    """
    args = sys.argv[1:]
    command_names = {"extract", "emails"}
    help_flags = {"--help", "-h", "--install-completion", "--show-completion"}

    if args and args[0] not in command_names and args[0] not in help_flags:
        sys.argv.insert(1, "extract")

    app()
