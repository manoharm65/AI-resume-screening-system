from unittest.mock import Mock

from src.github import GitHubClient, NoOpGitHubClient, github_username


def response(status: int, payload: object) -> Mock:
    result = Mock()
    result.status_code = status
    result.json.return_value = payload
    result.raise_for_status.return_value = None
    return result


def test_github_enrichment_scores_and_caches_profile() -> None:
    client = GitHubClient()
    client.session.get = Mock(
        side_effect=[
            response(200, {"public_repos": 3}),
            response(200, [{"name": "rag-api", "description": "RAG service", "language": "Python"}]),
            response(200, [{"created_at": "2026-09-20T12:00:00Z"}] * 5),
        ]
    )

    first = client.enrich("https://github.com/example")
    second = client.enrich("https://github.com/example")

    assert first.status == "success"
    assert first.profile_url == "https://github.com/example"
    assert first.score == 7
    assert second == first
    assert client.session.get.call_count == 3


def test_github_failures_are_structured() -> None:
    client = GitHubClient()
    client.session.get = Mock(return_value=response(403, {}))

    result = client.enrich("https://github.com/example")

    assert result.status == "rate_limited"
    assert result.profile_url == "https://github.com/example"
    assert result.score == 0


def test_github_username_is_derived_from_profile_url() -> None:
    assert github_username("https://github.com/raghuvardhan07") == "raghuvardhan07"
    assert github_username("https://github.com/raghuvardhan07/project") == "raghuvardhan07"
    assert NoOpGitHubClient().enrich("https://github.com/raghuvardhan07").username == "raghuvardhan07"