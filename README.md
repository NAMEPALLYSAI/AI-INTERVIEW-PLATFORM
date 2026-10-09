# PrepLine — AI Interview Preparation Platform

Web app for mock interviews: register, log in, upload a resume, answer generated questions, and review scored feedback.

## Stack

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- Database: MySQL

## File structure

```
AI INTERVIEW PLATFORM/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routers/
│   │   ├── auth_routes.py
│   │   ├── resume_routes.py
│   │   └── interview_routes.py
│   └── services/
│       ├── resume_parser.py
│       ├── questions.py
│       └── feedback.py
├── frontend/
│   ├── index.html          # login
│   ├── register.html
│   ├── dashboard.html
│   ├── resume.html
│   ├── interview.html
│   ├── feedback.html
│   ├── css/style.css
│   └── js/
├── database/schema.sql
├── uploads/
├── requirements.txt
└── .env.example
```

## Setup

1. Install MySQL and create the database:

```sql
CREATE DATABASE interview_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

You can also run `database/schema.sql`. Tables are created automatically on API startup as well.

2. Copy environment variables:

```bash
copy .env.example .env
```

Edit `.env` with your MySQL user, password, and a long `SECRET_KEY`.

3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Start the server from the `backend` folder so imports resolve:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Features

1. **User registration** — `/register.html` → `POST /api/auth/register`
2. **User login** — `/index.html` → `POST /api/auth/login`
3. **Resume upload** — PDF / DOCX / TXT, skill extraction
4. **Interview questions** — generated from role + resume skills
5. **Answer submission** — one answer per question, min 20 characters
6. **Feedback page** — score, strengths, and improvements

If `OPENAI_API_KEY` is set, question generation and feedback use the model in `.env`. Without a key, the built-in question bank and scoring rules still run.
