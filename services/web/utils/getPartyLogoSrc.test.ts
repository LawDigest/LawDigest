import { describe, expect, it, vi } from 'vitest';
import getPartyLogoSrc from './getPartyLogoSrc';

describe('getPartyLogoSrc', () => {
  it('uses local wide party logos for API party image paths', () => {
    expect(getPartyLogoSrc('/party/wide/1.png', false)).toBe('/images/parties/wide/1.png');
  });

  it('uses local dark party logos only when the dark asset exists', () => {
    expect(getPartyLogoSrc('/party/wide/1.png', true)).toBe('/images/parties/dark/1.png');
    expect(getPartyLogoSrc('/party/wide/3.png', true)).toBe('/images/parties/wide/3.png');
  });

  it('returns null when no image URL is available', () => {
    expect(getPartyLogoSrc(null, false)).toBeNull();
    expect(getPartyLogoSrc(undefined, false)).toBeNull();
  });

  it('falls back to the configured image origin for non-party image paths', () => {
    vi.stubEnv('NEXT_PUBLIC_IMAGE_URL', 'https://api.lawdigest.kr');
    expect(getPartyLogoSrc('/custom/logo.png', false)).toBe('https://api.lawdigest.kr/custom/logo.png');
    vi.unstubAllEnvs();
  });
});
