-- Real pgTAP found four new V2 business preconditions using serialization errors,
-- contrary to the established nonretryable HTTP 409 contract. Keep each guard
-- and its state checks; change only the SQLSTATE. Never edit historical files.
do $$
declare v_signature text; v_definition text;
begin
  foreach v_signature in array array[
    'public.confirm_workout_registration(uuid,uuid,integer,text)',
    'private.guard_skipped_workout_activity()',
    'public.create_weekly_plan_proposal_v4(uuid,jsonb)',
    'private.guard_realized_v2_plan_approval()'
  ] loop
    v_definition := pg_get_functiondef(v_signature::regprocedure);
    if position('errcode = ''40001''' in v_definition) = 0 then
      raise exception 'V2 conflict function differs from the reviewed candidate';
    end if;
    execute replace(v_definition, 'errcode = ''40001''', 'errcode = ''PT409''');
  end loop;
end;
$$;
