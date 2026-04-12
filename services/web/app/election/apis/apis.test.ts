import { afterEach, describe, expect, it } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';

const createAxiosError = (status: number) =>
  new AxiosError(`status-${status}`, undefined, undefined, undefined, {
    status,
    statusText: String(status),
    headers: {},
    config: { headers: new AxiosHeaders() },
    data: {},
  });

describe('shouldRecoverWithMock', () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_DOMAIN;
  });

  it('dev 도메인에서도 401은 mock fallback 하지 않는다', async () => {
    process.env.NEXT_PUBLIC_DOMAIN = 'https://dev.lawdigest.kr';
    const { shouldRecoverWithMock } = await import('./apis');

    expect(shouldRecoverWithMock(createAxiosError(401))).toBe(false);
  });

  it('dev 도메인에서 500은 mock fallback 한다', async () => {
    process.env.NEXT_PUBLIC_DOMAIN = 'https://dev.lawdigest.kr';
    const { shouldRecoverWithMock } = await import('./apis');

    expect(shouldRecoverWithMock(createAxiosError(500))).toBe(true);
  });
});
