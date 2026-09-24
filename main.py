from __future__ import annotations

import argparse
from pathlib import Path

from src.config import GITHUB_TOKEN
from src.github import GitHubClient, NoOpGitHubClient
from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Screen and rank resume PDFs.")
    parser.add_argument("--input", type=Path, default=Path("./resume_dataset_50"))
    parser.add_argument("--output", type=Path, default=Path("./output/results.json"))
    parser.add_argument("--no-github", action="store_true", help="Skip GitHub API requests")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    github_client = NoOpGitHubClient() if args.no_github else GitHubClient(token=GITHUB_TOKEN)
    result = run_pipeline(args.input, args.output, github_client=github_client)
    print("Processed:")
    print(f"  Total files: {result['summary']['total_files']}")
    print(f"  Successfully parsed: {result['summary']['successfully_parsed']}")
    print(f"  Eligible: {result['summary']['eligible_count']}")
    print(f"  Rejected: {result['summary']['rejected_count']}")
    print(f"  Failed: {result['summary']['failed_count']}")
    print(f"  Duplicates: {result['summary']['duplicate_count']}")
    if result["rejected_candidates"]:
        print("Rejection notes:")
        for index, candidate in enumerate(result["rejected_candidates"], start=1):
            reasons = "; ".join(candidate["rejection_reasons"])
            pdf_name = Path(candidate["source_file"]).name
            candidate_name = candidate["candidate_name"] or "Unknown candidate"
            print(f"  {index}. {pdf_name} - {candidate_name}: {reasons}")
    print(f"Detailed results are listed in: {args.output}")


if __name__ == "__main__":
    main()