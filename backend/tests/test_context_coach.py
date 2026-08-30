"""Safety and Structured Outputs tests for Phase 10 context extraction."""

import asyncio
import json
from datetime import date

import httpx
import pytest

from app.core.config import Settings
from app.modules.coach.context import (
    CheckInContextFacts,
    ContextCoachProviderError,
    OpenAICheckInContextCoach,
)


def _facts() -> CheckInContextFacts:
    return CheckInContextFacts(
        week_start=date(2026, 8, 31),
        timezone="Europe/Amsterdam",
        athlete_text="Woensdag kan ik niet en ik ben behoorlijk moe.",
    )


def test_context_coach_uses_strict_non_retained_output_without_tools() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "blocked_dates": ["2026-09-02"],
                                        "fatigue_level": "high",
                                        "missed_workout_reasons": ["fatigue"],
                                        "possible_injury_disciplines": [],
                                        "agenda_context": [],
                                        "clarifying_questions": [],
                                    }
                                ),
                            }
                        ],
                    }
                ]
            },
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            coach = OpenAICheckInContextCoach(
                Settings(environment="test", openai_api_key="secret-key"),
                client=client,
            )
            candidate = await coach.extract(_facts())
            assert candidate.blocked_dates == (date(2026, 9, 2),)

    asyncio.run(exercise())

    assert captured is not None
    body = json.loads(captured.content)
    assert body["store"] is False
    assert body["text"]["format"]["strict"] is True
    assert "tools" not in body
    assert json.loads(body["input"])["athlete_text"].startswith("Woensdag")


def test_context_coach_rejects_refusal() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "refusal", "refusal": "no"}],
                    }
                ]
            },
        )

    async def exercise() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            coach = OpenAICheckInContextCoach(
                Settings(environment="test", openai_api_key="secret-key"),
                client=client,
            )
            with pytest.raises(ContextCoachProviderError):
                await coach.extract(_facts())

    asyncio.run(exercise())
