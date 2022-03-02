import { createApp } from 'vue'
import { FrappeUI, Button } from 'frappe-ui'
import store from './store'
import router from './router'
import App from './App.vue'
import './index.css'

let app = createApp(App)
app.use(router)
app.use(store)
app.use(FrappeUI)
app.component('Button', Button)
app.config.unwrapInjectedRef = true // Will no longer be required after Vue 3.3
app.mount('#app')
