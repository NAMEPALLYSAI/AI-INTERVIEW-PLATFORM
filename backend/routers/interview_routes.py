import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from auth import get_current_user
from database import get_db
from models import Answer, Feedback, Interview, Question, Resume, User
from schemas import (
    AnswerSubmit,
    FeedbackItem,
    InterviewFeedbackOut,
    InterviewOut,
    InterviewStart,
    QuestionOut,
)
from services.feedback import generate_feedback
from services.questions import generate_questions, maybe_refine_with_llm
from services.resume_parser import skills_from_json

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("/start", response_model=InterviewOut)
def start_interview(
    payload: InterviewStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = None
    skills: list[str] = []
    if payload.resume_id:
        resume = (
            db.query(Resume)
            .filter(Resume.id == payload.resume_id, Resume.user_id == current_user.id)
            .first()
        )
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        skills = skills_from_json(resume.skills_json)

    questions = generate_questions(payload.target_role, skills)
    questions = maybe_refine_with_llm(payload.target_role, skills, questions)

    interview = Interview(
        user_id=current_user.id,
        resume_id=resume.id if resume else None,
        target_role=payload.target_role.strip(),
        status="in_progress",
    )
    db.add(interview)
    db.flush()
    for index, item in enumerate(questions):
        db.add(
            Question(
                interview_id=interview.id,
                prompt=item["prompt"],
                category=item["category"],
                sort_order=index,
            )
        )
    db.commit()
    interview = _owned_interview(db, interview.id, current_user.id)
    return _interview_out(db, interview)


@router.get("", response_model=list[InterviewOut])
def list_interviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Interview)
        .options(joinedload(Interview.questions).joinedload(Question.answer))
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )
    return [_interview_out(db, row) for row in rows]


@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _owned_interview(db, interview_id, current_user.id)
    return _interview_out(db, interview)


@router.post("/{interview_id}/questions/{question_id}/answer")
def submit_answer(
    interview_id: int,
    question_id: int,
    payload: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _owned_interview(db, interview_id, current_user.id)
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.interview_id == interview.id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = db.query(Answer).filter(Answer.question_id == question.id).first()
    if existing:
        existing.answer_text = payload.answer_text.strip()
        answer = existing
        if existing.feedback:
            db.delete(existing.feedback)
            db.flush()
    else:
        answer = Answer(
            question_id=question.id,
            user_id=current_user.id,
            answer_text=payload.answer_text.strip(),
        )
        db.add(answer)
        db.flush()

    result = generate_feedback(question.prompt, answer.answer_text, interview.target_role)
    db.add(
        Feedback(
            answer_id=answer.id,
            score=result["score"],
            strengths=json.dumps(result["strengths"]),
            improvements=json.dumps(result["improvements"]),
            detailed_feedback=result["detailed_feedback"],
        )
    )

    total = db.query(Question).filter(Question.interview_id == interview.id).count()
    answered = (
        db.query(Answer)
        .join(Question)
        .filter(Question.interview_id == interview.id)
        .count()
    )
    if answered >= total:
        interview.status = "completed"
    db.commit()
    return {"ok": True, "interview_status": interview.status}


@router.get("/{interview_id}/feedback", response_model=InterviewFeedbackOut)
def interview_feedback(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    interview = _owned_interview(db, interview_id, current_user.id)
    questions = (
        db.query(Question)
        .options(joinedload(Question.answer).joinedload(Answer.feedback))
        .filter(Question.interview_id == interview.id)
        .order_by(Question.sort_order)
        .all()
    )
    items = []
    scores = []
    for question in questions:
        if not question.answer or not question.answer.feedback:
            continue
        fb = question.answer.feedback
        items.append(
            FeedbackItem(
                question_id=question.id,
                question=question.prompt,
                category=question.category,
                answer=question.answer.answer_text,
                score=fb.score,
                strengths=_loads(fb.strengths),
                improvements=_loads(fb.improvements),
                detailed_feedback=fb.detailed_feedback or "",
            )
        )
        scores.append(fb.score)

    if not items:
        raise HTTPException(status_code=400, detail="Submit at least one answer to view feedback")

    overall = round(sum(scores) / len(scores))
    return InterviewFeedbackOut(
        interview_id=interview.id,
        target_role=interview.target_role,
        overall_score=overall,
        items=items,
    )


def _owned_interview(db: Session, interview_id: int, user_id: int) -> Interview:
    interview = (
        db.query(Interview)
        .options(joinedload(Interview.questions).joinedload(Question.answer))
        .filter(Interview.id == interview_id, Interview.user_id == user_id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


def _interview_out(db: Session, interview: Interview) -> InterviewOut:
    questions = sorted(interview.questions, key=lambda q: q.sort_order)
    return InterviewOut(
        id=interview.id,
        target_role=interview.target_role,
        status=interview.status,
        created_at=interview.created_at,
        questions=[
            QuestionOut(
                id=q.id,
                prompt=q.prompt,
                category=q.category,
                sort_order=q.sort_order,
                answered=q.answer is not None,
            )
            for q in questions
        ],
    )


def _loads(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [raw]
    except json.JSONDecodeError:
        return [raw]
