from __future__ import annotations

import json
import os
import re


STAR_HINTS = ("situation", "task", "action", "result", "because", "therefore", "for example")
STRONG_VERBS = (
    "implemented", "designed", "led", "improved", "reduced", "increased",
    "built", "optimized", "collaborated", "measured", "delivered",
)


def _heuristic_feedback(question: str, answer: str) -> dict:
    words = re.findall(r"[A-Za-z']+", answer.lower())
    word_count = len(words)
    score = 40

    if word_count >= 40:
        score += 15
    if word_count >= 80:
        score += 10
    if word_count >= 140:
        score += 5

    if any(hint in answer.lower() for hint in STAR_HINTS):
        score += 12
    verb_hits = sum(1 for verb in STRONG_VERBS if verb in answer.lower())
    score += min(12, verb_hits * 3)

    q_tokens = {t for t in re.findall(r"[A-Za-z']+", question.lower()) if len(t) > 4}
    overlap = len(q_tokens.intersection(set(words)))
    score += min(16, overlap)

    if word_count < 25:
        score -= 15

    score = max(20, min(95, score))

    strengths = []
    improvements = []
    if word_count >= 80:
        strengths.append("The answer has enough depth to sound interview-ready.")
    else:
        improvements.append("Add more concrete detail so the interviewer can follow your story.")
    if verb_hits:
        strengths.append("You used action-oriented language that hiring managers notice.")
    else:
        improvements.append("Use stronger action verbs such as implemented, led, or measured.")
    if any(hint in answer.lower() for hint in STAR_HINTS):
        strengths.append("The structure hints at a Situation-Action-Result narrative.")
    else:
        improvements.append("Frame the story with Situation, Action, and Result.")
    if overlap >= 3:
        strengths.append("You stayed close to the question instead of giving a generic speech.")
    else:
        improvements.append("Echo keywords from the question so the answer feels targeted.")

    detail = (
        f"Word count: {word_count}. This is a practice score based on structure, "
        f"specificity, and relevance to the prompt. Aim for a 60–90 second spoken answer "
        f"with one metric and a clear result."
    )
    return {
        "score": score,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "detailed_feedback": detail,
    }


def generate_feedback(question: str, answer: str, role: str) -> dict:
    base = _heuristic_feedback(question, answer)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return base
    try:
        import httpx

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        prompt = (
            f"Role: {role}\nQuestion: {question}\nAnswer: {answer}\n"
            "Score the answer 0-100. Return JSON with keys score, strengths (array), "
            "improvements (array), detailed_feedback (string)."
        )
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an interview coach. Reply with JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            return base
        parsed = json.loads(match.group(0))
        return {
            "score": int(max(0, min(100, parsed.get("score", base["score"])))),
            "strengths": list(parsed.get("strengths") or base["strengths"])[:4],
            "improvements": list(parsed.get("improvements") or base["improvements"])[:4],
            "detailed_feedback": str(parsed.get("detailed_feedback") or base["detailed_feedback"]),
        }
    except Exception:
        return base
