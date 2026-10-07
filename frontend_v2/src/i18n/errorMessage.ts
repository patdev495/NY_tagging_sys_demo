export type Translate = (key: string, params?: Record<string, unknown>) => string;

type ErrorLike = {
  code?: unknown;
  response?: { data?: { code?: unknown; error?: { code?: unknown }; detail?: { code?: unknown } } };
};

const codeToKey: Record<string, string> = {
  AGENT_CONNECTION_FAILED: 'errors.agentOffline',
  AGENT_OFFLINE: 'errors.agentOffline',
  PRINT_FAILED: 'errors.printFailed',
  TEMPLATE_NOT_FOUND: 'errors.templateMissing',
  UNAUTHORIZED: 'errors.unauthorized',
  FORBIDDEN: 'errors.forbidden',
  VALIDATION_ERROR: 'errors.validation',
};

function readCode(error: ErrorLike): string | undefined {
  const data = error.response?.data;
  const nested = data?.error ?? data?.detail;
  const code = error.code ?? data?.code ?? nested?.code;
  return typeof code === 'string' ? code : undefined;
}

export function userErrorMessage(error: unknown, t: Translate): string {
  const code = readCode((error ?? {}) as ErrorLike);
  return code && codeToKey[code] ? t(codeToKey[code]) : t('errors.unexpected');
}
