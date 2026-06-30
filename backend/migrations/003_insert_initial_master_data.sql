-- v1 temporary master data.
-- products.name is too strict for the current manual data because the same
-- product name can appear in meal, drink, and inventory categories.
alter table public.products drop constraint if exists products_name_key;
create unique index if not exists products_category_name_idx on public.products (category, name);

insert into public.stores (name, store_type, is_active)
values
  ('ドリンク売店', 'booth', true),
  ('フード売店', 'booth', true),
  ('ポップコーン売店', 'booth', true),
  ('DS倉庫', 'warehouse', true),
  ('CSL', 'booth', true),
  ('2-1（DS含）', 'booth', true),
  ('2-2（DS含）', 'booth', true),
  ('2-7（DS含）', 'booth', true),
  ('2-8（DS含）', 'booth', true),
  ('3-1', 'booth', true),
  ('3-5', 'booth', true),
  ('3-9', 'booth', true),
  ('3-11', 'booth', true),
  ('サウス', 'booth', true),
  ('インカム室', 'booth', true),
  ('3-9DS', 'booth', true)
on conflict (name) do update
set
  store_type = excluded.store_type,
  is_active = excluded.is_active,
  updated_at = now();

insert into public.products (category, name, unit, is_active)
values
  ('meal', '水', '食', true),
  ('meal', 'コーラ', '食', true),
  ('meal', 'お茶', '食', true),
  ('meal', 'ポップコーン 塩', '食', true),
  ('meal', 'ポップコーン キャラメル', '食', true),
  ('meal', 'ポップコーン MIX', '食', true),
  ('drink', '水', '本', true),
  ('drink', 'コーラ', '本', true),
  ('drink', 'お茶', '本', true),
  ('inventory', '水', '本', true),
  ('inventory', 'コーラ', '本', true),
  ('inventory', 'お茶', '本', true),
  ('inventory', 'ポップコーン 塩', '袋', true),
  ('inventory', 'ポップコーン キャラメル', '袋', true),
  ('inventory', 'ポップコーン MIX', '袋', true)
on conflict (category, name) do update
set
  unit = excluded.unit,
  is_active = excluded.is_active,
  updated_at = now();
