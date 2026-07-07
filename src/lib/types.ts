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
  store_assignments: unknown[]
}

export interface Store {
  id: number
  name: string
  store_type: string
  is_active: boolean
}

export interface Product {
  id: number
  name: string
  category: ProductCategory | string
  unit: string
  is_active: boolean
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
