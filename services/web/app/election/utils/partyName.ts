const CANONICAL_PARTY_NAMES = [
  '더불어민주당',
  '국민의힘',
  '개혁신당',
  '조국혁신당',
  '진보당',
  '정의당',
  '기본소득당',
  '새로운미래',
  '자유통일당',
  '민주노동당',
  '노동당',
  '녹색당',
  '무소속',
] as const;

function buildPartyKey(value: string) {
  return value.trim().replace(/\s+/g, '');
}

export function normalizePartyName(name: string | null | undefined) {
  const trimmed = name?.trim() ?? '';

  if (!trimmed || trimmed === 'undecided') {
    return trimmed;
  }

  const normalizedKey = buildPartyKey(trimmed);
  const canonical = CANONICAL_PARTY_NAMES.find((partyName) => buildPartyKey(partyName) === normalizedKey);

  return canonical ?? trimmed;
}

export function aggregatePartySnapshots<T extends { party_name: string; percentage: number }>(snapshots: T[]) {
  const aggregated = new Map<string, number>();

  snapshots.forEach((snapshot) => {
    const normalizedPartyName = normalizePartyName(snapshot.party_name);
    aggregated.set(normalizedPartyName, (aggregated.get(normalizedPartyName) ?? 0) + snapshot.percentage);
  });

  return Array.from(aggregated.entries()).map(([party_name, percentage]) => ({ party_name, percentage }));
}
