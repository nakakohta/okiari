import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'
import { supabase } from '@/lib/supabase'

type RetriableRequest = InternalAxiosRequestConfig & { _authRetry?: boolean }
let refreshPromise: ReturnType<typeof supabase.auth.refreshSession> | null = null

async function refreshSessionOnce() {
  if (!refreshPromise) {
    refreshPromise = supabase.auth.refreshSession().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:18000',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const accessToken = data.session?.access_token

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config as RetriableRequest | undefined
    if (error.response?.status === 401 && config && !config._authRetry) {
      config._authRetry = true
      const { data } = await refreshSessionOnce()
      if (data.session?.access_token) {
        config.headers.Authorization = `Bearer ${data.session.access_token}`
        return api.request(config)
      }

      const { data: current } = await supabase.auth.getSession()
      if (!current.session) window.location.assign('/login')
    }

    return Promise.reject(error)
  },
)
