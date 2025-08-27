import emitter from "@/emitter"
import {
  Button,
  frappeRequest,
  FrappeUI,
  onOutsideClickDirective,
  setConfig,
} from "frappe-ui"
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import { definePreset } from '@primevue/themes'
import { createApp } from "vue"
import VueTippy from "vue-tippy"

// Custom theme preset
const customPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{blue.50}',
      100: '{blue.100}',
      200: '{blue.200}',
      300: '{blue.300}',
      400: '{blue.400}',
      500: '#0149C1', // Màu primary của bạn
      600: '#013a9c',
      700: '{blue.700}',
      800: '{blue.800}',
      900: '{blue.900}',
      950: '{blue.950}'
    }
  }
})

import App from "./App.vue"
import "./index.css"
import router from "./router"
import { initSocket, RealTimeHandler } from "./socket"
import store from "./store"
import translationPlugin from "./translation"

const app = createApp(App)

setConfig("resourceFetcher", frappeRequest)
app.config.unwrapInjectedRef = true
app.config.globalProperties.emitter = emitter
app.provide("emitter", emitter)
app.use(translationPlugin)
app.use(router)
app.use(store)

// Cấu hình PrimeVue với theme custom
app.use(PrimeVue, {
  theme: {
    preset: customPreset,
    options: {
      prefix: 'p',
      darkModeSelector: 'system',
      cssLayer: false
    }
  }
})

app.use(FrappeUI, { socketio: false })
const socket = initSocket()
const realtime = new RealTimeHandler(socket)
app.provide("realtime", realtime)
app.config.globalProperties.$realtime = realtime
app.directive("on-outside-click", onOutsideClickDirective)
app.use(
  VueTippy,
  {
    directive: "tippy",
    component: "tippy",
  }
)
app.directive("focus", {
  mounted: (el) => el.focus(),
})

setConfig("resourceFetcher", (options) => {
  return frappeRequest({
    ...options,
    onError(err) {
      if (err.messages && err.messages[0]) {
        return
      }
    },
  })
})

app.component("Button", Button)
app.mount("#app")