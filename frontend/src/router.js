import { createRouter, createWebHistory } from 'vue-router'
import store from './store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
  },
  {
    path: '/folder/:entityName',
    name: 'Folder',
    component: () => import('@/pages/Home.vue'),
    props: true,
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: {
      isPublicRoute: true,
    },
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/Signup.vue'),
    meta: {
      isPublicRoute: true,
    },
  },
]

let router = createRouter({
  history: createWebHistory('/drive'),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.isPublicRoute)) {
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
