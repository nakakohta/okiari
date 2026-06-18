import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ログインページ
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },

    // ダッシュボード
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },

    // 食数報告
    {
      path: '/meal-report',
      name: 'mealreport',
      component: () => import('@/views/MealReportView.vue'),
    },

    // ドリンク補充
    {
      path: '/drink-supply',
      name: 'drinkreport',
      component: () => import('@/views/DrinkRefillView.vue'),
    },

    // 棚卸
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('@/views/InventoryView.vue'),
    },

    // ユーザ管理
    {
      path: '/user-management',
      name: 'usermanagement',
      component: () => import('@/views/UserManagement.vue'),
    },

    // 権限管理
    {
      path: '/permissions',
      name: 'permissions',
      component: () => import('@/views/PermissionSettingsView.vue'),
    },
    // アクセス時はとりあえずログイン画面へ(デフォ)
    {
      path: '/',
      redirect: '/login'
    }
  ]
})

export default router
