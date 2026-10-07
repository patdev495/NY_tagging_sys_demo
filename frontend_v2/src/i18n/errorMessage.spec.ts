import { describe, expect, it } from 'vitest';
import { userErrorMessage } from './errorMessage';

const messages: Record<string, string> = {
  'errors.agentOffline': 'Agent offline',
  'errors.unexpected': 'Something went wrong',
};

const t = (key: string) => messages[key] ?? key;

describe('userErrorMessage', () => {
  it('maps stable server codes instead of displaying server text', () => {
    expect(userErrorMessage({ response: { data: { code: 'AGENT_CONNECTION_FAILED', detail: 'nội bộ' } } }, t))
      .toBe('Agent offline');
  });

  it('uses localized generic fallback for unknown errors', () => {
    expect(userErrorMessage(new Error('secret internal error'), t)).toBe('Something went wrong');
  });
});
