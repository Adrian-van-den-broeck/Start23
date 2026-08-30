begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;
select plan(18);

select has_column(
  'public', 'plan_revisions', 'available_dates',
  'plan revisions persist canonical available dates'
);
select col_type_is(
  'public', 'plan_revisions', 'available_dates', 'date[]',
  'available dates use a date array'
);
select has_column(
  'public', 'plan_revisions', 'availability_source',
  'explicit availability provenance is persisted'
);
select has_column(
  'public', 'planned_workouts', 'scheduled_date',
  'planned workouts persist an athlete-local date'
);
select col_type_is(
  'public', 'planned_workouts', 'scheduled_date', 'date',
  'planned workout scheduling is date-only'
);
select has_trigger(
  'public', 'plan_revisions', 'plan_revisions_set_phase_10_dates',
  'revision date invariants are trigger-enforced'
);
select has_trigger(
  'public', 'planned_workouts', 'planned_workouts_set_phase_10_date',
  'planned workout dates are backfilled and checked'
);

select has_function(
  'public', 'get_previous_week_available_dates', array['uuid', 'date'],
  'explicit previous-week reuse has a bounded RPC'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.get_previous_week_available_dates(uuid,date)',
    'execute'
  ),
  'trusted backend can copy previous-week dates'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.get_previous_week_available_dates(uuid,date)',
    'execute'
  ),
  'athletes cannot bypass the backend reuse contract'
);
select has_function(
  'public', 'get_plan_revision_context_for_planning',
  array['uuid', 'uuid', 'integer'],
  'exact pending revision context has a bounded RPC'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.get_plan_revision_context_for_planning(uuid,uuid,integer)',
    'execute'
  ),
  'private pending-revision facts are not client-callable'
);
select has_function(
  'public', 'move_planned_workout',
  array['uuid', 'uuid', 'integer', 'date', 'jsonb'],
  'athlete moves use a date-only backend RPC'
);
select hasnt_function(
  'public', 'move_planned_workout',
  array['uuid', 'uuid', 'integer', 'timestamp with time zone', 'jsonb'],
  'the athlete-facing move RPC no longer accepts a timestamp'
);
select has_function(
  'public', 'get_calendar', array['date', 'date'],
  'calendar reads use date boundaries'
);
select hasnt_function(
  'public', 'get_calendar',
  array['timestamp with time zone', 'timestamp with time zone'],
  'calendar reads no longer accept timestamp boundaries'
);
select ok(
  position(
    '''scheduled_date''' in pg_get_functiondef(
      'public.get_weekly_plan(uuid,integer)'::regprocedure
    )
  ) > 0
  and position(
    '''scheduled_at''' in pg_get_functiondef(
      'public.get_weekly_plan(uuid,integer)'::regprocedure
    )
  ) = 0,
  'weekly-plan JSON exposes dates and no scheduled timestamp'
);
select ok(
  position(
    '''scheduled_date''' in pg_get_functiondef(
      'public.get_calendar(date,date)'::regprocedure
    )
  ) > 0
  and position(
    '''scheduled_at''' in pg_get_functiondef(
      'public.get_calendar(date,date)'::regprocedure
    )
  ) = 0,
  'calendar JSON exposes dates and no scheduled timestamp'
);

select * from finish();
rollback;
