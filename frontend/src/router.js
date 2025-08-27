import { createResource } from "frappe-ui"
import { createRouter, createWebHistory } from "vue-router"
import store from "./store"
import { manageBreadcrumbs } from "./utils/breadcrumbs"

function clearStore() {
  store.commit("setActiveEntity", null)
}

async function setRootBreadCrumb(to) {
  if (store.getters.isLoggedIn) {
    // Vietnamese title mapping
    const titleMapping = {
      'Home': 'Tài liệu của tôi',
      'Team': 'Nhóm',
      'Recents': 'Gần đây',
      'Favourites': 'Yêu thích',
      'Trash': 'Thùng rác',
      'Inbox': 'Hộp thư',
      'Shared': 'Chia sẻ',
      'Teams': 'Nhóm',
      'Login': 'Đăng nhập',
      'Signup': 'Đăng ký',
      'Setup': 'Thiết lập'
    }
    
    // Set Vietnamese title directly
    const vietnameseTitle = titleMapping[to.name] || to.name
    document.title = vietnameseTitle
    
    if (to.name !== "Team")
      store.commit("setBreadcrumbs", [
        { label: vietnameseTitle, name: to.name, route: to.path },
      ])
  }
}

const routes = [
  {
    path: "/",
    component: () => null,
    beforeEnter: async () => {
      if (!store.getters.isLoggedIn) return "/login"
      const settings = createResource({
        url: "/api/method/drive.api.product.get_settings",
        method: "GET",
        cache: "settings",
      })
      if (!settings.data) await settings.fetch()
      
      // If user has default team, go there
      if (settings.data.default_team) {
        return "/t/" + settings.data.default_team + "/team"
      }

      // If no teams available, go to teams page
      return "/teams"
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

// Update breadcrumbs when translations are ready
window.addEventListener('translationsReady', () => {
  // Re-run setRootBreadCrumb with current route to update with translations
  const currentRoute = router.currentRoute.value
  if (currentRoute && store.getters.isLoggedIn) {
    // Vietnamese title mapping
    const titleMapping = {
      'Home': 'Tài liệu của tôi',
      'Team': 'Nhóm',
      'Recents': 'Gần đây',
      'Favourites': 'Yêu thích',
      'Trash': 'Thùng rác',
      'Inbox': 'Hộp thư',
      'Shared': 'Chia sẻ',
      'Teams': 'Nhóm',
      'Login': 'Đăng nhập',
      'Signup': 'Đăng ký',
      'Setup': 'Thiết lập'
    }
    
    const vietnameseTitle = titleMapping[currentRoute.name] || currentRoute.name
    document.title = vietnameseTitle
    
    if (currentRoute.name !== "Team") {
      store.commit("setBreadcrumbs", [
        { label: vietnameseTitle, name: currentRoute.name, route: currentRoute.path },
      ])
    }
  }
})

export default router
