"""Audit-only characterization tests; passing assertions demonstrate current gaps."""
import asyncio
from datetime import date
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.modules.physiology.anti_stack import ScheduledWorkout
from app.modules.physiology.models import Discipline, IntensityBucket
from app.modules.planning.domain import PlanningConstraintError, canonical_schedule_instant, validate_manual_schedule
from app.modules.planning.schemas import WeeklyPlanResponse, PlannedWorkoutResponse, PlanValidationRequest
from app.modules.planning.service import PlanningService
from app.modules.health.service import build_readiness_response

@pytest.mark.parametrize('sport', list(Discipline))
def test_week_boundary_is_missing_from_actual_layout_service(sport):
    prior = ScheduledWorkout('previous-sunday', frozenset({sport}), IntensityBucket.HIGH,
                             canonical_schedule_instant(date(2026,10,25), timezone_name='Europe/Amsterdam'))
    current_id = uuid4()
    current = ScheduledWorkout(str(current_id), frozenset({sport}), IntensityBucket.HIGH,
                               canonical_schedule_instant(date(2026,10,26), timezone_name='Europe/Amsterdam'))
    with pytest.raises(PlanningConstraintError, match='more time'):
        validate_manual_schedule(workouts=(prior,current), moved_workout_id=None)
    # Use typed minimal projections because this probe targets service context,
    # not DTO validation (covered by the existing contract suite).
    workout = PlannedWorkoutResponse.model_construct(id=current_id,discipline=sport,intensity_bucket=IntensityBucket.HIGH)
    plan = WeeklyPlanResponse.model_construct(revision=1, timezone='Europe/Amsterdam', workouts=(workout,))
    class Repository:
        async def fetch_plan(self, token, plan_id): return plan
    service = PlanningService(Repository(), None, None)
    request = PlanValidationRequest(expected_revision=1, workouts=[{'workout_id':str(current_id),'scheduled_date':'2026-10-26'}])
    result = asyncio.run(service.validate_layout('synthetic-token',uuid4(),request))
    assert result.valid_for_generated_schedule is True
    assert result.warnings == ()


def test_production_accepts_only_old_load_review_while_new_planner_is_always_active():
    settings = Settings(_env_file=None, environment='production',
        supabase_publishable_key='synthetic-publishable', supabase_secret_key='synthetic-secret',
        physiology_review_record_id='phase13-only-review', physiology_accountable_owner='synthetic-reviewer',
        physiology_review_ruleset_version='phase-13-joren-ruleset-1')
    assert settings.environment == 'production'
    assert 'planning_review_ruleset_version' not in Settings.model_fields


def test_ready_does_not_inspect_data_api_configuration_or_required_rpc():
    settings=Settings(_env_file=None, environment='local',supabase_url='https://nonexistent.invalid',
                      supabase_publishable_key='',supabase_secret_key='')
    assert build_readiness_response(settings).status == 'ready'
