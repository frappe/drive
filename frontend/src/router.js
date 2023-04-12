import { createRouter, createWebHistory } from "vue-router";
import store from "./store";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("@/pages/Home.vue"),
  },
  {
    path: "/folder/:entityName",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    props: true,
  },
  {
    path: "/Document",
    name: "Document",
    meta: { sidebar: false },
    component: () => import("@/pages/Document.vue"),
  },
  {
    path: "/recent",
    name: "Recent",
    component: () => import("@/pages/Recent.vue"),
  },
  {
    path: "/shared",
    name: "Shared",
    component: () => import("@/pages/Shared.vue"),
  },
  {
    path: "/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
  },
  {
    path: "/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
  },
  {
    path: "/file/:entityName",
    name: "File",
    component: () => import("@/pages/File.vue"),
    props: true,
    meta: {
      isHybridRoute: true,
    },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/pages/Login.vue"),
    meta: {
      isPublicRoute: true,
    },
  },
  {
    path: "/signup",
    name: "Signup",
    component: () => import("@/pages/Signup.vue"),
    meta: {
      isPublicRoute: true,
    },
  },
  {
    path: "/test",
    name: "Test",
    component: () => import("@/pages/Test.vue"),
  },
  {
    path: "/workspace",
    name: "Workspace",
    redirect: () => {
      window.location.href = "/app";
    },
  },
];

let router = createRouter({
  history: createWebHistory("/drive"),
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.matched.some((record) => record.meta.isPublicRoute)) {
    if (store.getters.isLoggedIn) {
      next({ name: "Home" });
    } else {
      next();
    }
  } else {
    if (
      store.getters.isLoggedIn ||
      to.matched.some((record) => record.meta.isHybridRoute)
    ) {
      next();
    } else {
      import.meta.env.DEV ? next("/login") : (window.location.href = "/login");
    }
  }
});

export default router;
