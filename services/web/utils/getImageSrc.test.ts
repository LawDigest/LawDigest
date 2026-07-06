import { describe, expect, it, vi } from 'vitest';
import getImageSrc from './getImageSrc';

describe('getImageSrc', () => {
  it('prefixes relative paths with the configured image origin', () => {
    vi.stubEnv('NEXT_PUBLIC_IMAGE_URL', 'https://api.lawdigest.kr');
    expect(getImageSrc('/congressman/1.png')).toBe('https://api.lawdigest.kr/congressman/1.png');
    vi.unstubAllEnvs();
  });

  it('returns undefined when no path is available', () => {
    expect(getImageSrc(null)).toBeUndefined();
    expect(getImageSrc(undefined)).toBeUndefined();
    expect(getImageSrc('')).toBeUndefined();
  });
});
