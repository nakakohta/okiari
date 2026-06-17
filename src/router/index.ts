import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import UserManagement from '@/views/UserManagement.vue'
import MealReportView from '@/views/MealReportView.vue'
import DrinkRefillView from '@/views/DrinkRefillView.vue'
import InventoryView from '@/views/InventoryView.vue'
import PermissionSettingsView from '@/views/PermissionSettingsView.vue'

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
      component: DashboardView,
    },

    // 食数報告
    {
      path: '/meal-report',
      name: 'mealreport',
      component: MealReportView,
    },

    // ドリンク補充
    {
      path: '/drink-supply',
      name: 'drinkreport',
      component: DrinkRefillView,
    },

    // 棚卸
    {
      path: '/inventory',
      name: 'inventory',
      component: InventoryView,
    },

    // ユーザ管理
    {
      path: '/user-management',
      name: 'usermanagement',
      component: UserManagement,
    },

    // 権限管理
    {
      path: '/permissions',
      name: 'permissions',
      component: PermissionSettingsView,
    },
    // アクセス時はとりあえずログイン画面へ(デフォ)
    {
      path: '/',
      redirect: '/login'
    }
  ]
})

export default router
