import { defineStore } from 'pinia'
import { ref } from 'vue'

// テスト用のダミーアカウント
const DUMMY_USERS = [
  { email: 'admin@example.com', password: 'password123', role: 'admin' },
  { email: 'leader@example.com', password: 'password123', role: 'leader' },
  { email: 'staff@example.com', password: 'password123', role: 'viewer' }
]

export const useAuthStore = defineStore('auth', () => {
  const role = ref<string | null>(null)
  const user = ref<{ email: string } | null>(null)

  // ログイン関数(ダミー)
  async function login(email: string, password: string) {
    // 入力されたメアドとパスから一致するユーザを探す
    const foundUser = DUMMY_USERS.find(
      (u) => u.email === email && u.password === password
    )

    if(foundUser) {
      // 一致したらログイン
      user.value = { email: foundUser.email }
      role.value = foundUser.role
      return { success: true }
    } else {
      // 見つからなければエラー
      return { success: false, error: 'メールアドレスまたはパスワードが違います。' }
    }
  }
  // ログアウト
  function logout() {
    role.value = null
    user.value = null
  }

  return { role, user, login, logout }
})
