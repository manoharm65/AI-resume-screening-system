from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .models import GitHubResult


GITHUB_URL_PATTERN = re.compile(r"github\.com/([A-Za-z0-9][A-Za-z0-9-]*)", re.IGNORECASE)


def github_username(github_url: str | None) -> str | None:
    if not github_url:
        return None
    match = GITHUB_URL_PATTERN.search(github_url)
    return match.group(1) if match else None


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: float = 5.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/vnd.github+json"
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self._cache: dict[str, GitHubResult] = {}

    def enrich(self, github_url: str | None) -> GitHubResult:
        if not github_url:
            return GitHubResult(status="missing")
        username = github_username(github_url)
        if not username:
            return GitHubResult(status="invalid", error="Invalid GitHub profile URL")

        if username in self._cache:
            return self._cache[username]

        try:
            user_response = self.session.get(f"https://api.github.com/users/{username}", timeout=self.timeout)
            if user_response.status_code == 404:
                result = GitHubResult(status="unavailable", profile_url=github_url, username=username, error="GitHub profile not found")
                self._cache[username] = result
                return result
            if user_response.status_code == 403:
                result = GitHubResult(status="rate_limited", profile_url=github_url, username=username, error="GitHub API rate limit reached")
                self._cache[username] = result
                return result
            user_response.raise_for_status()
            user = user_response.json()

            repos_response = self.session.get(
                f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
                timeout=self.timeout,
            )
            repos_response.raise_for_status()
            repos = repos_response.json()
            events_response = self.session.get(
                f"https://api.github.com/users/{username}/events/public?per_page=30",
                timeout=self.timeout,
            )
            events_response.raise_for_status()
            events = events_response.json()
            result = self._build_result(username, user, repos, events)
        except requests.RequestException as exc:
            result = GitHubResult(status="error", profile_url=github_url, username=username, error=str(exc))
        except (TypeError, ValueError, KeyError) as exc:
            result = GitHubResult(status="error", profile_url=github_url, username=username, error=f"Invalid GitHub response: {exc}")

        self._cache[username] = result
        return result

    def _build_result(
        self,
        username: str,
        user: dict[str, Any],
        repos: list[dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> GitHubResult:
        python_repos = sum((repo.get("language") or "").lower() == "python" for repo in repos)
        ai_repos = sum(
            any(term in f"{repo.get('name', '')} {repo.get('description', '')}".lower() for term in ("ai", "llm", "rag", "agent", "ml"))
            for repo in repos
        )
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        recent_events = 0
        for event in events:
            created_at = event.get("created_at")
            if not created_at:
                continue
            try:
                if datetime.fromisoformat(created_at.replace("Z", "+00:00")) >= cutoff:
                    recent_events += 1
            except ValueError:
                continue
        activity_points = min(5, recent_events)
        relevance_points = min(5, python_repos + ai_repos)
        summary = {
            "public_repositories": user.get("public_repos", 0),
            "python_repositories": python_repos,
            "ai_related_repositories": ai_repos,
            "recently_updated_repositories": min(len(repos), 5),
            "recent_public_events": recent_events,
        }
        return GitHubResult(status="success", profile_url=f"https://github.com/{username}", username=username, score=activity_points + relevance_points, summary=summary)


class NoOpGitHubClient:
    def enrich(self, github_url: str | None) -> GitHubResult:
        return GitHubResult(status="skipped", profile_url=github_url, username=github_username(github_url))