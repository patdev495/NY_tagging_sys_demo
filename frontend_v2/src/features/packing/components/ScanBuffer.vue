<template>
  <div class="mb-3">
    <!-- Top indicator: Scanner State + Helper -->
    <div class="flex items-center justify-between px-1 mb-1.5 text-xs font-semibold">
      <div class="flex items-center gap-1.5">
        <span class="relative flex h-2 w-2">
          <span v-if="!isInputDisabled && jobOrder" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span :class="['relative inline-flex rounded-full h-2 w-2', (!isInputDisabled && jobOrder) ? 'bg-emerald-500' : (awaitingNext ? 'bg-amber-500' : 'bg-slate-400')]"></span>
        </span>
        <span :class="(!isInputDisabled && jobOrder) ? 'text-emerald-700 font-bold uppercase tracking-wide' : (awaitingNext ? 'text-amber-700 font-bold uppercase tracking-wide' : 'text-slate-500')">
          {{ (!disabled && jobOrder) ? (awaitingNext ? t('packing.waiting_next_carton_indicator') : t('packing.ready_to_scan')) : t('packing.scan_locked') }}
        </span>
      </div>

      <div class="text-slate-400 text-[11px] font-mono">
        <span v-if="!disabled && jobOrder">{{ awaitingNext ? t('packing.shortcut_space_next') : t('packing.shortcut_enter_scan_space_next') }}</span>
      </div>
    </div>

    <!-- Main Scanner Input Bar -->
    <div class="flex gap-2 items-stretch">
      <div class="relative flex-1 min-w-0">
        <input 
          type="text"
          :value="scanBuffer"
          @input="handleInput"
          @keydown.enter.prevent="!isInputDisabled && $emit('scan')"
          @keydown.space="handleSpace"
          :placeholder="disabled ? placeholder : (awaitingNext ? t('packing.scan_prompt_awaiting_next') : (!jobOrder ? t('packing.scan_prompt_job') : t('packing.scan_item_placeholder')))"
          ref="scanInput"
          :disabled="isInputDisabled"
          autocomplete="off"
          autocorrect="off"
          spellcheck="false"
          class="w-full h-12 md:h-14 px-4 bg-white border-2 rounded-xl text-slate-900 text-base md:text-lg font-barcode-mono font-bold text-center transition-all outline-none shadow-xs"
          :class="[
            isInputDisabled 
              ? (awaitingNext 
                  ? 'bg-amber-50/70 border-amber-400 text-amber-800 cursor-not-allowed select-none' 
                  : 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed')
              : (flashState === 'fail' 
                  ? 'border-rose-600 bg-rose-50 text-rose-900 animate-scan-fail' 
                  : (flashState === 'pass' 
                      ? 'border-emerald-600 bg-emerald-50 text-emerald-900 animate-scan-pass' 
                      : 'border-slate-300 hover:border-slate-400 focus:border-emerald-600 focus:ring-4 focus:ring-emerald-500/15 focus:bg-white')),
            hasErrors ? 'animate-shake' : ''
          ]"
        />
        <!-- Barcode icon overlay inside input -->
        <div class="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
          <i class="fas fa-barcode text-lg"></i>
        </div>
      </div>

      <!-- Action Button Next Carton -->
      <button 
        v-if="awaitingNext" 
        @click="handleNextCartonClick" 
        class="px-5 h-12 md:h-14 bg-emerald-600 hover:bg-emerald-700 text-white border border-emerald-700 rounded-xl font-bold flex items-center gap-2 whitespace-nowrap shadow-sm transition-all shrink-0 cursor-pointer"
        :class="hasErrors ? 'opacity-50 cursor-not-allowed grayscale-[40%]' : 'active:scale-95 animate-pulse-gentle'"
        :disabled="disabled || hasErrors"
        :title="hasErrors ? t('packing.clear_errors_before_next') : t('packing.next_carton_title')"
      >
        <i class="fas fa-plus-circle text-base"></i>
        <span>{{ t('packing.next_carton') }}</span>
        <span class="text-[10px] font-barcode-mono font-black px-1.5 py-0.5 bg-black/25 rounded tracking-wider">Space</span>
      </button>

      <!-- Action Button Pack Now (Partial) -->
      <button 
        v-else-if="allowPartial && scannedCount > 0 && jobOrder" 
        @click="$emit('pack-now')" 
        class="px-5 h-12 md:h-14 bg-blue-600 hover:bg-blue-700 text-white border border-blue-700 rounded-xl font-bold cursor-pointer flex items-center gap-2 whitespace-nowrap shadow-sm transition-all shrink-0 active:scale-95"
        :disabled="disabled"
        :title="t('packing.pack_now_title')"
      >
        <i class="fas fa-box-open text-base"></i>
        <span>{{ t('packing.pack_now') }}</span>
      </button>
    </div>

    <!-- Status Hints -->
    <div class="mt-1.5 px-1 min-h-[20px] flex items-center justify-center">
      <p class="text-xs text-rose-600 font-bold flex items-center gap-1.5" v-if="awaitingNext && hasErrors && !disabled">
        <i class="fas fa-exclamation-triangle"></i> {{ t('packing.clear_errors_before_next') }}
      </p>
      <p class="text-xs text-amber-700 font-bold flex items-center gap-1.5" v-else-if="awaitingNext && !disabled">
        <i class="fas fa-check-circle text-emerald-600"></i> {{ t('packing.carton_complete_hint') }}
      </p>
      <p class="text-xs text-rose-600 font-bold flex items-center gap-1.5" v-else-if="disabled && placeholder.includes('AGENT')">
        <i class="fas fa-plug-circle-xmark"></i> {{ t('packing.agent_offline_hint') }}
      </p>
      <p class="text-xs text-slate-500 font-medium" v-else-if="jobOrder && !disabled">
        {{ t('packing.waiting_scanner') }}
      </p>
    </div>

    <!-- Overflow Scans Area -->
    <div v-if="overflowScans.length > 0" class="mt-3 bg-amber-50 border border-amber-300 rounded-xl overflow-hidden shadow-xs animate-in">
      <div class="px-3.5 py-2 bg-amber-100/70 border-b border-amber-300 flex justify-between items-center text-amber-900 text-xs font-bold">
        <span class="flex items-center gap-1.5">
          <i class="fas fa-triangle-exclamation text-amber-600"></i> 
          {{ t('packing.overflow_title', { count: overflowScans.length }) }}
        </span>
        <button @click="$emit('clear-overflow')" class="bg-white border border-amber-300 text-amber-800 px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer hover:bg-amber-50">
          {{ t('packing.clear') }}
        </button>
      </div>
      <div class="max-h-[140px] overflow-y-auto p-2">
        <div v-for="(item, idx) in overflowScans" :key="idx" class="flex justify-between items-center px-3 py-1.5 bg-white rounded-lg mb-1 border border-amber-200 text-xs">
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-bold text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded">#{{ idx + 1 }}</span>
            <span class="font-barcode-mono font-bold text-slate-900 text-sm">{{ item.sn }}</span>
          </div>
          <span class="text-[11px] text-slate-400 font-mono">{{ item.time }}</span>
        </div>
      </div>
    </div>

    <!-- Invalid Scans Area -->
    <div v-if="invalidScans.length > 0" class="mt-3 bg-rose-50 border border-rose-300 rounded-xl overflow-hidden shadow-xs animate-in">
      <div class="px-3.5 py-2 bg-rose-100/70 border-b border-rose-300 flex justify-between items-center text-rose-900 text-xs font-bold">
        <span class="flex items-center gap-1.5">
          <i class="fas fa-circle-exclamation text-rose-600"></i> 
          {{ t('packing.invalid_scans_title') }} ({{ invalidScans.length }})
        </span>
        <button @click="$emit('clear-invalid')" class="bg-white border border-rose-300 text-rose-800 px-2 py-0.5 rounded text-[11px] font-bold cursor-pointer hover:bg-rose-50">
          {{ t('packing.clear') }}
        </button>
      </div>
      <div class="max-h-[140px] overflow-y-auto p-2">
        <div v-for="(err, idx) in [...invalidScans].reverse()" :key="idx" class="flex justify-between items-center px-3 py-1.5 bg-white rounded-lg mb-1 border border-rose-200 border-l-4 border-l-rose-500 text-xs">
          <div class="flex items-center gap-2">
            <span class="font-barcode-mono font-bold text-rose-700 text-sm">{{ err.sn }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider bg-rose-100 text-rose-800">
              {{ err.reason }}
            </span>
          </div>
          <span class="text-[11px] text-slate-400 font-mono">{{ err.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface InvalidScan {
  sn: string;
  time: string;
  type?: string;
  reason: string;
}

interface OverflowScan {
  sn: string;
  time: string;
}

const props = defineProps<{
  scanBuffer: string;
  jobOrder: string;
  awaitingNext: boolean;
  invalidScans: InvalidScan[];
  overflowScans: OverflowScan[];
  allowPartial: boolean;
  scannedCount: number;
  disabled: boolean;
  placeholder: string;
}>();

const emit = defineEmits<{
  (e: 'update:scanBuffer', val: string): void;
  (e: 'scan'): void;
  (e: 'next-carton'): void;
  (e: 'pack-now'): void;
  (e: 'clear-invalid'): void;
  (e: 'clear-overflow'): void;
}>();

const scanInput = ref<HTMLInputElement | null>(null);
const flashState = ref<'pass' | 'fail' | ''>('');
let flashTimer: ReturnType<typeof setTimeout> | null = null;
let focusLockTimer: ReturnType<typeof setInterval> | null = null;

const isInputDisabled = computed(() => props.disabled || props.awaitingNext);
const hasErrors = computed(() => (props.invalidScans?.length > 0) || (props.overflowScans?.length > 0));

const triggerFlash = (state: 'pass' | 'fail') => {
  flashState.value = state;
  if (flashTimer) clearTimeout(flashTimer);
  flashTimer = setTimeout(() => {
    flashState.value = '';
  }, 500);
};

// Watch for invalid scans increase to trigger fail animation
watch(() => props.invalidScans?.length, (newLen, oldLen) => {
  if (newLen && oldLen !== undefined && newLen > oldLen) {
    triggerFlash('fail');
  }
});

// Watch scanned count increase to trigger pass animation
watch(() => props.scannedCount, (newCount, oldCount) => {
  if (newCount > (oldCount || 0)) {
    triggerFlash('pass');
  }
});

const handleInput = (e: Event) => emit('update:scanBuffer', (e.target as HTMLInputElement).value);

const handleSpace = (e: KeyboardEvent) => {
  if (props.awaitingNext) {
    e.preventDefault();
    if (!hasErrors.value && !props.disabled) {
      emit('next-carton');
    }
  }
};

const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if (props.awaitingNext && (e.code === 'Space' || e.key === ' ')) {
    const target = e.target as HTMLElement;
    // Do not intercept if user is typing inside an editable field other than scan input
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
      if (target !== scanInput.value) return;
    }
    e.preventDefault();
    if (!hasErrors.value && !props.disabled) {
      emit('next-carton');
    }
  }
};

const handleNextCartonClick = () => {
  if (!hasErrors.value && !props.disabled) {
    emit('next-carton');
  }
};

const focusScan = () => {
  if (scanInput.value && !isInputDisabled.value) {
    scanInput.value.focus({ preventScroll: true });
  }
};

// When awaitingNext unlocks (switching to new carton), automatically focus the scan input
watch(isInputDisabled, (disabledNow, wasDisabled) => {
  if (wasDisabled && !disabledNow) {
    nextTick(() => {
      focusScan();
    });
  }
});

// Ergonomic Auto-Focus Lock: Maintain focus for scanner barcode gun
const handleGlobalClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  const isInteractive = target.closest('button, a, input, select, textarea, [role="dialog"]');
  if (!isInteractive && !isInputDisabled.value && scanInput.value) {
    setTimeout(focusScan, 100);
  }
};

onMounted(() => {
  focusScan();
  window.addEventListener('click', handleGlobalClick);
  window.addEventListener('keydown', handleGlobalKeyDown);
  focusLockTimer = setInterval(() => {
    // If no active element or active element is body, refocus scan input
    if (document.activeElement === document.body && !isInputDisabled.value) {
      focusScan();
    }
  }, 2000);
});

onUnmounted(() => {
  window.removeEventListener('click', handleGlobalClick);
  window.removeEventListener('keydown', handleGlobalKeyDown);
  if (focusLockTimer) clearInterval(focusLockTimer);
  if (flashTimer) clearTimeout(flashTimer);
});

defineExpose({ focusScan, triggerFlash, isInputDisabled });
</script>
