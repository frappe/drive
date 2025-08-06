import { createApp } from "vue"
import {
  FrappeUI,
  FormControl,
  onOutsideClickDirective,
  setConfig,
  frappeRequest,
  Button
} from "frappe-ui"

import store from "./store"
import translationPlugin from "./translation"
import router from "./router"
import App from "./App.vue"
import emitter from "@/emitter"
import "./index.css"
import VueTippy from "vue-tippy"
import { initSocket, RealTimeHandler } from "./socket"
import focusDirective from './utils/focus'
import { allUsers } from "@/resources/permissions"

const app = createApp(App)
setConfig("resourceFetcher", frappeRequest)
app.config.unwrapInjectedRef = true
app.config.globalProperties.emitter = emitter
app.config.globalProperties.$user = (user) => {
  return allUsers.data?.find?.((k) => k.name === user)
}

app.provide("emitter", emitter)
app.use(translationPlugin)
app.use(router)
app.use(store)

app.use(FrappeUI, { socketio: false })
const socket = initSocket()
const realtime = new RealTimeHandler(socket)

app.provide("realtime", realtime)
app.config.globalProperties.$realtime = realtime

app.directive("on-outside-click", onOutsideClickDirective)
app.directive("focus", focusDirective)

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

app.component("FormControl", FormControl)
app.component("Button", Button)

app.mount("#app")
