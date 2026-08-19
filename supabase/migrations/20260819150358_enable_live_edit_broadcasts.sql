drop policy if exists "okiari users can send board broadcasts" on realtime.messages;

create policy "okiari users can send board broadcasts"
on realtime.messages
for insert
to authenticated
with check (
  extension = 'broadcast'
  and (select realtime.topic()) like 'board:%'
  and exists (
    select 1
    from public.app_users u
    where u.id = (select auth.uid())
      and u.is_active = true
  )
);
