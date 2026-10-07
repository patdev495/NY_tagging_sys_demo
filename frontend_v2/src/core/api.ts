import axios, { type AxiosInstance } from 'axios';

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.DEV 
    ? `http://${window.location.hostname}:8001/api/v1` 
    : '/api/v1',
});

// Request Interceptor: Attach Bearer Token
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response Interceptor: Handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isLoginRoute = window.location.pathname.includes('/admin/login');
      if (!isLoginRoute && window.location.pathname.startsWith('/admin')) {
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_user');
        sessionStorage.removeItem('admin_session');
        window.location.href = `/admin/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
