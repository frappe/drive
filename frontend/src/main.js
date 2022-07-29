import { createApp } from 'vue';
import { FrappeUI, Button } from 'frappe-ui';
import store from './store';
import router from './router';
import App from './App.vue';
import './index.css';

const app = createApp(App);
app.use(router);
app.use(store);
app.use(FrappeUI);
app.component('Button', Button);
app.mount('#app');
