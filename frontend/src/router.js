import { createRouter, createWebHistory } from "vue-router"
import store from "./store"
import { manageBreadcrumbs } from "./utils/files"
import { createResource } from "frappe-ui"
import Dummy from "@/pages/Dummy.vue"
function clearStore() {
  store.commit("setActiveEntity", null)
}

async function setRootBreadCrumb(to) {
  if (store.getters.isLoggedIn) {
    document.title = __(to.name)
    if (to.name !== "Team")
      store.commit("setBreadcrumbs", [
        { label: __(to.name), name: to.name, route: to.path },
      ])
  }
}

const routes = [
  {
    path: "/signup",
    name: "Signup",
    component: () => import("@/pages/LoginSignup.vue"),
    beforeEnter: () => {
      if (store.getters.isLoggedIn) return "/"
    },
    meta: { allowGuest: true },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/pages/LoginSignup.vue"),
    beforeEnter: () => {
      if (store.getters.isLoggedIn) return "/"
    },
    meta: { allowGuest: true },
  },
  {
    path: "/setup",
    name: "Setup",
    component: () => import("@/pages/Setup.vue"),
  },
  {
    path: "/",
    name: "Home",
    component: () => import("@/pages/Personal.vue"),
    beforeEnter: [setRootBreadCrumb],
    props: true,
  },
  {
    path: "/inbox",
    name: "Inbox",
    // Load a skeleton template directly?
    component: () => import("@/pages/Notifications.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/teams",
    name: "Teams",
    component: () => import("@/pages/Teams.vue"),
  },
  {
    path: "/shared",
    name: "Shared",
    component: () => import("@/pages/Shared.vue"),
    beforeEnter: [setRootBreadCrumb],
    meta: { allowGuest: true },
  },
  {
    path: "/recents",
    name: "Recents",
    component: () => import("@/pages/Recents.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/documents",
    name: "Documents",
    component: () => import("@/pages/Documents.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/presentations",
    name: "Slides",
    component: () => import("@/pages/Slides.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/transfer",
    name: "Transfer",
    component: () => import("@/pages/QuickShare.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/:letter/:entityName/:slug?",
    component: Dummy,
    beforeEnter: async (to) => {
      return {
        path: `/g/${to.params.entityName}`,
      }
    },
  },
  {
    path: "/g/:entityName/",
    component: Dummy,
    beforeEnter: async (to) => {
      const entity = createResource({
        url: "/api/method/drive.api.files.get_entity_type",
        method: "GET",
        params: {
          entity_name: to.params.entityName,
        },
      })
      await entity.fetch()
      const letter = {
        folder: "d",
        document: "w",
        file: "f",
      }[entity.data.type]
      return {
        path: `/${letter}/${entity.data.name}`,
      }
    },
  },
  {
    path: "/t/:team/",
    name: "Team",
    component: () => import("@/pages/Team.vue"),
    beforeEnter: [setRootBreadCrumb],
    props: true,
  },
  {
    path: "/f/:entityName/:slug?",
    name: "File",
    component: () => import("@/pages/File.vue"),
    meta: { allowGuest: true, filePage: true },
    beforeEnter: [manageBreadcrumbs],
    props: true,
  },
  {
    path: "/d/:entityName/:slug?",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { allowGuest: true },
    beforeEnter: [manageBreadcrumbs],
    props: true,
  },
  {
    path: "/w/:entityName/:slug?",
    name: "Document",
    meta: { documentPage: true, allowGuest: true },
    component: () => import("@/pages/Document.vue"),
    props: true,
    beforeEnter: [manageBreadcrumbs],
  },
]

let router = createRouter({
  history: createWebHistory("/drive"),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (!store.getters.isLoggedIn && !to.meta.allowGuest) {
    next("/login?redirect-to=/drive" + to.path)
  } else {
    if (to.params.team) localStorage.setItem("recentTeam", to.params.team)
    clearStore()
    next()
  }
})

router.afterEach((to) => {
  sessionStorage.setItem("currentRoute", to.href)
})

export default router
