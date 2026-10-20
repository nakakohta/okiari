-- PR #12 collaborative tables. Application writes are performed by FastAPI with
-- the service-role key; browser clients only receive private Realtime broadcasts.

create table public.shared_boards (
  id bigint generated always as identity primary key,
  key text not null unique,
  revision bigint not null default 0 check (revision >= 0),
  updated_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint shared_boards_key_check check (
    key = any (array['drink-refill', 'meal-drink', 'meal-food', 'inventory'])
  )
);

create table public.dtable_rows (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  store_id bigint not null references public.stores(id),
  scope text not null check (scope = any (array['drink', 'consumable'])),
  item_name text not null default '',
  max_quantity integer not null default 0 check (max_quantity >= 0),
  requested_quantity integer not null default 0 check (requested_quantity >= 0),
  note text not null default '',
  status text not null default 'pending' check (
    status = any (array['pending', 'out_of_stock', 'completed'])
  ),
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.dtable_locks (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  store_id bigint not null references public.stores(id),
  scope text not null check (scope = any (array['drink', 'consumable'])),
  column_key text not null check (
    column_key = any (array['status', 'name', 'max_quantity', 'requested_quantity', 'note'])
  ),
  is_locked boolean not null default false,
  updated_by uuid references public.app_users(id),
  updated_at timestamptz not null default now(),
  unique (board_id, store_id, scope, column_key)
);

create table public.mdtable_rows (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  floor_group text not null check (floor_group = any (array['first', 'second', 'third'])),
  booth_type text not null default '' check (booth_type = any (array['', 'first', 'second', 'third'])),
  booth text not null default '',
  custom_booth text not null default '',
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.mdtable_columns (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  floor_group text not null check (floor_group = any (array['first', 'second', 'third'])),
  title text not null default '',
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.mdtable_cells (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  row_id bigint not null references public.mdtable_rows(id) on delete cascade,
  column_id bigint not null references public.mdtable_columns(id) on delete cascade,
  value text not null default '',
  updated_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (row_id, column_id)
);

create table public.mdtable_locks (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  floor_group text not null check (floor_group = any (array['first', 'second', 'third'])),
  column_key text not null default 'booth' check (column_key = 'booth'),
  is_locked boolean not null default false,
  updated_by uuid references public.app_users(id),
  updated_at timestamptz not null default now(),
  unique (board_id, floor_group, column_key)
);

create table public.mftable_sections (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  store_id bigint references public.stores(id),
  store_name text not null default 'CSL',
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.mftable_rows (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  section_id bigint not null references public.mftable_sections(id) on delete cascade,
  icon text not null default '🍛',
  item_name text not null default '',
  subtext text not null default '',
  note text not null default '',
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.mftable_containers (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  row_id bigint not null references public.mftable_rows(id) on delete cascade,
  name text not null default '',
  container_type text not null default 'register' check (
    container_type = any (array['insulated_box', 'food_warmer', 'register'])
  ),
  quantity integer not null default 0 check (
    quantity >= 0 and (container_type = 'register' or quantity <= 100)
  ),
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.mtable_rows (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  store_id bigint not null references public.stores(id),
  product_id bigint not null references public.products(id),
  expected_quantity integer not null default 0 check (expected_quantity >= 0),
  actual_quantity integer not null default 0 check (actual_quantity >= 0),
  difference integer generated always as (actual_quantity - expected_quantity) stored,
  is_confirmed boolean not null default false,
  note text not null default '',
  sort_order integer not null default 0,
  created_by uuid references public.app_users(id),
  updated_by uuid references public.app_users(id),
  deleted_by uuid references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table public.board_snapshots (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  revision bigint not null default 0,
  reason text not null,
  snapshot jsonb not null,
  created_by uuid not null references public.app_users(id),
  created_at timestamptz not null default now()
);

create index dtable_rows_scope_idx on public.dtable_rows (board_id, store_id, scope, sort_order)
  where deleted_at is null;
create index dtable_rows_store_id_idx on public.dtable_rows (store_id);
create index dtable_locks_store_id_idx on public.dtable_locks (store_id);
create index mdtable_rows_group_idx on public.mdtable_rows (board_id, floor_group, sort_order)
  where deleted_at is null;
create index mdtable_columns_group_idx on public.mdtable_columns (board_id, floor_group, sort_order)
  where deleted_at is null;
create index mdtable_cells_row_id_idx on public.mdtable_cells (row_id);
create index mdtable_cells_column_id_idx on public.mdtable_cells (column_id);
create index mftable_sections_order_idx on public.mftable_sections (board_id, sort_order)
  where deleted_at is null;
create index mftable_sections_store_id_idx on public.mftable_sections (store_id);
create index mftable_rows_section_idx on public.mftable_rows (section_id, sort_order)
  where deleted_at is null;
create index mftable_containers_row_idx on public.mftable_containers (row_id, sort_order)
  where deleted_at is null;
create index mtable_rows_order_idx on public.mtable_rows (board_id, sort_order)
  where deleted_at is null;
create index mtable_rows_store_id_idx on public.mtable_rows (store_id);
create index mtable_rows_product_id_idx on public.mtable_rows (product_id);
create index board_snapshots_board_idx on public.board_snapshots (board_id, created_at desc);

alter table public.shared_boards enable row level security;
alter table public.dtable_rows enable row level security;
alter table public.dtable_locks enable row level security;
alter table public.mdtable_rows enable row level security;
alter table public.mdtable_columns enable row level security;
alter table public.mdtable_cells enable row level security;
alter table public.mdtable_locks enable row level security;
alter table public.mftable_sections enable row level security;
alter table public.mftable_rows enable row level security;
alter table public.mftable_containers enable row level security;
alter table public.mtable_rows enable row level security;
alter table public.board_snapshots enable row level security;

revoke all on table
  public.shared_boards,
  public.dtable_rows,
  public.dtable_locks,
  public.mdtable_rows,
  public.mdtable_columns,
  public.mdtable_cells,
  public.mdtable_locks,
  public.mftable_sections,
  public.mftable_rows,
  public.mftable_containers,
  public.mtable_rows,
  public.board_snapshots
from anon, authenticated;

grant all on table
  public.shared_boards,
  public.dtable_rows,
  public.dtable_locks,
  public.mdtable_rows,
  public.mdtable_columns,
  public.mdtable_cells,
  public.mdtable_locks,
  public.mftable_sections,
  public.mftable_rows,
  public.mftable_containers,
  public.mtable_rows,
  public.board_snapshots
to service_role;

grant usage, select on all sequences in schema public to service_role;

insert into public.shared_boards (key)
values ('drink-refill'), ('meal-drink'), ('meal-food'), ('inventory')
on conflict (key) do nothing;

insert into public.stores (name, store_type, is_active)
values
  ('CSL', 'booth', true),
  ('VIP(ブルー)', 'booth', true),
  ('VIP(レッド)', 'booth', true),
  ('2-1', 'booth', true), ('2-2', 'booth', true), ('2-3', 'booth', true),
  ('2-4', 'booth', true), ('2-5', 'booth', true), ('2-6', 'booth', true),
  ('2-7', 'booth', true), ('2-8', 'booth', true),
  ('3-1', 'booth', true), ('3-3', 'booth', true), ('3-5', 'booth', true),
  ('3-7', 'booth', true), ('3-9', 'booth', true), ('3-11', 'booth', true),
  ('3-11(スイートラウンジ)', 'booth', true),
  ('その他', 'booth', true)
on conflict (name) do update
set is_active = true, updated_at = now();

alter table public.products drop constraint if exists products_name_key;
create unique index if not exists products_category_name_idx
  on public.products (category, name);

insert into public.products (category, name, unit, is_active)
values
  ('inventory', '水', '本', true),
  ('inventory', 'コーラ', '本', true),
  ('inventory', 'お茶', '本', true),
  ('inventory', 'ポップコーン 塩', '袋', true),
  ('inventory', 'ポップコーン キャラメル', '袋', true),
  ('inventory', 'ポップコーン MIX', '袋', true)
on conflict (category, name) do update
set unit = excluded.unit, is_active = true, updated_at = now();

-- Seed the same blank/default state that PR #12 rendered locally.
insert into public.dtable_rows (board_id, store_id, scope, sort_order)
select b.id, s.id, scopes.scope, 0
from public.shared_boards b
cross join public.stores s
cross join (values ('drink'), ('consumable')) as scopes(scope)
where b.key = 'drink-refill'
  and s.is_active = true
  and not exists (
    select 1 from public.dtable_rows r
    where r.board_id = b.id and r.store_id = s.id and r.scope = scopes.scope
  );

insert into public.dtable_locks (board_id, store_id, scope, column_key)
select b.id, s.id, scopes.scope, columns.column_key
from public.shared_boards b
cross join public.stores s
cross join (values ('drink'), ('consumable')) as scopes(scope)
cross join (values ('status'), ('name'), ('max_quantity'), ('requested_quantity'), ('note')) as columns(column_key)
where b.key = 'drink-refill'
  and s.is_active = true
on conflict (board_id, store_id, scope, column_key) do nothing;

-- Best-effort import of existing reports. Existing tables remain untouched.
insert into public.dtable_rows (
  board_id, store_id, scope, item_name, requested_quantity, note, status,
  sort_order, created_by, updated_by, created_at, updated_at
)
select
  b.id, rr.store_id, 'drink', p.name, rr.quantity, coalesce(rr.note, ''),
  case rr.status
    when 'completed' then 'completed'
    when 'cancelled' then 'out_of_stock'
    else 'pending'
  end,
  row_number() over (partition by rr.store_id order by rr.created_at, rr.id)::integer,
  rr.requested_by, coalesce(rr.completed_by, rr.requested_by), rr.created_at, rr.updated_at
from public.restock_reports rr
join public.products p on p.id = rr.product_id
cross join public.shared_boards b
where b.key = 'drink-refill';

insert into public.mdtable_rows (board_id, floor_group, sort_order)
select b.id, groups.floor_group, 0
from public.shared_boards b
cross join (values ('first'), ('second'), ('third')) as groups(floor_group)
where b.key = 'meal-drink'
  and not exists (
    select 1 from public.mdtable_rows r
    where r.board_id = b.id and r.floor_group = groups.floor_group
  );

insert into public.mdtable_columns (board_id, floor_group, title, sort_order)
select b.id, groups.floor_group, '商品名1', 0
from public.shared_boards b
cross join (values ('first'), ('second'), ('third')) as groups(floor_group)
where b.key = 'meal-drink'
  and not exists (
    select 1 from public.mdtable_columns c
    where c.board_id = b.id and c.floor_group = groups.floor_group
  );

insert into public.mdtable_cells (board_id, row_id, column_id)
select r.board_id, r.id, c.id
from public.mdtable_rows r
join public.mdtable_columns c
  on c.board_id = r.board_id and c.floor_group = r.floor_group
where r.deleted_at is null and c.deleted_at is null
on conflict (row_id, column_id) do nothing;

insert into public.mdtable_locks (board_id, floor_group)
select b.id, groups.floor_group
from public.shared_boards b
cross join (values ('first'), ('second'), ('third')) as groups(floor_group)
where b.key = 'meal-drink'
on conflict (board_id, floor_group, column_key) do nothing;

insert into public.mdtable_columns (board_id, floor_group, title, sort_order)
select b.id, groups.floor_group, p.name, row_number() over (partition by groups.floor_group order by p.id)::integer
from public.shared_boards b
cross join (values ('first'), ('second'), ('third')) as groups(floor_group)
join public.products p on p.category = 'meal' and p.is_active = true
where b.key = 'meal-drink'
  and not exists (
    select 1 from public.mdtable_columns c
    where c.board_id = b.id and c.floor_group = groups.floor_group and c.title = p.name
  );

insert into public.mdtable_rows (board_id, floor_group, booth_type, booth, sort_order)
select
  b.id,
  case when s.name like '2-%' then 'second' when s.name like '3-%' then 'third' else 'first' end,
  case when s.name like '2-%' then 'second' when s.name like '3-%' then 'third' else 'first' end,
  s.name,
  row_number() over (partition by case when s.name like '2-%' then 'second' when s.name like '3-%' then 'third' else 'first' end order by s.id)::integer
from public.shared_boards b
join (select distinct store_id from public.meal_reports) mr on true
join public.stores s on s.id = mr.store_id
where b.key = 'meal-drink'
  and not exists (
    select 1 from public.mdtable_rows r
    where r.board_id = b.id and r.booth = s.name and r.deleted_at is null
  );

insert into public.mdtable_cells (board_id, row_id, column_id, value, updated_by, updated_at)
select r.board_id, r.id, c.id, latest.quantity::text, latest.reported_by, latest.updated_at
from public.mdtable_rows r
join public.mdtable_columns c on c.board_id = r.board_id and c.floor_group = r.floor_group
join public.products p on p.name = c.title and p.category = 'meal'
join public.stores s on s.name = r.booth
join lateral (
  select mr.quantity, mr.reported_by, mr.updated_at
  from public.meal_reports mr
  where mr.store_id = s.id and mr.product_id = p.id
  order by mr.report_date desc, mr.updated_at desc limit 1
) latest on true
on conflict (row_id, column_id) do update
set value = excluded.value, updated_by = excluded.updated_by, updated_at = excluded.updated_at;

insert into public.mtable_rows (
  board_id, store_id, product_id, expected_quantity, actual_quantity, is_confirmed,
  note, sort_order, created_by, updated_by, created_at, updated_at
)
select
  b.id, ic.store_id, ic.product_id, ic.expected_quantity, ic.actual_quantity,
  ic.is_confirmed, coalesce(ic.note, ''),
  row_number() over (order by ic.check_date, ic.created_at, ic.id)::integer,
  ic.checked_by, ic.checked_by, ic.created_at, ic.updated_at
from public.inventory_checks ic
cross join public.shared_boards b
where b.key = 'inventory';

do $$
declare
  v_board_id bigint;
  v_section_id bigint;
  v_row_id bigint;
begin
  select id into v_board_id from public.shared_boards where key = 'meal-food';
  select id into v_section_id
  from public.mftable_sections
  where board_id = v_board_id and deleted_at is null
  order by sort_order, id limit 1;

  if v_section_id is null then
    insert into public.mftable_sections (board_id, store_id, store_name, sort_order)
    select v_board_id, id, 'CSL', 0 from public.stores where name = 'CSL'
    returning id into v_section_id;
  end if;

  select id into v_row_id
  from public.mftable_rows
  where section_id = v_section_id and deleted_at is null
  order by sort_order, id limit 1;

  if v_row_id is null then
    insert into public.mftable_rows (board_id, section_id, icon, item_name, subtext, sort_order)
    values (v_board_id, v_section_id, '🍛', 'ライス', 'ごはん系', 0)
    returning id into v_row_id;

    insert into public.mftable_containers
      (board_id, row_id, name, container_type, quantity, sort_order)
    values
      (v_board_id, v_row_id, '', 'insulated_box', 100, 0),
      (v_board_id, v_row_id, '', 'insulated_box', 100, 1);
  end if;
end
$$;

create schema if not exists private;

create or replace function private.notify_board_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_board_id bigint;
  v_board_key text;
  v_revision bigint;
  v_actor uuid;
begin
  v_board_id := coalesce(
    nullif(to_jsonb(new) ->> 'board_id', '')::bigint,
    nullif(to_jsonb(old) ->> 'board_id', '')::bigint
  );
  v_actor := coalesce(
    nullif(to_jsonb(new) ->> 'updated_by', '')::uuid,
    nullif(to_jsonb(new) ->> 'created_by', '')::uuid,
    nullif(to_jsonb(new) ->> 'deleted_by', '')::uuid,
    nullif(to_jsonb(old) ->> 'updated_by', '')::uuid
  );

  update public.shared_boards
  set revision = revision + 1,
      updated_at = now(),
      updated_by = coalesce(v_actor, updated_by)
  where id = v_board_id
  returning key, revision into v_board_key, v_revision;

  if v_board_key is not null then
    perform realtime.send(
      jsonb_build_object(
        'boardKey', v_board_key,
        'revision', v_revision,
        'table', tg_table_name,
        'operation', tg_op
      ),
      'changed',
      'board:' || v_board_key,
      true
    );
  end if;

  return null;
end;
$$;

revoke all on function private.notify_board_change() from public, anon, authenticated;

create trigger dtable_rows_board_change after insert or update or delete on public.dtable_rows
for each row execute function private.notify_board_change();
create trigger dtable_locks_board_change after insert or update or delete on public.dtable_locks
for each row execute function private.notify_board_change();
create trigger mdtable_rows_board_change after insert or update or delete on public.mdtable_rows
for each row execute function private.notify_board_change();
create trigger mdtable_columns_board_change after insert or update or delete on public.mdtable_columns
for each row execute function private.notify_board_change();
create trigger mdtable_cells_board_change after insert or update or delete on public.mdtable_cells
for each row execute function private.notify_board_change();
create trigger mdtable_locks_board_change after insert or update or delete on public.mdtable_locks
for each row execute function private.notify_board_change();
create trigger mftable_sections_board_change after insert or update or delete on public.mftable_sections
for each row execute function private.notify_board_change();
create trigger mftable_rows_board_change after insert or update or delete on public.mftable_rows
for each row execute function private.notify_board_change();
create trigger mftable_containers_board_change after insert or update or delete on public.mftable_containers
for each row execute function private.notify_board_change();
create trigger mtable_rows_board_change after insert or update or delete on public.mtable_rows
for each row execute function private.notify_board_change();

drop policy if exists "okiari users can receive board broadcasts" on realtime.messages;
create policy "okiari users can receive board broadcasts"
on realtime.messages
for select
to authenticated
using (
  extension = 'broadcast'
  and (select realtime.topic()) like 'board:%'
  and exists (
    select 1 from public.app_users u
    where u.id = (select auth.uid()) and u.is_active = true
  )
);
