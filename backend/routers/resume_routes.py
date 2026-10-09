import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Resume, User
from schemas import ResumeOut
from services.resume_parser import extract_skills, extract_text, skills_from_json, skills_to_json

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED = {".pdf", ".docx", ".txt"}


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=400, detail="Please upload a PDF, DOCX, or TXT file")

    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be 8MB or smaller")

    try:
        text = extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored_name = f"{current_user.id}_{uuid.uuid4().hex}{suffix}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    skills = extract_skills(text)
    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_path=str(stored_path),
        parsed_text=text[:20000],
        skills_json=skills_to_json(skills),
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return _to_out(resume)


@router.get("", response_model=list[ResumeOut])
def list_resumes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return [_to_out(row) for row in rows]


def _to_out(resume: Resume) -> ResumeOut:
    text = resume.parsed_text or ""
    return ResumeOut(
        id=resume.id,
        original_filename=resume.original_filename,
        skills=skills_from_json(resume.skills_json),
        created_at=resume.created_at,
        excerpt=(text[:280] + "…") if len(text) > 280 else text,
    )
