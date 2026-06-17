<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// ログインしているユーザの権限を取得
const auth = useAuthStore()
</script>
<template>
  <aside class="sidebar">
    <ul class="logo">
      <h1>OkiAri</h1>
      <p>Food Admin</p>
    </ul>

    <ul class="nav-list">
      <li>
        <RouterLink to="/dashboard" active-class="active">ダッシュボード</RouterLink>
      </li>
      <li>
        <RouterLink to="/meal-report" active-class="active">食数報告</RouterLink>
      </li>
      <li>
        <RouterLink to="/drink-supply" active-class="active">ドリンク補充</RouterLink>
      </li>
      <li>
        <RouterLink to="/inventory" active-class="active">棚卸</RouterLink>
      </li>

      <li v-if="auth.role === 'admin'">
        <RouterLink to="/user-management" active-class="active">ユーザ管理</RouterLink>
      </li>
      <li v-if="auth.role === 'admin'">
        <RouterLink to="/permissions" active-class="active">権限設定</RouterLink>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
/* 既存のサイドバーのCSSに、RouterLink用のスタイルを少し調整 */
.sidebar {
  width: 260px;
  background-color: #0d1b2a; /* 画像のような深い紺色 */
  color: white;
  padding: 24px;
  min-height: 100vh;
}

.logo {
  margin-bottom: 40px;
}
.logo h1 {
  font-size: 24px;
  margin: 0;
}
.logo p {
  font-size: 12px;
  color: #6b7280;
  margin: 4px 0 0 0;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* RouterLinkはブラウザ上では「aタグ」に変換されるため、aタグに対してスタイルを当てる */
.nav-list a {
  display: block;
  color: #a0aec0;
  text-decoration: none;
  padding: 14px 16px;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-list a:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: white;
}
</style>
