-- The original candidate compiles but fails on its first pending-revision edit:
-- subtraction binds before JSON extraction (unknown - unknown, SQLSTATE 42725).
-- Correct only those two expressions; retain the original reviewed candidate.
do $$
declare v_definition text;
begin
  v_definition := pg_get_functiondef(
    'public.create_v6_weekly_plan_proposal(uuid,jsonb)'::regprocedure);
  if position('v_prior.payload -> ''v6_frozen_snapshot'' -' in v_definition) = 0
    or position('p_payload -> ''v6_frozen_snapshot'' -' in v_definition) = 0 then
    raise exception 'V6 writer definition differs from the reviewed candidate';
  end if;
  v_definition := replace(v_definition,
    'v_prior.payload -> ''v6_frozen_snapshot'' -',
    '(v_prior.payload -> ''v6_frozen_snapshot'') -');
  v_definition := replace(v_definition,
    'p_payload -> ''v6_frozen_snapshot'' -',
    '(p_payload -> ''v6_frozen_snapshot'') -');
  execute v_definition;
end;
$$;
