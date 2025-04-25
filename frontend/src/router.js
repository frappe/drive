import { createRouter, createWebHistory } from "vue-router"
import store from "./store"
import { getTeams, translate } from "./resources/files"
import { settings } from "./resources/permissions"
import { manageBreadcrumbs } from "./utils/files"

function clearStore() {
  store.commit("setActiveEntity", null)
}

async function setRootBreadCrumb(to) {
  if (store.getters.isLoggedIn) {
    document.title = to.name
    store.commit("setBreadcrumbs", [{ label: to.name, route: to.path }])
  }
  document
    .querySelector(`head meta[property="og:title"]`)
    .setAttribute("content", "Drive - " + to.name)
  document
    .querySelector(`head meta[name="twitter:title"]`)
    .setAttribute("content", "Drive - " + to.name)
  document
    .querySelector(`head meta[property="og:image"]`)
    .setAttribute("content", "")
  document
    .querySelector(`head meta[name="twitter:image"]`)
    .setAttribute("content", "")
}

const routes = [
  {
    path: "/",
    component: () => null,
    beforeEnter: async () => {
      if (!store.getters.isLoggedIn) return "/login"
      await settings.fetch()
      return "/t/" + settings.data.default_team
    },
  },
  {
    path: "/t/:team/notifications",
    name: "Inbox",
    // Load a skeleton template directly?
    component: () => import("@/pages/Notifications.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/:team/",
    redirect: (to) => ({
      name: "Home",
      team: to.params.team,
    }),
  },
  {
    path: "/t/:team/",
    name: "Home",
    component: () => import("@/pages/Personal.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/team",
    name: "Team",
    component: () => import("@/pages/Team.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/recents",
    name: "Recents",
    component: () => import("@/pages/Recents.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
    beforeEnter: [setRootBreadCrumb],
  },
  {
    path: "/t/:team/file/:entityName",
    name: "File",
    component: () => import("@/pages/File.vue"),
    meta: { allowGuest: true, filePage: true },
    beforeEnter: [manageBreadcrumbs],
    props: true,
  },
  {
    path: "/t/:team/folder/:entityName",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { allowGuest: true },
    beforeEnter: [manageBreadcrumbs],
    props: true,
  },
  {
    path: "/t/:team/document/:entityName",
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
