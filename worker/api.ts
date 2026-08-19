import { createClient, type SupabaseClient } from '@supabase/supabase-js'

export interface ApiEnv {
  SUPABASE_URL?: string
  SUPABASE_PUBLISHABLE_KEY?: string
  SUPABASE_SERVICE_ROLE_KEY?: string
  SUPABASE_SECRET_KEY?: string
}

type JsonRecord = Record<string, unknown>
type RoleCode = 'admin' | 'leader' | 'sub_leader' | 'viewer'

interface StoreAssignment {
  store_id: number
  can_view: boolean
  can_edit: boolean
}

interface AuthContext {
  client: SupabaseClient
  userId: string
  profile: JsonRecord
  role: JsonRecord
  roleCode: RoleCode
  assignments: StoreAssignment[]
}

class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
  }
}

const BOARD_TABLES: Record<string, string[]> = {
  'drink-refill': ['dtable_rows', 'dtable_locks'],
  'meal-drink': ['mdtable_rows', 'mdtable_columns', 'mdtable_cells', 'mdtable_locks'],
  'meal-food': ['mftable_sections', 'mftable_rows', 'mftable_containers'],
  inventory: ['mtable_rows'],
}

const RESOURCE_TABLES: Record<string, string> = {
  'd-rows': 'dtable_rows',
  'md-rows': 'mdtable_rows',
  'md-columns': 'mdtable_columns',
  'md-cells': 'mdtable_cells',
  'mf-sections': 'mftable_sections',
  'mf-rows': 'mftable_rows',
  'mf-containers': 'mftable_containers',
  'm-rows': 'mtable_rows',
}

const RESOURCE_BOARDS: Record<string, string> = {
  'd-rows': 'drink-refill',
  'md-rows': 'meal-drink',
  'md-columns': 'meal-drink',
  'md-cells': 'meal-drink',
  'mf-sections': 'meal-food',
  'mf-rows': 'meal-food',
  'mf-containers': 'meal-food',
  'm-rows': 'inventory',
}

const WRITE_FIELDS: Record<string, Set<string>> = {
  'd-rows': new Set(['store_id', 'scope', 'item_name', 'max_quantity', 'requested_quantity', 'note', 'status', 'sort_order']),
  'md-rows': new Set(['floor_group', 'booth_type', 'booth', 'custom_booth', 'sort_order']),
  'md-columns': new Set(['floor_group', 'title', 'sort_order']),
  'md-cells': new Set(['row_id', 'column_id', 'value']),
  'mf-sections': new Set(['store_id', 'store_name', 'sort_order']),
  'mf-rows': new Set(['section_id', 'icon', 'item_name', 'subtext', 'note', 'sort_order']),
  'mf-containers': new Set(['row_id', 'name', 'container_type', 'quantity', 'sort_order']),
  'm-rows': new Set(['store_id', 'product_id', 'expected_quantity', 'actual_quantity', 'note', 'is_confirmed', 'sort_order']),
}

const IMMUTABLE_FIELDS: Record<string, Set<string>> = {
  'd-rows': new Set(['store_id', 'scope']),
  'md-rows': new Set(['floor_group']),
  'md-columns': new Set(['floor_group']),
  'md-cells': new Set(['row_id', 'column_id']),
  'mf-sections': new Set(),
  'mf-rows': new Set(['section_id']),
  'mf-containers': new Set(['row_id']),
  'm-rows': new Set(),
}

const STORE_SELECT = 'id,name,store_type,is_active,drink_refill_visible,drink_refill_sort_order,created_at,updated_at'
const PRODUCT_SELECT = 'id,name,category,unit,is_active,created_at,updated_at'
const REPORT_STORE_SELECT = 'id,name,store_type,is_active,created_at,updated_at'
const REPORT_PRODUCT_SELECT = 'id,name,category,unit,is_active,created_at,updated_at'
const REPORT_USER_SELECT = 'id,display_name,email'
const MEAL_SELECT = `id,report_date,store_id,product_id,quantity,reported_by,note,created_at,updated_at,store:stores(${REPORT_STORE_SELECT}),product:products(${REPORT_PRODUCT_SELECT}),reporter:app_users!meal_reports_reported_by_fkey(${REPORT_USER_SELECT})`
const RESTOCK_SELECT = `id,requested_at,completed_at,store_id,product_id,quantity,status,requested_by,completed_by,note,created_at,updated_at,store:stores(${REPORT_STORE_SELECT}),product:products(${REPORT_PRODUCT_SELECT}),requested_by_user:app_users!restock_reports_requested_by_fkey(${REPORT_USER_SELECT}),completed_by_user:app_users!restock_reports_completed_by_fkey(${REPORT_USER_SELECT})`
const INVENTORY_CHECK_SELECT = `id,check_date,store_id,product_id,expected_quantity,actual_quantity,difference,checked_by,is_confirmed,note,created_at,updated_at,store:stores(${REPORT_STORE_SELECT}),product:products(${REPORT_PRODUCT_SELECT}),checker:app_users!inventory_checks_checked_by_fkey(${REPORT_USER_SELECT})`

function bearerToken(request: Request) {
  const match = (request.headers.get('Authorization') || '').match(/^Bearer\s+(.+)$/i)
  return match?.[1] || ''
}

function serviceKey(env: ApiEnv) {
  return env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY || ''
}

function assertConfigured(env: ApiEnv) {
  if (!env.SUPABASE_URL || !serviceKey(env)) {
    throw new ApiError(503, 'Database service is not configured')
  }
}

async function requireAuth(request: Request, env: ApiEnv): Promise<AuthContext> {
  assertConfigured(env)
  const token = bearerToken(request)
  if (!token) throw new ApiError(401, 'Not authenticated')

  const client = createClient(env.SUPABASE_URL!, serviceKey(env), {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
  })
  const { data: authData, error: authError } = await client.auth.getUser(token)
  if (authError || !authData.user) throw new ApiError(401, 'Not authenticated')

  const { data: profile, error: profileError } = await client
    .from('app_users')
    .select('id,display_name,email,role_id,is_active,created_at,updated_at,role:app_roles(id,code,name,description,created_at)')
    .eq('id', authData.user.id)
    .maybeSingle()
  if (profileError) throw new ApiError(503, 'User profile could not be loaded')
  if (!profile) throw new ApiError(403, 'Authenticated user is not registered')
  if (profile.is_active === false) throw new ApiError(403, 'Inactive user')

  const roleValue = profile.role as JsonRecord | JsonRecord[] | null
  const role = (Array.isArray(roleValue) ? roleValue[0] : roleValue) || {}
  const roleCode = role.code
  if (!['admin', 'leader', 'sub_leader', 'viewer'].includes(String(roleCode))) {
    throw new ApiError(403, 'User role is not configured')
  }

  const { data: assignments, error: assignmentError } = await client
    .from('user_store_assignments')
    .select('store_id,can_view,can_edit')
    .eq('user_id', authData.user.id)
  if (assignmentError) throw new ApiError(503, 'Store assignments could not be loaded')

  return {
    client,
    userId: authData.user.id,
    profile: profile as JsonRecord,
    role,
    roleCode: roleCode as RoleCode,
    assignments: (assignments || []) as StoreAssignment[],
  }
}

function requireRoles(context: AuthContext, ...roles: RoleCode[]) {
  if (!roles.includes(context.roleCode)) throw new ApiError(403, 'Forbidden')
}

function canAccessStore(context: AuthContext, storeId: number, edit = false, board = false) {
  if (context.roleCode === 'admin' || (board && context.roleCode === 'leader')) return true
  return context.assignments.some((item) => item.store_id === storeId && (edit ? item.can_edit : item.can_view))
}

function requireStoreAccess(context: AuthContext, storeId: number | null, edit = false, board = false) {
  if (context.roleCode === 'admin' || (board && context.roleCode === 'leader')) return
  if (storeId === null || !canAccessStore(context, storeId, edit, board)) {
    throw new ApiError(403, 'Store permission is required')
  }
}

function now() {
  return new Date().toISOString()
}

function asRecord(value: unknown): JsonRecord {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new ApiError(400, 'Invalid request body')
  return value as JsonRecord
}

async function body(request: Request) {
  try {
    return asRecord(await request.json())
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(400, 'Invalid JSON body')
  }
}

function ensureResult<T>(data: T | null, error: { message: string } | null, message: string): T {
  if (error) {
    console.error(message, error.message)
    throw new ApiError(502, message)
  }
  if (data === null) throw new ApiError(404, 'Record not found')
  return data
}

async function getBoard(context: AuthContext, key: string) {
  if (!BOARD_TABLES[key]) throw new ApiError(404, 'Board not found')
  const result = await context.client
    .from('shared_boards')
    .select('id,key,revision,updated_at')
    .eq('key', key)
    .maybeSingle()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Board could not be loaded')
}

async function getRow(context: AuthContext, table: string, id: number) {
  const result = await context.client.from(table).select('*').eq('id', id).maybeSingle()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Row could not be loaded')
}

async function activeRows(context: AuthContext, table: string, boardId: number) {
  let query = context.client.from(table).select('*').eq('board_id', boardId)
  if (table !== 'mdtable_cells' && !['dtable_locks', 'mdtable_locks'].includes(table)) {
    query = query.is('deleted_at', null)
  }
  const orderColumn = ['mdtable_cells', 'dtable_locks', 'mdtable_locks'].includes(table) ? 'id' : 'sort_order'
  const result = await query.order(orderColumn)
  return ensureResult(result.data as JsonRecord[] | null, result.error, 'Board rows could not be loaded')
}

function resolveResource(boardKey: string, resource: string) {
  const table = RESOURCE_TABLES[resource]
  if (!table || RESOURCE_BOARDS[resource] !== boardKey) throw new ApiError(404, 'Board resource not found')
  return table
}

function validateValues(resource: string, values: JsonRecord, create: boolean) {
  const allowed = WRITE_FIELDS[resource]
  if (!allowed) throw new ApiError(404, 'Board resource not found')
  const unknown = Object.keys(values).filter((key) => !allowed.has(key))
  if (unknown.length) throw new ApiError(400, `Unsupported fields: ${unknown.join(', ')}`)
  if (!Object.keys(values).length) throw new ApiError(400, 'No values were supplied')
  if (!create && Object.keys(values).some((key) => IMMUTABLE_FIELDS[resource].has(key))) {
    throw new ApiError(400, 'Relationship fields cannot be changed')
  }
  if ('status' in values && !['pending', 'out_of_stock', 'completed'].includes(String(values.status))) {
    throw new ApiError(400, 'Invalid restock status')
  }
  if ('container_type' in values && !['insulated_box', 'food_warmer', 'register'].includes(String(values.container_type))) {
    throw new ApiError(400, 'Invalid container type')
  }
  for (const field of ['max_quantity', 'requested_quantity', 'quantity', 'expected_quantity', 'actual_quantity', 'sort_order']) {
    if (!(field in values)) continue
    const value = values[field]
    if (!Number.isInteger(value) || Number(value) < 0 || Number(value) > 2_147_483_647) {
      throw new ApiError(400, `${field} must be a non-negative integer`)
    }
  }
  return values
}

async function resourceStore(context: AuthContext, resource: string, values: JsonRecord, existing: JsonRecord = {}) {
  const source = { ...existing, ...values }
  if (['d-rows', 'mf-sections', 'm-rows'].includes(resource)) return Number(source.store_id)
  if (resource === 'mf-rows') {
    const section = await getRow(context, 'mftable_sections', Number(source.section_id))
    return Number(section.store_id)
  }
  if (resource === 'mf-containers') {
    const row = await getRow(context, 'mftable_rows', Number(source.row_id))
    const section = await getRow(context, 'mftable_sections', Number(row.section_id))
    return Number(section.store_id)
  }
  if (resource === 'md-rows' || resource === 'md-cells') {
    const row = resource === 'md-cells'
      ? await getRow(context, 'mdtable_rows', Number(source.row_id))
      : source
    const booth = String(row.booth || '')
    if (!booth || booth === 'その他') return null
    const result = await context.client.from('stores').select('id').eq('name', booth).maybeSingle()
    if (result.error) throw new ApiError(502, 'Store could not be resolved')
    return result.data ? Number(result.data.id) : null
  }
  return null
}

async function requireBoardWrite(context: AuthContext, resource: string, values: JsonRecord, existing: JsonRecord = {}) {
  requireRoles(context, 'admin', 'leader', 'sub_leader')
  if (resource === 'md-columns' && context.roleCode === 'sub_leader') throw new ApiError(403, 'Forbidden')
  requireStoreAccess(context, await resourceStore(context, resource, values, existing), true, true)
  if (context.roleCode === 'sub_leader' && resource === 'm-rows' && existing.is_confirmed) {
    throw new ApiError(403, 'Confirmed inventory rows cannot be edited')
  }
  if (resource === 'm-rows' && 'is_confirmed' in values && values.is_confirmed !== existing.is_confirmed) {
    requireRoles(context, 'admin', 'leader')
  }
}

async function replaceInventory(context: AuthContext, row: JsonRecord) {
  if (!row.is_confirmed) return
  const storeId = Number(row.store_id)
  const productId = Number(row.product_id)
  const existing = await context.client
    .from('inventories')
    .select('id')
    .eq('store_id', storeId)
    .eq('product_id', productId)
    .maybeSingle()
  if (existing.error) throw new ApiError(502, 'Inventory could not be loaded')
  const values = { quantity: Number(row.actual_quantity), updated_by: context.userId, updated_at: now() }
  const result = existing.data
    ? await context.client.from('inventories').update(values).eq('id', existing.data.id)
    : await context.client.from('inventories').insert({ store_id: storeId, product_id: productId, ...values })
  if (result.error) throw new ApiError(502, 'Inventory could not be saved')
}

async function readBoard(context: AuthContext, key: string) {
  const board = await getBoard(context, key)
  const entries = await Promise.all(
    BOARD_TABLES[key].map(async (table) => [table, await activeRows(context, table, Number(board.id))] as const),
  )
  return { board, ...Object.fromEntries(entries) }
}

async function createBoardResource(context: AuthContext, key: string, resource: string, request: Request) {
  const table = resolveResource(key, resource)
  const board = await getBoard(context, key)
  const payload = await body(request)
  const values = validateValues(resource, asRecord(payload.values), true)
  await requireBoardWrite(context, resource, values)
  const insert = { ...values, board_id: board.id, created_by: context.userId, updated_by: context.userId }
  const query = resource === 'md-cells'
    ? context.client.from(table).upsert(insert, { onConflict: 'board_id,row_id,column_id' }).select('*').single()
    : context.client.from(table).insert(insert).select('*').single()
  const result = await query
  const created = ensureResult(result.data as JsonRecord | null, result.error, 'Row could not be created')
  if (resource === 'm-rows') await replaceInventory(context, created)
  return created
}

async function updateBoardResource(context: AuthContext, key: string, resource: string, id: number, request: Request) {
  const table = resolveResource(key, resource)
  const board = await getBoard(context, key)
  const existing = await getRow(context, table, id)
  if (Number(existing.board_id) !== Number(board.id) || existing.deleted_at) throw new ApiError(404, 'Row not found')
  const payload = await body(request)
  const values = validateValues(resource, asRecord(payload.values), false)
  await requireBoardWrite(context, resource, values, existing)
  const result = await context.client
    .from(table)
    .update({ ...values, updated_by: context.userId, updated_at: now() })
    .eq('id', id)
    .select('*')
    .single()
  const updated = ensureResult(result.data as JsonRecord | null, result.error, 'Row could not be updated')
  if (resource === 'm-rows') await replaceInventory(context, updated)
  return updated
}

async function deleteBoardResource(context: AuthContext, key: string, resource: string, id: number) {
  requireRoles(context, 'admin')
  const table = resolveResource(key, resource)
  const board = await getBoard(context, key)
  const existing = await getRow(context, table, id)
  if (Number(existing.board_id) !== Number(board.id)) throw new ApiError(404, 'Row not found')
  const result = await context.client
    .from(table)
    .update({ deleted_at: now(), deleted_by: context.userId, updated_by: context.userId, updated_at: now() })
    .eq('id', id)
    .select('*')
    .single()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Row could not be deleted')
}

async function reorderBoardResource(context: AuthContext, key: string, resource: string, request: Request) {
  const table = resolveResource(key, resource)
  const board = await getBoard(context, key)
  const payload = await body(request)
  if (!Array.isArray(payload.items)) throw new ApiError(400, 'Invalid reorder request')
  for (const raw of payload.items) {
    const item = asRecord(raw)
    const existing = await getRow(context, table, Number(item.id))
    if (Number(existing.board_id) !== Number(board.id)) throw new ApiError(404, 'Row not found')
    await requireBoardWrite(context, resource, {}, existing)
    const result = await context.client
      .from(table)
      .update({ sort_order: Number(item.sort_order), updated_by: context.userId, updated_at: now() })
      .eq('id', Number(item.id))
    if (result.error) throw new ApiError(502, 'Order could not be saved')
  }
  return { ok: true }
}

async function updateBoardLock(context: AuthContext, key: string, request: Request) {
  requireRoles(context, 'admin', 'leader')
  const board = await getBoard(context, key)
  const payload = await body(request)
  let table: string
  let onConflict: string
  let values: JsonRecord
  if (key === 'drink-refill') {
    values = { board_id: board.id, store_id: payload.store_id, scope: payload.scope, column_key: payload.column_key }
    table = 'dtable_locks'
    onConflict = 'board_id,store_id,scope,column_key'
  } else if (key === 'meal-drink') {
    values = { board_id: board.id, floor_group: payload.floor_group, column_key: payload.column_key }
    table = 'mdtable_locks'
    onConflict = 'board_id,floor_group,column_key'
  } else {
    throw new ApiError(400, 'This board has no shared locks')
  }
  const result = await context.client
    .from(table)
    .upsert({ ...values, is_locked: Boolean(payload.is_locked), updated_by: context.userId, updated_at: now() }, { onConflict })
    .select('*')
    .single()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Lock could not be saved')
}

async function clearBoard(context: AuthContext, key: string, request: Request) {
  requireRoles(context, 'admin')
  const board = await getBoard(context, key)
  const payload = await body(request)
  const common = { updated_by: context.userId, updated_at: now() }
  if (key === 'drink-refill') {
    const result = await context.client.from('dtable_rows')
      .update({ ...common, status: 'pending', requested_quantity: 0, note: '' })
      .eq('board_id', board.id).eq('store_id', payload.store_id).eq('scope', payload.scope).is('deleted_at', null)
    if (result.error) throw new ApiError(502, 'Board could not be cleared')
  } else if (key === 'meal-drink') {
    const rows = await context.client.from('mdtable_rows').select('id').eq('board_id', board.id).eq('floor_group', payload.floor_group).is('deleted_at', null)
    if (rows.error) throw new ApiError(502, 'Board could not be cleared')
    const ids = (rows.data || []).map((item) => item.id)
    if (ids.length) {
      const result = await context.client.from('mdtable_cells').update({ ...common, value: '' }).eq('board_id', board.id).in('row_id', ids)
      if (result.error) throw new ApiError(502, 'Board could not be cleared')
    }
  } else if (key === 'inventory') {
    const result = await context.client.from('mtable_rows')
      .update({ ...common, actual_quantity: 0, note: '', is_confirmed: false })
      .eq('board_id', board.id).is('deleted_at', null)
    if (result.error) throw new ApiError(502, 'Board could not be cleared')
  } else if (key === 'meal-food') {
    const [rows, containers] = await Promise.all([
      context.client.from('mftable_rows').update({ ...common, note: '' }).eq('board_id', board.id).is('deleted_at', null),
      context.client.from('mftable_containers').update({ ...common, quantity: 0 }).eq('board_id', board.id).is('deleted_at', null),
    ])
    if (rows.error || containers.error) throw new ApiError(502, 'Board could not be cleared')
  } else {
    throw new ApiError(404, 'Board not found')
  }
  return { ok: true }
}

function allowedStoreIds(context: AuthContext, edit = false) {
  if (context.roleCode === 'admin') return null
  return context.assignments.filter((item) => edit ? item.can_edit : item.can_view).map((item) => item.store_id)
}

async function readReports(context: AuthContext, table: string, select: string, order: string, url: URL) {
  const ids = allowedStoreIds(context)
  if (ids?.length === 0) return []
  let query = context.client.from(table).select(select)
  if (ids) query = query.in('store_id', ids)
  if (table === 'meal_reports' && url.searchParams.get('report_date')) {
    query = query.eq('report_date', url.searchParams.get('report_date')!)
  }
  const result = await query.order(order, { ascending: false }).limit(500)
  return ensureResult(result.data as JsonRecord[] | null, result.error, 'Reports could not be loaded')
}

async function requireActiveRecord(context: AuthContext, table: 'stores' | 'products', id: number, category?: string) {
  let query = context.client.from(table).select('id').eq('id', id).eq('is_active', true)
  if (category) query = query.eq('category', category)
  const result = await query.maybeSingle()
  if (result.error || !result.data) throw new ApiError(404, `Active ${table === 'stores' ? 'store' : 'product'} not found`)
}

async function createReport(context: AuthContext, table: string, select: string, request: Request, category: string) {
  requireRoles(context, 'admin', 'leader', 'sub_leader')
  const payload = await body(request)
  const storeId = Number(payload.store_id)
  const productId = Number(payload.product_id)
  requireStoreAccess(context, storeId, true)
  await Promise.all([
    requireActiveRecord(context, 'stores', storeId),
    requireActiveRecord(context, 'products', productId, category),
  ])
  const actorField = table === 'meal_reports' ? 'reported_by' : table === 'restock_reports' ? 'requested_by' : 'checked_by'
  const insert = { ...payload, [actorField]: context.userId }
  const result = await context.client.from(table).insert(insert).select(select).single()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Report could not be created')
}

async function updateReport(context: AuthContext, table: string, select: string, id: number, request: Request, statusOnly = false) {
  requireRoles(context, 'admin', 'leader', 'sub_leader')
  const existing = await getRow(context, table, id)
  requireStoreAccess(context, Number(existing.store_id), true)
  const payload = await body(request)
  const updates: JsonRecord = { ...payload, updated_at: now() }
  if (table === 'meal_reports') updates.reported_by = context.userId
  if (table === 'inventory_checks') updates.checked_by = context.userId
  if (table === 'restock_reports') {
    const status = String(statusOnly ? payload.status : payload.status || existing.status)
    if (status === 'completed') {
      updates.completed_at = now()
      updates.completed_by = context.userId
    } else if (['requested', 'working', 'cancelled'].includes(status)) {
      updates.completed_at = null
      updates.completed_by = null
    }
  }
  const result = await context.client.from(table).update(updates).eq('id', id).select(select).single()
  const updated = ensureResult(result.data as JsonRecord | null, result.error, 'Report could not be updated')
  if (table === 'inventory_checks' && updated.is_confirmed) await replaceInventory(context, updated)
  return updated
}

async function upsertMealReport(context: AuthContext, request: Request) {
  requireRoles(context, 'admin', 'leader', 'sub_leader')
  const payload = await body(request)
  const storeId = Number(payload.store_id)
  const productId = Number(payload.product_id)
  requireStoreAccess(context, storeId, true)
  await Promise.all([
    requireActiveRecord(context, 'stores', storeId),
    requireActiveRecord(context, 'products', productId, 'meal'),
  ])
  const result = await context.client.from('meal_reports')
    .upsert({ ...payload, reported_by: context.userId, updated_at: now() }, { onConflict: 'report_date,store_id,product_id' })
    .select(MEAL_SELECT).single()
  return ensureResult(result.data as JsonRecord | null, result.error, 'Meal report could not be saved')
}

async function route(context: AuthContext, request: Request, url: URL): Promise<unknown> {
  const { pathname } = url
  if ((pathname === '/auth/me' || pathname === '/me') && request.method === 'GET') {
    return { user: context.profile, role: context.role, store_assignments: context.assignments }
  }
  if (pathname === '/stores' && request.method === 'GET') {
    const result = await context.client.from('stores').select(STORE_SELECT).eq('is_active', true).order('name')
    return ensureResult(result.data as JsonRecord[] | null, result.error, 'Stores could not be loaded')
  }
  if (pathname === '/products' && request.method === 'GET') {
    let query = context.client.from('products').select(PRODUCT_SELECT).eq('is_active', true)
    const category = url.searchParams.get('category')
    if (category) query = query.eq('category', category)
    const result = await query.order('category').order('name')
    return ensureResult(result.data as JsonRecord[] | null, result.error, 'Products could not be loaded')
  }

  if (pathname === '/meal-reports' && request.method === 'GET') return readReports(context, 'meal_reports', MEAL_SELECT, 'report_date', url)
  if (pathname === '/meal-reports' && request.method === 'POST') return createReport(context, 'meal_reports', MEAL_SELECT, request, 'meal')
  if (pathname === '/meal-reports/cell' && request.method === 'PUT') return upsertMealReport(context, request)
  if (pathname === '/drink-refills' && request.method === 'GET') return readReports(context, 'restock_reports', RESTOCK_SELECT, 'requested_at', url)
  if (pathname === '/drink-refills' && request.method === 'POST') return createReport(context, 'restock_reports', RESTOCK_SELECT, request, 'drink')
  if (pathname === '/inventory-checks' && request.method === 'GET') return readReports(context, 'inventory_checks', INVENTORY_CHECK_SELECT, 'check_date', url)
  if (pathname === '/inventory-checks' && request.method === 'POST') return createReport(context, 'inventory_checks', INVENTORY_CHECK_SELECT, request, 'inventory')

  const mealUpdate = pathname.match(/^\/meal-reports\/(\d+)$/)
  if (mealUpdate && request.method === 'PATCH') return updateReport(context, 'meal_reports', MEAL_SELECT, Number(mealUpdate[1]), request)
  const refillStatus = pathname.match(/^\/drink-refills\/(\d+)\/status$/)
  if (refillStatus && request.method === 'PATCH') return updateReport(context, 'restock_reports', RESTOCK_SELECT, Number(refillStatus[1]), request, true)
  const refillUpdate = pathname.match(/^\/drink-refills\/(\d+)$/)
  if (refillUpdate && request.method === 'PATCH') return updateReport(context, 'restock_reports', RESTOCK_SELECT, Number(refillUpdate[1]), request)
  const inventoryUpdate = pathname.match(/^\/inventory-checks\/(\d+)$/)
  if (inventoryUpdate && request.method === 'PATCH') return updateReport(context, 'inventory_checks', INVENTORY_CHECK_SELECT, Number(inventoryUpdate[1]), request)

  const clearMatch = pathname.match(/^\/boards\/([^/]+)\/actions\/clear$/)
  if (clearMatch && request.method === 'POST') return clearBoard(context, clearMatch[1], request)
  const lockMatch = pathname.match(/^\/boards\/([^/]+)\/lock$/)
  if (lockMatch && request.method === 'PUT') return updateBoardLock(context, lockMatch[1], request)
  const orderMatch = pathname.match(/^\/boards\/([^/]+)\/([^/]+)\/order$/)
  if (orderMatch && request.method === 'PUT') return reorderBoardResource(context, orderMatch[1], orderMatch[2], request)
  const rowMatch = pathname.match(/^\/boards\/([^/]+)\/([^/]+)\/(\d+)$/)
  if (rowMatch && request.method === 'PATCH') return updateBoardResource(context, rowMatch[1], rowMatch[2], Number(rowMatch[3]), request)
  if (rowMatch && request.method === 'DELETE') return deleteBoardResource(context, rowMatch[1], rowMatch[2], Number(rowMatch[3]))
  const resourceMatch = pathname.match(/^\/boards\/([^/]+)\/([^/]+)$/)
  if (resourceMatch && request.method === 'POST') return createBoardResource(context, resourceMatch[1], resourceMatch[2], request)
  const boardMatch = pathname.match(/^\/boards\/([^/]+)$/)
  if (boardMatch && request.method === 'GET') return readBoard(context, boardMatch[1])

  throw new ApiError(404, 'API route not found')
}

export async function handleApiRequest(request: Request, env: ApiEnv) {
  try {
    const context = await requireAuth(request, env)
    const result = await route(context, request, new URL(request.url))
    return Response.json(result)
  } catch (error) {
    if (error instanceof ApiError) return Response.json({ detail: error.message }, { status: error.status })
    console.error('Unhandled API error', error)
    return Response.json({ detail: 'Unexpected server error' }, { status: 500 })
  }
}
