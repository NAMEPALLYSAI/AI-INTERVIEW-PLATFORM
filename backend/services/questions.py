from __future__ import annotations

import os
import random

QUESTION_BANK = {
    "behavioral": [
        "Tell me about a time you faced a tight deadline. How did you prioritize and what was the result?",
        "Describe a conflict with a teammate and how you resolved it.",
        "Give an example of a project you owned from start to finish.",
        "Tell me about a mistake you made at work or in a project. What did you learn?",
    ],
    "hr": [
        "Walk me through your background and why you are pursuing this role.",
        "What are your strengths, and where are you still growing?",
        "Why should we hire you for this position?",
        "Where do you see yourself in the next three years?",
    ],
    "python": [
        "How would you explain the difference between a list, tuple, and dictionary in Python, and when would you use each?",
        "Describe how you would debug a slow Python API endpoint in production.",
    ],
    "javascript": [
        "Explain event loop, promises, and async/await as if interviewing for a frontend role.",
        "How would you prevent memory leaks in a JavaScript single-page application?",
    ],
    "sql": [
        "How would you write a query to find duplicate records and then keep only the latest one?",
        "Explain INNER JOIN vs LEFT JOIN with an interview-style example from your resume.",
    ],
    "react": [
        "How do you decide between local state, context, and a global store in React?",
        "Walk through how you would optimize a slow React list rendering thousands of rows.",
    ],
    "java": [
        "Explain OOP principles with an example from a Java project you have worked on.",
        "How does the JVM garbage collector affect application performance?",
    ],
    "aws": [
        "Design a simple, highly available web app on AWS and justify each service.",
        "How would you secure secrets and environment variables in a cloud deployment?",
    ],
    "machine learning": [
        "How would you evaluate a classification model beyond accuracy?",
        "Walk through how you would handle imbalanced data in a real project.",
    ],
    "fastapi": [
        "How would you structure a FastAPI service with authentication, validation, and database sessions?",
        "What would you do if an interview coding task required uploading files and parsing PDFs?",
    ],
    "leadership": [
        "Describe how you motivated a team or classmates when progress stalled.",
        "How do you give and receive feedback?",
    ],
}


def _match_categories(skills: list[str], role: str) -> list[str]:
    haystack = " ".join(skills + [role]).lower()
    matched = []
    for key in QUESTION_BANK:
        if key in {"behavioral", "hr"}:
            continue
        if key in haystack:
            matched.append(key)
    return matched


def generate_questions(role: str, skills: list[str], count: int = 6) -> list[dict]:
    selected: list[tuple[str, str]] = []
    selected.append(("hr", QUESTION_BANK["hr"][0]))
    selected.append(("behavioral", random.choice(QUESTION_BANK["behavioral"])))

    for category in _match_categories(skills, role):
        prompt = random.choice(QUESTION_BANK[category])
        selected.append((category, prompt))
        if len(selected) >= count:
            break

    while len(selected) < count:
        category = random.choice(["hr", "behavioral"])
        prompt = random.choice(QUESTION_BANK[category])
        if prompt not in {item[1] for item in selected}:
            selected.append((category, prompt))

    skill_note = ", ".join(skills[:6]) if skills else "your experience"
    selected.append(
        (
            "role",
            f"For the {role} role, which part of {skill_note} is most relevant, and how would you apply it in the first 90 days?",
        )
    )

    unique = []
    seen = set()
    for category, prompt in selected:
        if prompt not in seen:
            unique.append({"category": category.title(), "prompt": prompt})
            seen.add(prompt)
    return unique[:count]


def maybe_refine_with_llm(role: str, skills: list[str], questions: list[dict]) -> list[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return questions
    try:
        import httpx

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        skill_list = ", ".join(skills) or "general software skills"
        user_prompt = (
            f"Create {len(questions)} concise interview questions for a {role} candidate "
            f"with skills: {skill_list}. Mix behavioral and technical. Return JSON array "
            f'of objects with keys "category" and "prompt".'
        )
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You generate interview questions. Reply with JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.4,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        import json
        import re

        match = re.search(r"\[.*\]", content, re.S)
        if not match:
            return questions
        parsed = json.loads(match.group(0))
        cleaned = []
        for item in parsed:
            if isinstance(item, dict) and item.get("prompt"):
                cleaned.append(
                    {
                        "category": str(item.get("category", "Technical")),
                        "prompt": str(item["prompt"]),
                    }
                )
        return cleaned[: len(questions)] or questions
    except Exception:
        return questions
