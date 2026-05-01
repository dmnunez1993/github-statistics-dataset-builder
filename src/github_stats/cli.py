from __future__ import annotations

from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from .extractor import extract_all_repos

app = typer.Typer(
    help=(
        "Extract commit statistics from a directory of git repositories "
        "and write a Polars-compatible CSV dataset."
    ),
    no_args_is_help=True,
)


@app.command()
def main(
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
) -> None:
    email_set = set(emails) if emails else None
    email_info = (
        f" (filtering to {len(email_set)} email(s))" if email_set else ""
    )
    typer.echo(f"Scanning repositories in '{repos_dir}'{email_info}...")

    records = extract_all_repos(repos_dir, email_set)

    if not records:
        typer.echo("No matching commits found.", err=True)
        raise typer.Exit(code=1)

    df = pl.DataFrame(records)

    output.parent.mkdir(parents=True, exist_ok=True)

    _DEDUP_COLS = ["author_email", "commit_date", "lines_added", "lines_removed", "files_changed", "languages"]

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
