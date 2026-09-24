from pathlib import Path
from unittest.mock import Mock, patch

from src.github import GitHubClient
from src.models import Candidate, GitHubResult
from src.parser import ParsedResume, ResumeParseError
from src.pipeline import run_pipeline


def test_pipeline_continues_after_one_bad_resume(tmp_path: Path) -> None:
    input_path = tmp_path / "input"
    input_path.mkdir()
    good_file = input_path / "good.pdf"
    bad_file = input_path / "bad.pdf"
    good_file.write_bytes(b"good resume")
    bad_file.write_bytes(b"bad resume")
    output_path = tmp_path / "output" / "results.json"
    candidate = Candidate(
        source_file=str(good_file),
        candidate_name="Asha Rao",
        skills=["Python"],
        ai_evidence=["Built a RAG pipeline"],
    )
    github = Mock(spec=GitHubClient)
    github.enrich.return_value = GitHubResult(status="missing")

    def fake_extract(path: Path) -> ParsedResume:
        if path == bad_file:
            raise ResumeParseError("bad PDF")
        return ParsedResume(path, 1, "resume text", [])

    with patch("src.pipeline.extract_resume_text", side_effect=fake_extract), patch(
        "src.pipeline.extract_candidate_with_fallback", return_value=(candidate, None)
    ):
        result = run_pipeline(input_path, output_path, github)

    assert result["summary"]["total_files"] == 2
    assert result["summary"]["eligible_count"] == 1
    assert result["summary"]["failed_count"] == 1
    assert result["summary"]["successfully_parsed"] == 1
    assert result["summary"]["duplicate_count"] == 0
    assert result["ranked_candidates"][0]["github_username"] is None
    assert output_path.exists()