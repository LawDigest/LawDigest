/**
 * 국회 좌석도 배치 순서(왼→오른쪽).
 *
 * 의석 1위 정당을 왼쪽 끝, 2위 정당을 오른쪽 끝에 두고, 그 아래 순위 정당들을
 * 가운데에 의석 많은 순으로 채운다. 좌석은 이 순서대로 왼쪽부터 색을 채운다.
 */
export function orderPartiesByBloc<T extends { congressman_count: number }>(parties: T[]): T[] {
  const sorted = [...parties].sort((a, b) => b.congressman_count - a.congressman_count);
  if (sorted.length <= 2) return sorted;

  const [first, second, ...rest] = sorted;
  // 왼쪽: 1위 → 가운데: 3위 이하(의석 많은 순) → 오른쪽: 2위
  return [first, ...rest, second];
}
