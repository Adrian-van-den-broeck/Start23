-- Persist only the bounded public explanation for an already-created pending
-- weekly-plan proposal. The function cannot create, approve, or alter a plan.

create function public.set_weekly_plan_proposal_explanation(
  p_athlete_id uuid,
  p_proposal_id uuid,
  p_explanation text
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_explanation text := btrim(p_explanation);
  v_current text;
begin
  if coalesce((select auth.jwt() ->> 'role'), '') <> 'service_role' then
    raise exception 'trusted backend authorization required' using errcode = '42501';
  end if;
  if v_explanation is null
     or char_length(v_explanation) not between 1 and 900
     or v_explanation ~* '\m(tss|training[[:space:]]+stress[[:space:]]+score|planned[[:space:]]+load|realized[[:space:]]+load)\M' then
    raise exception 'public coach explanation is invalid' using errcode = '23514';
  end if;

  update public.change_proposals
  set public_explanation = v_explanation
  where id = p_proposal_id
    and athlete_id = p_athlete_id
    and kind = 'plan_revision'
    and state = 'pending'
    and public_explanation in (
      'A deterministic weekly plan is ready for review.',
      'A rest-only weekly revision is ready for review.'
    )
  returning public_explanation into v_current;

  if v_current is not null then
    return v_current;
  end if;

  select public_explanation into v_current
  from public.change_proposals
  where id = p_proposal_id
    and athlete_id = p_athlete_id
    and kind = 'plan_revision';
  if not found then
    raise exception 'weekly plan proposal not found' using errcode = 'P0002';
  end if;
  return v_current;
end;
$$;

revoke all on function public.set_weekly_plan_proposal_explanation(
  uuid, uuid, text
) from public, anon, authenticated, service_role;
grant execute on function public.set_weekly_plan_proposal_explanation(
  uuid, uuid, text
) to service_role;
