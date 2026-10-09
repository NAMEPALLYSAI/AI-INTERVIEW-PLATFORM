from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ResumeOut(BaseModel):
    id: int
    original_filename: str
    skills: list[str]
    created_at: datetime
    excerpt: str


class InterviewStart(BaseModel):
    target_role: str = Field(min_length=2, max_length=160)
    resume_id: int | None = None


class QuestionOut(BaseModel):
    id: int
    prompt: str
    category: str
    sort_order: int
    answered: bool


class InterviewOut(BaseModel):
    id: int
    target_role: str
    status: str
    created_at: datetime
    questions: list[QuestionOut]


class AnswerSubmit(BaseModel):
    answer_text: str = Field(min_length=20, max_length=8000)


class FeedbackItem(BaseModel):
    question_id: int
    question: str
    category: str
    answer: str
    score: int
    strengths: list[str]
    improvements: list[str]
    detailed_feedback: str


class InterviewFeedbackOut(BaseModel):
    interview_id: int
    target_role: str
    overall_score: int
    items: list[FeedbackItem]
