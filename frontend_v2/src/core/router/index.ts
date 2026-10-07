import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import CustomerSelectPage from '../../views/CustomerSelectPage.vue';
import UIPackingPage from '../../views/UIPackingPage.vue';
import ErroPackingPage from '../../views/ErroPackingPage.vue';
import AdminLayout from '../layouts/AdminLayout.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'CustomerSelect',
    component: CustomerSelectPage,
  },
  {
    path: '/packing/ui',
    name: 'UIPacking',
    component: UIPackingPage,
  },
  {
    path: '/packing/erro',
    name: 'ErroPacking',
    component: ErroPackingPage,
  },
  {
    path: '/packing/a11',
    redirect: '/packing/erro',
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../../views/admin/DashboardPage.vue'),
      },
      {
        path: 'production-runs',
        name: 'ProductionRuns',
        component: () => import('../../views/admin/ProductionRunsPage.vue'),
      },
      {
        path: 'customers',
        name: 'CustomerManagement',
        component: () => import('../../views/admin/CustomerManagementPage.vue'),
      },
      {
        path: 'products',
        name: 'ProductManagement',
        component: () => import('../../views/admin/ProductManagementPage.vue'),
      },
      {
        path: 'history',
        name: 'CartonHistory',
        component: () => import('../../views/admin/CartonHistoryPage.vue'),
      },
      {
        path: 'stats',
        name: 'SNLookup',
        component: () => import('../../views/admin/SNLookupPage.vue'),
      },
    ]
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../../views/admin/LoginPage.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  // Check for admin routes
  if (to.path.startsWith('/admin')) {
    if (to.name === 'AdminLogin') {
      next();
      return;
    }

    const isAuthenticated = !!sessionStorage.getItem('auth_token') || sessionStorage.getItem('admin_session') === 'true';
    if (isAuthenticated) {
      next();
    } else {
      next({ name: 'AdminLogin', query: { redirect: to.fullPath } });
    }
    return;
  }

  next();
});


export default router;
