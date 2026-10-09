-- Realtime clients only need authenticated read access. Application writes continue to
-- pass through FastAPI, where role and store assignment checks are enforced.
revoke all privileges on all tables in schema public from anon;

revoke all privileges on all tables in schema public from authenticated;

grant select on table
  public.app_roles,
  public.app_users,
  public.stores,
  public.products,
  public.user_store_assignments,
  public.meal_reports,
  public.restock_reports,
  public.inventory_checks,
  public.inventories
to authenticated;

alter table public.meal_reports enable row level security;
alter table public.restock_reports enable row level security;
alter table public.inventory_checks enable row level security;
alter table public.inventories enable row level security;

create index if not exists user_store_assignments_realtime_access_idx
  on public.user_store_assignments (user_id, store_id, can_view, can_edit);

-- Align the database role code with the application role code (`sub_leader`).
drop policy if exists "users can insert assigned meal reports" on public.meal_reports;
create policy "users can insert assigned meal reports"
on public.meal_reports
for insert
to authenticated
with check (
  public.current_app_role() = any (array['admin', 'leader', 'sub_leader'])
  and (
    public.current_app_role() = 'admin'
    or exists (
      select 1
      from public.user_store_assignments usa
      where usa.user_id = (select auth.uid())
        and usa.store_id = meal_reports.store_id
        and usa.can_edit = true
    )
  )
  and reported_by = (select auth.uid())
);

drop policy if exists "users can update assigned meal reports" on public.meal_reports;
create policy "users can update assigned meal reports"
on public.meal_reports
for update
to authenticated
using (
  public.current_app_role() = 'admin'
  or (
    public.current_app_role() = any (array['leader', 'sub_leader'])
    and exists (
      select 1
      from public.user_store_assignments usa
      where usa.user_id = (select auth.uid())
        and usa.store_id = meal_reports.store_id
        and usa.can_edit = true
    )
  )
)
with check (
  public.current_app_role() = 'admin'
  or (
    public.current_app_role() = any (array['leader', 'sub_leader'])
    and exists (
      select 1
      from public.user_store_assignments usa
      where usa.user_id = (select auth.uid())
        and usa.store_id = meal_reports.store_id
        and usa.can_edit = true
    )
  )
);

drop policy if exists "users can create assigned restock reports" on public.restock_reports;
create policy "users can create assigned restock reports"
on public.restock_reports
for insert
to authenticated
with check (
  public.current_app_role() = any (array['admin', 'leader', 'sub_leader'])
  and (
    public.current_app_role() = 'admin'
    or exists (
      select 1
      from public.user_store_assignments usa
      where usa.user_id = (select auth.uid())
        and usa.store_id = restock_reports.store_id
        and usa.can_edit = true
    )
  )
  and requested_by = (select auth.uid())
  and status = 'requested'
  and completed_at is null
  and completed_by is null
);

drop policy if exists "users can insert assigned inventory checks" on public.inventory_checks;
create policy "users can insert assigned inventory checks"
on public.inventory_checks
for insert
to authenticated
with check (
  public.current_app_role() = any (array['admin', 'leader', 'sub_leader'])
  and (
    public.current_app_role() = 'admin'
    or exists (
      select 1
      from public.user_store_assignments usa
      where usa.user_id = (select auth.uid())
        and usa.store_id = inventory_checks.store_id
        and usa.can_edit = true
    )
  )
  and checked_by = (select auth.uid())
  and is_confirmed = false
);

-- Postgres Changes only publishes explicitly enabled tables.
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'meal_reports'
  ) then
    alter publication supabase_realtime add table public.meal_reports;
  end if;
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'restock_reports'
  ) then
    alter publication supabase_realtime add table public.restock_reports;
  end if;
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'inventory_checks'
  ) then
    alter publication supabase_realtime add table public.inventory_checks;
  end if;
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'inventories'
  ) then
    alter publication supabase_realtime add table public.inventories;
  end if;
end
$$;
