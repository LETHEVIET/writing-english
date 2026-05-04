"""Check for app updates via GitHub Releases API."""

from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from writing_english.app.constants import APP_VERSION

logger = logging.getLogger(__name__)

GITHUB_API_RELEASES = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
CHECK_INTERVAL_HOURS = 6


@dataclass
class UpdateInfo:
    version: str
    tag_name: str
    name: str
    body: str
    html_url: str
    published_at: str
    download_urls: list[str]


def parse_version(version: str) -> tuple[int, int, int]:
    cleaned = version.strip().lstrip("v")
    parts = cleaned.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def _get_repo_slug() -> Optional[str]:
    import subprocess
    from pathlib import Path

    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        url = result.stdout.strip()
        if not url:
            return None
        url = url.removesuffix(".git").rstrip("/")
        if "github.com" in url:
            if url.startswith("git@"):
                path = url.split(":", 1)[1] if ":" in url else ""
            elif url.startswith("https://"):
                path = url.split("github.com/", 1)[1] if "github.com/" in url else ""
            else:
                return None
            return path
    except Exception:
        return None
    return None


def check_for_update(
    owner: str,
    repo: str,
    last_check: Optional[datetime] = None,
) -> Optional[UpdateInfo]:
    if last_check is not None:
        elapsed = datetime.now(timezone.utc) - last_check
        if elapsed.total_seconds() < CHECK_INTERVAL_HOURS * 3600:
            logger.debug("Skipping update check (checked recently)")
            return None

    url = GITHUB_API_RELEASES.format(owner=owner, repo=repo)
    logger.debug("Checking for updates: %s", url)

    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "writing-english-app",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        logger.debug("Update check failed: %s", e)
        return None

    tag = data.get("tag_name", "")
    latest_version = tag.lstrip("v")

    if not is_newer(latest_version, APP_VERSION):
        logger.debug("Current version %s is up to date", APP_VERSION)
        return None

    assets = data.get("assets", [])
    download_urls = [
        a["browser_download_url"]
        for a in assets
        if isinstance(a, dict) and "browser_download_url" in a
    ]

    return UpdateInfo(
        version=latest_version,
        tag_name=tag,
        name=data.get("name", tag),
        body=data.get("body", ""),
        html_url=data.get("html_url", ""),
        published_at=data.get("published_at", ""),
        download_urls=download_urls,
    )
