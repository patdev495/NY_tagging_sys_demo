import { describe, it, expect, beforeEach } from 'vitest';
import router from '../index';

describe('Router Customer Isolation and Navigation', () => {
  beforeEach(async () => {
    localStorage.clear();
    sessionStorage.clear();
    await router.push('/');
  });

  it('navigates to / (CustomerSelect) by default when no customer is selected in localStorage', async () => {
    await router.push('/');
    expect(router.currentRoute.value.path).toBe('/');
    expect(router.currentRoute.value.name).toBe('CustomerSelect');
  });

  it('routes to /packing/ui for UI customer flow', async () => {
    localStorage.setItem('selected_customer', 'UI');
    await router.push('/packing/ui');
    expect(router.currentRoute.value.path).toBe('/packing/ui');
    expect(router.currentRoute.value.name).toBe('UIPacking');
  });

  it('routes to /packing/erro for the Erro weight-scale flow', async () => {
    localStorage.setItem('selected_customer', 'ERRO');
    await router.push('/packing/erro');
    expect(router.currentRoute.value.path).toBe('/packing/erro');
    expect(router.currentRoute.value.name).toBe('ErroPacking');
  });

  it('redirects the temporary legacy route to /packing/erro', async () => {
    localStorage.setItem('selected_customer', 'ERRO');
    await router.push('/packing/a11');
    expect(router.currentRoute.value.path).toBe('/packing/erro');
    expect(router.currentRoute.value.name).toBe('ErroPacking');
  });

  it('always lands on / (CustomerSelect) on root path', async () => {
    localStorage.setItem('selected_customer', 'UI');
    await router.push('/');
    expect(router.currentRoute.value.path).toBe('/');
    expect(router.currentRoute.value.name).toBe('CustomerSelect');
  });
});
