import { createRouter, createWebHistory } from 'vue-router';
import store from './store';

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
    path: '/shared',
    name: 'Shared',
    component: () => import('@/pages/Shared.vue'),
  },
  {
    path: '/shared/folder/:entityName',
    name: 'SharedFolder',
    component: () => import('@/pages/Shared.vue'),
    props: true,
  },
  {
    path: '/favourites',
    name: 'Favourites',
    component: () => import('@/pages/Favourites.vue'),
  },
  {
    path: '/trash',
    name: 'Trash',
    component: () => import('@/pages/Trash.vue'),
  },
  {
    path: '/file/:entityName',
    name: 'File',
    component: () => import('@/pages/File.vue'),
    meta: {
      isHybridRoute: true,
    },
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
];

let router = createRouter({
  history: createWebHistory('/drive'),
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.isPublicRoute)) {
    if (store.getters.isLoggedIn) {
      next({ name: 'Home' });
    } else {
      next();
    }
  } else {
    if (store.getters.isLoggedIn || ((record) => record.meta.isHybridRoute)) {
      next();
    } else {
      next('/login');
    }
  }
});

export default router;
