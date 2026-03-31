import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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

export default router
