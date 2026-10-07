import { ref } from 'vue';
import type { Product } from '../../../types/api';

export interface UseTemplateViewerOptions {
  getAgentUrl?: () => string;
  getLocalTemplateDir?: () => string;
  onTemplateFound?: () => void;
  notify?: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
}

export function getProductTemplateFilename(product: Product | null): string {
  if (!product) return 'carton_base.btw';
  const canonicalFallback = product.template_type === 'erro_05'
    ? 'erro_05.btw'
    : (product.template_type === 'erro_04'
      ? 'erro_04.btw'
      : (product.template_type === 'erro_03'
        ? 'erro_03.btw'
        : (product.template_type === 'erro_02'
          ? 'erro_02.btw'
          : (product.template_type === 'erro_01'
            ? 'erro_01.btw'
            : (product.template_type === 'detailed' ? 'carton_detail_1M_W.btw' : 'carton_base.btw')))));
  const rawPath = product.template_path || canonicalFallback;
  return rawPath.split(/[\\/]/).pop() || canonicalFallback;
}

export function useTemplateViewer(options: UseTemplateViewerOptions = {}) {
  const isOpening = ref<boolean>(false);
  const isOpeningFolder = ref<boolean>(false);
  const showMissingModal = ref<boolean>(false);
  const missingFilename = ref<string>('');
  const targetFolder = ref<string>('');
  const viewerErrorMessage = ref<string>('');

  const getAgentUrl = (): string => {
    return options.getAgentUrl?.() || 'http://127.0.0.1:8080';
  };

  const getLocalTemplateDir = (): string => {
    return options.getLocalTemplateDir?.() || 'D:\\PAT\\Templates';
  };

  const openProductTemplate = async (product: Product | null): Promise<boolean> => {
    if (!product) return false;

    isOpening.value = true;
    viewerErrorMessage.value = '';
    const filename = getProductTemplateFilename(product);
    const folder = getLocalTemplateDir();
    const agentUrl = getAgentUrl();

    try {
      const resp = await fetch(`${agentUrl}/open-template`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder, filename }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        if (resp.status === 404 && (!errData.detail || errData.detail === 'Not Found')) {
          viewerErrorMessage.value = `Chưa tìm thấy tính năng mở tem trên Print Agent tại ${agentUrl}. Vui lòng khởi động lại Print Agent.`;
        } else {
          viewerErrorMessage.value = errData.detail || errData.message || 'Lỗi khi yêu cầu mở tệp template';
        }
        options.notify?.(viewerErrorMessage.value, 'error');
        return false;
      }

      const data = await resp.json();
      if (data.exists && data.success) {
        showMissingModal.value = false;
        options.onTemplateFound?.();
        options.notify?.(`Đã mở tệp ${filename} bằng BarTender`, 'success');
        return true;
      } else {
        missingFilename.value = filename;
        targetFolder.value = folder;
        showMissingModal.value = true;
        options.notify?.(`Không tìm thấy file mẫu tem ${filename}`, 'warning');
        return false;
      }
    } catch (err: any) {
      viewerErrorMessage.value = `Không thể kết nối đến Print Agent tại ${agentUrl}. Vui lòng kiểm tra lại phần mềm NY Print Agent.`;
      options.notify?.(viewerErrorMessage.value, 'error');
      return false;
    } finally {
      isOpening.value = false;
    }
  };

  const openTemplateFolder = async (customFolder?: string): Promise<boolean> => {
    isOpeningFolder.value = true;
    viewerErrorMessage.value = '';
    const folder = customFolder || targetFolder.value || getLocalTemplateDir();
    const agentUrl = getAgentUrl();

    try {
      const resp = await fetch(`${agentUrl}/open-dir`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        viewerErrorMessage.value = errData.detail || errData.message || 'Lỗi khi yêu cầu mở thư mục';
        options.notify?.(viewerErrorMessage.value, 'error');
        return false;
      }
      options.notify?.(`Đã mở thư mục ${folder} trong File Explorer`, 'success');
      return true;
    } catch (err: any) {
      viewerErrorMessage.value = `Không thể kết nối đến Print Agent tại ${agentUrl} để mở thư mục.`;
      options.notify?.(viewerErrorMessage.value, 'error');
      return false;
    } finally {
      isOpeningFolder.value = false;
    }
  };

  const closeMissingModal = () => {
    showMissingModal.value = false;
  };

  return {
    isOpening,
    isOpeningFolder,
    showMissingModal,
    missingFilename,
    targetFolder,
    viewerErrorMessage,
    openProductTemplate,
    openTemplateFolder,
    closeMissingModal,
    getProductTemplateFilename,
  };
}
