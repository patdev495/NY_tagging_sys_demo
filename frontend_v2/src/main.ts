import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './core/router';
import i18n from './i18n';
import './index.css';

const app = createApp(App);
app.use(createPinia());
app.use(i18n);
app.use(router);
app.mount('#app');
