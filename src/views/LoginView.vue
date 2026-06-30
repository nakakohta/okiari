<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const errorMessage = ref('')

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

async function handleLogin() {
  errorMessage.value = ''
  const result = await auth.login(email.value, password.value)

  if (result.success) {
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.push(redirect)
    return
  }

  errorMessage.value = result.error || 'ログインできませんでした'
}
</script>

<template>
  <div class="login-wrapper">
    <header class="brand-header">
      <div class="brand-inner">
        <h1>OkiAri</h1>
        <p>沖縄アリーナ飲食業務管理</p>
      </div>
    </header>

    <main class="login-card-container">
      <section class="login-card">
        <h2>ログイン</h2>
        <p>登録済みのアカウントでログインしてください。</p>

        <form class="login-form" @submit.prevent="handleLogin">
          <label>
            メールアドレス
            <input v-model="email" type="email" autocomplete="email" placeholder="example@mail.com" required />
          </label>

          <label>
            パスワード
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="パスワード"
              required
            />
          </label>

          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

          <button type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'ログイン中...' : 'ログイン' }}
          </button>
        </form>
      </section>
    </main>
  </div>
</template>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  background-color: #f8fafc;
}

.brand-header {
  background-color: #0d1b2a;
  padding: 40px 24px 76px;
}

.brand-inner {
  max-width: 560px;
  margin: 0 auto;
}

.brand-inner h1 {
  color: #3b82f6;
  font-size: 48px;
  font-weight: 900;
  margin: 0;
}

.brand-inner p {
  color: #cbd5e1;
  margin: 8px 0 0;
}

.login-card-container {
  display: flex;
  justify-content: center;
  padding: 0 24px 40px;
  margin-top: -44px;
}

.login-card {
  width: 100%;
  max-width: 520px;
  background: white;
  border-radius: 8px;
  padding: 36px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.login-card h2 {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 800;
}

.login-card > p {
  margin: 0 0 24px;
  color: #64748b;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
  color: #334155;
}

input {
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 16px;
}

button {
  background-color: #ff7a00;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
  margin: 0;
}
</style>
