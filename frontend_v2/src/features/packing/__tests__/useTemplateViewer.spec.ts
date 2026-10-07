import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTemplateViewer, getProductTemplateFilename } from '../composables/useTemplateViewer';
import type { Product } from '../../../types/api';

describe('useTemplateViewer Composable', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('getProductTemplateFilename', () => {
    it('resolves canonical template names correctly for various template_types', () => {
      expect(getProductTemplateFilename(null)).toBe('carton_base.btw');

      const uiStd: Product = { id: 1, customer_id: 1, item_name: 'P1', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'standard', allow_partial: 0 };
      expect(getProductTemplateFilename(uiStd)).toBe('carton_base.btw');

      const uiDetail: Product = { id: 2, customer_id: 1, item_name: 'P2', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'detailed', allow_partial: 0 };
      expect(getProductTemplateFilename(uiDetail)).toBe('carton_detail_1M_W.btw');

      const erro01: Product = { id: 3, customer_id: 2, item_name: 'P3', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'erro_01', allow_partial: 0 };
      expect(getProductTemplateFilename(erro01)).toBe('erro_01.btw');

      const erro02: Product = { id: 4, customer_id: 2, item_name: 'P4', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'erro_02', allow_partial: 0 };
      expect(getProductTemplateFilename(erro02)).toBe('erro_02.btw');

      const erro03: Product = { id: 5, customer_id: 2, item_name: 'P5', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'erro_03', allow_partial: 0 };
      expect(getProductTemplateFilename(erro03)).toBe('erro_03.btw');

      const erro04: Product = { id: 6, customer_id: 2, item_name: 'P6', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'erro_04', allow_partial: 0 };
      expect(getProductTemplateFilename(erro04)).toBe('erro_04.btw');

      const erro05: Product = { id: 7, customer_id: 2, item_name: 'P7', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'erro_05', allow_partial: 0 };
      expect(getProductTemplateFilename(erro05)).toBe('erro_05.btw');

      const customPath: Product = { id: 8, customer_id: 1, item_name: 'P8', packed_qty: 10, start_part: 'CN', middle_part: '1', template_type: 'standard', template_path: 'D:\\PAT\\Templates\\custom_label.btw', allow_partial: 0 };
      expect(getProductTemplateFilename(customPath)).toBe('custom_label.btw');
    });
  });

  describe('openProductTemplate', () => {
    const sampleProduct: Product = {
      id: 1,
      customer_id: 2,
      item_name: 'Erro 01 Item',
      packed_qty: 5,
      start_part: 'CN',
      middle_part: '1',
      template_type: 'erro_01',
      allow_partial: 0,
    };

    it('returns true and does not open modal when template file exists', async () => {
      const onTemplateFound = vi.fn();
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, exists: true, message: 'Opened', filename: 'erro_01.btw' }),
      }));

      const { openProductTemplate, showMissingModal, isOpening } = useTemplateViewer({
        getAgentUrl: () => 'http://127.0.0.1:8080',
        getLocalTemplateDir: () => 'D:\\PAT\\Templates',
        onTemplateFound,
      });

      const promise = openProductTemplate(sampleProduct);
      expect(isOpening.value).toBe(true);
      const result = await promise;

      expect(result).toBe(true);
      expect(isOpening.value).toBe(false);
      expect(showMissingModal.value).toBe(false);
      expect(onTemplateFound).toHaveBeenCalled();
      expect(fetch).toHaveBeenCalledWith(
        'http://127.0.0.1:8080/open-template',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ folder: 'D:\\PAT\\Templates', filename: 'erro_01.btw' }),
        })
      );
    });

    it('opens missing modal and sets filenames when template file is missing', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: false, exists: false, message: 'Not found', filename: 'erro_01.btw' }),
      }));

      const { openProductTemplate, showMissingModal, missingFilename, targetFolder } = useTemplateViewer({
        getAgentUrl: () => 'http://127.0.0.1:8080',
        getLocalTemplateDir: () => 'D:\\PAT\\Templates',
      });

      const result = await openProductTemplate(sampleProduct);

      expect(result).toBe(false);
      expect(showMissingModal.value).toBe(true);
      expect(missingFilename.value).toBe('erro_01.btw');
      expect(targetFolder.value).toBe('D:\\PAT\\Templates');
    });

    it('handles network / connection failure when agent is offline', async () => {
      vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Connection refused')));

      const { openProductTemplate, showMissingModal, viewerErrorMessage } = useTemplateViewer({
        getAgentUrl: () => 'http://127.0.0.1:8080',
      });

      const result = await openProductTemplate(sampleProduct);

      expect(result).toBe(false);
      expect(showMissingModal.value).toBe(false);
      expect(viewerErrorMessage.value).toContain('Không thể kết nối đến Print Agent');
    });
  });

  describe('openTemplateFolder', () => {
    it('calls /open-dir endpoint with target folder', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true, message: 'Dir opened' }),
      }));

      const { openTemplateFolder, isOpeningFolder } = useTemplateViewer({
        getAgentUrl: () => 'http://127.0.0.1:8080',
        getLocalTemplateDir: () => 'D:\\PAT\\Templates',
      });

      const promise = openTemplateFolder('D:\\PAT\\CustomDir');
      expect(isOpeningFolder.value).toBe(true);
      const res = await promise;

      expect(res).toBe(true);
      expect(isOpeningFolder.value).toBe(false);
      expect(fetch).toHaveBeenCalledWith(
        'http://127.0.0.1:8080/open-dir',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ folder: 'D:\\PAT\\CustomDir' }),
        })
      );
    });
  });
});
