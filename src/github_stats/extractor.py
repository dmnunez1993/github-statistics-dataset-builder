from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import git
import typer

from .languages import (
    get_language_counts_from_files,
    get_language_for_file,
    get_languages_from_files,
)


def _process_commit(commit: git.Commit) -> dict:
    """Extract a flat record from a single commit."""
    try:
        total = commit.stats.total
        file_stats = commit.stats.files
        files = list(file_stats.keys())
    except Exception:
        total = {"insertions": 0, "deletions": 0, "files": 0}
        file_stats = {}
        files = []

    languages = get_languages_from_files(files)
    language_file_counts = get_language_counts_from_files(files)
    language_lines_added = _sum_language_file_stats(file_stats, "insertions")
    language_lines_removed = _sum_language_file_stats(file_stats, "deletions")
    committed_dt = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
    parent_count = len(commit.parents)

    return {
        "commit_hash": commit.hexsha,
        "is_merge_commit": parent_count > 1,
        "parent_count": parent_count,
        "author_name": commit.author.name,
        "author_email": commit.author.email,
        "commit_date": committed_dt.isoformat(),
        "lines_added": total.get("insertions", 0),
        "lines_removed": total.get("deletions", 0),
        "files_changed": total.get("files", 0),
        "languages": "|".join(languages),
        "language_file_counts": json.dumps(language_file_counts, sort_keys=True),
        "language_lines_added": json.dumps(language_lines_added, sort_keys=True),
        "language_lines_removed": json.dumps(language_lines_removed, sort_keys=True),
    }


def _sum_language_file_stats(
    file_stats: dict[str, dict],
    stat_name: str,
) -> dict[str, int]:
    totals: dict[str, int] = {}
    for filename, stats in file_stats.items():
        lang = get_language_for_file(filename)
        if not lang:
            continue
        totals[lang] = totals.get(lang, 0) + int(stats.get(stat_name, 0))
    return dict(sorted(totals.items()))


def extract_repo_stats(
    repo_path: Path,
    emails: set[str] | None = None,
) -> list[dict]:
    """Extract commit records from a single git repository.

    Args:
        repo_path: Path to the git repository root.
        emails: If provided, only commits whose author email is in this set
                are included (privacy filter).

    Returns:
        List of commit record dicts. Empty if the path is not a git repo.
    """
    try:
        repo = git.Repo(repo_path)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        typer.echo(f"  [skip] '{repo_path}' could not be opened as a git repository.")
        return []

    records: list[dict] = []
    total_commits = 0
    matched_commits = 0

    for commit in repo.iter_commits(all=True):
        total_commits += 1
        if emails is not None and commit.author.email not in emails:
            continue
        matched_commits += 1
        records.append(_process_commit(commit))

    if emails is not None:
        typer.echo(
            f"  '{repo_path.name}': {matched_commits}/{total_commits} commit(s) matched."
        )
    else:
        typer.echo(f"  '{repo_path.name}': {total_commits} commit(s) found.")

    return records


def collect_repo_emails(repo_path: Path) -> set[str]:
    """Collect unique author emails from a single git repository."""
    try:
        repo = git.Repo(repo_path)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        typer.echo(f"  [skip] '{repo_path}' could not be opened as a git repository.")
        return set()

    emails = {
        commit.author.email
        for commit in repo.iter_commits(all=True)
        if commit.author.email
    }
    typer.echo(f"  '{repo_path.name}': {len(emails)} author email(s) found.")
    return emails


def _find_repos(root: Path) -> list[Path]:
    """Recursively find all git repository roots under *root*.

    Stops descending into a directory once a .git entry is found there.
    """
    if (root / ".git").exists():
        return [root]
    repos: list[Path] = []
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir())
    except PermissionError:
        return []
    for child in children:
        repos.extend(_find_repos(child))
    return repos


def extract_all_repos(
    repos_dir: Path,
    emails: set[str] | None = None,
) -> list[dict]:
    """Recursively discover all git repositories under *repos_dir* and extract
    commit stats from each one.

    Args:
        repos_dir: Root directory to search for git repositories.
        emails: Privacy filter — only commits from these author emails are kept.

    Returns:
        Combined list of commit records from all discovered repositories.
    """
    all_records: list[dict] = []
    repos = _find_repos(repos_dir)
    typer.echo(f"Found {len(repos)} git repository/repositories to scan.")

    for path in repos:
        records = extract_repo_stats(path, emails)
        all_records.extend(records)

    typer.echo(f"Total commits collected: {len(all_records)}.")
    return all_records


def collect_all_emails(repos_dir: Path) -> set[str]:
    """Recursively discover all git repositories under *repos_dir* and collect
    unique author emails from their commits.
    """
    all_emails: set[str] = set()
    repos = _find_repos(repos_dir)
    typer.echo(f"Found {len(repos)} git repository/repositories to scan.")

    for path in repos:
        all_emails.update(collect_repo_emails(path))

    typer.echo(f"Total unique author emails found: {len(all_emails)}.")
    return all_emails
