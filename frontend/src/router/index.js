import { createRouter, createWebHistory } from 'vue-router'
import { auth } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/', component: () => import('../views/Dashboard.vue') },
  { path: '/devices', component: () => import('../views/Devices.vue') },
  { path: '/config', component: () => import('../views/Config.vue') },
  { path: '/monitor', component: () => import('../views/Monitor.vue') },
  { path: '/credentials', component: () => import('../views/Credentials.vue') },
  { path: '/tasks', component: () => import('../views/Tasks.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  if (!to.meta.public && !auth.isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
