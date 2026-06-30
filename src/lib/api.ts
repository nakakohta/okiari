// フロント側で毎回トークンを意識せずに
// await api.get('/users')　みたいにかけるようにするやつ

import axios from 'axios'
import { supabase } from '@/lib/supabase'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const accessToken = data.session?.access_token

  if(accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if(error.response?.status === 401) {
      // 未ログイン・期限切れ・不正トークン
      await supabase.auth.signOut()
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)
