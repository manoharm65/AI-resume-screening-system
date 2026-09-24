from __future__ import annotations

import re
from pathlib import Path

from .models import Candidate, Project


EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d ()-]{7,}\d)")
GITHUB_PATTERN = re.compile(r"https?://(?:www\.)?github\.com/[A-Za-z0-9][A-Za-z0-9-]*(?:/[^\s]*)?", re.IGNORECASE)
GITHUB_PROFILE_PATTERN = re.compile(r"^https?://(?:www\.)?github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/?$", re.IGNORECASE)
SECTION_PATTERN = re.compile(
    r"^(?:technical )?(?:skills?|projects?|experience|work experience|internships?|education|summary|profile|certifications?)\s*:?(?:\s|$)",
    re.IGNORECASE,
)
SKILL_PATTERN = re.compile(r"(?:skills?|technologies|tech stack|languages?)\s*:\s*(.+)", re.IGNORECASE)
PROJECT_SECTION_PATTERN = re.compile(r"^(?:personal |academic |key )?projects?\s*:?(?:\s|$)", re.IGNORECASE)
EXPERIENCE_SECTION_PATTERN = re.compile(r"^(?:work )?experience|internships?", re.IGNORECASE)
SKILL_VOCABULARY: tuple[tuple[str, str], ...] = (
    ("Python", r"\bpython\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Django", r"\bdjango\b"),
    ("Flask", r"\bflask\b"),
    ("PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("MongoDB", r"\bmongodb\b"),
    ("Redis", r"\bredis\b"),
    ("Docker", r"\bdocker\b"),
    ("AWS", r"\baws\b"),
    ("GCP", r"\bgcp|google cloud\b"),
    ("React", r"\breact(?:\.js|js)?\b"),
    ("Next.js", r"\bnext\.js\b"),
    ("Java", r"\bjava\b"),
    ("JavaScript", r"\bjavascript\b|\bjs\b"),
    ("TypeScript", r"\btypescript\b"),
    ("C++", r"\bc\+\+\b"),
    ("SQL", r"\bsql\b"),
    ("LangChain", r"\blangchain\b"),
    ("LangGraph", r"\blanggraph\b"),
    ("RAG", r"\brag\b|retrieval[- ]augmented generation"),
    ("LLM", r"\bllms?\b|large language model"),
    ("OpenAI", r"\bopenai\b"),
    ("Gemini", r"\bgemini\b"),
    ("Machine Learning", r"\bmachine learning\b|\bml\b"),
    ("Embeddings", r"\bembeddings?\b"),
    ("Vector Search", r"\bvector (?:search|database|store)\b|pgvector"),
    ("AI Agents", r"\bagentic\b|\bmulti-agent\b|\bagents?\b|tool calling"),
    ("Kafka", r"\bkafka\b"),
    ("Celery", r"\bcelery\b"),
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("CI/CD", r"\bci/cd\b|github actions|jenkins"),
)


def _clean_line(line: str) -> str:
    return " ".join(line.replace("•", " ").split()).strip(" |:-")


def _section_lines(lines: list[str], section_pattern: re.Pattern[str]) -> list[str]:
    section: list[str] = []
    collecting = False
    for line in lines:
        if section_pattern.search(line):
            collecting = True
            continue
        if collecting and SECTION_PATTERN.match(line):
            break
        if collecting:
            cleaned = _clean_line(line)
            if cleaned:
                section.append(cleaned)
    return section


def _skills(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        match = SKILL_PATTERN.search(line)
        if match:
            values.extend(part.strip(" .:") for part in re.split(r"[,|;·]", match.group(1)) if part.strip(" .:"))
    full_text = " ".join(lines)
    for skill, pattern in SKILL_VOCABULARY:
        if re.search(pattern, full_text, re.IGNORECASE):
            values.append(skill)
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            unique_values.append(value)
    return unique_values


def _github_url(text: str, links: list[str]) -> str | None:
    candidates = list(dict.fromkeys([*GITHUB_PATTERN.findall(text), *[link for link in links if GITHUB_PATTERN.search(link)]]))
    profiles = [url for url in candidates if GITHUB_PROFILE_PATTERN.match(url.rstrip("/"))]
    return profiles[0].rstrip("/") if profiles else (candidates[0].rstrip("/") if candidates else None)


def _projects(lines: list[str]) -> list[Project]:
    project_lines = _section_lines(lines, PROJECT_SECTION_PATTERN)
    if not project_lines:
        return []
    description = " ".join(project_lines)
    name_parts = project_lines[:8] if len(project_lines[0].split()) < 3 else [project_lines[0]]
    name = " ".join(name_parts)[:160]
    readable_evidence = [line for line in project_lines if len(line.split()) >= 8]
    if not readable_evidence:
        readable_evidence = [description]
    return [
        Project(
            name=name,
            description=description,
            technologies=_skills(project_lines),
            evidence=readable_evidence[:20],
        )
    ]


def _first_name(lines: list[str], email: str | None) -> str | None:
    for line in lines[:8]:
        cleaned = _clean_line(line)
        if not cleaned or not re.search(r"[A-Za-z]", cleaned) or EMAIL_PATTERN.search(cleaned) or GITHUB_PATTERN.search(cleaned):
            continue
        if SECTION_PATTERN.match(cleaned) or re.search(r"\b(?:phone|linkedin|mobile)\b", cleaned, re.IGNORECASE):
            continue
        if len(cleaned.split()) <= 5 and not re.search(r"[@:/|]", cleaned):
            return cleaned
    return email.split("@")[0] if email else None


def extract_candidate(text: str, source_file: Path | str, links: list[str] | None = None) -> Candidate:
    """Extract conservative candidate fields without inventing missing information."""
    lines = [line for line in text.splitlines() if line.strip()]
    email_match = EMAIL_PATTERN.search(text)
    github_url = _github_url(text, links or [])
    phone_match = PHONE_PATTERN.search(text)
    projects = _projects(lines)
    experience = _section_lines(lines, EXPERIENCE_SECTION_PATTERN)

    return Candidate(
        source_file=str(source_file),
        candidate_name=_first_name(lines, email_match.group(0) if email_match else None),
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        github_url=github_url,
        skills=_skills(lines),
        projects=projects,
        experience=experience,
        python_evidence=[line for line in lines if re.search(r"\bpython\b", line, re.IGNORECASE)],
        ai_evidence=[
            line
            for line in lines
            if re.search(r"\b(?:ai|ml|llm|rag|langchain|langgraph|retrieval|embedding|agent|openai|gemini)\b", line, re.IGNORECASE)
        ],
        engineering_evidence=[line for line in lines if re.search(r"\b(?:test|cache|redis|docker|api|async|ci/cd|queue)\b", line, re.IGNORECASE)],
    )