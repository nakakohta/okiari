-- Keep the global store master intact because meal reports and inventory use it.
-- These fields control only the stores shown on the drink-refill board.
alter table public.stores
  add column if not exists drink_refill_visible boolean not null default false,
  add column if not exists drink_refill_sort_order integer;

update public.stores
set
  drink_refill_visible = false,
  drink_refill_sort_order = null;

update public.stores
set
  drink_refill_visible = true,
  drink_refill_sort_order = case name
    when 'フード売店' then 10
    when 'CSL' then 20
    when 'VIP(ブルー)' then 30
    when 'VIP(レッド)' then 40
    when '2-1（DS含）' then 100
    when '2-2（DS含）' then 110
    when '2-7（DS含）' then 120
    when '2-8（DS含）' then 130
    when '3-1' then 200
    when '3-5' then 210
    when '3-9' then 220
    when '3-11' then 230
    when '3-11(スイートラウンジ)' then 240
    when 'その他' then 900
  end
where name in (
  'フード売店',
  'CSL',
  'VIP(ブルー)',
  'VIP(レッド)',
  '2-1（DS含）',
  '2-2（DS含）',
  '2-7（DS含）',
  '2-8（DS含）',
  '3-1',
  '3-5',
  '3-9',
  '3-11',
  '3-11(スイートラウンジ)',
  'その他'
);

alter table public.stores
  drop constraint if exists stores_drink_refill_order_check;

alter table public.stores
  add constraint stores_drink_refill_order_check
  check (not drink_refill_visible or drink_refill_sort_order is not null);
