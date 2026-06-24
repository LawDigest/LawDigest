import { describe, expect, it } from 'vitest';
import { getGovernmentAdministrationName, isGovernmentProposerKind } from './governmentProposer';

describe('governmentProposer', () => {
  it('정부 발의자 구분을 판별한다', () => {
    expect(isGovernmentProposerKind('GOVERNMENT')).toBe(true);
    expect(isGovernmentProposerKind('정부')).toBe(true);
    expect(isGovernmentProposerKind('CONGRESSMAN')).toBe(false);
  });

  it('2025-06-03 이후 정부법안은 이재명 정부로 표시한다', () => {
    expect(getGovernmentAdministrationName('2025-06-03')).toBe('이재명 정부');
    expect(getGovernmentAdministrationName('2026-06-04')).toBe('이재명 정부');
  });

  it('기준일 이전 정부법안은 대한민국 정부로 표시한다', () => {
    expect(getGovernmentAdministrationName('2025-06-02')).toBe('대한민국 정부');
  });
});
