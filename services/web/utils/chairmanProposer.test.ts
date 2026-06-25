import { describe, expect, it } from 'vitest';
import { getChairmanProposerInfo, isChairmanBill, isChairmanProposerKind } from './chairmanProposer';

describe('chairmanProposer', () => {
  it('위원장 발의자 구분을 판별한다', () => {
    expect(isChairmanProposerKind('CHAIRMAN')).toBe(true);
    expect(isChairmanProposerKind('위원장')).toBe(true);
    expect(isChairmanProposerKind('GOVERNMENT')).toBe(false);
  });

  it('proposer_kind 또는 실제 발의자 문자열로 위원장안을 판별한다', () => {
    expect(isChairmanBill({ proposerKind: 'CHAIRMAN' })).toBe(true);
    expect(isChairmanBill({ proposerText: '국토교통위원장' })).toBe(true);
    expect(isChairmanBill({ proposerText: '대한민국 정부' })).toBe(false);
  });

  it('위원회명과 공식 위원회 로고 경로를 반환한다', () => {
    expect(
      getChairmanProposerInfo({
        proposerKind: 'CHAIRMAN',
        proposerText: '국토교통위원장',
        committee: '국토교통위원회',
      }),
    ).toMatchObject({
      proposerTitle: '국토교통위원장',
      committeeName: '국토교통위원회',
      logoSrc: '/images/committees/ltc.jpg',
      accentColor: '#143f74',
    });
  });

  it('위원회 개편 전후 명칭을 같은 공식 로고로 연결한다', () => {
    expect(getChairmanProposerInfo({ proposerText: '환경노동위원장', committee: '환경노동위원회' })?.logoSrc).toBe(
      '/images/committees/environment.jpg',
    );
    expect(
      getChairmanProposerInfo({ proposerText: '기후에너지환경노동위원장', committee: '기후에너지환경노동위원회' })
        ?.logoSrc,
    ).toBe('/images/committees/environment.jpg');
  });

  it('알 수 없는 위원회는 실제 문자열만 유지하고 공통 위원회 로고를 쓴다', () => {
    expect(getChairmanProposerInfo({ proposerKind: 'CHAIRMAN', proposerText: '새위원장' })).toMatchObject({
      proposerTitle: '새위원장',
      committeeName: '',
      logoSrc: '/images/committees/committee.jpg',
    });
  });
});
