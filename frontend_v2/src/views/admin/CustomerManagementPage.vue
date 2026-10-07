<template>
  <div class="p-8">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900">Customer Management</h1>
        <p class="text-slate-500">Add, edit, or remove customer information in the system.</p>
      </div>
      <button v-if="authStore.isAdmin" @click="openCreateModal" class="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-colors shadow-md">
        <Plus class="w-5 h-5" />
        Add Customer
      </button>
    </div>

    <!-- Search bar -->
    <div class="mb-6 relative">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
      <input 
        v-model="searchQuery"
        type="text" 
        placeholder="Search by code or name..." 
        class="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
      >
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200">
            <th class="p-4 font-semibold text-slate-700">ID</th>
            <th class="p-4 font-semibold text-slate-700">Customer Code</th>
            <th class="p-4 font-semibold text-slate-700">Customer Name</th>
            <th v-if="authStore.isAdmin" class="p-4 font-semibold text-slate-700 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="customer in filteredCustomers" :key="customer.id" class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
            <td class="p-4 text-slate-500 text-sm">#{{ customer.id }}</td>
            <td class="p-4 font-bold text-indigo-900">{{ customer.code }}</td>
            <td class="p-4 text-slate-700">{{ customer.name }}</td>
            <td v-if="authStore.isAdmin" class="p-4 text-right">
              <div class="flex justify-end gap-2">
                <button @click="openEditModal(customer)" class="p-2 text-slate-400 hover:text-indigo-600 transition-colors" title="Edit">
                  <Edit2 class="w-5 h-5" />
                </button>
                <button @click="confirmDelete(customer)" class="p-2 text-slate-400 hover:text-red-600 transition-colors" title="Delete">
                  <Trash2 class="w-5 h-5" />
                </button>
              </div>
            </td>
          </tr>

          <tr v-if="filteredCustomers.length === 0">
            <td colspan="4" class="p-12 text-center text-slate-400 italic">No customers found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Form -->
    <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-indigo-900 text-white">
          <h2 class="text-xl font-bold">{{ isEdit ? 'Update Customer' : 'Add New Customer' }}</h2>
          <button @click="showModal = false" class="hover:bg-white/20 p-1 rounded-lg transition-colors">
            <X class="w-6 h-6" />
          </button>
        </div>
        
        <form @submit.prevent="saveCustomer" class="p-6 space-y-4">
          <div class="space-y-1">
            <label class="text-sm font-semibold text-slate-700">Customer Code</label>
            <input 
              v-model="form.code"
              type="text" 
              required
              placeholder="e.g. APPLE, SAMSUNG..." 
              class="w-full p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
              :disabled="isEdit"
            >
            <p class="text-xs text-slate-400">This code is usually an abbreviation, used to generate carton S/Ns.</p>
          </div>
          
          <div class="space-y-1">
            <label class="text-sm font-semibold text-slate-700">Customer Name</label>
            <input 
              v-model="form.name"
              type="text" 
              required
              placeholder="Enter full name..." 
              class="w-full p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
            >
          </div>

          <div class="pt-4 flex gap-3">
            <button type="button" @click="showModal = false" class="flex-1 px-4 py-3 rounded-lg border border-slate-200 font-semibold text-slate-600 hover:bg-slate-50 transition-colors">
              Cancel
            </button>
            <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-3 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors shadow-md disabled:opacity-50">
              {{ isSubmitting ? 'Saving...' : 'Save Information' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Plus, Search, Edit2, Trash2, X } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import catalogApi from '../../features/catalog/api';
import { useSystemStore } from '../../core/stores/system';
import { useAuthStore } from '../../core/stores/auth';
import type { Customer } from '../../types/api';

const { t } = useI18n();

const system = useSystemStore();
const authStore = useAuthStore();
const customers = ref<Customer[]>([]);

const searchQuery = ref<string>('');
const showModal = ref<boolean>(false);
const isEdit = ref<boolean>(false);
const isSubmitting = ref<boolean>(false);
const currentId = ref<number | null>(null);

const form = ref<{
  code: string;
  name: string;
}>({
  code: '',
  name: ''
});

const filteredCustomers = computed(() => {
  if (!searchQuery.value) return customers.value;
  const q = searchQuery.value.toLowerCase();
  return customers.value.filter(c => 
    c.code.toLowerCase().includes(q) || 
    c.name.toLowerCase().includes(q)
  );
});

const fetchCustomers = async () => {
  try {
    const res = await catalogApi.getCustomers();
    customers.value = res.data;
  } catch (err) {
    system.showNotification(t('customers.load_failed'), 'error');
  }
};

const openCreateModal = () => {
  isEdit.value = false;
  currentId.value = null;
  form.value = { code: '', name: '' };
  showModal.value = true;
};

const openEditModal = (customer: Customer) => {
  isEdit.value = true;
  currentId.value = customer.id;
  form.value = { code: customer.code, name: customer.name };
  showModal.value = true;
};

const saveCustomer = async () => {
  isSubmitting.value = true;
  try {
    if (isEdit.value && currentId.value !== null) {
      await catalogApi.updateCustomer(currentId.value, form.value);
      system.showNotification(t('customers.update_success'), 'success');
    } else {
      await catalogApi.createCustomer(form.value);
      system.showNotification(t('customers.create_success'), 'success');
    }
    showModal.value = false;
    await fetchCustomers();
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'Error saving data';
    system.showNotification(msg, 'error');
  } finally {
    isSubmitting.value = false;
  }
};

const confirmDelete = async (customer: Customer) => {
  if (confirm(`Are you sure you want to delete customer "${customer.name}"? This action cannot be undone.`)) {
    try {
      await catalogApi.deleteCustomer(customer.id);
      system.showNotification(t('customers.delete_success'), 'success');
      await fetchCustomers();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Could not delete this customer (possibly due to related data)';
      system.showNotification(msg, 'error');
    }
  }
};

onMounted(fetchCustomers);
</script>
