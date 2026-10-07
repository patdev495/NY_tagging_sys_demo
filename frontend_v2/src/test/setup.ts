import { config } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import i18n from '../i18n';

const pinia = createPinia();
setActivePinia(pinia);
config.global.plugins = [i18n, pinia];
