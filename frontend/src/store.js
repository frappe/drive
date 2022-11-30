import { createStore } from 'vuex';
import { call } from 'frappe-ui';

let getCookies = () => {
  return Object.fromEntries(
    document.cookie
      .split('; ')
      .map((cookie) => cookie.split('='))
      .map((entry) => [entry[0], decodeURIComponent(entry[1])])
  );
};

const store = createStore({
  state: {
    auth: {
      loading: false,
      user_id: getCookies().user_id,
    },
    user: {
      fullName: getCookies().full_name,
      imageURL: getCookies().user_image,
    },
    uploads: [],
    sortOrder: JSON.parse(localStorage.getItem('sortOrder')) || {
      label: 'Modified',
      field: 'modified',
      ascending: false,
    },
    view: JSON.parse(localStorage.getItem('view')) || 'grid',
    entityInfo: null,
    showInfo: false,
    hasWriteAccess: false,
  },
  getters: {
    isLoggedIn: (state) => {
      return state.auth.user_id && state.auth.user_id !== 'Guest';
    },
    uploadsInProgress: (state) => {
      return state.uploads.filter((upload) => !upload.completed);
    },
    uploadsCompleted: (state) => {
      return state.uploads.filter((upload) => upload.completed);
    },
  },
  mutations: {
    setAuth(state, auth) {
      Object.assign(state.auth, auth);
    },
    setUser(state, user) {
      Object.assign(state.user, user);
    },
    setUploads(state, uploads) {
      state.uploads = uploads;
    },
    pushToUploads(state, upload) {
      state.uploads.push(upload);
    },
    updateUpload(state, payload) {
      let index = state.uploads.findIndex(
        (upload) => upload.uuid == payload.uuid
      );
      Object.assign(state.uploads[index], payload);
    },
    setSortOrder(state, payload) {
      localStorage.setItem('sortOrder', JSON.stringify(payload));
      state.sortOrder = payload;
    },
    toggleView(state, payload) {
      localStorage.setItem('view', JSON.stringify(payload));
      state.view = payload;
    },
    setEntityInfo(state, payload) {
      state.entityInfo = payload;
    },
    setShowInfo(state, payload) {
      state.showInfo = payload;
    },
    setHasWriteAccess(state, payload) {
      state.hasWriteAccess = payload;
    },
  },
  actions: {
    async login({ commit }, payload) {
      commit('setAuth', { loading: true });
      let res = await call('login', {
        usr: payload.email,
        pwd: payload.password,
      });
      if (res) {
        commit('setAuth', {
          loading: false,
          user_id: getCookies().user_id,
        });
        commit('setUser', {
          fullName: getCookies().full_name,
          imageURL: getCookies().user_image
            ? window.location.origin + getCookies().user_image
            : null,
        });
        return res;
      }
      return false;
    },
    async logout({ commit }) {
      commit('setAuth', { loading: true });
      await call('logout');
      window.location.reload();
    },
    clearUploads({ commit }) {
      commit('setUploads', []);
    },
  },
});

export default store;
