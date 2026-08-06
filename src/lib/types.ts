export type RoleCode = 'admin' | 'leader' | 'sub_leader' | 'viewer'
export type ProductCategory = 'meal' | 'drink' | 'inventory'
export type RestockStatus = 'requested' | 'working' | 'completed' | 'cancelled'

export interface Role {
  id: number
  code: RoleCode | string
  name: string
  description?: string | null
  created_at?: string | null
}

export interface AppUser {
  id: string
  display_name: string | null
  email: string
  role_id: number
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
  role?: Role | null
}

export interface MeResponse {
  user: AppUser
  role: Role
  store_assignments: StoreAssignment[]
}

export interface StoreAssignment {
  store_id: number
  can_view: boolean
  can_edit: boolean
}

export interface Store {
  id: number
  name: string
  store_type: string
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface Product {
  id: number
  name: string
  category: ProductCategory | string
  unit: string
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface MealReport {
  id: number
  report_date: string
  store_id: number
  product_id: number
  quantity: number
  reported_by?: string | null
  note?: string | null
  created_at?: string | null
  updated_at?: string | null
  store?: Store | null
  product?: Product | null
}

export interface RestockReport {
  id: number
  requested_at: string
  completed_at?: string | null
  store_id: number
  product_id: number
  quantity: number
  status: RestockStatus
  requested_by?: string | null
  completed_by?: string | null
  note?: string | null
  created_at?: string | null
  updated_at?: string | null
  store?: Store | null
  product?: Product | null
}

export interface InventoryCheck {
  id: number
  check_date: string
  store_id: number
  product_id: number
  expected_quantity: number
  actual_quantity: number
  difference?: number | null
  checked_by?: string | null
  is_confirmed: boolean
  note?: string | null
  created_at?: string | null
  store?: Store | null
  product?: Product | null
}

export interface SharedBoard {
  id: number
  key: 'drink-refill' | 'meal-drink' | 'meal-food' | 'inventory'
  revision: number
  updated_at: string
}

export interface DTableRow {
  id: number
  board_id: number
  store_id: number
  scope: 'drink' | 'consumable'
  item_name: string
  max_quantity: number
  requested_quantity: number
  note: string
  status: 'pending' | 'out_of_stock' | 'completed'
  sort_order: number
  updated_at: string
}

export interface DTableLock {
  id: number
  store_id: number
  scope: 'drink' | 'consumable'
  column_key: 'status' | 'name' | 'max_quantity' | 'requested_quantity' | 'note'
  is_locked: boolean
}

export interface MDTableRow {
  id: number
  board_id: number
  floor_group: 'first' | 'second' | 'third'
  booth_type: '' | 'first' | 'second' | 'third'
  booth: string
  custom_booth: string
  sort_order: number
}

export interface MDTableColumn {
  id: number
  board_id: number
  floor_group: 'first' | 'second' | 'third'
  title: string
  sort_order: number
}

export interface MDTableCell {
  id: number
  board_id: number
  row_id: number
  column_id: number
  value: string
  updated_at: string
}

export interface MDTableLock {
  id: number
  floor_group: 'first' | 'second' | 'third'
  column_key: 'booth'
  is_locked: boolean
}

export interface MFTableSection {
  id: number
  board_id: number
  store_id: number | null
  store_name: string
  sort_order: number
}

export interface MFTableRow {
  id: number
  board_id: number
  section_id: number
  icon: string
  item_name: string
  subtext: string
  note: string
  sort_order: number
}

export interface MFTableContainer {
  id: number
  board_id: number
  row_id: number
  name: string
  container_type: 'insulated_box' | 'food_warmer' | 'register'
  quantity: number
  sort_order: number
}

export interface MTableRow {
  id: number
  board_id: number
  store_id: number
  product_id: number
  expected_quantity: number
  actual_quantity: number
  difference: number
  note: string
  is_confirmed: boolean
  sort_order: number
  updated_at: string
}

export interface DrinkBoardData {
  board: SharedBoard
  dtable_rows: DTableRow[]
  dtable_locks: DTableLock[]
}

export interface MealDrinkBoardData {
  board: SharedBoard
  mdtable_rows: MDTableRow[]
  mdtable_columns: MDTableColumn[]
  mdtable_cells: MDTableCell[]
  mdtable_locks: MDTableLock[]
}

export interface MealFoodBoardData {
  board: SharedBoard
  mftable_sections: MFTableSection[]
  mftable_rows: MFTableRow[]
  mftable_containers: MFTableContainer[]
}

export interface InventoryBoardData {
  board: SharedBoard
  mtable_rows: MTableRow[]
}
