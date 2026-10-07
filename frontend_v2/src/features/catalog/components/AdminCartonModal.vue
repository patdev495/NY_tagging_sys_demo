<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
    <form class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl space-y-4" @submit.prevent="submit">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-xl font-black text-slate-900">Tạo Carton Admin</h2>
          <p class="text-sm text-slate-500">{{ product?.item_name }} · <span class="font-semibold text-indigo-600">{{ templateBadgeName }}</span></p>
        </div>
        <button type="button" class="text-slate-400 hover:text-slate-600" @click="$emit('close')">✕</button>
      </div>

      <label class="block text-sm font-bold text-slate-700">
        Số thứ tự *
        <input v-model.number="form.sequence" min="1" required type="number" class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
      </label>

      <label class="block text-sm font-bold text-slate-700">
        Lý do tạo *
        <input v-model.trim="form.reason" required class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" placeholder="Ví dụ: Bổ sung lịch sử tem" />
      </label>

      <label class="block text-sm font-bold text-slate-700">
        Công lệnh *
        <input v-model.trim="form.job_order" required class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" placeholder="Ví dụ: JO-2026-001" />
      </label>

      <label class="block text-sm font-bold text-slate-700">
        Trọng lượng (kg) *
        <input v-model.number="form.weight" required type="number" step="0.001" class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
      </label>

      <!-- Thông báo cho tem không dùng PO/Lot (erro_02) -->
      <div v-if="templateType === 'erro_02'" class="rounded-lg bg-sky-50 border border-sky-200 p-3 text-xs text-sky-800 flex items-center gap-2">
        <i class="fas fa-info-circle text-sky-500"></i>
        <span>Mẫu tem <b>Erro 02 (Amazon SSCC)</b> tự sinh mã sê-ri chuẩn SSCC (00), không cần nhập PO và Lot.</span>
      </div>

      <!-- Trường PO động theo mẫu tem -->
      <label v-if="showPO" class="block text-sm font-bold text-slate-700">
        {{ poLabel }} <span v-if="isPORequired" class="text-rose-600">*</span>
        <input
          v-model.trim="form.po_number"
          :required="isPORequired"
          :placeholder="poPlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
        />
      </label>

      <!-- Trường LOT động theo mẫu tem -->
      <label v-if="showLot" class="block text-sm font-bold text-slate-700">
        {{ lotLabel }} <span v-if="isLotRequired" class="text-rose-600">*</span>
        <input
          v-model.trim="form.lot_number"
          :required="isLotRequired"
          :placeholder="lotPlaceholder"
          class="mt-1 w-full rounded-lg border border-slate-300 p-2 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
        />
      </label>

      <div class="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-900">
        Carton sẽ được tạo với Mã trạm <b>ADMIN</b>. Số đã tạo không thể thu hồi; in lỗi sẽ dùng chức năng In lại (Reprint).
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100" @click="$emit('close')">Hủy</button>
        <button :disabled="submitting" class="rounded-lg bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-sm font-bold text-white shadow-sm disabled:opacity-50 transition-colors">
          {{ submitting ? 'Đang tạo…' : 'Tạo và in' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Product } from '../../../types/api';

const { t } = useI18n();

const props = defineProps<{ show: boolean; product: Product | null; submitting: boolean }>();
const emit = defineEmits<{
  close: [];
  submit: [data: { sequence: number; reason: string; job_order: string; weight: number; po_number?: string; lot_number?: string }];
}>();

const form = reactive({ sequence: 1, reason: '', job_order: '', weight: 0, po_number: '', lot_number: '' });

const templateType = computed(() => props.product?.template_type || '');

const templateBadgeName = computed(() => {
  const map: Record<string, string> = {
    erro_01: 'Erro 01 (Carton SN + Rev)',
    erro_02: 'Erro 02 (Amazon SSCC)',
    erro_03: 'Erro 03 (Luxshare)',
    erro_04: 'Erro 04 (CAT5E/6A)',
    erro_05: 'Erro 05 (Dây nhảy)',
  };
  return map[templateType.value] || templateType.value || 'Standard';
});

// Logic PO:
// - erro_01: Bắt buộc
// - erro_02, erro_03: Không dùng trên tem -> Ẩn
// - erro_04: Bắt buộc
// - erro_05: Tùy chọn (in vào trường Batch)
const showPO = computed(() => {
  return ['erro_01', 'erro_04', 'erro_05'].includes(templateType.value);
});

const isPORequired = computed(() => {
  return ['erro_01', 'erro_04'].includes(templateType.value);
});

const poLabel = computed(() => {
  if (templateType.value === 'erro_05') return 'Mã đơn / Batch (PO)';
  return 'Mã Đơn Hàng (PO Number)';
});

const poPlaceholder = computed(() => {
  if (templateType.value === 'erro_05') return 'Ví dụ: B432-22156381 (tùy chọn)';
  return 'Ví dụ: B432-22156381';
});

// Logic LOT:
// - erro_01: Bắt buộc
// - erro_02, erro_04: Không dùng trên tem -> Ẩn
// - erro_03: Tùy chọn, mặc định 92607933
// - erro_05: Tùy chọn, mặc định theo ngày hiện tại
const showLot = computed(() => {
  return ['erro_01', 'erro_03', 'erro_05'].includes(templateType.value);
});

const isLotRequired = computed(() => {
  return templateType.value === 'erro_01';
});

const lotLabel = computed(() => {
  if (templateType.value === 'erro_03') return 'Mã Số Lô (Lot Number)';
  if (templateType.value === 'erro_05') return 'Mã Lô / Lot Code';
  return 'Mã Số Lô (Lot Number)';
});

const lotPlaceholder = computed(() => {
  if (templateType.value === 'erro_03') return 'Mặc định: 92607933 (để trống nếu dùng mặc định)';
  if (templateType.value === 'erro_05') return 'Mặc định: ngày hiện tại YYYYMMDD';
  return 'Ví dụ: 92607933';
});

watch(
  () => props.product,
  (product) => {
    form.sequence = 1;
    form.reason = '';
    form.job_order = '';
    form.weight = product?.target_weight ?? 0;
    form.po_number = '';
    form.lot_number = '';
  },
  { immediate: true }
);

const submit = () => {
  emit('submit', {
    ...form,
    po_number: showPO.value ? (form.po_number?.trim() || undefined) : undefined,
    lot_number: showLot.value ? (form.lot_number?.trim() || undefined) : undefined,
  });
};
</script>
