import { createRouter, createWebHistory } from "vue-router"
import store from "./store"
import { getTeams } from "./resources/files"

function redir404(to, from, next) {
  if (store.getters.isLoggedIn) {
    next()
  } else {
    next("/login")
  }
}

function clearStore(to, from) {
  if (from.name === "Document" || to.name === "Document") {
    store.commit("setShowInfo", false)
    return
  }
  if (from.name === "Whiteboard" || to.name === "Whiteboard") {
    store.commit("setShowInfo", false)
    return
  } else {
    store.commit("setEntityInfo", [])
    store.commit("setCurrentFolder", [])
    store.commit("setCurrentEntitites", [])
  }
}

function setRootBreadCrumb(to) {
  if (store.getters.isLoggedIn) {
    document.title = to.name
    store.commit("setBreadcrumbs", [{ label: to.name, route: to.path }])
  }
}

const routes = [
  {
    path: "/",
    component: () => null,
    beforeEnter: async () => {
      if (store.getters.isLoggedIn) {
        await getTeams.fetch()
        return "/" + Object.keys(getTeams.data)[0]
      }
      return "/login"
    },
  },
  {
    path: "/:team/notifications",
    name: "Notifications",
    // Load a skeleton template directly?
    component: () => import("@/pages/Notifications.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/:team",
    name: "Home",
    component: () => import("@/pages/Home.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/:team/recents",
    name: "Recents",
    component: () => import("@/pages/Recents.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/:team/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/:team/personal",
    name: "My Space",
    component: () => import("@/pages/Personal.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/:team/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/:team/file/:entityName",
    name: "File",
    component: () => import("@/pages/File.vue"),
    meta: { sidebar: true, isHybridRoute: true, filePage: true },
    props: true,
  },
  {
    path: "/:team/folder/:entityName",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { sidebar: true, isHybridRoute: true },
    props: true,
  },
  {
    path: "/:team/document/:entityName",
    name: "Document",
    meta: { sidebar: false, documentPage: true, isHybridRoute: true },
    component: () => import("@/pages/Document.vue"),
    props: true,
    beforeEnter: [clearStore],
  },
  {
    path: "/login",
    name: "Login",
    redirect: () => {
      window.location.href = "/login"
    },
  },
  {
    path: "/:pathMatch(.*)*/",
    name: "Error",
    component: () => import("@/pages/Error.vue"),
    beforeEnter: [redir404, clearStore],
    meta: {
      errorPage: true,
    },
    props: true,
  },
]

let router = createRouter({
  history: createWebHistory("/drive"),
  routes,
})

router.beforeEach((to, from, next) => {
  const redirect = sessionStorage.getItem("redirect")
  switch (true) {
    case !store.getters.isLoggedIn && to.meta.isHybridRoute:
      sessionStorage.setItem("redirect", JSON.stringify(to.fullPath))
      next()
      break
    case !store.getters.isLoggedIn:
      next("/login")
      break
    case store.getters.isLoggedIn:
      if (redirect) {
        next(JSON.parse(redirect))
        sessionStorage.removeItem("redirect")
      } else {
        next()
      }
      break
    default:
      next("/login")
      break
  }
})

router.afterEach((to) => {
  sessionStorage.setItem("currentRoute", to.href)
})

export default router
