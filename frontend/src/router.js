import { createRouter, createWebHistory } from 'vue-router'
import store from './store'

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
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/Signup.vue'),
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
  if (to.matched.some((record) => record.meta.isLoginPage)) {
    if (store.getters.isLoggedIn) {
      next({ name: 'Home' })
    } else {
      next()
    }
  } else {
    if (store.getters.isLoggedIn) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router
