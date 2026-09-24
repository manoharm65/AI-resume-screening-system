from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
import unicodedata
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from pypdf import PdfReader


class _PypdfNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith("Ignoring wrong pointing object")


logging.getLogger("pypdf._reader").addFilter(_PypdfNoiseFilter())


class ResumeParseError(Exception):
    """Raised when a resume cannot produce usable text."""


@dataclass(frozen=True)
class ParsedResume:
    file_path: Path
    page_count: int
    text: str
    links: list[str]


SUPPORTED_RESUME_SUFFIXES = {".pdf", ".docx", ".txt"}


def discover_resume_files(input_path: Path) -> list[Path]:
    """Return supported resume files under a directory, including nested folders."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_path}")

    return sorted(
        path for path in input_path.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_RESUME_SUFFIXES
    )


def discover_pdf_files(input_path: Path) -> list[Path]:
    """Backward-compatible PDF-only discovery helper."""
    return [path for path in discover_resume_files(input_path) if path.suffix.lower() == ".pdf"]


def normalize_text(text: str) -> str:
    """Normalize PDF layout artifacts while preserving useful line boundaries."""
    normalized = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_pdf_text(file_path: Path) -> ParsedResume:
    """Extract normalized text from one PDF or raise a descriptive parse error."""
    try:
        reader = PdfReader(str(file_path))
        page_text = [(page.extract_text() or "") for page in reader.pages]
        links: list[str] = []
        for page in reader.pages:
            annotations = page.get("/Annots", []) or []
            try:
                page_annotations = list(annotations)
            except TypeError:
                page_annotations = []
            for annotation in page_annotations:
                annotation_object = annotation.get_object()
                action = annotation_object.get("/A")
                uri = action.get("/URI") if action else None
                if uri:
                    links.append(str(uri))
    except Exception as exc:
        raise ResumeParseError(f"Unable to read PDF: {exc}") from exc

    text = normalize_text("\n".join(page_text))
    if not text:
        raise ResumeParseError("PDF contains no extractable text")

    return ParsedResume(file_path=file_path, page_count=len(reader.pages), text=text, links=list(dict.fromkeys(links)))


def extract_docx_text(file_path: Path) -> ParsedResume:
    """Extract paragraph text from a DOCX resume without requiring python-docx."""
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    try:
        with ZipFile(file_path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except (BadZipFile, KeyError, ElementTree.ParseError, OSError) as exc:
        raise ResumeParseError(f"Unable to read DOCX: {exc}") from exc

    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        paragraphs.append("".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)))
    text = normalize_text("\n".join(paragraphs))
    if not text:
        raise ResumeParseError("DOCX contains no extractable text")
    return ParsedResume(file_path=file_path, page_count=1, text=text, links=[])


def extract_text_resume(file_path: Path) -> ParsedResume:
    """Extract a plain-text resume."""
    try:
        text = normalize_text(file_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError) as exc:
        raise ResumeParseError(f"Unable to read TXT: {exc}") from exc
    if not text:
        raise ResumeParseError("TXT contains no extractable text")
    return ParsedResume(file_path=file_path, page_count=1, text=text, links=[])


def extract_resume_text(file_path: Path) -> ParsedResume:
    """Extract one supported resume according to its file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(file_path)
    if suffix == ".docx":
        return extract_docx_text(file_path)
    if suffix == ".txt":
        return extract_text_resume(file_path)
    raise ResumeParseError(f"Unsupported resume format: {file_path.suffix}")