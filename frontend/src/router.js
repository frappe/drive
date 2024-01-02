import { createRouter, createWebHistory } from "vue-router";
import store from "./store";

function redir404(to) {
  if (store.getters.isLoggedIn && to.fullPath === "/") {
    return { name: "Home" };
  } else if (!store.getters.isLoggedIn && to.fullPath === "/") {
    return { name: "Login" };
  }
}

const routes = [
  {
    path: "/home",
    name: "Home",
    component: () => import("@/pages/Home.vue"),
  },
  {
    path: "/:pathMatch(.*)*/",
    name: "Error",
    component: () => import("@/pages/Error.vue"),
    beforeEnter: [redir404],
    props: true,
  },
  {
    path: "/file/:entityName",
    name: "File",
    component: () => import("@/pages/File.vue"),
    meta: { sidebar: true, isHybridRoute: true, filePage: true },
    props: true,
  },
  {
    path: "/folder/:entityName",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { sidebar: true, isHybridRoute: true },
    props: true,
  },
  {
    path: "/document/:entityName",
    name: "Document",
    meta: { sidebar: false, documentPage: true, isHybridRoute: true },
    component: () => import("@/pages/Document.vue"),
    props: true,
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

const HybridRouteArray = ["File", "Folder", "Document"];

router.beforeEach((to, from, next) => {
  // If they hit a public page log them in
  if (to.matched.some((record) => record.meta.isPublicRoute)) {
    if (store.getters.isLoggedIn) {
      next({ name: "Home" });
    } else {
      next();
    }
  } else {
    // Prepend "Shared/" to the breadcrumbs if an authenticated user navigated to a file by pasting a link
    if (
      store.getters.isLoggedIn ||
      to.matched.some((record) => record.meta.isHybridRoute)
    ) {
      if (to.href !== sessionStorage.getItem("currentRoute")) {
        if (from.fullPath === "/" && HybridRouteArray.includes(to.name)) {
          store.commit("setCurrentBreadcrumbs", [
            { label: "Shared", route: "/shared" },
          ]);
        }
      }
      next();
    } else {
      if (to.name === "Error") {
        next();
      } else {
        next("/login");
      }
      //import.meta.env.DEV ? next("/login") : (window.location.href = "/login");
    }
  }
});

router.afterEach((to, from, failure) => {
  sessionStorage.setItem("currentRoute", to.href);
});

export default router;
