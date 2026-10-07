<template>
  <div class="min-h-screen w-full bg-slate-100 text-slate-900 flex flex-col p-2 md:p-3 select-none">
    <div class="w-full flex-1 flex flex-col bg-white border border-slate-200 rounded-xl p-3 md:p-4 shadow-xs">
      <AppHeader
        :isAudioActive="isAudioActive"
        @toggle-audio="toggleAudio"
        @show-emergency="openEmergencyModal"
        @show-settings="showSettings = true"
        @home="resetSession"
      />

      <!-- Slim Workflow Stepper Bar -->
      <nav aria-label="Workflow Steps" class="flex items-center justify-between px-3.5 py-2 my-2 bg-slate-50 border border-slate-200 rounded-lg text-xs shrink-0">
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-500 uppercase tracking-wider text-[11px]">{{ t('packing.workflow_progress') }}</span>
          <div class="flex items-center gap-1.5 font-bold">
            <span :class="currentStep === 1 ? 'px-2.5 py-1 rounded bg-blue-600 text-white shadow-xs' : 'px-2 py-0.5 rounded bg-slate-200 text-slate-600'">
              {{ t('packing.step_1_job_order') }}
            </span>
            <i class="fas fa-chevron-right text-[10px] text-slate-400"></i>
            <span :class="currentStep === 2 ? 'px-2.5 py-1 rounded bg-blue-600 text-white shadow-xs' : (currentStep > 2 ? 'px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200' : 'px-2 py-0.5 rounded bg-slate-100 text-slate-400')">
              {{ t('packing.step_2_confirm_order') }}
            </span>
            <i class="fas fa-chevron-right text-[10px] text-slate-400"></i>
            <span :class="currentStep === 3 ? 'px-2.5 py-1 rounded bg-emerald-600 text-white shadow-xs' : 'px-2 py-0.5 rounded bg-slate-100 text-slate-400'">
              {{ t('packing.step_3_scan_pack') }}
            </span>
          </div>
        </div>

        <div v-if="jobOrder" class="flex items-center gap-3 font-mono text-xs">
          <span class="text-slate-600">{{ t('packing.job_order_abbr') }} <strong class="text-slate-900 font-barcode-mono font-bold">{{ jobOrder }}</strong></span>
          <span v-if="currentProduct" class="text-slate-600 hidden sm:inline">| {{ t('packing.product_abbr') }} <strong class="text-slate-900">{{ currentProduct.item_name }}</strong></span>
        </div>
      </nav>

      <!-- Bước 1: Nhập Công Lệnh -->
      <JobOrderInputStep
        v-if="currentStep === 1"
        ref="jobOrderInputStepRef"
        v-model="inputJobOrder"
        :isLoading="isLoadingJobOrder"
        :hasError="hasJobOrderError"
        :errorText="jobOrderErrorText"
        @submit="submitJobOrder"
      />

      <!-- Bước 2: Thông tin đơn hàng (Product Card) -->
      <ProductCardStep
        v-else-if="currentStep === 2"
        :jobOrder="jobOrder"
        :jobOrderDetails="jobOrderDetails"
        @changeJobOrder="changeJobOrder"
        @enterScanning="enterScanning"
      />

      <!-- Bước 3: Giao diện quét mã -->
      <section class="mt-1 flex-1 flex flex-col" v-else-if="currentStep === 3">
        <div class="flex flex-col lg:flex-row gap-3 xl:gap-4 items-stretch lg:items-start flex-1">
          <div class="flex-[1.4] min-w-0 flex flex-col">
            <SessionHeader
              :product="currentProduct!"
              :jobOrder="jobOrder"
              v-model:cartonOrigin="cartonOrigin"
              v-model:cartonNumberStr="cartonNumberStr"
              :cartonNumberRange="cartonNumberRange"
              :snPreview="snPreview"
              v-model:snPattern="snPattern"
              :customYYMM="customYYMM"
              :hasCartonNumberError="hasCartonNumberError"
              :cartonNumberErrorText="cartonNumberErrorText"
              :isOpeningTemplate="isOpeningTemplate"
              @open-template="handleOpenTemplate"
              @back="currentStep = 2"
              @focus-scan="focusScan"
              @submit-carton-number="handleCartonNumberSubmit"
              @clear-carton-error="hasCartonNumberError = false; cartonNumberErrorText = '';"
            />

            <!-- Thanh tóm tắt Công lệnh & Tiến độ thùng -->
            <div class="mb-3 bg-slate-50 p-3 px-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 bg-blue-50 rounded-lg border border-blue-200 flex items-center justify-center text-blue-600">
                  <i class="fas fa-boxes-stacked text-sm"></i>
                </div>
                <div>
                  <div class="text-xs font-bold text-slate-500 uppercase tracking-wider leading-none mb-1">{{ t('packing.packing_progress', 'Tiến Độ Đóng Thùng') }}</div>
                  <div class="text-sm font-extrabold text-slate-800">
                    {{ t('packing.scanned') }}: <span class="text-blue-700 font-barcode-mono font-black text-base">{{ scannedCartonsCount }}</span> / <span class="font-barcode-mono font-black text-base">{{ jobOrderDetails?.total_cartons }}</span> {{ t('packing.cartons_unit', 'thùng') }}
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2 w-full sm:w-auto">
                <button @click="showCartonSlotsModal = true" class="flex-1 sm:flex-none px-3.5 py-1.5 bg-white text-blue-700 hover:bg-blue-50 border border-slate-300 hover:border-blue-300 rounded-lg font-bold cursor-pointer transition-colors flex items-center justify-center gap-1.5 text-xs shadow-2xs">
                  <i class="fas fa-list-check"></i> {{ t('packing.view_details', 'Sơ đồ thùng') }}
                </button>
                <button @click="changeJobOrder" class="flex-1 sm:flex-none px-3.5 py-1.5 bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 rounded-lg font-bold cursor-pointer transition-colors flex items-center justify-center gap-1.5 text-xs shadow-2xs">
                  <i class="fas fa-arrow-rotate-left"></i> {{ t('packing.change_job_order', 'Đổi Work Order') }}
                </button>
              </div>
            </div>

            <!-- Rescan Mode Alert -->
            <div v-if="isRescanMode" class="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-3 flex justify-between items-center text-amber-950 animate-in">
              <div class="flex items-center gap-2.5">
                <i class="fas fa-rotate text-amber-600 text-sm animate-spin"></i>
                <span class="text-xs"><strong>{{ t('packing.rescan_mode', { sn: rescanCartonSN }) }}</strong></span>
              </div>
              <button @click="cancelRescan" class="bg-amber-100 border border-amber-300 px-3 py-1 rounded text-amber-900 font-bold cursor-pointer hover:bg-amber-200 text-xs">
                <i class="fas fa-times mr-1"></i> {{ t('packing.cancel') }}
              </button>
            </div>

            <!-- Progress & Agent Status -->
            <div class="mb-3 bg-white p-3 rounded-xl border border-slate-200">
              <div v-if="settings.printMode === 'local' && !agentConnected" class="bg-rose-50 border border-rose-300 rounded-lg p-2.5 mb-2.5 text-rose-800 text-xs flex items-center gap-2 animate-in">
                <i class="fas fa-triangle-exclamation text-rose-600 text-base"></i>
                <span><strong>{{ t('packing.agent_offline') }}</strong></span>
              </div>

              <div v-if="settings.printMode === 'local' && agentConnected && templateMissing" class="bg-amber-50 border border-amber-300 rounded-lg p-2.5 mb-2.5 text-amber-800 text-xs flex items-center justify-between gap-2 animate-in">
                <div class="flex items-center gap-2">
                  <i class="fas fa-file-circle-exclamation text-amber-600 text-base"></i>
                  <span><strong>{{ t('packing.template_missing', { file: templateFilename }) }}</strong></span>
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                  <button
                    type="button"
                    @click="openTemplateFolder()"
                    :disabled="isOpeningFolder"
                    class="px-2 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 font-bold text-[11px] flex items-center gap-1 cursor-pointer transition-colors"
                    :title="t('packing.open_folder_btn', 'Mở Thư Mục')"
                  >
                    <i v-if="isOpeningFolder" class="fas fa-spinner fa-spin text-xs"></i>
                    <i v-else class="fas fa-folder-open text-xs"></i>
                    <span>{{ t('packing.open_folder_btn', 'Mở Thư Mục') }}</span>
                  </button>
                  <button
                    type="button"
                    @click="handleOpenTemplate"
                    :disabled="isOpeningTemplate"
                    class="px-2 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white font-bold text-[11px] flex items-center gap-1 cursor-pointer transition-colors"
                  >
                    <i v-if="isOpeningTemplate" class="fas fa-spinner fa-spin text-xs"></i>
                    <i v-else class="fas fa-rotate-right text-xs"></i>
                    <span>{{ t('common.retry', 'Thử Lại') }}</span>
                  </button>
                </div>
              </div>

              <div class="flex justify-between items-end mb-1.5">
                <span class="text-sm font-bold text-slate-700">
                  {{ t('packing.item_quantity') }}: <strong class="text-slate-900 font-barcode-mono text-xl">{{ scannedItems.length }}</strong> / {{ currentProduct?.packed_qty || 0 }} pcs
                </span>
                <span class="text-xs text-blue-700 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200 font-mono">{{ progressPercent }}%</span>
              </div>
              <div class="h-3 bg-slate-100 rounded-full overflow-hidden relative border border-slate-200">
                <div class="h-full bg-emerald-600 transition-all duration-300" :style="{ width: progressPercent + '%' }"></div>
              </div>
            </div>

            <PrintStatusBanner
              :lastCarton="lastCarton"
              :agentErrorMessage="agentErrorMessage"
              @retry="finalizeCarton(true)"
            />

            <ScanBuffer
              ref="scanRef"
              v-model:scanBuffer="scanBuffer"
              :disabled="isCheckingItemSN || (settings.printMode === 'local' && (!agentConnected || templateMissing)) || (!selectedSlotId && !isRescanMode)"
              :placeholder="(!selectedSlotId && !isRescanMode) ? t('packing.select_slot_first_placeholder') : ((settings.printMode === 'local' && !agentConnected) ? t('packing.scan_placeholder_offline') : (templateMissing ? t('packing.scan_placeholder_missing') : t('packing.scan_placeholder')))"
              :jobOrder="jobOrder"
              :awaitingNext="awaitingNext"
              :invalidScans="invalidScans"
              :overflowScans="overflowScans"
              :allowPartial="currentProduct?.allow_partial === 1"
              :scannedCount="scannedItems.length"
              @scan="handleScan"
              @next-carton="startNextCarton"
              @pack-now="finalizeCarton()"
              @clear-invalid="invalidScans = []"
              @clear-overflow="overflowScans = []"
            />
          </div>

          <!-- Scanned Serials List Panel -->
          <ScannedList
            :items="scannedItems"
            @clear="scannedItems = []"
            @remove-item="removeScannedItem"
          />
        </div>
      </section>
    </div>

    <!-- Modals -->
    <CartonSlotsModal
      :show="showCartonSlotsModal"
      :jobOrder="jobOrder"
      :totalCartons="jobOrderDetails?.total_cartons"
      :scannedCount="scannedCartonsCount"
      :slots="jobOrderSlots"
      :selectedSlotId="selectedSlotId"
      @close="showCartonSlotsModal = false"
      @selectSlot="handleSlotClickInModal"
    />

    <CartonVerificationModal
      ref="cartonVerificationModalRef"
      :show="showVerificationModal"
      :carton="cartonToVerify"
      :currentProduct="currentProduct"
      :scannedCount="scannedItems.length"
      @close="showVerificationModal = false"
      @verified="confirmVerification"
      @resetSession="resetSession"
      @scanAlert="playScanAlert"
    />

    <ItemSNConflictModal
      :show="showItemSNConflictModal"
      :conflict="itemSNConflict"
      @close="showItemSNConflictModal = false; focusScan()"
    />

    <SettingsModal :show="showSettings" @close="showSettings = false" />
    <EmergencyReprintModal 
      :show="showEmergencyModal" 
      :isReprinting="isEmergencyReprinting"
      @close="closeEmergencyModal" 
      @reprint="onEmergencyReprint" 
      @rescan="handleRescan"
    />

    <TemplateMissingModal
      :show="showTemplateMissingModal"
      :filename="templateViewerMissingFilename"
      :folder="templateViewerTargetFolder"
      :errorMessage="viewerErrorMessage"
      :isOpeningFolder="isOpeningFolder"
      :isRetrying="isOpeningTemplate"
      @close="closeTemplateMissingModal"
      @openFolder="openTemplateFolder()"
      @retry="handleOpenTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useSettingsStore } from '../core/stores/settings';
import { useSystemStore } from '../core/stores/system';
import catalogApi from '../features/catalog/api';
import type { Product, Carton } from '../types/api';

import AppHeader from '../core/components/AppHeader.vue';
import SessionHeader from '../features/packing/components/SessionHeader.vue';
import ScanBuffer from '../features/packing/components/ScanBuffer.vue';
import ScannedList from '../features/packing/components/ScannedList.vue';
import PrintStatusBanner from '../features/print/components/PrintStatusBanner.vue';
import SettingsModal from '../features/settings/components/SettingsModal.vue';
import EmergencyReprintModal from '../features/print/components/EmergencyReprintModal.vue';
import JobOrderInputStep from '../features/packing/components/JobOrderInputStep.vue';
import ProductCardStep from '../features/packing/components/ProductCardStep.vue';
import CartonSlotsModal from '../features/packing/components/CartonSlotsModal.vue';
import CartonVerificationModal from '../features/packing/components/CartonVerificationModal.vue';
import TemplateMissingModal from '../features/packing/components/TemplateMissingModal.vue';
import ItemSNConflictModal from '../features/packing/components/ItemSNConflictModal.vue';

import { useAgentHealth } from '../features/packing/composables/useAgentHealth';
import { useTemplateViewer } from '../features/packing/composables/useTemplateViewer';
import { usePackingAudio } from '../features/packing/composables/usePackingAudio';
import { useJobOrderWorkflow } from '../features/packing/composables/useJobOrderWorkflow';
import { useCartonPrinting } from '../features/packing/composables/useCartonPrinting';
import { usePackingStatePersistence } from '../features/packing/composables/usePackingStatePersistence';

const { t } = useI18n();
const settings = useSettingsStore();
const system = useSystemStore();

const scanRef = ref<any>(null);
const jobOrderInputStepRef = ref<any>(null);
const cartonVerificationModalRef = ref<any>(null);
const currentProduct = ref<Product | null>(null);
let statusTimer: any = null;

const {
  agentConnected,
  templateMissing,
  templateFilename,
  checkTemplateExists,
  checkAgentHealth,
  startPolling,
  stopPolling
} = useAgentHealth({
  settings,
  currentProduct,
});

const {
  isOpening: isOpeningTemplate,
  isOpeningFolder,
  showMissingModal: showTemplateMissingModal,
  missingFilename: templateViewerMissingFilename,
  targetFolder: templateViewerTargetFolder,
  viewerErrorMessage,
  openProductTemplate,
  openTemplateFolder,
  closeMissingModal: closeTemplateMissingModal,
} = useTemplateViewer({
  getAgentUrl: () => settings.agentUrl || 'http://127.0.0.1:8080',
  getLocalTemplateDir: () => settings.localTemplateDir || 'D:\\PAT\\Templates',
  onTemplateFound: () => {
    checkTemplateExists();
  },
  notify: (msg, type) => system.showNotification(msg, type),
});

const handleOpenTemplate = () => {
  openProductTemplate(currentProduct.value);
};

const { isAudioActive, initAudio, playSuccessSound, playScanAlert, toggleAudio } = usePackingAudio({
  audioDeviceId: settings.audioDeviceId,
});

const focusScan = () => { nextTick(() => { if (scanRef.value) scanRef.value.focusScan(); }); initAudio(); };

const workflow = useJobOrderWorkflow({
  system,
  currentProduct,
  focusScan,
  checkTemplateExists,
  startPolling,
  stopPolling,
  playScanAlert,
  jobOrderInputRef: jobOrderInputStepRef,
  cartonVerificationModalRef,
});

const {
  currentStep, inputJobOrder, isLoadingJobOrder, jobOrderDetails, jobOrderSlots, cartonNumberStr,
  selectedSlotId, jobOrder, cartonOrigin, customSN, snPattern, customYYMM, awaitingNext,
  suggestedSNValue, suggestedSNPreview, backupScannedItems, scannedItems, scanBuffer, invalidScans,
  overflowScans, lastCarton, hadJobOrder, savedSessionState, isRescanMode, rescanCartonSN,
  isSNManual, snExists, isCheckingItemSN, showItemSNConflictModal, itemSNConflict,
  showSettings, showEmergencyModal, showCartonSlotsModal, showVerificationModal,
  cartonToVerify, hasCartonNumberError, cartonNumberErrorText, hasJobOrderError, jobOrderErrorText,
  scannedCartonsCount, progressPercent, snPreview, cartonNumberRange, submitJobOrder, changeJobOrder,
  refreshJobOrderDetails, enterScanning, selectSlot, handleSlotClickInModal, handleCartonNumberSubmit,
  refreshNextSN, handleScan, handleRescan, cancelRescan, startNextCarton, resetSession, setOnFinalizeCarton
} = workflow;

const { agentErrorMessage, finalizeCarton, confirmVerification, handleEmergencyReprint } = useCartonPrinting({
  settings, system, currentProduct, jobOrder, selectedSlotId, cartonOrigin, customSN, customYYMM,
  isSNManual, snPreview, snExists, scannedItems, jobOrderSlots, lastCarton, backupScannedItems,
  isRescanMode, rescanCartonSN, showVerificationModal, cartonToVerify, playSuccessSound,
  stopAgentPolling: stopPolling, resetSession: () => resetSession(), selectSlot, focusScan,
  hadJobOrder, savedSessionState, currentStep, cartonNumberStr, suggestedSNPreview, awaitingNext
});

setOnFinalizeCarton(finalizeCarton);

const persistence = usePackingStatePersistence({
  currentStep, inputJobOrder, jobOrderDetails, jobOrderSlots, cartonNumberStr, selectedSlotId, jobOrder,
  cartonOrigin, currentProduct, scannedItems, customSN, snPattern, awaitingNext, suggestedSNValue,
  suggestedSNPreview, backupScannedItems, lastCarton, invalidScans, isSNManual, overflowScans,
  isRescanMode, rescanCartonSN, showVerificationModal, cartonToVerify
});

const removeScannedItem = (index: number) => {
  if (index >= 0 && index < scannedItems.value.length) {
    scannedItems.value.splice(index, 1);
  }
};

const openEmergencyModal = () => {
  hadJobOrder.value = !!jobOrder.value;
  showEmergencyModal.value = true;
};

const isEmergencyReprinting = ref(false);

const closeEmergencyModal = () => {
  showEmergencyModal.value = false;
  if (!hadJobOrder.value) resetSession();
};

const onEmergencyReprint = async (carton: Carton) => {
  if (isEmergencyReprinting.value) return;
  isEmergencyReprinting.value = true;
  try {
    const ok = await handleEmergencyReprint(carton);
    if (ok) {
      showEmergencyModal.value = false;
      if (!hadJobOrder.value) resetSession();
    }
  } finally {
    isEmergencyReprinting.value = false;
  }
};

const checkSystem = async () => {
  try {
    await catalogApi.getCustomers();
    system.isOnline = true;
  } catch { system.isOnline = false; }
};

onMounted(() => {
  persistence.restoreState();
  persistence.initPersistence();
  settings.loadSettings();
  checkSystem();
  checkAgentHealth();
  startPolling(5000);
  nextTick(() => { 
    if (showVerificationModal.value) {
      if (cartonVerificationModalRef.value) cartonVerificationModalRef.value.focusInput();
    } else if (currentStep.value === 1 && jobOrderInputStepRef.value) {
      jobOrderInputStepRef.value.focusInput();
    } else {
      focusScan();
    }
  });
  statusTimer = setInterval(() => { checkSystem(); refreshNextSN(); }, 3000);
  
  window.addEventListener('click', (e) => { 
    if (showSettings.value || showEmergencyModal.value) return; 
    const target = e.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'SELECT') return; 
    if (showVerificationModal.value) {
      if (cartonVerificationModalRef.value) cartonVerificationModalRef.value.focusInput();
    } else if (currentStep.value === 3) {
      focusScan(); 
    }
  });
  if (jobOrder.value) refreshJobOrderDetails();
  window.addEventListener('focus', refreshJobOrderDetails);
});

onUnmounted(() => { 
  if (statusTimer) clearInterval(statusTimer); 
  stopPolling();
  window.removeEventListener('focus', refreshJobOrderDetails);
});
</script>
