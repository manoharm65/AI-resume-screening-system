# AI Resume Screening and Ranking System

## Overview

A production-minded Python CLI that processes a folder of resumes, extracts structured candidate information, applies deterministic eligibility rules, ranks only eligible candidates, optionally enriches GitHub activity, and writes an explainable JSON report.

The system supports PDF, DOCX, and TXT resumes. PDF remains the primary required format.

## Quick Start

```powershell
python main.py --input ./resume_dataset_50 --output ./output/results.json
```

Run without external GitHub requests:

```powershell
python main.py --input ./resume_dataset_50 --output ./output/results.json --no-github
```

Install dependencies and run tests:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

## Processing Flow

```text
Resume files
	-> format-aware text extraction
	-> normalization and structured candidate extraction
	-> deterministic Python + AI eligibility filter
	-> scoring of eligible candidates only
	-> optional GitHub enrichment
	-> descending ranking
	-> output/results.json
```

## Eligibility Rules

A candidate is eligible only when both conditions are satisfied:

1. Genuine Python evidence exists in skills, projects, work, or implementation details.
2. Meaningful AI, LLM, RAG, machine-learning, or agentic implementation evidence exists.

JavaScript, Java, React, and Next.js are acceptable supporting technologies. A high ranking score can never override a failed hard filter.

## Ranking Model

Only eligible candidates receive a ranking number and score:

| Category | Maximum |
|---|---:|
| AI / Agentic / RAG project depth | 40 |
| Python and backend engineering | 30 |
| Cloud, deployment, and full stack | 15 |
| GitHub activity | 10 |
| Engineering depth | 5 |
| **Total** | **100** |

The JSON exposes both `rank` and `ranking_number`, plus `score`, `total_score`, category breakdowns, evidence, penalties, strengths, and concerns.

## GitHub Enrichment

GitHub profile URLs are extracted from visible resume text and PDF hyperlink annotations. The optional client caches results per username and uses public profile data, repositories, and recent public events. GitHub failure, rate limiting, missing profiles, and private profiles do not fail the batch.

Use `GITHUB_TOKEN` through `.env` or the environment when higher GitHub API limits are needed. Never commit secrets.

## Output

The generated [output/results.json](output/results.json) contains:

- Ranked eligible candidates with `rank` and `ranking_number`
- Rejected candidates with concrete rejection reasons
- Matched skills and project summaries
- Score breakdown, evidence, penalties, strengths, and concerns
- GitHub URL, username, status, summary, and enrichment errors
- Parse failures and duplicate-file records
- Batch counts including successfully parsed, eligible, rejected, failed, and duplicate files

## Project Structure

```text
main.py                 CLI entry point
src/parser.py           PDF, DOCX, and TXT discovery/extraction
src/models.py           Pydantic data contracts
src/utils.py            Conservative candidate extraction and normalization
src/eligibility.py      Deterministic hard filter
src/scorer.py           Explainable 100-point ranking score
src/github.py           Cached public GitHub enrichment
src/llm.py              Provider-independent extraction boundary/fallback
src/pipeline.py         Batch orchestration and JSON output
tests/                  Focused unit and integration tests
output/                 Generated results and reference documents
```

## Design Decisions

- Eligibility is deterministic and happens before ranking.
- Skills listed alone can support Python detection, but meaningful AI eligibility requires implementation evidence.
- The default extractor is provider-independent and works without an API key.
- Scores are explainable, capped, and supported by evidence. Thin LLM/API wrappers receive visible penalties.
- Each resume is isolated so one malformed file or network failure cannot stop the batch.
- Duplicate files are detected by SHA-256 content hash and reported separately.

## Reference Documents

Generated guides are available in `output/`:

- `project_approach_and_results.pdf`: formal overview of approach, design, execution, and achieved results.
- `technical_reference_guide.pdf`: file-by-file and function-by-function explanation for interview preparation.

## Future Improvements

- Add a real LLM provider adapter with structured Pydantic output and caching.
- Add OCR fallback for scanned PDFs.
- Split consolidated project sections into multiple project records.
- Add a small HTML report for quick review of top candidates.

## Scope

No frontend, database, authentication, deployment, or vector database is required for this assignment. The input dataset is never modified.