import io
import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "mysql",
    "postgresql", "mongodb", "html", "css", "react", "angular", "vue", "node",
    "fastapi", "django", "flask", "spring", "aws", "azure", "docker", "kubernetes",
    "git", "linux", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "excel", "power bi", "tableau",
    "communication", "leadership", "project management", "agile", "scrum",
]


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix in {".docx"}:
        document = Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs)
    if suffix in {".txt"}:
        return content.decode("utf-8", errors="ignore")
    raise ValueError("Upload a PDF, DOCX, or TXT resume")


def extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", lowered):
            found.append(skill.title() if skill not in {"c++", "c#", "sql", "nlp", "aws", "html", "css"} else skill.upper() if skill in {"sql", "nlp", "aws", "html", "css"} else skill)
    ordered = []
    for skill in found:
        if skill not in ordered:
            ordered.append(skill)
    return ordered[:18]


def skills_to_json(skills: list[str]) -> str:
    return json.dumps(skills)


def skills_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
