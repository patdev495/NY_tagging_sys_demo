<template>
  <div class="h-screen w-full bg-slate-100 text-slate-800 flex flex-col p-2 md:p-3 overflow-hidden box-border select-none">
    <div :class="['w-full h-full flex flex-col bg-white border border-slate-200/90 rounded-2xl p-2 md:p-3 shadow-xl box-border', currentStep === 3 ? 'overflow-hidden justify-between' : 'overflow-y-auto justify-start gap-2']">
      
      <!-- Top Slim Navigation Header (Always Visible) -->
      <ErroHeader
        :isAgentOnline="isAgentOnline"
        :agentUrl="settings.agentUrl || 'http://127.0.0.1:8080'"
        :scaleStatus="scaleStatus"
        @showSettings="showSettingsModal = true"
        @switchCustomer="switchCustomer"
      />

      <!-- Workflow Stepper Bar (Always Visible) -->
      <ErroStepperBar
        :currentStep="currentStep"
        :jobOrder="activeJobOrder || pendingResolution?.job_order"
        :factoryPartNumber="activeFactoryPartNumber || pendingResolution?.factory_part_number"
        :productItemName="selectedProduct?.item_name || pendingResolution?.product.item_name"
      />

      <!-- Bước 1: Nhập Công Lệnh -->
      <ErroJobOrderStep
        v-if="currentStep === 1"
        @resolved="handleJobOrderResolved"
      />

      <!-- Bước 2: Xác Nhận Đơn Hàng & PO/LOT -->
      <ErroProductCardStep
        v-else-if="currentStep === 2"
        :jobOrder="activeJobOrder || pendingResolution?.job_order || ''"
        :resolution="pendingResolution"
        :initialPo="activePO"
        :initialLot="activeLot"
        @changeJobOrder="changeJobOrder"
        @confirm="confirmJobOrderResolution"
      />

      <!-- Bước 3: Trạm Cân & Đóng Thùng -->
      <template v-else-if="currentStep === 3">
        <!-- Active Product & Batch Bar -->
        <ErroActiveProductBar
          :activeJobOrder="activeJobOrder"
          :activeFactoryPartNumber="activeFactoryPartNumber"
          :selectedProduct="selectedProduct"
          :jobOrderPlannedCartons="jobOrderPlannedCartons"
          :jobOrderPackedCartonsCount="jobOrderPackedCartonsCount"
          :jobOrderTotalQty="jobOrderTotalQty"
          :activePO="activePO"
          :activeLot="activeLot"
          :isOpeningTemplate="isOpeningTemplate"
          @showCartons="showCartonsModal = true"
          @openTemplate="handleOpenTemplate"
          @editBatch="showBatchModal = true"
          @changeJobOrder="clearSelectedProduct"
        />

        <!-- Offline Warning Banner -->
        <div v-if="!isAgentOnline" class="mb-2 px-3.5 py-2 rounded-xl bg-rose-50 border border-rose-300 text-rose-800 text-xs font-semibold flex items-center justify-between gap-3 shadow-xs animate-in">
          <div class="flex items-center gap-2.5">
            <div class="w-6 h-6 rounded-lg bg-rose-500 text-white flex items-center justify-center shrink-0">
              <i class="fas fa-exclamation-triangle text-xs"></i>
            </div>
            <div>
              <span class="font-black text-rose-900">{{ t('erro.agent_not_connected') }}</span>
              <span class="text-rose-700 ml-1.5 text-[11px]">
                {{ t('erro.agent_not_connected_hint', { url: settings.agentUrl || 'http://127.0.0.1:8080' }) }}
              </span>
            </div>
          </div>
          <button @click="pollScaleStatus" class="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shrink-0 cursor-pointer shadow-xs flex items-center gap-1">
            <i class="fas fa-rotate-right text-[10px]"></i>
            <span>{{ t('erro.retry') }}</span>
          </button>
        </div>

        <!-- Template Missing Warning Banner (Pre-flight Check) -->
        <div v-if="settings.printMode !== 'centralized' && isAgentOnline && templateMissing" class="mb-2 px-3.5 py-2 rounded-xl bg-amber-50 border border-amber-300 text-amber-800 text-xs font-semibold flex items-center justify-between gap-3 shadow-xs animate-in">
          <div class="flex items-center gap-2.5">
            <div class="w-6 h-6 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0">
              <i class="fas fa-file-circle-exclamation text-xs"></i>
            </div>
            <div>
              <span class="font-black text-amber-900">{{ t('erro.template_missing', { filename: templateFilename }) }}</span>
              <span class="text-amber-700 ml-1.5 text-[11px]">
                Vui lòng sao chép file <strong>{{ templateFilename }}</strong> vào thư mục <code>{{ settings.localTemplateDir || 'D:\\PAT\\Templates' }}</code> trên máy tính này.
              </span>
            </div>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              @click="openTemplateFolder()"
              :disabled="isOpeningFolder"
              class="px-2.5 py-1 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-900 font-bold text-xs transition-all flex items-center gap-1 cursor-pointer"
              :title="t('erro.open_template_folder_title')"
            >
              <i v-if="isOpeningFolder" class="fas fa-spinner fa-spin text-xs"></i>
              <i v-else class="fas fa-folder-open text-xs"></i>
              <span>{{ t('erro.open_folder') }}</span>
            </button>
            <button @click="checkTemplateExists" class="px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold transition-all shrink-0 cursor-pointer shadow-xs flex items-center gap-1">
              <i class="fas fa-rotate-right text-[10px]"></i>
              <span>{{ t('erro.check_again') }}</span>
            </button>
          </div>
        </div>

        <!-- Main Packing Station Cockpit Grid -->
        <main class="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-0">
          <!-- Left: Live Scale Gauge & Action Controls (8 Cols) -->
          <div class="lg:col-span-8 flex flex-col justify-between h-full gap-2 min-h-0">
            <ScaleDigitalGauge
              :scaleReading="scaleReading"
              :scaleStatus="scaleStatus"
              :isAgentOnline="isAgentOnline"
              :toleranceResult="toleranceResult"
              :selectedProduct="selectedProduct"
              :isPrinting="isPrinting"
            />

            <ErroSerialControl
              :currentSNPreview="currentSNPreview"
            />

            <!-- Giant Primary Print Action Button -->
            <button
              @click="triggerWeighAndPrint"
              :disabled="isPrinting || !selectedProduct || labelPreviewErrors.length > 0 || (settings.printMode !== 'centralized' && templateMissing)"
              :class="[
                'w-full py-3 md:py-3.5 rounded-xl font-black text-base md:text-lg transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md shrink-0',
                (settings.printMode !== 'centralized' && templateMissing)
                  ? 'bg-amber-600 hover:bg-amber-700 active:scale-[0.99] text-white shadow-amber-600/20'
                : (toleranceResult.canPrint && labelPreviewErrors.length === 0 && (selectedProduct?.template_type === 'erro_02' || selectedProduct?.template_type === 'erro_03' || selectedProduct?.template_type === 'erro_05' || activePO?.trim())
                    ? 'bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white shadow-emerald-600/30'
                    : 'bg-rose-600 hover:bg-rose-700 active:scale-[0.99] text-white shadow-rose-600/20')
              ]"
            >
              <i v-if="isPrinting" class="fas fa-spinner fa-spin text-lg"></i>
              <i v-else-if="settings.printMode !== 'centralized' && templateMissing" class="fas fa-file-circle-exclamation text-lg"></i>
              <i v-else-if="toleranceResult.canPrint" class="fas fa-print text-lg"></i>
              <i v-else class="fas fa-triangle-exclamation text-lg"></i>
              <span>{{ printActionText }}</span>
            </button>
          </div>

          <!-- Right: Session Stats & Last Carton Info (4 Cols) -->
          <div class="lg:col-span-4 flex flex-col h-full gap-2 min-h-0 justify-between">
            <ErroLabelPrintPreview
              :product="selectedProduct"
              :carton-s-n="currentSNPreview"
              :po="activePO"
              :lot="activeLot"
              :now="previewTime"
              @validation-change="labelPreviewErrors = $event"
            />
          </div>
        </main>
      </template>

      <!-- Modals -->
      <ErroBatchConfigModal :show="showBatchModal" :po="activePO" :lot="activeLot" :isTem3="selectedProduct?.template_type === 'erro_03'" @close="cancelBatchConfig" @save="saveBatchConfig" />
      <SettingsModal :show="showSettingsModal" @close="showSettingsModal = false" />
      <ScaleToleranceErrorModal :show="showToleranceErrorModal" :details="toleranceErrorDetails" @close="showToleranceErrorModal = false" />
      <ErroJobOrderCartonsModal :show="showCartonsModal" :job-order="activeJobOrder" :product="selectedProduct" :planned-cartons="jobOrderPlannedCartons" :total-qty="jobOrderTotalQty" @close="showCartonsModal = false" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useSettingsStore } from '../core/stores/settings';
import { useSystemStore } from '../core/stores/system';
import type { ErroJobOrderResolution, Product } from '../types/api';

import SettingsModal from '../features/settings/components/SettingsModal.vue';
import ErroHeader from '../features/packing/weight_scale/components/ErroHeader.vue';
import ErroStepperBar from '../features/packing/weight_scale/components/ErroStepperBar.vue';
import ErroProductCardStep from '../features/packing/weight_scale/components/ErroProductCardStep.vue';
import ErroActiveProductBar from '../features/packing/weight_scale/components/ErroActiveProductBar.vue';
import ScaleDigitalGauge from '../features/packing/weight_scale/components/ScaleDigitalGauge.vue';
import ErroSerialControl from '../features/packing/weight_scale/components/ErroSerialControl.vue';
import ErroLabelPrintPreview from '../features/packing/weight_scale/components/ErroLabelPrintPreview.vue';
import ScaleToleranceErrorModal from '../features/packing/weight_scale/components/ScaleToleranceErrorModal.vue';
import ErroJobOrderStep from '../features/packing/weight_scale/components/ErroJobOrderStep.vue';
import ErroBatchConfigModal from '../features/packing/weight_scale/components/ErroBatchConfigModal.vue';
import ErroJobOrderCartonsModal from '../features/packing/weight_scale/components/ErroJobOrderCartonsModal.vue';
import TemplateMissingModal from '../features/packing/components/TemplateMissingModal.vue';

import { useScaleStream } from '../features/packing/weight_scale/composables/useScaleStream';
import { useErroSerialNumber } from '../features/packing/weight_scale/composables/useErroSerialNumber';
import { useWeighAndPrint } from '../features/packing/weight_scale/composables/useWeighAndPrint';
import { useAgentHealth } from '../features/packing/composables/useAgentHealth';
import { useTemplateViewer } from '../features/packing/composables/useTemplateViewer';

const router = useRouter();
const { t } = useI18n();
const settings = useSettingsStore();
const system = useSystemStore();

// Workflow Step State (1: Nhập Công Lệnh, 2: Xác Nhận Đơn Hàng, 3: Cân & Đóng Thùng)
const currentStep = ref<1 | 2 | 3>(1);

// Modals State
const showBatchModal = ref(false);
const showSettingsModal = ref(false);
const showCartonsModal = ref(false);

// Active Selection State
const selectedProduct = ref<Product | null>(null);
const pendingResolution = ref<ErroJobOrderResolution | null>(null);

const activeJobOrder = ref<string>(localStorage.getItem('erro_active_job_order') || '');
const activeFactoryPartNumber = ref<string>(localStorage.getItem('erro_active_factory_pn') || '');
const activeCustomerRef = ref<string>(localStorage.getItem('erro_active_customer_ref') || '');
const jobOrderTotalQty = ref<number>(Number(localStorage.getItem('erro_job_order_total_qty') || '0'));
const jobOrderPlannedCartons = ref<number>(Number(localStorage.getItem('erro_job_order_planned_cartons') || '0'));
const jobOrderPackedCartonsCount = ref<number>(Number(localStorage.getItem('erro_job_order_packed_count') || '0'));

const activePO = ref<string>(localStorage.getItem('erro_active_po') || '');
const automaticLot = () => {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
};
const activeLot = ref<string>(automaticLot());
const labelPreviewErrors = ref<string[]>([]);
const previewTime = ref(new Date());

const printActionText = computed(() => {
  if (isPrinting.value) return t('erro.sending_print');
  if (settings.printMode !== 'centralized' && templateMissing.value) {
    return t('erro.template_missing_action', { filename: templateFilename.value });
  }
  if (labelPreviewErrors.value.length) return t('erro.label_data_missing');
  return toleranceResult.value.canPrint ? t('erro.weigh_and_print') : t('erro.tolerance_action');
});

// 1. Scale Stream Composable
const {
  isAgentOnline,
  scaleReading,
  scaleStatus,
  pollScaleStatus,
  startPolling,
  stopPolling,
} = useScaleStream(() => settings.agentUrl || 'http://127.0.0.1:8080');

// 2. S/N Sequence Composable (Strict Monotonic - ADR 0005)
const {
  currentSNPreview,
  fetchNextSN,
  advanceSequence,
} = useErroSerialNumber(selectedProduct);

// 3. Weigh & Print Orchestrator Composable (No Reprint - ADR 0005)
const {
  isPrinting,
  lastPackedCarton,
  showToleranceErrorModal,
  toleranceErrorDetails,
  toleranceResult,
  triggerWeighAndPrint,
} = useWeighAndPrint({
  selectedProduct,
  activeJobOrder,
  activePO,
  activeLot,
  isAgentOnline,
  scaleReading,
  scaleStatus,
  advanceSequence,
  notify: (msg, type) => system.showNotification(msg, type),
  getSettings: () => ({
    agentUrl: settings.agentUrl,
    printerName: settings.printerName,
    templatePath: settings.templatePath,
    stationId: settings.stationId,
    localTemplateDir: settings.localTemplateDir,
  }),
  openProductModal: () => system.showNotification(t('erro.enter_job_order_first'), 'warning'),
  openBatchModal: () => { showBatchModal.value = true; },

});

// 4. Agent & Template Health Composable
const {
  templateMissing,
  templateFilename,
  checkTemplateExists,
} = useAgentHealth({
  settings: computed(() => ({
    printMode: settings.printMode || 'local',
    agentUrl: settings.agentUrl || 'http://127.0.0.1:8080',
    localTemplateDir: settings.localTemplateDir || 'D:\\PAT\\Templates',
  })),
  currentProduct: selectedProduct,
});

// 5. Template Viewer Composable
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
  openProductTemplate(selectedProduct.value);
};

watch([selectedProduct, isAgentOnline], () => {
  if (isAgentOnline.value) {
    checkTemplateExists();
  }
});

watch(currentSNPreview, () => {
  previewTime.value = new Date();
});

watch(lastPackedCarton, async (carton) => {
  if (carton) {
    jobOrderPackedCartonsCount.value += 1;
    localStorage.setItem('erro_job_order_packed_count', String(jobOrderPackedCartonsCount.value));
    await fetchNextSN();
  }
});

// Navigation & Config Actions
const switchCustomer = () => {
  localStorage.removeItem('selected_customer');
  router.push('/');
};

const SESSION_KEYS = [
  'erro_active_po', 'erro_active_lot', 'erro_active_job_order',
  'erro_active_factory_pn', 'erro_active_customer_ref',
  'erro_job_order_total_qty', 'erro_job_order_planned_cartons',
  'erro_job_order_packed_count', 'erro_selected_product_id',
];

const clearPackingSession = () => {
  activePO.value = '';
  activeLot.value = '';
  activeJobOrder.value = '';
  activeFactoryPartNumber.value = '';
  activeCustomerRef.value = '';
  jobOrderTotalQty.value = 0;
  jobOrderPlannedCartons.value = 0;
  jobOrderPackedCartonsCount.value = 0;
  SESSION_KEYS.forEach((k) => localStorage.removeItem(k));
};

const activateProduct = (product: Product) => {
  selectedProduct.value = product;
  system.showNotification(t('erro.product_selected', { name: product.item_name }), 'success');
  fetchNextSN();
};

const saveBatchConfig = (payload: { po: string; lot: string }) => {
  activePO.value = payload.po;
  activeLot.value = automaticLot();
  localStorage.setItem('erro_active_po', activePO.value);
  localStorage.setItem('erro_active_lot', activeLot.value);
  showBatchModal.value = false;
  system.showNotification(t('erro.po_lot_saved'), 'success');
};

const cancelBatchConfig = () => { showBatchModal.value = false; };

const handleJobOrderResolved = (resolution: ErroJobOrderResolution) => {
  activeLot.value = automaticLot();
  pendingResolution.value = resolution;
  currentStep.value = 2;
};

const changeJobOrder = () => {
  currentStep.value = 1;
  pendingResolution.value = null;
};

const confirmJobOrderResolution = (payload: { po: string; lot: string }) => {
  if (!pendingResolution.value) return;
  const resolution = pendingResolution.value;
  pendingResolution.value = null;

  clearPackingSession();
  activeJobOrder.value = resolution.job_order;
  activeFactoryPartNumber.value = resolution.factory_part_number;
  activeCustomerRef.value = resolution.customer_ref;
  jobOrderTotalQty.value = resolution.total_qty;
  jobOrderPlannedCartons.value = resolution.planned_cartons;
  jobOrderPackedCartonsCount.value = resolution.packed_cartons_count;
  activePO.value = payload.po;
  activeLot.value = automaticLot();

  const stateMap: Record<string, string> = {
    erro_active_job_order: activeJobOrder.value, erro_active_factory_pn: activeFactoryPartNumber.value,
    erro_active_customer_ref: activeCustomerRef.value, erro_job_order_total_qty: String(jobOrderTotalQty.value),
    erro_job_order_planned_cartons: String(jobOrderPlannedCartons.value), erro_job_order_packed_count: String(jobOrderPackedCartonsCount.value),
    erro_active_po: activePO.value, erro_active_lot: activeLot.value,
  };
  Object.entries(stateMap).forEach(([k, v]) => localStorage.setItem(k, v));

  activateProduct(resolution.product);
  currentStep.value = 3;
};

const clearSelectedProduct = () => {
  selectedProduct.value = null;
  pendingResolution.value = null;
  currentStep.value = 1;
  clearPackingSession();
  system.showNotification(t('erro.start_new_run'), 'info');
};

// Global Hotkeys Listener (F9, Enter, Esc)
const handleKeyDown = (event: KeyboardEvent) => {
  if (currentStep.value !== 3) return;
  if (showToleranceErrorModal.value && ['Enter', 'Escape', ' ', 'Space'].includes(event.key)) {
    event.preventDefault();
    showToleranceErrorModal.value = false;
    return;
  }
  if (event.key === 'F9' || event.code === 'F9' || event.keyCode === 120) {
    event.preventDefault();
    triggerWeighAndPrint();
  }
};

onMounted(() => {
  localStorage.removeItem('erro_selected_product_id');
  activeLot.value = automaticLot();
  startPolling();
  window.addEventListener('keydown', handleKeyDown, true);
});

onUnmounted(() => {
  stopPolling();
  window.removeEventListener('keydown', handleKeyDown, true);
});
</script>
