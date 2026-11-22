"""Server-written athlete text is Dutch by default and English on request."""

import ast
import re
from collections.abc import Iterator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Settings
from app.core.error_messages import DUTCH_ERROR_MESSAGES
from app.core.errors import configure_error_handling
from app.core.i18n import LanguageMiddleware, resolve_language
from app.core.security import AuthenticatedIdentity, InvalidAccessTokenError
from app.main import create_app
from app.modules.activities.messages import ACTIVITY_FEEDBACK_MESSAGES
from app.modules.activities.schemas import ActivityResponse
from app.modules.coach.context import (
    CheckInContextCandidate,
    deterministic_context_fallback,
)
from app.modules.coach.weekly_plan import (
    CoachWorkoutFacts,
    WeeklyPlanCoachFacts,
    deterministic_weekly_plan_explanation,
)
from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.planning.messages import WARNING_MESSAGES, proposal_explanation
from app.modules.planning.schemas import (
    ChangeProposalSummaryResponse,
    PlanWarningResponse,
)
from app.modules.workouts.catalog import TrainingPhase

_APP_ROOT = Path(__file__).resolve().parents[1] / "app"
_MIGRATIONS = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
_ENGLISH = {"Accept-Language": "en"}
_FORBIDDEN_PRIVATE_LOAD = re.compile(
    r"\b(?:tss|training\s+stress\s+score|planned\s+load|realized\s+load)\b",
    flags=re.IGNORECASE,
)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, "nl"),
        ("", "nl"),
        ("en", "en"),
        ("EN-gb", "en"),
        ("nl-BE", "nl"),
        ("fr-FR, de;q=0.9", "nl"),
        ("en-US,en;q=0.9,nl;q=0.8", "en"),
        ("nl;q=0.2, en;q=0.8", "en"),
        ("en;q=0, fr", "nl"),
        ("en;q=abc", "nl"),
        ("en;q=1.5", "nl"),
        ("*", "nl"),
    ],
)
def test_accept_language_resolves_to_dutch_unless_english_is_asked_for(
    header: str | None,
    expected: str,
) -> None:
    assert resolve_language(header) == expected


# --- Errors -----------------------------------------------------------------


class _UnexpectedFailure(Exception):
    pass


def _error_app() -> FastAPI:
    application = FastAPI()
    configure_error_handling(application)
    application.add_middleware(LanguageMiddleware)

    @application.get("/coded")
    async def coded() -> None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "proposal_stale",
                "message": "The plan changed after this schedule request was prepared.",
            },
        )

    @application.get("/uncoded")
    async def uncoded() -> None:
        raise HTTPException(
            status_code=422,
            detail="Descending zone boundaries must be contiguous.",
        )

    @application.get("/unknown-code")
    async def unknown_code() -> None:
        raise HTTPException(
            status_code=409,
            detail={"code": "some_future_code", "message": "A future conflict."},
        )

    @application.get("/validated")
    async def validated(count: int) -> int:
        return count

    @application.get("/unexpected")
    async def unexpected() -> None:
        raise _UnexpectedFailure("private detail")

    return application


@pytest.fixture
def error_client() -> Iterator[TestClient]:
    with TestClient(_error_app(), raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize(
    ("path", "status_code", "code", "dutch", "english"),
    [
        (
            "/coded",
            409,
            "proposal_stale",
            "Dit voorstel is gebaseerd op een oudere versie van je plan.",
            "The plan changed after this schedule request was prepared.",
        ),
        (
            "/uncoded",
            422,
            "validation_failed",
            "Het verzoek bevat ongeldige gegevens.",
            "Descending zone boundaries must be contiguous.",
        ),
        (
            "/unknown-code",
            409,
            "some_future_code",
            "De gegevens zijn intussen gewijzigd. Vernieuw en probeer opnieuw.",
            "A future conflict.",
        ),
        (
            "/validated?count=many",
            422,
            "validation_failed",
            "Het verzoek bevat ongeldige gegevens.",
            "The request failed validation.",
        ),
        (
            "/unexpected",
            500,
            "internal_error",
            "Er ging onverwacht iets mis.",
            "An unexpected error occurred.",
        ),
    ],
)
def test_error_message_is_dutch_by_default_and_english_on_request(
    error_client: TestClient,
    path: str,
    status_code: int,
    code: str,
    dutch: str,
    english: str,
) -> None:
    default = error_client.get(path)
    explicit_dutch = error_client.get(path, headers={"Accept-Language": "nl"})
    english_response = error_client.get(path, headers=_ENGLISH)

    for response in (default, explicit_dutch, english_response):
        assert response.status_code == status_code
        assert response.json()["error"]["code"] == code
    assert default.json()["error"]["message"] == dutch
    assert explicit_dutch.json()["error"]["message"] == dutch
    assert english_response.json()["error"]["message"] == english
    assert default.json()["error"].keys() == english_response.json()["error"].keys()


def test_language_never_changes_error_details(error_client: TestClient) -> None:
    dutch = error_client.get("/validated?count=many").json()["error"]
    english = error_client.get("/validated?count=many", headers=_ENGLISH).json()
    assert dutch["details"] == english["error"]["details"]


def test_real_authentication_error_follows_language() -> None:
    with TestClient(create_app(Settings(environment="test"))) as client:
        dutch = client.get("/api/v1/onboarding")
        english = client.get("/api/v1/onboarding", headers=_ENGLISH)

    assert dutch.status_code == english.status_code == 401
    assert dutch.json()["error"]["code"] == "authentication_required"
    assert dutch.json()["error"]["message"] == (
        "Je sessie is verlopen of ongeldig. Log opnieuw in."
    )
    assert english.json()["error"]["message"] == "Invalid authentication credentials"
    assert dutch.headers["Content-Language"] == "nl"
    assert english.headers["Content-Language"] == "en"
    assert "Accept-Language" in english.headers["Vary"]


def _literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _raised_error_codes() -> set[str]:
    """Collect every stable error code the application can put in a response."""
    snake_case = re.compile(r"^[a-z][a-z0-9_]+$")
    codes: set[str] = set()
    for path in _APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = str(getattr(node.func, "id", getattr(node.func, "attr", "")))
                if name.endswith("Error") and node.args:
                    code = _literal(node.args[0])
                    if code and snake_case.match(code):
                        codes.add(code)
            if isinstance(node, ast.Tuple) and len(node.elts) == 2:
                code, message = (_literal(element) for element in node.elts)
                if code and message and snake_case.match(code) and " " in message:
                    codes.add(code)
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    key_text = _literal(key) if key is not None else None
                    value_text = _literal(value)
                    if (
                        key_text
                        and value_text
                        and snake_case.match(value_text)
                        and " " in key_text
                    ):
                        codes.add(value_text)
    return codes


def test_every_raised_error_code_has_dutch_wording() -> None:
    codes = _raised_error_codes()
    # Guard the scan itself so a refactor cannot make this test vacuous.
    assert {
        "proposal_stale",
        "pioneer_code_invalid",
        "activity_rpe_immutable",
        "checkin_context_stale",
        "planned_external_activity_already_completed",
    } <= codes
    assert sorted(codes - DUTCH_ERROR_MESSAGES.keys()) == []


# --- Planning warnings, activity feedback, proposals and labels -----------------


class _PublicTexts(BaseModel):
    warnings: list[PlanWarningResponse]
    activity: ActivityResponse
    proposal: ChangeProposalSummaryResponse
    candidate: CheckInContextCandidate


def _public_texts() -> _PublicTexts:
    now = datetime(2026, 8, 13, 15, tzinfo=timezone.utc)
    return _PublicTexts(
        warnings=[
            PlanWarningResponse(
                rule_id="injury_redistribution",
                code="all_disciplines_blocked_rest_only",
                severity="warning",
                message=(
                    "Every goal discipline is currently blocked. This pending "
                    "revision contains rest only and requires your confirmation."
                ),
            ),
            PlanWarningResponse(
                rule_id="soft_boundaries",
                code="distance_only_swim_excluded_from_time_ratio",
                severity="info",
                message="Afstandsgestuurde zwemtrainingen staan in meters.",
            ),
            PlanWarningResponse(
                rule_id="soft_boundaries",
                code="some_future_warning",
                severity="warning",
                message="A future warning.",
            ),
        ],
        activity=ActivityResponse(
            id=uuid4(),
            planned_workout_id=None,
            discipline=Discipline.RUN,
            source="canonical_summary",
            started_at=now,
            timezone="Europe/Brussels",
            duration_minutes=Decimal(45),
            distance_meters=None,
            elevation_gain_meters=None,
            rpe=6,
            rpe_submitted_at=now,
            match_status="unmatched",
            processing_state="complete",
            qualitative_result="unplanned",
            public_message=(
                "Deze extra training stond niet in je actieve planning. "
                "Een eventuele aanpassing blijft eerst een voorstel."
            ),
            correction_proposal_id=None,
            metrics=None,
            created_at=now,
            updated_at=now,
        ),
        proposal=ChangeProposalSummaryResponse(
            id=uuid4(),
            kind="plan_revision",
            state="pending",
            reason_codes=("weekly_plan_ready",),
            public_explanation="A deterministic weekly plan is ready for review.",
            ruleset_version="test",
            created_at=now,
        ),
        candidate=deterministic_context_fallback(),
    )


@pytest.fixture
def text_client() -> Iterator[TestClient]:
    application = FastAPI()
    application.add_middleware(LanguageMiddleware)
    stored = _public_texts()

    @application.get("/texts", response_model=_PublicTexts)
    async def texts() -> _PublicTexts:
        return stored

    with TestClient(application) as client:
        yield client


def test_public_text_is_dutch_by_default(text_client: TestClient) -> None:
    body = text_client.get("/texts").json()

    assert [warning["message"] for warning in body["warnings"]] == [
        "Alle disciplines zijn momenteel geblokkeerd. Daarom bevat dit voorstel "
        "alleen rust.",
        "Afstandsgestuurde zwemtrainingen staan in meters in het plan; de "
        "80/20-tijdverdeling bevat alleen trainingen met een vastgelegde duur.",
        "Dit voorstel heeft een aandachtspunt. Controleer het voor goedkeuring.",
    ]
    assert body["activity"]["public_message"] == (
        "Deze extra training stond niet in je actieve planning. "
        "Een eventuele aanpassing blijft eerst een voorstel."
    )
    assert body["proposal"]["public_explanation"] == (
        "Je persoonlijke weekvoorstel staat klaar om te controleren."
    )
    assert body["candidate"]["clarifying_questions"] == [
        "Welke dagen ben je niet beschikbaar en hoe vermoeid voel je je?"
    ]


def test_public_text_is_english_on_request(text_client: TestClient) -> None:
    body = text_client.get("/texts", headers=_ENGLISH).json()

    assert [warning["message"] for warning in body["warnings"]] == [
        "All disciplines are currently blocked, so this proposal contains only rest.",
        "Distance-based swim workouts appear in metres in the plan; the 80/20 "
        "time split only includes workouts with a recorded duration.",
        "This proposal has a point of attention. Review it before approving.",
    ]
    assert body["activity"]["public_message"] == (
        "This extra workout was not in your active plan. "
        "Any adjustment will remain a proposal first."
    )
    assert body["proposal"]["public_explanation"] == (
        "Your personal weekly proposal is ready to review."
    )
    assert body["candidate"]["clarifying_questions"] == [
        "Which days are you unavailable and how tired do you feel?"
    ]


def test_language_changes_wording_only(text_client: TestClient) -> None:
    dutch = text_client.get("/texts").json()
    english = text_client.get("/texts", headers=_ENGLISH).json()

    def without_text(body: dict[str, Any]) -> dict[str, Any]:
        for warning in body["warnings"]:
            warning.pop("message")
        body["activity"].pop("public_message")
        body["proposal"].pop("public_explanation")
        body["candidate"].pop("clarifying_questions")
        return body

    assert without_text(dutch) == without_text(english)


def test_unrecognised_activity_feedback_falls_back_to_its_result() -> None:
    activity = _public_texts().activity.model_copy(
        update={
            "public_message": "Historische feedback.",
            "qualitative_result": "overshoot",
        }
    )
    assert activity.model_dump()["public_message"] == (
        "Deze training viel zwaarder uit dan gepland. "
        "Een eventuele aanpassing blijft eerst een voorstel."
    )


def test_deterministic_weekly_explanation_is_worded_in_both_languages() -> None:
    explanation = deterministic_weekly_plan_explanation(
        WeeklyPlanCoachFacts(
            week_start=date(2026, 8, 10),
            timezone="Europe/Brussels",
            phase=TrainingPhase.BASE,
            workouts=tuple(
                CoachWorkoutFacts(
                    discipline=discipline,
                    name="Training",
                    scheduled_date=date(2026, 8, 10 + offset),
                    duration_minutes=Decimal(45),
                    intensity=IntensityBucket.LOW,
                )
                for offset, discipline in enumerate(
                    (Discipline.SWIM, Discipline.BIKE, Discipline.RUN)
                )
            ),
            rest_days=(date(2026, 8, 13), date(2026, 8, 16)),
        )
    ).public_explanation

    assert proposal_explanation(explanation, "nl") == (
        "Dit weekvoorstel verdeelt 3 trainingen over fietsen, hardlopen, zwemmen, "
        "met 2 geplande rustdagen. De trainingsdagen volgen je bevestigde "
        "beschikbaarheid; bekijk het voorstel en keur het pas goed als de week "
        "voor jou haalbaar voelt."
    )
    assert proposal_explanation(explanation, "en") == (
        "This weekly proposal spreads 3 workouts over cycling, running, swimming, "
        "with 2 planned rest days. The training days follow your confirmed "
        "availability; review the proposal and only approve it if the week feels "
        "achievable for you."
    )
    assert proposal_explanation("Vrije tekst van de coach.", "en") == (
        "Vrije tekst van de coach."
    )


def test_every_generated_warning_code_has_both_languages() -> None:
    codes: set[str] = set()
    for path in (_APP_ROOT / "modules" / "planning").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {
                "PlanningWarning",
                "PlanWarningResponse",
            }:
                for keyword in node.keywords:
                    code = _literal(keyword.value)
                    if keyword.arg == "code" and code is not None:
                        codes.add(code)
    assert "all_disciplines_blocked_rest_only" in codes
    assert sorted(codes - WARNING_MESSAGES.keys()) == []


def test_every_stored_activity_feedback_sentence_has_both_languages() -> None:
    source = (_APP_ROOT / "modules" / "physiology" / "activity.py").read_text(
        encoding="utf-8"
    )
    sentences: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.keyword) and node.arg == "public_message":
            sentences.update(
                text
                for child in ast.walk(node.value)
                if (text := _literal(child)) is not None
            )
    latest_default = sorted(
        re.findall(
            r"public_message text not null default '([^']+)'",
            "\n".join(
                path.read_text(encoding="utf-8") for path in _MIGRATIONS.glob("*.sql")
            ),
        )
    )
    assert len(sentences) == 7
    assert latest_default
    assert sorted(sentences | set(latest_default)) == sorted(
        ACTIVITY_FEEDBACK_MESSAGES.keys()
    )


def test_catalogs_are_complete_translated_and_free_of_private_load_terms() -> None:
    localized_catalogs = [
        *WARNING_MESSAGES.values(),
        *ACTIVITY_FEEDBACK_MESSAGES.values(),
    ]
    for text in localized_catalogs:
        assert text.keys() == {"nl", "en"}
        assert text["nl"] != text["en"]
    for wording in [
        *DUTCH_ERROR_MESSAGES.values(),
        *(value for text in localized_catalogs for value in text.values()),
    ]:
        assert wording.strip() == wording
        assert not _FORBIDDEN_PRIVATE_LOAD.search(wording)


class _TokenVerifier:
    def __init__(self, owner: UUID) -> None:
        self._owner = owner

    def verify(self, access_token: str) -> AuthenticatedIdentity:
        if access_token != "athlete":
            raise InvalidAccessTokenError
        return AuthenticatedIdentity(
            user_id=self._owner, role="authenticated", athlete_id=self._owner
        )


@pytest.fixture
def option_client() -> Iterator[TestClient]:
    application = create_app(
        Settings(environment="test"),
        access_token_verifier=_TokenVerifier(uuid4()),
    )
    with TestClient(application) as client:
        yield client


def test_goal_and_setup_option_labels_follow_language(
    option_client: TestClient,
) -> None:
    auth = {"Authorization": "Bearer athlete"}
    goals_nl = option_client.get("/api/v1/onboarding/goal-options", headers=auth)
    goals_en = option_client.get(
        "/api/v1/onboarding/goal-options", headers={**auth, **_ENGLISH}
    )
    routes_nl = option_client.get("/api/v1/onboarding/zone-options/swim", headers=auth)
    routes_en = option_client.get(
        "/api/v1/onboarding/zone-options/swim", headers={**auth, **_ENGLISH}
    )

    assert [option["label"] for option in goals_nl.json()] == [
        "Wedstrijd of evenement",
        "Algemene fitheid",
        "Gewichtsverlies",
        "Spieropbouw",
    ]
    assert [option["label"] for option in goals_en.json()] == [
        "Race or event",
        "General fitness",
        "Weight loss",
        "Muscle gain",
    ]
    assert [option["label"] for option in routes_nl.json()] == [
        "Ik ken mijn waarden",
        "Ik wil mijn waarden testen",
        "Ik wil rustig beginnen en laten kalibreren",
    ]
    assert [option["label"] for option in routes_en.json()] == [
        "I know my values",
        "I want to test my values",
        "I want to start easy and let my values calibrate",
    ]
    for dutch, english in ((goals_nl, goals_en), (routes_nl, routes_en)):
        assert [
            {key: value for key, value in option.items() if key != "label"}
            for option in dutch.json()
        ] == [
            {key: value for key, value in option.items() if key != "label"}
            for option in english.json()
        ]
