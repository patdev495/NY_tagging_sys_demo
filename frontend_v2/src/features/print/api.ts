import api from '../../core/api';
import type { Carton } from '../../types/api';

export default {
  updateCartonStatus(cartonId: number, status: string) {
    return api.patch(`/print/carton/${cartonId}/status`, { status });
  },
  searchCarton(sn: string) {
    return api.get<Carton>('/cartons/search', { params: { carton_sn: sn } });
  },
  reprintCarton(cartonId: number, templatePath: string, printerName: string) {
    return api.post(`/print/carton/${cartonId}/reprint`, null, { 
      params: { template_path: templatePath, printer_name: printerName }
    });
  },
  /** Lấy cấu hình in từ server */
  getPrintConfig() {
    return api.get('/print/config');
  },
  /** Gửi lệnh in qua Backend → Agent Server */
  serverPrint(cartonId: number, printerName?: string, fallbackTemplatePath?: string) {
    return api.post(`/print/carton/${cartonId}/server-print`, null, {
      params: { 
        printer_name: printerName || undefined,
        fallback_template_path: fallbackTemplatePath || undefined,
      }
    });
  },
  /** Gửi lệnh in qua Local Agent (Chạy tại máy trạm) */
  async agentPrint(agentUrl: string, xmlContent: string, printerName?: string, localTemplateDir?: string) {
    try {
      const response = await fetch(`${agentUrl}/print`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          xml_content: xmlContent,
          printer_name: printerName || null,
          local_template_dir: localTemplateDir || null
        })
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = data.detail && typeof data.detail === 'object' ? data.detail : {};
        const error = new Error('Agent print failed') as Error & { code?: string };
        error.code = typeof detail.code === 'string' ? detail.code : 'PRINT_FAILED';
        throw error;
      }
      return data;
    } catch (err: any) {
      if (err.message?.includes('Failed to fetch')) {
        throw new Error('AGENT_CONNECTION_FAILED');
      }
      throw err;
    }
  },
  async agentHealth(agentUrl: string) {
    const response = await fetch(`${agentUrl}/health`);
    if (!response.ok) throw new Error('AGENT_CONNECTION_FAILED');
    return response.json() as Promise<{ bartender_ready: boolean }>;
  },
  /** Lấy danh sách máy in khả dụng từ Server/Agent */
  getAvailablePrinters() {
    return api.get<string[]>('/print/printers');
  },
  /** Lấy IP của Client từ server */
  whoami() {
    return api.get<{ ip: string }>('/print/whoami');
  },
  /** Lấy file .xml của thùng để in qua Agent */
  download_carton_btxml(cartonId: number, templatePath: string) {
    return api.get<string>(`/print/carton/${cartonId}/btxml`, {
      params: { template_path: templatePath },
      responseType: 'text'
    });
  },
  /** Lấy danh sách template .btw có sẵn trên server */
  getTemplates() {
    return api.get<{ templates: { name: string; path: string; size_bytes: number; updated_at: string }[] }>('/print/templates');
  },
  /** Kiểm tra tính hợp lệ của file template */
  validateTemplate(templateName: string, folder?: string) {
    return api.post<{ valid: boolean; message: string; resolved_path: string | null }>('/print/validate-template', { 
      template_name: templateName,
      folder: folder || undefined
    });
  },
  /** Lấy danh sách 7 tem BarTender chuẩn của hệ thống kèm trạng thái */
  getCanonicalTemplates(folder?: string) {
    return api.get<{
      templates: {
        filename: string;
        customer: string;
        type: string;
        name: string;
        exists: boolean;
        resolved_path: string | null;
      }[];
      templates_dir: string;
    }>('/print/canonical-templates', { params: { folder: folder || undefined } });
  },
  /** Khởi động lại BarTender COM Engine (Admin only) */
  restartEngine() {
    return api.post<{ success: boolean; message: string; bartender_ready: boolean }>('/print/restart-engine');
  }
};
