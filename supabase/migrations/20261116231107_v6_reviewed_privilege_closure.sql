-- Forward-only least-privilege correction. Owner approval still required for production.
-- Do not touch platform-owned schemas/default ACLs or historical function bodies.
-- Dxtm is unrelated to supported catalog reads; TRUNCATE bypasses row security.
revoke truncate, references, trigger, maintain on table
  public.workout_templates, public.workout_segments,
  public.workout_template_phase_tags, public.workout_template_zone_requirements
  from service_role;
-- Only application-owner defaults in the exposed application schema are corrected.
-- Provider-owned storage/auth/realtime/graphql defaults are deliberately untouched.
alter default privileges for role postgres in schema public
  revoke truncate, references, trigger, maintain on tables from anon, authenticated, service_role;
-- Close SQL NULL bypass of the existing preference CAS precondition.
create or replace function public.save_frequency_preferences(p_expected_revision integer, p_operation_id uuid, p_preferences jsonb)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare owner uuid := private.current_athlete_id(); old private.frequency_preferences; current_revision integer; total integer;
begin
  if owner is null then raise exception 'authentication required' using errcode = '42501'; end if;
  if p_expected_revision is null or p_expected_revision < 0 or p_operation_id is null then
    raise exception 'frequency preference precondition required' using errcode='23514';
  end if;
  perform private.lock_frequency(owner);
  if jsonb_typeof(p_preferences) is distinct from 'object' or
    (select array_agg(k order by k) from jsonb_object_keys(p_preferences) k) is distinct from array['bike','run','swim'] then
    raise exception 'invalid frequency preference' using errcode = '23514';
  end if;
  if exists (select 1 from jsonb_each(p_preferences) e where e.value <> 'null'::jsonb and
    (e.value::text !~ '^(0|[1-9][0-9]*)$' or length(e.value::text) > 2)) then
    raise exception 'invalid frequency preference' using errcode = '23514';
  end if;
  select coalesce(sum(case when value = 'null'::jsonb then 0 else value::text::integer end),0)
    into total from jsonb_each(p_preferences);
  if total > 24 then raise exception 'technical frequency input envelope exceeded' using errcode = '23514'; end if;
  select * into old from private.frequency_preferences where athlete_id = owner and operation_id = p_operation_id;
  if found then
    if old.preferences <> p_preferences or old.revision <> p_expected_revision + 1 or old.change_reference <> 'athlete_confirmation' then
      raise exception 'frequency operation conflict' using errcode = 'PT409';
    end if;
    return jsonb_build_object('revision',old.revision,'operation_id',old.operation_id,'preferences',old.preferences,
      'confirmed_at',old.confirmed_at,'recorded_at',old.recorded_at,'reconfirmation_required',old.reconfirm_sports);
  end if;
  select coalesce(max(revision),0) into current_revision from private.frequency_preferences where athlete_id = owner;
  if current_revision <> p_expected_revision then raise exception 'frequency preference changed' using errcode = 'PT409'; end if;
  insert into private.frequency_preferences(athlete_id,revision,operation_id,preferences,confirmed_at,confirmation_actor,change_reference)
    values(owner,current_revision+1,p_operation_id,p_preferences,clock_timestamp(),owner,'athlete_confirmation');
  return private.frequency_preference(owner);
end $$;
revoke all on function public.get_checkin_plan_proposal(uuid) from public, anon;
grant execute on function public.get_checkin_plan_proposal(uuid) to authenticated;
revoke all on function public.create_activity_summary_v2(uuid,text,jsonb) from public, anon;
grant execute on function public.create_activity_summary_v2(uuid,text,jsonb) to authenticated;
revoke all on function public.get_workout_registration(uuid) from public, anon;
grant execute on function public.get_workout_registration(uuid) to authenticated;
revoke all on function public.confirm_workout_registration(uuid,uuid,integer,text) from public, anon;
grant execute on function public.confirm_workout_registration(uuid,uuid,integer,text) to authenticated;
revoke all on function public.get_v6_weekly_plan(uuid,integer) from public, anon;
grant execute on function public.get_v6_weekly_plan(uuid,integer) to authenticated;
revoke all on function public.get_v6_mobile_weekly_plan(uuid,integer) from public, anon;
grant execute on function public.get_v6_mobile_weekly_plan(uuid,integer) to authenticated;
revoke all on function public.get_v6_mobile_calendar(date,date) from public, anon;
grant execute on function public.get_v6_mobile_calendar(date,date) to authenticated;
revoke all on function public.get_v6_move_workout_context(uuid) from public, anon;
grant execute on function public.get_v6_move_workout_context(uuid) to authenticated;
revoke all on function private.v6_revision_workouts(uuid) from public, anon;
grant execute on function private.v6_revision_workouts(uuid) to authenticated;
revoke all on function public.get_frequency_preferences() from public, anon;
grant execute on function public.get_frequency_preferences() to authenticated;
revoke all on function public.save_frequency_preferences(integer,uuid,jsonb) from public, anon;
grant execute on function public.save_frequency_preferences(integer,uuid,jsonb) to authenticated;
revoke all on function public.report_frequency_interruption(uuid,text,text) from public, anon;
grant execute on function public.report_frequency_interruption(uuid,text,text) to authenticated;
revoke all on function public.get_v6_frequency_swipe_receipt(uuid) from public, anon;
grant execute on function public.get_v6_frequency_swipe_receipt(uuid) to authenticated;
-- Keep the private invoker dependency callable; no private table/view grant.
-- No role membership, enrollment, authorization decision or source activation.
notify pgrst, 'reload schema';
