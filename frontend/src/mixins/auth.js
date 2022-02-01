export function checkAuthenticationStatus() {
  let cookie = Object.fromEntries(
    document.cookie
      .split('; ')
      .map((part) => part.split('='))
      .map((d) => [d[0], decodeURIComponent(d[1])])
  )
  let isLoggedIn = cookie.user_id && cookie.user_id !== 'Guest'
  return [cookie, isLoggedIn]
}

export default {
  data() {
    return {
      auth: {
        isLoggedIn: false,
        user: null,
        user_image: null,
        cookie: null,
      },
    }
  },
  created() {
    [this.auth.cookie, this.auth.isLoggedIn] = checkAuthenticationStatus()
  },
}
