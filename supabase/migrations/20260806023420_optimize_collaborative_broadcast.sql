-- Broadcast the changed normalized record so connected clients can merge it
-- directly instead of all refetching the complete board after every keystroke.
create or replace function private.notify_board_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_new jsonb;
  v_old jsonb;
  v_board_id bigint;
  v_board_key text;
  v_revision bigint;
  v_actor uuid;
begin
  if tg_op <> 'DELETE' then
    v_new := to_jsonb(new);
  end if;
  if tg_op <> 'INSERT' then
    v_old := to_jsonb(old);
  end if;

  v_board_id := coalesce(
    nullif(v_new ->> 'board_id', '')::bigint,
    nullif(v_old ->> 'board_id', '')::bigint
  );
  v_actor := coalesce(
    nullif(v_new ->> 'updated_by', '')::uuid,
    nullif(v_new ->> 'created_by', '')::uuid,
    nullif(v_new ->> 'deleted_by', '')::uuid,
    nullif(v_old ->> 'updated_by', '')::uuid
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
        'operation', tg_op,
        'record', v_new,
        'oldRecord', v_old
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
