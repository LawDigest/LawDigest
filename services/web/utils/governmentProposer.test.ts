import { describe, expect, it } from 'vitest';
import { getGovernmentAdministrationName, isGovernmentBill, isGovernmentProposerKind } from './governmentProposer';

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

  it('운영 API가 proposer_kind를 아직 주지 않아도 ARC 정부안이면 정부법안으로 본다', () => {
    expect(
      isGovernmentBill({
        billId: 'ARC_B2H6E0N6J0F4P0I9E3O7T0V8H6F9R0',
        representativeProposerCount: 0,
        publicProposerCount: 0,
      }),
    ).toBe(true);
  });

  it('의원/위원장안과 섞이지 않도록 ARC와 빈 발의자 조건을 함께 본다', () => {
    expect(
      isGovernmentBill({
        billId: 'PRC_B2H6E0N6J0F4P0I9E3O7T0V8H6F9R0',
        representativeProposerCount: 0,
        publicProposerCount: 0,
      }),
    ).toBe(false);
    expect(
      isGovernmentBill({
        billId: 'ARC_B2H6E0N6J0F4P0I9E3O7T0V8H6F9R0',
        representativeProposerCount: 1,
        publicProposerCount: 0,
      }),
    ).toBe(false);
  });

  it('기준일 이전 정부법안은 대한민국 정부로 표시한다', () => {
    expect(getGovernmentAdministrationName('2025-06-02')).toBe('대한민국 정부');
  });
});
