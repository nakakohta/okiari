import { api } from '@/lib/api'
import type {
  AppUser,
  InventoryCheck,
  MealReport,
  Product,
  ProductCategory,
  RestockReport,
  RestockStatus,
  Role,
  Store,
} from '@/lib/types'

export const mastersService = {
  async stores() {
    const { data } = await api.get<Store[]>('/stores')
    return data
  },
  async products(category: ProductCategory) {
    const { data } = await api.get<Product[]>('/products', { params: { category } })
    return data
  },
}

export const userService = {
  async list() {
    const { data } = await api.get<AppUser[]>('/users')
    return data
  },
  async create(payload: {
    display_name: string
    email: string
    password: string
    role_id: number
    is_active: boolean
  }) {
    const { data } = await api.post<AppUser>('/users', payload)
    return data
  },
  async updateRole(userId: string, roleId: number) {
    const { data } = await api.patch<AppUser>(`/users/${userId}/role`, { role_id: roleId })
    return data
  },
  async updateStatus(userId: string, isActive: boolean) {
    const { data } = await api.patch<AppUser>(`/users/${userId}/status`, { is_active: isActive })
    return data
  },
}

export const roleService = {
  async list() {
    const { data } = await api.get<Role[]>('/roles')
    return data
  },
  async create(payload: { code: string; name: string; description?: string | null }) {
    const { data } = await api.post<Role>('/roles', payload)
    return data
  },
  async update(roleId: number, payload: { code?: string; name?: string; description?: string | null }) {
    const { data } = await api.patch<Role>(`/roles/${roleId}`, payload)
    return data
  },
  async remove(roleId: number) {
    await api.delete(`/roles/${roleId}`)
  },
}

export const reportService = {
  async mealReports() {
    const { data } = await api.get<MealReport[]>('/meal-reports')
    return data
  },
  async createMealReport(payload: {
    report_date: string
    store_id: number
    product_id: number
    quantity: number
    note?: string | null
  }) {
    const { data } = await api.post<MealReport>('/meal-reports', payload)
    return data
  },
  async drinkRefills() {
    const { data } = await api.get<RestockReport[]>('/drink-refills')
    return data
  },
  async createDrinkRefill(payload: {
    store_id: number
    product_id: number
    quantity: number
    note?: string | null
  }) {
    const { data } = await api.post<RestockReport>('/drink-refills', payload)
    return data
  },
  async updateDrinkStatus(reportId: number, status: RestockStatus) {
    const { data } = await api.patch<RestockReport>(`/drink-refills/${reportId}/status`, { status })
    return data
  },
  async inventoryChecks() {
    const { data } = await api.get<InventoryCheck[]>('/inventory-checks')
    return data
  },
  async createInventoryCheck(payload: {
    check_date: string
    store_id: number
    product_id: number
    expected_quantity?: number | null
    actual_quantity: number
    is_confirmed: boolean
    note?: string | null
  }) {
    const { data } = await api.post<InventoryCheck>('/inventory-checks', payload)
    return data
  },
}
