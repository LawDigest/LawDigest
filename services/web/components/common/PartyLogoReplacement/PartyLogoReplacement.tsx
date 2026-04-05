const PARTY_COLORS: Record<string, string> = {
  더불어민주당: '#152484',
  국민의힘: '#e61e2b',
  조국혁신당: '#004098',
  개혁신당: '#FF6B00',
  진보당: '#D6001C',
  새로운미래: '#00A0E9',
  사회민주당: '#F5A200',
  무소속: '#6B7280',
};

function getPartyColor(partyName: string): string {
  const matched = Object.entries(PARTY_COLORS).find(([key]) => partyName.includes(key) || key.includes(partyName));
  return matched?.[1] ?? '#9CA3AF';
}

function getInitial(partyName: string): string {
  // '더불어민주당' → '민', '국민의힘' → '국' 등 핵심 글자 추출
  const SHORT: Record<string, string> = {
    더불어민주당: '민',
    국민의힘: '국',
    조국혁신당: '혁',
    개혁신당: '개',
    진보당: '진',
    새로운미래: '새',
    사회민주당: '사',
    무소속: '무',
  };
  const matched = Object.entries(SHORT).find(([key]) => partyName.includes(key) || key.includes(partyName));
  if (matched) return matched[1];
  return partyName[0] ?? '?';
}

export default function PartyLogoReplacement({
  partyName,
  circle,
  color: colorProp,
}: {
  partyName: string;
  circle: boolean;
  color?: string;
}) {
  const color = colorProp ?? getPartyColor(partyName);
  const initial = getInitial(partyName);

  if (circle) {
    return (
      <div
        className="w-[54px] h-[54px] rounded-full flex justify-center items-center text-white text-sm font-bold shrink-0"
        style={{ backgroundColor: color }}
        title={partyName}>
        {initial}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1" title={partyName}>
      <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
      <span className="text-sm font-semibold text-gray-3 dark:text-gray-1 truncate">{partyName}</span>
    </div>
  );
}
