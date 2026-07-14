<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ref } from 'vue'
const mealMenuOpen = ref(false)
const drinkMenuOpen = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <h1>OkiAri</h1>
      <p>Food Admin</p>
    </div>

    <nav class="nav-list">
      <RouterLink to="/dashboard" active-class="active">ダッシュボード</RouterLink>
      <div class="menu-group">
        <button
          class="menu-button"
          @click="mealMenuOpen = !mealMenuOpen"
        >
          食数報告
          <span>{{ mealMenuOpen ? "▲" : "▼" }}</span>
        </button>

        <div v-if="mealMenuOpen" class="submenu">
          <RouterLink to="/meal-report-drink">ドリンク売店</RouterLink>
          <RouterLink to="/meal-report-food">フード売店</RouterLink>
        </div>
      </div>
      <div class="menu-group">
        <button
          class="menu-button"
          @click="drinkMenuOpen = !drinkMenuOpen"
        >
          ドリンク補充
          <span>{{ drinkMenuOpen ? "▲" : "▼" }}</span>
        </button>

        <div v-if="drinkMenuOpen" class="submenu">
          <RouterLink to="/drink-supply-drink">ドリンク補充</RouterLink>
          <RouterLink to="/drink-supply-pop">ポップコーン</RouterLink>
        </div>
      </div>
      <RouterLink to="/inventory" active-class="active">棚卸</RouterLink>
      <RouterLink v-if="auth.canManage" to="/user-management" active-class="active">ユーザ管理</RouterLink>
      <RouterLink v-if="auth.canManage" to="/permissions" active-class="active">権限設定</RouterLink>
    </nav>

    <div class="account">
      <p>{{ auth.user?.display_name || auth.user?.email }}</p>
      <span>{{ auth.roleDetail?.name || auth.role }}</span>
      <button type="button" @click="logout">ログアウト</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background-color: #0d1b2a;
  color: white;
  padding: 24px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.logo {
  margin-bottom: 36px;
}

.logo h1 {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
  color: #3b82f6;
}

.logo p {
  font-size: 12px;
  color: #a0aec0;
  margin: 4px 0 0;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-list a {
  display: block;
  color: #cbd5e1;
  text-decoration: none;
  padding: 12px 14px;
  border-radius: 8px;
  font-weight: 700;
}

.nav-list a:hover,
.nav-list a.active {
  background-color: #ff7a00;
  color: white;
}

.account {
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  padding-top: 18px;
}

.account p {
  margin: 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.account span {
  display: block;
  margin: 4px 0 12px;
  color: #a0aec0;
  font-size: 12px;
}

.account button {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: transparent;
  color: white;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
}

.menu-button {
  width: 100%;
  background: transparent;
  border: none;
  color: #cbd5e1;
  padding: 12px 14px;
  border-radius: 8px;
  text-align: left;
  font-weight: 700;
  cursor: pointer;

  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-button:hover {
  background: #ff7a00;
  color: white;
}

.submenu {
  display: flex;
  flex-direction: column;
  margin-left: 20px;
}

.submenu a {
  padding: 8px 14px;
  font-size: 14px;
}
</style>
