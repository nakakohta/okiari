import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/meal-report',
      name: 'mealreport',
      component: () => import('@/views/MealReportView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/drink-supply',
      name: 'drinkreport',
      component: () => import('@/views/DrinkRefillView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/inventory',
      name: 'inventory',
      component: () => import('@/views/InventoryView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/user-management',
      name: 'usermanagement',
      component: () => import('@/views/UserManagement.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/user-management/add',
      name: 'useradd',
      component: () => import('@/views/UserAddView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/permissions',
      name: 'permissions',
      component: () => import('@/views/PermissionSettingsView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/',
      redirect: '/login',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.initialize()

  if (to.name === 'login' && auth.isAuthenticated) {
    return '/dashboard'
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && !allowedRoles.includes(auth.role || '')) {
    return '/dashboard'
  }
})

export default router
