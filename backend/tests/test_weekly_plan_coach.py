"""Contract tests for the constrained, TSS-free OpenAI coach adapter."""

import asyncio
import json
from datetime import date
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.coach.weekly_plan import (
    CoachProviderError,
    CoachWorkoutFacts,
    OpenAIWeeklyPlanCoach,
    WeeklyPlanCoachExplanation,
    WeeklyPlanCoachFacts,
    deterministic_weekly_plan_explanation,
)
from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.workouts.catalog import TrainingPhase


def _facts() -> WeeklyPlanCoachFacts:
    return WeeklyPlanCoachFacts(
        week_start=date(2026, 8, 24),
        timezone="Europe/Amsterdam",
        phase=TrainingPhase.BASE,
        workouts=(
            CoachWorkoutFacts(
                discipline=Discipline.RUN,
                name="Rustige duurloop",
                scheduled_date=date(2026, 8, 25),
                duration_minutes=Decimal("45"),
                intensity=IntensityBucket.LOW,
            ),
        ),
        rest_days=(date(2026, 8, 24), date(2026, 8, 26)),
    )


def test_deterministic_explanation_describes_dates_without_inventing_times() -> None:
    result = deterministic_weekly_plan_explanation(_facts())

    assert "trainingsdagen" in result.public_explanation
    assert "De tijden" not in result.public_explanation


def test_openai_coach_sends_only_allowlisted_facts_and_strict_schema() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "public_explanation": (
                                            "Je rustige duurloop staat op dinsdag. "
                                            "Controleer het voorstel en keur het "
                                            "alleen goed als deze week haalbaar is."
                                        )
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    async def exercise() -> WeeklyPlanCoachExplanation:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            coach = OpenAIWeeklyPlanCoach(
                Settings(environment="test", openai_api_key="secret-key"),
                client=client,
            )
            return await coach.explain(_facts())

    result = asyncio.run(exercise())

    assert "dinsdag" in result.public_explanation
    assert captured is not None
    body = json.loads(captured.content)
    disclosed_facts = json.loads(body["input"])
    serialized = json.dumps(disclosed_facts).casefold()
    assert "tss" not in serialized
    assert "load" not in serialized
    assert set(disclosed_facts) == {
        "week_start",
        "timezone",
        "phase",
        "workouts",
        "rest_days",
        "requires_athlete_confirmation",
    }
    assert body["store"] is False
    assert body["text"]["format"]["type"] == "json_schema"
    assert body["text"]["format"]["strict"] is True
    assert captured.headers["authorization"] == "Bearer secret-key"


def test_openai_coach_rejects_refusal_and_private_load_language() -> None:
    with pytest.raises(ValidationError, match="private-load"):
        WeeklyPlanCoachExplanation(public_explanation="Je geplande TSS is prima.")

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
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
        ) as client:
            coach = OpenAIWeeklyPlanCoach(
                Settings(environment="test", openai_api_key="secret-key"),
                client=client,
            )
            with pytest.raises(CoachProviderError):
                await coach.explain(_facts())

    asyncio.run(exercise())
