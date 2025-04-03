import { createRouter, createWebHistory } from "vue-router"
import store from "./store"
import { getTeams, translate } from "./resources/files"

function redir404(to, from, next) {
  if (store.getters.isLoggedIn) {
    next()
  } else {
    next("/login")
  }
}

function clearStore() {
  store.commit("setEntityInfo", [])
  store.commit("setCurrentFolder", [])
  store.commit("setCurrentEntitites", [])
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
      if (!store.getters.isLoggedIn) return
      await getTeams.fetch()
      if (store.getters.isLoggedIn)
        if (Object.keys(getTeams.data.message || getTeams.data).length)
          return "/t/" + Object.keys(getTeams.data.message || getTeams.data)[0]
        else return "/teams"

      return "/login"
    },
  },
  {
    path: "/folder/:entityName",
    component: () => null,
    beforeEnter: async (to) => {
      await getTeams.fetch()
      await translate.fetch()
      return {
        name: "Folder",
        params: {
          team: Object.keys(getTeams.data)[0],
          entityName:
            translate.data[to.params.entityName] || to.params.entityName,
        },
      }
    },
  },
  {
    path: "/document/:entityName",
    component: () => null,
    beforeEnter: async (to) => {
      await getTeams.fetch()
      await translate.fetch()
      return {
        name: "Document",
        params: {
          team: Object.keys(getTeams.data)[0],
          entityName:
            translate.data[to.params.entityName] || to.params.entityName,
        },
      }
    },
  },
  {
    path: "/file/:entityName",
    component: () => null,
    beforeEnter: async (to) => {
      await getTeams.fetch()
      await translate.fetch()
      return {
        name: "File",
        params: {
          team: Object.keys(getTeams.data)[0],
          entityName:
            translate.data[to.params.entityName] || to.params.entityName,
        },
      }
    },
  },
  {
    path: "/t/:team/notifications",
    name: "Notifications",
    // Load a skeleton template directly?
    component: () => import("@/pages/Notifications.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },

  {
    path: "/t/:team/team",
    name: "Team",
    component: () => import("@/pages/Team.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/t/:team/recents",
    name: "Recents",
    component: () => import("@/pages/Recents.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/t/:team/favourites",
    name: "Favourites",
    component: () => import("@/pages/Favourites.vue"),
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
    path: "/t/:team/trash",
    name: "Trash",
    component: () => import("@/pages/Trash.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
  },
  {
    path: "/:team/file/:entityName",
    redirect: (to) => ({
      name: "File",
      team: to.params.team,
      entityName: to.params.entityName,
    }),
  },
  {
    path: "/t/:team/file/:entityName",
    name: "File",
    component: () => import("@/pages/File.vue"),
    meta: { isHybridRoute: true, filePage: true },
    props: true,
  },
  {
    path: "/:team/folder/:entityName",
    redirect: (to) => ({
      name: "Folder",
      team: to.params.team,
      entityName: to.params.entityName,
    }),
  },
  {
    path: "/t/:team/folder/:entityName",
    name: "Folder",
    component: () => import("@/pages/Folder.vue"),
    meta: { sidebar: true, isHybridRoute: true },
    props: true,
  },
  {
    path: "/:team/document/:entityName",
    redirect: (to) => ({
      name: "Document",
      team: to.params.team,
      entityName: to.params.entityName,
    }),
  },
  {
    path: "/t/:team/document/:entityName",
    name: "Document",
    meta: { sidebar: false, documentPage: true, isHybridRoute: true },
    component: () => import("@/pages/Document.vue"),
    props: true,
    beforeEnter: [clearStore],
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
    path: "/shared",
    name: "Shared",
    component: () => import("@/pages/Shared.vue"),
    beforeEnter: [setRootBreadCrumb, clearStore],
    meta: { allowGuest: true },
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

router.beforeEach(async (to, from, next) => {
  if (!store.getters.isLoggedIn && !to.meta.allowGuest) {
    next("/login")
  } else {
    if (to.params.team) localStorage.setItem("recentTeam", to.params.team)
    next()
  }
})

router.afterEach((to) => {
  // nextTick(
  //   () =>
  //     (document.title =
  //       store.state.breadcrumbs[store.state.breadcrumbs.length - 1].label ||
  //       to.name)
  // )
  sessionStorage.setItem("currentRoute", to.href)
})

export default router
