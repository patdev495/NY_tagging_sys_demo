<template>
  <div class="h-screen flex items-center justify-center bg-linear-to-br from-slate-950 to-indigo-950 text-white relative">
    <!-- Top-right language switch -->
    <div class="absolute top-6 right-6 z-10 flex items-center gap-2">
      <LanguageSwitch variant="dark" />
    </div>

    <div class="w-full max-w-[420px] p-10 bg-white/5 backdrop-blur-2xl border border-white/10 rounded-[24px] shadow-2xl animate-in">
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-linear-to-tr from-blue-500 to-violet-500 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl shadow-[0_0_20px_rgba(59,130,246,0.5)]">
          <i class="fas fa-user-shield"></i>
        </div>
        <h2 class="m-0 text-[1.5rem] font-bold tracking-tight">{{ t('admin.login_title') }}</h2>
        <p class="text-slate-400 text-[0.85rem] mt-2">{{ t('admin.login_system_subtitle') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="flex flex-col gap-5">
        <!-- Username Field -->
        <div class="flex flex-col gap-1.5">
          <label for="username" class="text-[0.75rem] font-semibold uppercase tracking-wider text-slate-400">{{ t('admin.username') }}</label>
          <div class="relative flex items-center">
            <i class="fas fa-user absolute left-4 text-slate-500"></i>
            <input 
              id="username"
              v-model="username" 
              type="text" 
              :placeholder="t('admin.username_placeholder')" 
              required
              ref="userInput"
              class="w-full pl-12 pr-4 py-3 bg-slate-900/60 border border-white/10 rounded-xl text-white text-[1rem] outline-none transition-all focus:border-blue-500 focus:bg-slate-900/80 focus:ring-4 focus:ring-blue-500/10"
            />
          </div>
        </div>

        <!-- Password Field -->
        <div class="flex flex-col gap-1.5">
          <label for="password" class="text-[0.75rem] font-semibold uppercase tracking-wider text-slate-400">{{ t('admin.password') }}</label>
          <div class="relative flex items-center">
            <i class="fas fa-lock absolute left-4 text-slate-500"></i>
            <input 
              id="password"
              v-model="password" 
              type="password" 
              placeholder="••••••••" 
              required
              class="w-full pl-12 pr-4 py-3 bg-slate-900/60 border border-white/10 rounded-xl text-white text-[1rem] outline-none transition-all focus:border-blue-500 focus:bg-slate-900/80 focus:ring-4 focus:ring-blue-500/10"
            />
          </div>
          <p v-if="error" class="text-rose-400 text-[0.8rem] font-medium mt-1">{{ error }}</p>
        </div>

        <button type="submit" :disabled="loading" class="mt-2 p-3.5 bg-blue-500 text-white border-none rounded-xl font-bold text-[1rem] cursor-pointer transition-all flex items-center justify-center hover:bg-blue-600 hover:-translate-y-0.5 hover:shadow-[0_10px_20px_-10px_rgba(37,99,235,0.5)] active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed">
          <span v-if="!loading">{{ t('admin.login') }}</span>
          <i v-else class="fas fa-spinner fa-spin"></i>
        </button>
        
        <router-link to="/" class="text-center text-slate-400 no-underline text-[0.85rem] font-medium flex items-center justify-center gap-2 mt-2 transition-colors hover:text-white">
          <i class="fas fa-arrow-left"></i> {{ t('admin.return_packing') }}
        </router-link>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../../core/stores/auth';
import { userErrorMessage } from '../../i18n/errorMessage';
import LanguageSwitch from '../../core/components/LanguageSwitch.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const username = ref<string>('admin');
const password = ref<string>('');
const error = ref<string>('');
const loading = ref<boolean>(false);
const userInput = ref<HTMLInputElement | null>(null);

const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    await authStore.login(username.value, password.value);
    const redirectPath = (route.query.redirect as string) || '/admin';
    router.push(redirectPath);
  } catch (err: unknown) {
    error.value = userErrorMessage(err, t);
    password.value = '';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (userInput.value) userInput.value.focus();
});
</script>
