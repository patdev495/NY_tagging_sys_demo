export type ScaleToleranceStatus =
  | 'DISCONNECTED'
  | 'UNSTABLE'
  | 'UNDERWEIGHT'
  | 'OVERWEIGHT'
  | 'READY';

export interface ScaleToleranceParams {
  isConnected: boolean;
  currentWeight: number;
  isStable: boolean;
  product?: {
    min_weight?: number;
    target_weight?: number;
    max_weight?: number;
  } | null;
}

export interface ScaleToleranceResult {
  status: ScaleToleranceStatus;
  canPrint: boolean;
  message: string;
  diffFromTarget?: number;
}

export function evaluateScaleTolerance(params: ScaleToleranceParams): ScaleToleranceResult {
  if (!params.isConnected) {
    return {
      status: 'DISCONNECTED',
      canPrint: false,
      message: 'Mất kết nối với cân điện tử (Print Agent)',
    };
  }

  if (!params.isStable) {
    return {
      status: 'UNSTABLE',
      canPrint: false,
      message: 'Cân đang dao động, vui lòng chờ ổn định...',
    };
  }

  const { min_weight, target_weight, max_weight } = params.product || {};
  const weight = params.currentWeight;

  if (min_weight !== undefined && min_weight !== null && weight < min_weight) {
    return {
      status: 'UNDERWEIGHT',
      canPrint: false,
      message: `Thiếu trọng lượng (Hiện tại: ${weight.toFixed(3)}kg < Tối thiểu: ${min_weight.toFixed(3)}kg)`,
      diffFromTarget: target_weight ? weight - target_weight : undefined,
    };
  }

  if (max_weight !== undefined && max_weight !== null && weight > max_weight) {
    return {
      status: 'OVERWEIGHT',
      canPrint: false,
      message: `Thừa trọng lượng (Hiện tại: ${weight.toFixed(3)}kg > Tối đa: ${max_weight.toFixed(3)}kg)`,
      diffFromTarget: target_weight ? weight - target_weight : undefined,
    };
  }

  return {
    status: 'READY',
    canPrint: true,
    message: 'Trọng lượng đạt chuẩn. Sẵn sàng in tem Erro [F9]',
    diffFromTarget: target_weight ? weight - target_weight : 0,
  };
}

export function generateErro01SNPreview(pkgPrefix: string, yymm: string, sequence: number | string): string {
  const seqStr = String(sequence).padStart(6, '0');
  return `${pkgPrefix || ''}${yymm || ''}${seqStr}`;
}
