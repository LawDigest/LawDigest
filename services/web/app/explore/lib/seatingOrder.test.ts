import { describe, expect, it } from 'vitest';
import { orderPartiesByBloc } from './seatingOrder';

const p = (name: string, count: number) => ({ name, party_name: name, congressman_count: count });

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

  it('진보당은 의석수와 무관하게 2위(오른쪽) 옆이 아닌 1위(왼쪽) 옆에 배치한다', () => {
    const ordered = orderPartiesByBloc([
      p('더불어민주당', 170),
      p('국민의힘', 108),
      p('조국혁신당', 12),
      p('개혁신당', 3),
      p('진보당', 3),
      p('사회민주당', 1),
    ]);
    expect(ordered.map((x) => x.name)).toEqual([
      '더불어민주당',
      '진보당',
      '조국혁신당',
      '개혁신당',
      '사회민주당',
      '국민의힘',
    ]);
  });
});
