<template>
  <div v-if="show" class="fixed inset-0 bg-slate-900/75 flex justify-center items-center z-[2000] p-3 md:p-6" @click.self="$emit('close')" role="dialog" aria-modal="true">
    <div class="bg-white rounded-xl w-full max-w-[620px] shadow-2xl text-slate-800 border border-slate-300 overflow-hidden max-h-[90vh] flex flex-col animate-in">
      <!-- Header -->
      <div class="px-5 py-3.5 border-b border-slate-200 flex justify-between items-center bg-slate-50 shrink-0">
        <div class="flex items-center gap-2.5 text-slate-900">
          <div class="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
            <i class="fas fa-sliders text-sm"></i>
          </div>
          <div>
            <h2 class="m-0 text-base font-black text-slate-900 leading-tight">{{ t('settings.title') }}</h2>
            <p class="m-0 text-xs text-slate-500">{{ t('settings.subtitle') }}</p>
          </div>
        </div>
        <button 
          @click="$emit('close')" 
          class="w-8 h-8 rounded-lg bg-white hover:bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-500 hover:text-slate-800 cursor-pointer transition-colors"
          :title="t('settings.close_title')"
        >
          <i class="fas fa-times text-sm"></i>
        </button>
      </div>

      <!-- Tab Navigation Bar -->
      <div class="px-5 pt-2 border-b border-slate-200 bg-slate-100/60 flex gap-2 shrink-0">
        <button 
          type="button"
          @click="activeTab = 'print'" 
          :class="['px-3.5 py-2 font-bold text-xs rounded-t-lg transition-colors border-t border-x cursor-pointer flex items-center gap-1.5', activeTab === 'print' ? 'bg-white border-slate-200 text-blue-700 -mb-px shadow-2xs' : 'bg-transparent border-transparent text-slate-600 hover:text-slate-900']"
        >
          <i class="fas fa-print"></i>
          <span>{{ t('settings.tab_print') }}</span>
        </button>
        <button 
          type="button"
          @click="activeTab = 'scale'" 
          :class="['px-3.5 py-2 font-bold text-xs rounded-t-lg transition-colors border-t border-x cursor-pointer flex items-center gap-1.5', activeTab === 'scale' ? 'bg-white border-slate-200 text-emerald-700 -mb-px shadow-2xs' : 'bg-transparent border-transparent text-slate-600 hover:text-slate-900']"
        >
          <i class="fas fa-weight-scale"></i>
          <span>{{ t('settings.tab_scale') }}</span>
        </button>
        <button 
          type="button"
          @click="activeTab = 'system'" 
          :class="['px-3.5 py-2 font-bold text-xs rounded-t-lg transition-colors border-t border-x cursor-pointer flex items-center gap-1.5', activeTab === 'system' ? 'bg-white border-slate-200 text-slate-900 -mb-px shadow-2xs' : 'bg-transparent border-transparent text-slate-600 hover:text-slate-900']"
        >
          <i class="fas fa-gear"></i>
          <span>{{ t('settings.tab_system') }}</span>
        </button>
      </div>

      <!-- Tab Content Area (Scrollable) -->
      <div class="px-6 py-4 overflow-y-auto flex-1 space-y-4 text-xs">
        
        <!-- ================= TAB 1: MÁY IN & BARTENDER ================= -->
        <div v-show="activeTab === 'print'" class="space-y-4 animate-in">
          <!-- Print Mode Toggle -->
          <div>
            <label class="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              {{ t('settings.print_mode') }}
            </label>
            <div class="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg border border-slate-200">
              <button 
                type="button"
                @click="formData.printMode = 'centralized'"
                :class="['flex items-center justify-center gap-2 py-2 rounded-md font-bold transition-colors cursor-pointer', formData.printMode === 'centralized' ? 'bg-white text-blue-700 shadow-xs border border-slate-200' : 'text-slate-600 hover:bg-slate-200/50']"
              >
                <i class="fas fa-server"></i>
                <span>{{ t('settings.centralized') }}</span>
              </button>
              <button 
                type="button"
                @click="formData.printMode = 'local'"
                :class="['flex items-center justify-center gap-2 py-2 rounded-md font-bold transition-colors cursor-pointer', formData.printMode === 'local' ? 'bg-white text-blue-700 shadow-xs border border-slate-200' : 'text-slate-600 hover:bg-slate-200/50']"
              >
                <i class="fas fa-desktop"></i>
                <span>{{ t('settings.local_agent') }}</span>
              </button>
            </div>
          </div>

          <!-- Mode Info Banner -->
          <div v-if="formData.printMode === 'centralized'" class="rounded-lg p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-start gap-2.5">
            <i class="fas fa-server text-base text-emerald-600 mt-0.5"></i>
            <div>
              <strong class="block font-bold">{{ t('settings.centralized_title') }}</strong>
              <span class="block mt-0.5 text-slate-600">{{ t('settings.centralized_desc') }}</span>
            </div>
          </div>

          <div v-else class="rounded-lg p-3 bg-blue-50 border border-blue-200 text-blue-900 flex items-start gap-2.5">
            <i class="fas fa-bolt text-base text-blue-600 mt-0.5"></i>
            <div>
              <strong class="block font-bold">{{ t('settings.local_title') }}</strong>
              <span class="block mt-0.5 text-slate-600">{{ t('settings.local_desc') }}</span>
            </div>
          </div>

          <!-- Agent URL (if local) -->
          <div v-if="formData.printMode === 'local'" class="space-y-2 bg-blue-50/50 p-3.5 rounded-xl border border-blue-200">
            <label class="block font-bold text-slate-700">
              <i class="fas fa-link mr-1 text-blue-600"></i>{{ t('settings.agent_url') }}
            </label>
            <div class="flex gap-2">
              <input 
                :value="detectingAgent ? t('settings.detecting_agent') : formData.agentUrl" 
                type="text" 
                readonly 
                class="flex-1 h-9 px-3 border border-slate-300 rounded-lg bg-slate-100 text-slate-600 font-barcode-mono font-bold cursor-not-allowed" 
              />
              <button 
                type="button"
                @click="discoverAgent" 
                class="h-9 px-3 bg-blue-50 text-blue-700 border border-blue-300 rounded-lg font-bold flex items-center gap-1.5 cursor-pointer hover:bg-blue-100 disabled:opacity-50" 
                :title="t('settings.discover_agent_title')"
                :disabled="detectingAgent"
              >
                <i class="fas fa-search" :class="{'fa-spin': detectingAgent}"></i>
                <span>{{ t('settings.discover_agent') }}</span>
              </button>
            </div>
            <p class="text-[11px] text-slate-500 m-0">{{ t('settings.agent_description') }}</p>
          </div>

          <!-- Common Template Directory Configuration (Both Centralized & Local) -->
          <div class="space-y-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="font-bold text-slate-700 flex items-center gap-1.5 m-0">
                  <i class="fas fa-folder-open text-amber-600"></i>
                  <span>{{ t('settings.template_directory') }}</span>
                </label>
                <span class="text-[10px] font-bold text-slate-500 bg-slate-200 px-2 py-0.5 rounded">{{ t('settings.shared_modes') }}</span>
              </div>
              <input 
                v-model="formData.localTemplateDir" 
                type="text" 
                placeholder="D:\PAT\Templates" 
                class="w-full h-9 px-3 border border-slate-300 rounded-lg bg-white text-slate-900 font-mono font-bold" 
                :class="{ 'border-rose-500 bg-rose-50': dirError }"
              />
              <p class="text-[11px] text-slate-500 mt-1 m-0">
                {{ t('settings.template_directory_description', { location: formData.printMode === 'local' ? t('settings.local_workstation') : t('settings.server_machine') }) }}
              </p>
            </div>

            <!-- Canonical Templates Verification Box -->
            <div class="pt-2 border-t border-slate-200 space-y-2">
              <div class="flex items-center justify-between">
                <div>
                  <span class="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                    <i class="fas fa-layer-group text-indigo-600"></i>
                    <span>{{ t('settings.standard_templates') }}</span>
                  </span>
                  <p class="text-[10px] text-slate-500 m-0">
                    {{ t('settings.compare_templates') }} <span class="font-mono font-bold text-slate-700">{{ formData.localTemplateDir || 'D:\PAT\Templates' }}</span>
                  </p>
                </div>
                <button 
                  type="button" 
                  @click="checkAllTemplates" 
                  :disabled="isCheckingTemplates" 
                  class="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-xs disabled:opacity-50 transition-colors"
                  :title="formData.printMode === 'local' ? t('settings.check_templates_local') : t('settings.check_templates_server')"
                >
                  <i class="fas fa-arrows-rotate" :class="{'fa-spin': isCheckingTemplates}"></i>
                  <span>{{ isCheckingTemplates ? t('settings.checking') : t('settings.check_templates') }}</span>
                </button>
              </div>

              <!-- Template List Table -->
              <div class="rounded-lg border border-slate-200 bg-white overflow-hidden max-h-52 overflow-y-auto">
                <table class="w-full text-left border-collapse text-[11px]">
                  <thead>
                    <tr class="bg-slate-100/80 text-slate-600 border-b border-slate-200 text-[10px] uppercase font-bold">
                      <th class="py-1.5 px-2.5">{{ t('settings.template_file') }}</th>
                      <th class="py-1.5 px-2">{{ t('settings.template_customer') }}</th>
                      <th class="py-1.5 px-2">{{ t('settings.template_scope') }}</th>
                      <th class="py-1.5 px-2 text-right">{{ t('settings.template_status') }}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    <tr v-for="tpl in CANONICAL_TEMPLATES" :key="tpl.filename" class="hover:bg-slate-50/80">
                      <td class="py-1.5 px-2.5 font-mono font-bold text-slate-800">
                        📄 {{ tpl.filename }}
                      </td>
                      <td class="py-1.5 px-2">
                        <span 
                          :class="[
                            'text-[9px] font-black uppercase px-1.5 py-0.5 rounded',
                            tpl.customer === 'ERRO' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                          ]"
                        >
                          {{ tpl.customer }}
                        </span>
                      </td>
                      <td class="py-1.5 px-2 text-slate-600 truncate max-w-[200px]" :title="tpl.desc">
                        {{ tpl.desc }}
                      </td>
                      <td class="py-1.5 px-2 text-right">
                        <span v-if="templateCheckResults[tpl.filename]?.checking" class="text-slate-400 font-bold text-[10px]">
                          <i class="fas fa-spinner fa-spin"></i>
                        </span>
                        <span 
                          v-else-if="templateCheckResults[tpl.filename]?.exists" 
                          class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[10px]"
                        >
                          <i class="fas fa-circle-check text-emerald-500"></i>
                          <span>{{ t('settings.ready') }}</span>
                        </span>
                        <span 
                          v-else-if="templateCheckResults[tpl.filename] && !templateCheckResults[tpl.filename]?.exists" 
                          class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold text-[10px]"
                          :title="templateCheckResults[tpl.filename]?.error || t('settings.no_printers_found', { mode: '' })"
                        >
                          <i class="fas fa-triangle-exclamation text-rose-500"></i>
                          <span>{{ t('settings.missing_file') }}</span>
                        </span>
                        <span v-else class="text-slate-400 text-[10px] italic">
                          {{ t('settings.not_checked') }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Printer Selection -->
          <div>
            <label class="block mb-1 font-bold text-slate-700">
              <i class="fas fa-print mr-1 text-blue-600"></i>{{ t('settings.printer_name') }}
            </label>
            <div class="flex gap-2 items-center">
              <select v-model="formData.printerName" class="flex-1 h-9 px-3 border border-slate-300 rounded-lg bg-white text-slate-900 font-medium">
                <option value="">-- {{ t('settings.default_printer') }} --</option>
                <option v-if="formData.printerName && !availablePrinters.some(p => (typeof p === 'string' ? p : p.name) === formData.printerName)" :value="formData.printerName">
                  🖨️ {{ formData.printerName }} ({{ t('settings.selected') || 'Selected' }})
                </option>
                <option v-for="p in availablePrinters" :key="typeof p === 'string' ? p : (p.name || Math.random().toString())" :value="typeof p === 'string' ? p : p.name">
                  🖨️ {{ typeof p === 'string' ? p : (p.name || 'Unknown Printer') }} {{ typeof p === 'string' ? '' : (p.port ? `(${p.port})` : '') }}
                </option>
              </select>
              <button 
                type="button"
                @click="loadPrinters" 
                class="h-9 px-3 bg-slate-100 border border-slate-300 rounded-lg flex items-center gap-1 cursor-pointer text-slate-700 hover:bg-slate-200" 
                :title="t('settings.refresh_printers')"
              >
                <i class="fas fa-sync-alt" :class="{'fa-spin': loadingPrinters}"></i>
                <span>{{ t('settings.reload') }}</span>
              </button>
            </div>
          </div>

          <!-- BarTender Engine Diagnostics -->
          <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-2">
            <div class="flex items-center justify-between">
              <label class="font-bold text-slate-800 flex items-center gap-1.5 m-0">
                <i class="fas fa-stethoscope text-indigo-600"></i>
                <span>{{ t('settings.engine_diagnostics') }}</span>
              </label>
              <span :class="['text-[10px] font-black uppercase px-2 py-0.5 rounded-full flex items-center gap-1', bartenderStatus === 'ready' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300']">
                <span class="w-1.5 h-1.5 rounded-full" :class="bartenderStatus === 'ready' ? 'bg-emerald-500' : 'bg-rose-500'"></span>
                <span>{{ bartenderStatus === 'ready' ? t('settings.ready') : t('settings.offline') }}</span>
              </span>
            </div>
            
            <p class="text-[11px] text-slate-500 m-0 leading-relaxed">
              {{ t('settings.engine_description') }}
            </p>

            <div v-if="authStore.isAdmin" class="pt-1">
              <button 
                type="button"
                @click="handleRestartEngine" 
                :disabled="isRestartingEngine"
                class="h-8 w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer border-none"
              >
                <i class="fas fa-arrows-rotate" :class="{ 'fa-spin': isRestartingEngine }"></i>
                <span>{{ isRestartingEngine ? t('settings.restarting_engine') : t('settings.restart_engine') }}</span>
              </button>
            </div>
            <div v-else class="text-[10px] text-slate-400 italic">
              {{ t('settings.engine_admin_only') }}
            </div>
          </div>
        </div>

        <!-- ================= TAB 2: CÂN ĐIỆN TỬ (RS-232) ================= -->
        <div v-show="activeTab === 'scale'" class="space-y-4 animate-in">
          <div>
            <label class="block mb-1 font-bold text-slate-700">
              <i class="fas fa-weight-scale mr-1 text-emerald-600"></i>{{ t('settings.scale_port') }}
            </label>
            <div class="flex gap-2 items-center">
              <select v-model="formData.scalePort" class="flex-1 h-9 px-3 border border-slate-300 rounded-lg bg-white text-slate-900 font-medium">
                <option value="">-- {{ t('settings.auto_detect') }} --</option>
                <option v-if="formData.scalePort && !availableScalePorts.some(p => p.device === formData.scalePort)" :value="formData.scalePort">
                  ⚖️ {{ formData.scalePort }} ({{ t('settings.selected') }})
                </option>
                <option v-for="p in availableScalePorts" :key="p.device" :value="p.device">
                  ⚖️ {{ p.device }} ({{ p.description || 'Cổng COM' }})
                </option>
              </select>
              <button 
                type="button"
                @click="loadScaleStatus" 
                class="h-9 px-3 bg-slate-100 border border-slate-300 rounded-lg flex items-center gap-1 cursor-pointer text-slate-700 hover:bg-slate-200" 
                :title="t('settings.scan_ports_title')"
              >
                <i class="fas fa-sync-alt" :class="{'fa-spin': loadingScale}"></i>
                <span>{{ t('settings.scan_ports') }}</span>
              </button>
            </div>
            <small class="block mt-1.5 text-slate-500 text-[11px]">
              {{ t('settings.scale_instruction') }}
            </small>
          </div>

          <!-- Scale Live Diagnostic Card -->
          <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-2">
            <span class="font-bold text-slate-800 block">{{ t('settings.technical_specification') }}</span>
            <ul class="list-disc pl-4 space-y-1 text-slate-600 text-[11px]">
              <li>{{ t('settings.scale_baudrate') }}: <strong>9600 bps</strong></li>
              <li>Data Bits: <strong>8</strong> • Stop Bits: <strong>1</strong> • Parity: <strong>None</strong></li>
              <li>{{ t('settings.scale_tare_instruction') }}</li>
            </ul>
          </div>
        </div>

        <!-- ================= TAB 3: HỆ THỐNG & THIẾT BỊ ================= -->
        <div v-show="activeTab === 'system'" class="space-y-4 animate-in">
          <!-- Language -->
          <div>
            <label class="block mb-1 font-bold text-slate-700">
              <i class="fas fa-globe mr-1 text-blue-600"></i>{{ t('settings.language') }}
            </label>
            <select v-model="formData.language" class="w-full h-9 px-3 border border-slate-300 rounded-lg bg-white text-slate-900 font-medium">
              <option value="vi">{{ t('settings.language_vi') }}</option>
              <option value="en">{{ t('settings.language_en') }}</option>
            </select>
          </div>

          <!-- Station ID -->
          <div>
            <label class="block mb-1 font-bold text-slate-700">
              <i class="fas fa-fingerprint mr-1 text-slate-600"></i>{{ t('settings.station_id') }}
            </label>
            <div class="relative flex items-center">
              <input 
                :value="system.stationId || t('settings.detecting')" 
                readonly 
                class="w-full h-9 px-3 border border-slate-300 rounded-lg bg-slate-100 text-slate-600 font-barcode-mono font-bold cursor-not-allowed" 
              />
              <span class="absolute right-2.5 bg-slate-200 text-slate-700 text-[10px] font-black px-1.5 py-0.5 rounded">
                AUTO
              </span>
            </div>
          </div>

          <!-- Audio Device Output -->
          <div>
            <label class="block mb-1 font-bold text-slate-700">
              <i class="fas fa-volume-high mr-1 text-emerald-600"></i>{{ t('settings.audio_output') }}
            </label>
            <select v-model="formData.audioDeviceId" class="w-full h-9 px-3 border border-slate-300 rounded-lg bg-white text-slate-900 font-medium">
              <option value="">{{ t('settings.audio_output_default') }}</option>
              <option v-for="d in audioDevices" :key="d.id" :value="d.id">{{ d.label }}</option>
            </select>
            <small class="block mt-1 text-slate-500 text-[11px]">{{ t('settings.audio_output_hint') }}</small>
          </div>
        </div>

      </div>

      <!-- Pinned Footer Buttons -->
      <div class="px-5 py-3 border-t border-slate-200 bg-slate-100 flex justify-end gap-2.5 shrink-0">
        <button 
          type="button"
          @click="$emit('close')" 
          class="h-9 px-4 rounded-lg border border-slate-300 bg-white text-slate-700 font-bold cursor-pointer transition-colors hover:bg-slate-50 hover:text-slate-900 text-xs"
        >
          {{ t('settings.close') }}
        </button>
        <button 
          type="button"
          @click="handleSave" 
          class="h-9 px-5 rounded-lg bg-blue-600 text-white font-bold cursor-pointer transition-colors hover:bg-blue-700 text-xs shadow-xs active:scale-95"
        >
          {{ t('settings.save') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useSystemStore } from '../../../core/stores/system';
import { useAuthStore } from '../../../core/stores/auth';
import { useSettingsModal } from '../composables/useSettingsModal';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const { t } = useI18n();
const system = useSystemStore();
const authStore = useAuthStore();

const {
  activeTab,
  bartenderStatus,
  isRestartingEngine,
  dirError,
  formData,
  audioDevices,
  availablePrinters,
  loadingPrinters,
  detectingAgent,
  availableScalePorts,
  loadingScale,
  CANONICAL_TEMPLATES,
  templateCheckResults,
  isCheckingTemplates,
  checkAllTemplates,
  handleRestartEngine,
  loadScaleStatus,
  discoverAgent,
  loadPrinters,
  handleSave,
} = useSettingsModal(props, () => emit('close'));
</script>
