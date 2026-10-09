-- Keep collaborative tables API-only while making the intended service-role access
-- explicit to RLS inspection tools.
do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'shared_boards', 'dtable_rows', 'dtable_locks', 'mdtable_rows',
    'mdtable_columns', 'mdtable_cells', 'mdtable_locks', 'mftable_sections',
    'mftable_rows', 'mftable_containers', 'mtable_rows', 'board_snapshots'
  ]
  loop
    execute format(
      'create policy "FastAPI service role only" on public.%I for all to service_role using (true) with check (true)',
      table_name
    );
  end loop;
end
$$;

create index shared_boards_updated_by_idx on public.shared_boards (updated_by);
create index dtable_rows_created_by_idx on public.dtable_rows (created_by);
create index dtable_rows_updated_by_idx on public.dtable_rows (updated_by);
create index dtable_rows_deleted_by_idx on public.dtable_rows (deleted_by);
create index dtable_locks_updated_by_idx on public.dtable_locks (updated_by);
create index mdtable_rows_created_by_idx on public.mdtable_rows (created_by);
create index mdtable_rows_updated_by_idx on public.mdtable_rows (updated_by);
create index mdtable_rows_deleted_by_idx on public.mdtable_rows (deleted_by);
create index mdtable_columns_created_by_idx on public.mdtable_columns (created_by);
create index mdtable_columns_updated_by_idx on public.mdtable_columns (updated_by);
create index mdtable_columns_deleted_by_idx on public.mdtable_columns (deleted_by);
create index mdtable_cells_board_id_idx on public.mdtable_cells (board_id);
create index mdtable_cells_updated_by_idx on public.mdtable_cells (updated_by);
create index mdtable_locks_updated_by_idx on public.mdtable_locks (updated_by);
create index mftable_sections_created_by_idx on public.mftable_sections (created_by);
create index mftable_sections_updated_by_idx on public.mftable_sections (updated_by);
create index mftable_sections_deleted_by_idx on public.mftable_sections (deleted_by);
create index mftable_rows_board_id_idx on public.mftable_rows (board_id);
create index mftable_rows_created_by_idx on public.mftable_rows (created_by);
create index mftable_rows_updated_by_idx on public.mftable_rows (updated_by);
create index mftable_rows_deleted_by_idx on public.mftable_rows (deleted_by);
create index mftable_containers_board_id_idx on public.mftable_containers (board_id);
create index mftable_containers_created_by_idx on public.mftable_containers (created_by);
create index mftable_containers_updated_by_idx on public.mftable_containers (updated_by);
create index mftable_containers_deleted_by_idx on public.mftable_containers (deleted_by);
create index mtable_rows_created_by_idx on public.mtable_rows (created_by);
create index mtable_rows_updated_by_idx on public.mtable_rows (updated_by);
create index mtable_rows_deleted_by_idx on public.mtable_rows (deleted_by);
create index board_snapshots_created_by_idx on public.board_snapshots (created_by);
