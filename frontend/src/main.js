import { createApp } from 'vue';
import { FrappeUI, Button, onOutsideClickDirective, setConfig, frappeRequest } from 'frappe-ui';
import store from './store';
import router from './router';
import App from './App.vue';
import mitt from 'mitt';
import './index.css';

setConfig('resourceFetcher', frappeRequest)
const emitter = mitt();

const app = createApp(App);
app.config.globalProperties.emitter = emitter;
app.use(router);
app.use(store);
app.use(FrappeUI);
app.directive('on-outside-click', onOutsideClickDirective);
app.component('Button', Button);
app.mount('#app');
