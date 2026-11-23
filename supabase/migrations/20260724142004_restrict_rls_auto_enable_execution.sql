-- public.rls_auto_enable() is Supabase's automatic-RLS event trigger function.
-- It is created by the hosted platform, not by any migration in this repo, so a
-- fresh database (Database CI, local `supabase db start`) does not have it.
-- The revoke only runs when the function exists. On hosted this migration was
-- already applied unconditionally and is not re-run, so hosted behavior is
-- unchanged; this guard only lets the migration chain replay on a fresh database.
do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke execute
    on function public.rls_auto_enable()
    from public, anon, authenticated;
  end if;
end
$$;
