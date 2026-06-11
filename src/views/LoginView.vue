<script setup lang="ts">
import { ref } from 'vue'

// 入力値を管理する変数（TypeScriptの型推論が効いています）
const email = ref('')
const password = ref('')

// ログインボタンを押した時の処理
const handleLogin = () => {
  alert(`ログインを試みます\nメール: ${email.value}\nパスワード: ********`)
  // 🔗 ここに後からバックエンド（Supabase/FastAPI）との連携処理を書きます
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2 class="login-title">ログイン</h2>

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
      </form>
    </div>
  </div>
</template>

<style scoped>
/* 画面全体の背景（グレーで中央配置） */
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f3f4f6; /* 薄いグレー */
}

/* ログインボックスの白いカード */
.login-card {
  background-color: #ffffff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  width: 100%;
  max-width: 400px; /* カードの最大横幅 */
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #1f2937; /* 濃いグレー */
  font-size: 24px;
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
  background-color: #2563eb; /* 綺麗な青 */
  color: white;
  border: none;
  padding: 14px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-top: 10px;
}

.login-button:hover {
  background-color: #1d4ed8; /* ホバー時に少し濃い青に */
}
</style>
