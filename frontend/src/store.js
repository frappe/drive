import { createStore } from 'vuex'
import { call } from 'frappe-ui'

let getCookies = () => {
  return Object.fromEntries(
    document.cookie
      .split('; ')
      .map((cookie) => cookie.split('='))
      .map((entry) => [entry[0], decodeURIComponent(entry[1])])
  )
}

const store = createStore({
  state: {
    auth: {
      loading: false,
      user_id: getCookies().user_id,
    },
    user: {
      fullName: getCookies().full_name,
      imageURL: null,
    },
  },
  getters: {
    isLoggedIn: (state) => {
      return state.auth.user_id && state.auth.user_id !== 'Guest'
    },
  },
  mutations: {
    setAuth(state, auth) {
      Object.assign(state.auth, auth)
    },
    setUser(state, user) {
      Object.assign(state.user, user)
    },
  },
  actions: {
    async login({ commit }, payload) {
      commit('setAuth', { loading: true })
      let res = await call('login', {
        usr: payload.email,
        pwd: payload.password,
      })
      if (res) {
        commit('setAuth', {
          loading: false,
          user_id: getCookies().user_id,
        })
        return res
      }
      return false
    },
  },
})

export default store
