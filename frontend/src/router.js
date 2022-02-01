import { createRouter, createWebHistory } from 'vue-router'
import { checkAuthenticationStatus } from '@/mixins/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: {
      isLoginPage: true,
    },
  },
]

let router = createRouter({
  history: createWebHistory('/drive'),
  routes,
})

router.beforeEach((to, from, next) => {
  let [, isLoggedIn] = checkAuthenticationStatus()
  if (to.matched.some((record) => record.meta.isLoginPage)) {
    if (isLoggedIn) {
      next({ name: 'Home' })
    } else {
      next()
    }
  } else {
    if (isLoggedIn) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router
