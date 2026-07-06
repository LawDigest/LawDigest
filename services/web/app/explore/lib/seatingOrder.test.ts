import { describe, expect, it } from 'vitest';
import { orderPartiesByBloc } from './seatingOrder';

const p = (name: string, count: number) => ({ name, congressman_count: count });

describe('orderPartiesByBloc', () => {
  it('1위는 왼쪽, 2위는 오른쪽, 나머지는 가운데에 의석 많은 순으로 배치한다', () => {
    const ordered = orderPartiesByBloc([p('C', 30), p('A', 170), p('D', 12), p('B', 108), p('E', 20)]);
    expect(ordered.map((x) => x.name)).toEqual(['A', 'C', 'E', 'D', 'B']);
  });

  it('정당이 2개 이하면 1위 왼쪽·2위 오른쪽만 유지한다', () => {
    expect(orderPartiesByBloc([p('B', 108), p('A', 170)]).map((x) => x.name)).toEqual(['A', 'B']);
    expect(orderPartiesByBloc([p('A', 170)]).map((x) => x.name)).toEqual(['A']);
    expect(orderPartiesByBloc([])).toEqual([]);
  });
});
