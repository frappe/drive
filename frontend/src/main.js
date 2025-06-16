import { createApp } from "vue"
import {
  FrappeUI,
  Button,
  onOutsideClickDirective,
  setConfig,
  frappeRequest,
} from "frappe-ui"
import store from "./store"
import translationPlugin from "./translation"
import router from "./router"
import App from "./App.vue"
import emitter from "@/emitter"
import "./index.css"
import VueTippy from "vue-tippy"
import { initSocket, RealTimeHandler } from "./socket"

const app = createApp(App)
setConfig("resourceFetcher", frappeRequest)
app.config.unwrapInjectedRef = true
app.config.globalProperties.emitter = emitter
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
app.use(
  VueTippy,
  // optional
  {
    directive: "tippy", // => v-tippy
    component: "tippy", // => <tippy/>
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
