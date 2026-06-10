import { frappeRequest } from 'frappe-ui'
import store from '@/store'

const systemTheme = window.matchMedia('(prefers-color-scheme: dark)')

export function getThemeMode() {
  return document.documentElement.getAttribute('data-theme-mode') || 'light'
}

function resolveTheme(mode) {
  const preference = mode.toLowerCase()
  if (preference === 'automatic') {
    return systemTheme.matches ? 'dark' : 'light'
  }
  return preference
}

function applyTheme(mode) {
  const root = document.documentElement
  const preference = mode.toLowerCase()
  const resolved = resolveTheme(preference)

  root.classList.add('theme-switching')
  root.style.colorScheme = resolved
  root.setAttribute('data-theme', resolved)
  root.setAttribute('data-theme-mode', preference)

  requestAnimationFrame(() => {
    root.classList.remove('theme-switching')
  })
}

export async function setupTheme() {
  if (import.meta.env.DEV) {
    if (store.getters.isLoggedIn) {
      const boot = await frappeRequest({
        url: 'drive.www.drive.get_context_for_dev',
        method: 'POST',
      })
      applyTheme(boot?.desk_theme || 'Light')
    } else {
      applyTheme('Light')
    }
  } else {
    applyTheme(getThemeMode())
  }

  systemTheme.addEventListener('change', () => {
    if (getThemeMode() === 'automatic') applyTheme('automatic')
  })
}

export function switchTheme(theme) {
  applyTheme(theme)

  if (store.getters.isLoggedIn) {
    frappeRequest({
      url: 'frappe.core.doctype.user.user.switch_theme',
      params: { theme },
    })
  }
}
