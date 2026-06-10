import { createApp } from 'vue'
import {
  FrappeUI,
  FormControl,
  onOutsideClickDirective,
  setConfig,
  frappeRequest,
  Button,
} from 'frappe-ui'

import store from './store'
import router from './router'
import App from './App.vue'
import emitter from '@/emitter'
import './index.css'
import { initSocket } from './socket'
import focusDirective from './utils/focus'
import translation from './translation'
import { setupTheme } from './utils/setupTheme'

const app = createApp(App)
setConfig('resourceFetcher', frappeRequest)
app.config.unwrapInjectedRef = true
app.config.globalProperties.emitter = emitter

app.provide('emitter', emitter)
app.use(router)
app.use(store)
app.use(translation, 'drive.api.product.get_translations')

app.use(FrappeUI, { socketio: false })
app.provide('socket', initSocket())

app.directive('on-outside-click', onOutsideClickDirective)
app.directive('focus', focusDirective)

setConfig('resourceFetcher', (options) => {
  return frappeRequest({
    ...options,
    onError(err) {
      if (err.messages && err.messages[0]) {
        return
      }
    },
  })
})

app.component('FormControl', FormControl)
app.component('Button', Button)

setupTheme().then(() => app.mount('#app'))
