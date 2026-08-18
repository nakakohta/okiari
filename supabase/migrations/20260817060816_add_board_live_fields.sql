-- Ephemeral, server-authoritative values used by the shared FastAPI WebSocket.
-- Browser clients never access this table directly.
create table public.board_live_fields (
  id bigint generated always as identity primary key,
  board_id bigint not null references public.shared_boards(id) on delete cascade,
  resource text not null check (
    resource = any (array[
      'd-rows', 'md-rows', 'md-columns', 'md-cells',
      'mf-rows', 'mf-containers', 'm-rows'
    ])
  ),
  record_id bigint not null,
  field text not null,
  value jsonb not null,
  revision bigint not null check (revision > 0),
  updated_by uuid not null references public.app_users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (board_id, resource, record_id, field)
);

alter table public.board_live_fields enable row level security;

revoke all on table public.board_live_fields from anon, authenticated;
revoke all on sequence public.board_live_fields_id_seq from anon, authenticated;
grant select, insert, update, delete on table public.board_live_fields to service_role;
grant usage, select on sequence public.board_live_fields_id_seq to service_role;

create policy "FastAPI service role only"
on public.board_live_fields
for all
to service_role
using (true)
with check (true);

create index board_live_fields_board_revision_idx
  on public.board_live_fields (board_id, revision desc);

create index board_live_fields_updated_by_idx
  on public.board_live_fields (updated_by);
