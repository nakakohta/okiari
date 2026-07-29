import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import type { AppUser, MeResponse, Role, StoreAssignment } from '@/lib/types'

export const useAuthStore = defineStore('auth', () => {
  const initialized = ref(false)
  const loading = ref(false)
  const role = ref<string | null>(null)
  const roleDetail = ref<Role | null>(null)
  const user = ref<AppUser | null>(null)
  const storeAssignments = ref<StoreAssignment[]>([])

  const isAuthenticated = computed(() => Boolean(user.value))
  const canManage = computed(() => role.value === 'admin')
  const canEditReports = computed(() => ['admin', 'leader', 'sub_leader'].includes(role.value || ''))

  function reset() {
    role.value = null
    roleDetail.value = null
    user.value = null
    storeAssignments.value = []
  }

  async function fetchMe() {
    const { data } = await api.get<MeResponse>('/auth/me')
    user.value = data.user
    roleDetail.value = data.role
    role.value = data.role.code
    storeAssignments.value = data.store_assignments
    return data
  }

  function canViewStore(storeId: number) {
    return role.value === 'admin' || storeAssignments.value.some(
      (assignment) => assignment.store_id === storeId && assignment.can_view,
    )
  }

  function canEditStore(storeId: number) {
    return role.value === 'admin' || (
      canEditReports.value && storeAssignments.value.some(
        (assignment) => assignment.store_id === storeId && assignment.can_edit,
      )
    )
  }

  async function initialize() {
    if (initialized.value) return
    initialized.value = true
    const { data } = await supabase.auth.getSession()
    if (!data.session) {
      reset()
      return
    }
    try {
      await fetchMe()
    } catch {
      reset()
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) {
        return { success: false, error: 'メールアドレスまたはパスワードが正しくありません' }
      }
      await fetchMe()
      return { success: true }
    } catch {
      reset()
      return { success: false, error: 'ログイン情報を取得できませんでした' }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await supabase.auth.signOut()
    reset()
  }

  return {
    initialized,
    loading,
    role,
    roleDetail,
    user,
    storeAssignments,
    isAuthenticated,
    canManage,
    canEditReports,
    canViewStore,
    canEditStore,
    initialize,
    fetchMe,
    login,
    logout,
  }
})
