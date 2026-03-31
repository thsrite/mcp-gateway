import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
    },
    {
      path: '/servers',
      name: 'ServerList',
      component: () => import('../views/ServerList.vue'),
    },
    {
      path: '/servers/:id',
      name: 'ServerDetail',
      component: () => import('../views/ServerDetail.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const { useAuthStore } = await import('../stores/auth')
  const auth = useAuthStore()

  if (!auth.loaded) {
    try {
      await auth.fetchAuthStatus()
    } catch {
      return true
    }
  }

  if (auth.authEnabled && !auth.token) {
    return '/login'
  }

  return true
})

export default router
