const DEFAULT_REDIRECT = '/drive'

export function getLoginUrl(redirectTo = DEFAULT_REDIRECT) {
  const target =
    !redirectTo || redirectTo === '/drive/login' ? DEFAULT_REDIRECT : redirectTo
  return '/login?redirect-to=' + encodeURIComponent(target)
}

export function redirectToLogin(redirectTo) {
  window.location.href = getLoginUrl(redirectTo)
}
