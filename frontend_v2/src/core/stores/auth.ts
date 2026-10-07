import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api';

export interface AuthUser {
  id: number;
  username: string;
  role: 'admin' | 'qa' | string;
  full_name?: string;
  is_active?: number;
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(sessionStorage.getItem('auth_token'));
  const user = ref<AuthUser | null>(
    sessionStorage.getItem('auth_user')
      ? JSON.parse(sessionStorage.getItem('auth_user')!)
      : null
  );

  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const isQA = computed(() => user.value?.role === 'qa');
  const roleName = computed(() => (user.value?.role || '').toUpperCase());

  async function login(username: string, password: string) {
    const res = await api.post('/auth/login', { username, password });
    const data = res.data;
    
    token.value = data.access_token;
    user.value = data.user;
    
    sessionStorage.setItem('auth_token', data.access_token);
    sessionStorage.setItem('auth_user', JSON.stringify(data.user));
    // Keep backward compatibility for router guard
    sessionStorage.setItem('admin_session', 'true');
    
    return data.user;
  }

  function logout() {
    token.value = null;
    user.value = null;
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_user');
    sessionStorage.removeItem('admin_session');
  }

  async function fetchCurrentUser() {
    if (!token.value) return null;
    try {
      const res = await api.get('/auth/me');
      user.value = res.data;
      sessionStorage.setItem('auth_user', JSON.stringify(res.data));
      return res.data;
    } catch (e) {
      logout();
      return null;
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isQA,
    roleName,
    login,
    logout,
    fetchCurrentUser
  };
});
