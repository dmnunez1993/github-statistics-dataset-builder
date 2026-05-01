from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import git

from .languages import get_languages_from_files


def _process_commit(commit: git.Commit) -> dict:
    """Extract a flat record from a single commit."""
    try:
        total = commit.stats.total
        files = list(commit.stats.files.keys())
    except Exception:
        total = {"insertions": 0, "deletions": 0, "files": 0}
        files = []

    languages = get_languages_from_files(files)
    committed_dt = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)

    return {
        "author_name": commit.author.name,
        "author_email": commit.author.email,
        "commit_date": committed_dt.isoformat(),
        "lines_added": total.get("insertions", 0),
        "lines_removed": total.get("deletions", 0),
        "files_changed": total.get("files", 0),
        "languages": "|".join(languages),
    }


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
        return []

    records: list[dict] = []

    for commit in repo.iter_commits(all=True):
        if emails is not None and commit.author.email not in emails:
            continue
        records.append(_process_commit(commit))

    return records


def extract_all_repos(
    repos_dir: Path,
    emails: set[str] | None = None,
) -> list[dict]:
    """Walk *repos_dir* and extract commit stats from every git repository found.

    Each immediate subdirectory of *repos_dir* is treated as a candidate repo.

    Args:
        repos_dir: Directory that directly contains one or more git repositories.
        emails: Privacy filter — only commits from these author emails are kept.

    Returns:
        Combined list of commit records from all discovered repositories.
    """
    all_records: list[dict] = []

    for path in sorted(repos_dir.iterdir()):
        if not path.is_dir():
            continue
        records = extract_repo_stats(path, emails)
        all_records.extend(records)

    return all_records
