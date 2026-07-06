import { describe, expect, it } from 'vitest';
import { buildHemicycle } from './hemicycle';

describe('buildHemicycle', () => {
  it('생성된 좌석 수는 항상 총 의석과 일치한다', () => {
    [1, 10, 50, 108, 170, 300, 305].forEach((total) => {
      const { seats } = buildHemicycle(total);
      expect(seats.length).toBe(total);
    });
  });

  it('총 의석이 많을수록 행 수가 늘어난다', () => {
    expect(buildHemicycle(300).rows).toBeGreaterThan(buildHemicycle(30).rows);
    expect(buildHemicycle(30).rows).toBeGreaterThanOrEqual(2);
  });

  it('좌석은 왼쪽(π)에서 오른쪽(0)으로 각도가 감소하도록 정렬된다', () => {
    const { seats } = buildHemicycle(120);
    for (let i = 1; i < seats.length; i += 1) {
      expect(seats[i].theta).toBeLessThanOrEqual(seats[i - 1].theta + 1e-9);
    }
  });

  it('좌석이 없으면 빈 결과를 반환한다', () => {
    expect(buildHemicycle(0)).toEqual({ rows: 0, seats: [], rowGap: 0 });
  });
});
