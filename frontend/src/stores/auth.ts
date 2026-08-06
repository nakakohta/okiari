import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import type { AppUser, MeResponse, Role } from '@/lib/types'

export const useAuthStore = defineStore('auth', () => {
  const initialized = ref(false)
  const loading = ref(false)
  const role = ref<string | null>(null)
  const roleDetail = ref<Role | null>(null)
  const user = ref<AppUser | null>(null)

  const isAuthenticated = computed(() => Boolean(user.value))
  const canManage = computed(() => role.value === 'admin')
  const canEditReports = computed(() => ['admin', 'leader', 'sub_leader'].includes(role.value || ''))

  function reset() {
    role.value = null
    roleDetail.value = null
    user.value = null
  }

  async function fetchMe() {
    const { data } = await api.get<MeResponse>('/auth/me')
    user.value = data.user
    roleDetail.value = data.role
    role.value = data.role.code
    return data
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
    isAuthenticated,
    canManage,
    canEditReports,
    initialize,
    fetchMe,
    login,
    logout,
  }
})
