from __future__ import annotations

from pydantic import BaseModel, Field


class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    source_file: str
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    github_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    python_evidence: list[str] = Field(default_factory=list)
    ai_evidence: list[str] = Field(default_factory=list)
    engineering_evidence: list[str] = Field(default_factory=list)


class EligibilityResult(BaseModel):
    eligible: bool
    rejection_reasons: list[str] = Field(default_factory=list)
    python_evidence: list[str] = Field(default_factory=list)
    ai_evidence: list[str] = Field(default_factory=list)


class ParseFailure(BaseModel):
    status: str = "failed"
    file: str
    error: str


class Penalty(BaseModel):
    reason: str
    points: int


class ScoreResult(BaseModel):
    total: int
    categories: dict[str, int]
    evidence: dict[str, list[str]] = Field(default_factory=dict)
    penalties: list[Penalty] = Field(default_factory=list)


class GitHubResult(BaseModel):
    status: str
    profile_url: str | None = None
    username: str | None = None
    score: int = 0
    summary: dict[str, object] = Field(default_factory=dict)
    error: str | None = None