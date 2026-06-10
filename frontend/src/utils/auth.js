export function redirectToLogin(redirectTo = '/drive') {
  window.location.href =
    '/login?redirect-to=' + encodeURIComponent(redirectTo)
}

export function loginRedirectTarget(path) {
  return path === '/login' ? '/drive' : '/drive' + path
}
