
<script setup lang="ts">
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSidebarStore } from '@/stores/sidebar'
import { computed, ref, watch } from 'vue'

const auth = useAuthStore()
const sidebar = useSidebarStore()
const router = useRouter()
const route = useRoute()

// スマホ用メニュー
const mobileMenu = ref<'meal' | 'drink' | 'more' | null>(null)

const mealMenuOpen = computed(() => {
  return sidebar.mealMenuOpen || route.path.startsWith('/meal-report')
})

const drinkMenuOpen = computed(() => {
  return sidebar.drinkMenuOpen || route.path.startsWith('/drink-supply')
})

// ページ移動時にメニューを閉じる
watch(
  () => route.fullPath,
  () => {
    mobileMenu.value = null
  }
)

function toggleMobileMenu(menu: 'meal' | 'drink' | 'more') {
  mobileMenu.value = mobileMenu.value === menu ? null : menu
}

async function logout() {
  mobileMenu.value = null
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  
    <!-- パソコン用サイドバー -->
    <aside class="sidebar desktop-sidebar">
      <div class="logo">
        <h1>OkiAri</h1>
        <p>Food Admin</p>
      </div>

      <nav class="nav-list">
        <RouterLink to="/dashboard" active-class="active">
          ダッシュボード
        </RouterLink>

        <div class="menu-group">
          <button
            class="menu-button"
            :class="{ active: route.path.startsWith('/meal-report') }"
            @click="sidebar.toggleMealMenu()"
          >
            食数報告
            <span>{{ mealMenuOpen ? '▲' : '▼' }}</span>
          </button>

          <div v-if="mealMenuOpen" class="submenu">
            <RouterLink to="/meal-report-drink" active-class="active">
              ドリンク売店
            </RouterLink>
            <RouterLink to="/meal-report-food" active-class="active">
              フード売店
            </RouterLink>
          </div>
        </div>

        <div class="menu-group">
          <button
            class="menu-button"
            :class="{ active: route.path.startsWith('/drink-supply') }"
            @click="sidebar.toggleDrinkMenu()"
          >
            ドリンク補充
            <span>{{ drinkMenuOpen ? '▲' : '▼' }}</span>
          </button>

          <div v-if="drinkMenuOpen" class="submenu">
            <RouterLink to="/drink-supply-drink" active-class="active">
              ドリンク補充
            </RouterLink>
            <RouterLink to="/drink-supply-pop" active-class="active">
              ポップコーン
            </RouterLink>
          </div>
        </div>

        <RouterLink to="/inventory" active-class="active">
          棚卸
        </RouterLink>

        <RouterLink v-if="auth.canManage" to="/user-management" active-class="active">
          ユーザ管理
        </RouterLink>

        <RouterLink v-if="auth.canManage" to="/permissions" active-class="active">
          権限設定
        </RouterLink>
      </nav>

      <div class="account">
        <p>{{ auth.user?.display_name || auth.user?.email }}</p>
        <span>{{ auth.roleDetail?.name || auth.role }}</span>
        <button type="button" @click="logout">ログアウト</button>
      </div>
    </aside>

    <!-- スマートフォン用ヘッダー -->
    <header class="mobile-header">
      <div class="mobile-logo">
        <h1>OkiAri</h1>
        <p>Food Admin</p>
      </div>
    </header>

    <!-- スマートフォン用ボトムナビゲーション -->
    <div class="mobile-navigation">

      <!-- サブメニュー表示エリア -->
      <div v-if="mobileMenu" class="mobile-submenu">

        <template v-if="mobileMenu === 'meal'">
          <RouterLink to="/meal-report-drink">
            ドリンク売店
          </RouterLink>
          <RouterLink to="/meal-report-food">
            フード売店
          </RouterLink>
        </template>

        <template v-if="mobileMenu === 'drink'">
          <RouterLink to="/drink-supply-drink">
            ドリンク補充
          </RouterLink>
          <RouterLink to="/drink-supply-pop">
            ポップコーン
          </RouterLink>
        </template>

        <template v-if="mobileMenu === 'more'">
          <RouterLink
            v-if="auth.canManage"
            to="/user-management"
          >
            ユーザ管理
          </RouterLink>

          <RouterLink
            v-if="auth.canManage"
            to="/permissions"
          >
            権限設定
          </RouterLink>

          <div class="mobile-account">
            <span>{{ auth.user?.display_name || auth.user?.email }}</span>
            <button type="button" @click="logout">
              ログアウト
            </button>
          </div>
        </template>

      </div>

      <!-- 下部の5つのメニュー -->
      <nav class="bottom-nav">

        <RouterLink
          to="/dashboard"
          class="bottom-item"
          active-class="selected"
        >
          <span class="nav-icon">⌂</span>
          <span>ダッシュボード</span>
        </RouterLink>

        <button
          type="button"
          class="bottom-item"
          :class="{
            selected: route.path.startsWith('/meal-report') ||
              mobileMenu === 'meal'
          }"
          @click="toggleMobileMenu('meal')"
        >
          <span class="nav-icon">▤</span>
          <span>食数報告</span>
        </button>

        <button
          type="button"
          class="bottom-item"
          :class="{
            selected: route.path.startsWith('/drink-supply') ||
              mobileMenu === 'drink'
          }"
          @click="toggleMobileMenu('drink')"
        >
          <span class="nav-icon">♧</span>
          <span>ドリンク</span>
        </button>

        <RouterLink
          to="/inventory"
          class="bottom-item"
          active-class="selected"
        >
          <span class="nav-icon">▣</span>
          <span>棚卸</span>
        </RouterLink>

        <button
          type="button"
          class="bottom-item"
          :class="{ selected: mobileMenu === 'more' }"
          @click="toggleMobileMenu('more')"
        >
          <span class="nav-icon">•••</span>
          <span>その他</span>
        </button>

      </nav>
    </div>
  
</template>

<style scoped>

/* =================================
   パソコン用サイドバー
================================= */

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 260px;
  min-width: 260px;
  flex-shrink: 0;
  background: #0d1b2a;
  color: white;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.logo {
  margin-bottom: 36px;
}

.logo h1 {
  font-size: 24px;
  font-weight: 800;
  color: #3b82f6;
}

.logo p {
  font-size: 12px;
  color: #cbd5e1;
  margin-top: 4px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-list a {
  display: block;
  color: #e2e8f0;
  text-decoration: none;
  padding: 12px 14px;
  border-radius: 8px;
  font-weight: 700;
}

.nav-list a:hover,
.nav-list a.active {
  background: #ff7a00;
  color: white;
}

.menu-button {
  width: 100%;
  min-height: 44px;
  padding: 12px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #e2e8f0;
  text-align: left;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
}

.menu-button:hover,
.menu-button.active {
  background: #ff7a00;
  color: white;
}

.submenu {
  display: flex;
  flex-direction: column;
  margin-left: 12px;
}

.account {
  margin-top: auto;
  border-top: 1px solid rgba(255,255,255,.18);
  padding-top: 18px;
}

.account p {
  overflow-wrap: anywhere;
  font-weight: 700;
}

.account span {
  display: block;
  margin: 4px 0 12px;
  color: #cbd5e1;
  font-size: 12px;
}

.account button {
  width: 100%;
  padding: 10px;
  border: 1px solid rgba(255,255,255,.3);
  border-radius: 8px;
  background: transparent;
  color: white;
  cursor: pointer;
}

/* =================================
   スマートフォン用
================================= */

.mobile-header,
.mobile-navigation {
  display: none;
}

@media screen and (max-width: 767px) {

  .desktop-sidebar {
    display: none;
  }

  /* 上部ロゴ */
  .mobile-header {
    display: flex;
    width: 100%;
    height: 64px;
    align-items: center;
    padding: 8px 16px;
    background: #0d1b2a;
  }

  .mobile-logo h1 {
    color: #3b82f6;
    font-size: 23px;
    font-weight: 800;
  }

  .mobile-logo p {
    color: #cbd5e1;
    font-size: 11px;
  }

  /* ボトムナビゲーション全体 */
  .mobile-navigation {
    display: block;
    position: fixed;
    z-index: 1000;
    bottom: 0;
    left: 0;
    width: 100%;
    padding-bottom: env(safe-area-inset-bottom);
    background: #ffffff;
    border-top: 1px solid #e2e8f0;
    box-shadow: 0 -3px 12px rgba(0,0,0,.08);
  }

  /* 5つのボタン */
  .bottom-nav {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    width: 100%;
    height: 64px;
  }

  .bottom-item {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 4px;
    min-width: 0;
    padding: 4px 1px;
    border: none;
    background: transparent;
    color: #64748b;
    text-decoration: none;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .nav-icon {
    font-size: 22px;
    line-height: 1;
  }

  .bottom-item.selected {
    color: #2563eb;
  }

  /* サブメニュー */
  .mobile-submenu {
    position: absolute;
    bottom: calc(64px + env(safe-area-inset-bottom));
    left: 8px;
    right: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 -4px 20px rgba(0,0,0,.12);
  }

  .mobile-submenu a {
    display: block;
    padding: 14px;
    border-radius: 8px;
    color: #1e293b;
    font-weight: 600;
    text-decoration: none;
  }

  .mobile-submenu a.router-link-active {
    background: #eff6ff;
    color: #2563eb;
  }

  .mobile-account {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    border-top: 1px solid #e2e8f0;
    color: #334155;
    font-size: 12px;
  }

  .mobile-account button {
    padding: 12px;
    border: none;
    border-radius: 8px;
    background: #fee2e2;
    color: #b91c1c;
    font-weight: 700;
  }
}
</style>
