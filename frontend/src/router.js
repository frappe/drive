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
    path: "/",
    name: "Home",
    component: () => import("@/pages/Personal.vue"),
    beforeEnter: [setRootBreadCrumb],
    props: true,
  },
  {
    path: "/f/:entityName/",
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

      return {
        path: `/t/${entity.data.team}/${entity.data.type}/${entity.data.name}`,
      }
    },
  },
  // {
  //   path: "/t/:team/",
  //   name: "Home",
  //   component: () => import("@/pages/Personal.vue"),
  //   beforeEnter: [setRootBreadCrumb],
  //   props: true,
  // },
  {
    path: "/t/:team/inbox",
    name: "Inbox",
    // Load a skeleton template directly?
    component: () => import("@/pages/Notifications.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/",
    name: "Team",
    component: () => import("@/pages/Team.vue"),
    beforeEnter: [setRootBreadCrumb],
    props: true,
  },

  {
    path: "/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/recents",
    name: "Recents",
    component: () => import("@/pages/Recents.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/documents",
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
    path: "/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
    beforeEnter: [setRootBreadCrumb],
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
    path: "/t/:team/folder/:entityName/:slug?",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { allowGuest: true },
    beforeEnter: [manageBreadcrumbs],
    props: true,
  },
  {
    path: "/d/:entityName/:slug?",
    name: "Document",
    meta: { documentPage: true, allowGuest: true },
    component: () => import("@/pages/Document.vue"),
    props: true,
    beforeEnter: [manageBreadcrumbs],
  },
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
    path: "/teams",
    name: "Teams",
    component: () => import("@/pages/Teams.vue"),
  },
  {
    path: "/setup",
    name: "Setup",
    component: () => import("@/pages/Setup.vue"),
  },
  {
    path: "/shared",
    name: "Shared",
    component: () => import("@/pages/Shared.vue"),
    beforeEnter: [setRootBreadCrumb],
    meta: { allowGuest: true },
  },
]

let router = createRouter({
  history: createWebHistory("/drive"),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (!store.getters.isLoggedIn && !to.meta.allowGuest) {
    next("/login")
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
