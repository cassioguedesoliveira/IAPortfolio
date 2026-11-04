"""LLM-as-judge metric for open-ended answers.

The judge is any ``callable(prompt) -> str``; it must reply with JSON such as
``{"score": 4, "reason": "..."}`` (score 1-5). We normalise to [0, 1] and treat
unparseable replies as failures so a flaky judge never silently inflates results.
"""
from __future__ import annotations

import json
import re
from typing import Callable

from .metrics import Metric

RUBRIC = """You are a strict grader. Compare the ANSWER with the REFERENCE.
Score 1-5: 5 = fully correct and complete, 3 = partially correct, 1 = wrong or contradicts the reference.
Reply ONLY with JSON: {{"score": <1-5>, "reason": "<one sentence>"}}

QUESTION: {question}
REFERENCE: {reference}
ANSWER: {answer}"""


def make_judge_metric(judge: Callable[[str], str]) -> Metric:
    def llm_judge(output: str, expected: str, params: dict) -> float:
        prompt = RUBRIC.format(question=params.get("question", ""), reference=expected, answer=output)
        reply = judge(prompt)
        match = re.search(r"\{.*\}", reply, flags=re.S)
        if not match:
            return 0.0
        try:
            score = float(json.loads(match.group(0))["score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return 0.0
        return min(max((score - 1) / 4, 0.0), 1.0)

    return llm_judge
