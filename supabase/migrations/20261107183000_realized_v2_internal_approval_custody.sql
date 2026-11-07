-- Real execution found that v16's owner-bound approval path calls service-only
-- v15 -> v14 -> v13 guards and always fails for the authenticated owner.
-- Extend the INTERNAL identity checks to match v16; EXECUTE stays service-only.
-- No grants, RLS policies, historical values, queries or calculations change.
do $$
declare v_version integer; v_definition text;
  v_guard text := 'if coalesce((select auth.jwt() ->> ''role''), '''') <> ''service_role'' then';
begin
  foreach v_version in array array[13,14,15] loop
    v_definition := pg_get_functiondef(format(
      'public.get_plan_load_history_for_planning_v%s(uuid,date)', v_version)::regprocedure);
    if position(v_guard in v_definition) = 0 then
      raise exception 'History reader differs from the reviewed prerequisite';
    end if;
    v_definition := replace(v_definition, v_guard,
      'if coalesce((select auth.jwt() ->> ''role''), '''') <> ''service_role''
        and (select auth.uid()) is distinct from p_athlete_id then');
    execute v_definition;
  end loop;
end;
$$;
