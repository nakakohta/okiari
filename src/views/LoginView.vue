<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// import { supabase } from '@/lib/supabase'

// 入力値を管理する変数
const email = ref('')
const password = ref('')
// const errorMessage = ref('')
// const loading = ref(false)

const router = useRouter() //ルータのインスタンス
const auth = useAuthStore()

// ログインボタンを押した時の処理(フロント側テスト用)
const handleLogin = async () => {
  const result = await auth.login(email.value, password.value)

  if(result.success) {
    // ログイン成功時
    alert(`ログイン成功！\n現在の権限: ${auth.role} でダッシュボードへ移動します`)
    router.push('/dashboard')
  } else {
    // ログイン失敗時
    alert(result.error)
  }
}

// supabase用ログイン関連処理
// const login = async () => {
//   errorMessage.value = ''
//   loading.value = true

//   const { data, error } = await supabase.auth.signInWithPassword({
//     email: email.value,
//     password: password.value,
//   })

//   loading.value = false
//   if(error) {
//     errorMessage.value = 'メールアドレスまたはパスワードが正しくありません'
//     return
//   }

//   const accessToken = data.session?.access_token

//   if(!accessToken) {
//     errorMessage.value = 'ログイン情報を取得できませんでした'
//     return
//   }

//   router.push('/dashbord')
// }
</script>

<template>
  <div class="login-wrapper">
    <div class="brand-header">
      <div class="brand-inner">
        <h1 class="brand-title">OkiAri</h1>
        <h2 class="brand-subtitle">Food Manager</h2>
        <p class="brand-desc">沖縄アリーナ飲食業務管理</p>
      </div>
    </div>
    <div class="login-card-container">
      <div class="login-card">
        <div class="form-body">
          <h3 class="form-title">ログイン</h3>
          <p class="form-subtitle">権限に応じたメニューを表示します。</p>
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label for="email">メールアドレス</label>
              <input
                type="email"
                id="email"
                v-model="email"
                placeholder="example@mail.com"
                required
              />
            </div>

            <div class="form-group">
              <label for="password">パスワード</label>
              <input
                type="password"
                id="password"
                v-model="password"
                placeholder="パスワードを入力"
                required
              />
            </div>

            <button type="submit" class="login-button">ログイン</button>

            <!-- supabaseにしたときにコメントアウト外して -->
            <!-- <button type="submit" :disabled="loading" class="login-button">
              {{ loading ? 'ログイン中...' : 'ログイン' }}
            </button>

            <p v-if="errorMessage">{{ errorMessage }}</p> -->
          </form>

          <p class="footer-note">50人以上の同時利用を想定した現場入力UI</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 画面全体の背景（グレーで中央配置） */
.login-wrapper {
  position: relative;
  display: flex;
  min-height: 100vh;
  background-color: #f8f9fa;
  flex-direction: column;
}

/* ヘッダー */
.brand-header {
  background-color: #0d1b2a;
  width: 100%;
  padding: 35px 24px 65px 24px;
  text-align: center;
}

.brand-inner {
  max-width: 700px;
  margin: 0 auto;
  text-align: left;
}

.brand-title {
  font-size: 50px;
  font-weight: 880;
  color: #004bff;
  margin: 0;
}

.brand-subtitle {
  font-size: 30px;
  font-weight: 700;
  color: #004bff;
  margin: 4px 0 0 0;
}

.brand-desc {
  font-size: 13px;
  color: #a0aec0;
  margin: 12px 0 0 0;
}

/* ログインカード内の設定 */
.login-card-container {
  width: 100%;
  padding: 0 24px 40px 24px;
  margin-top: -45px;
  display: flex;
  justify-content: center;
}

/* ログインボックスの白いカード */
.login-card {
  width: 100%;
  background-color: #ffffff;
  padding: 40px;
  border-radius: 32px;
  box-shadow: 0 20px 40px -1px rgba(0, 0, 0, 0.05);
  width: 100%;
  max-width: 550px; /* カードの最大横幅 */
  overflow: hidden;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #1f2937; /* 濃いグレー */
  font-size: 24px;
}

/* ログインフォーム関連 */
.form-body {
  padding: 10px;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.form-subtitle {
  font-size: 13px;
  color: #718096;
  margin: 8px 0 24px 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: bold;
  color: #4b5563;
}

/* 入力フォームの枠線など */
.form-group input {
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

/* 入力欄をクリックした時（フォーカス時）の青枠 */
.form-group input:focus {
  border-color: #3b82f6;
}

/* ログインボタン */
.login-button {
  background-color: #ff7a00; /* 綺麗な青 */
  color: white;
  border: none;
  padding: 14px;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 12px;
}

.login-button:hover {
  background-color: #e66e00; /* ホバー時に少し暗く */
}

/* 下の説明文 */
.footer-note {
  text-align: center;
  font-size: 11px;
  color: #a0aec0;
  margin-top: 32px;
  margin-bottom: 0;
}
</style>
