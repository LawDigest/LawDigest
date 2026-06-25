const COMMITTEE_LOGO_BASE_PATH = '/images/committees';
const COMMITTEE_ACCENT_COLOR = '#143f74';

type CommitteeLogoKey =
  | 'committee'
  | 'steering'
  | 'legislation'
  | 'policy'
  | 'finance'
  | 'edu'
  | 'science'
  | 'uft'
  | 'defense'
  | 'adminhom'
  | 'cst'
  | 'agri'
  | 'industry'
  | 'health'
  | 'environment'
  | 'ltc'
  | 'intelligence'
  | 'women'
  | 'budget'
  | 'moral'
  | 'spc';

type CommitteeLogoDefinition = {
  committeeName: string;
  proposerTitle: string;
  logoKey: CommitteeLogoKey;
};

export type ChairmanProposerInfo = {
  committeeName: string;
  proposerTitle: string;
  logoSrc: string;
  logoAlt: string;
  accentColor: string;
};

const COMMITTEE_LOGOS: CommitteeLogoDefinition[] = [
  { committeeName: '국회운영위원회', proposerTitle: '국회운영위원장', logoKey: 'steering' },
  { committeeName: '법제사법위원회', proposerTitle: '법제사법위원장', logoKey: 'legislation' },
  { committeeName: '정무위원회', proposerTitle: '정무위원장', logoKey: 'policy' },
  { committeeName: '기획재정위원회', proposerTitle: '기획재정위원장', logoKey: 'finance' },
  { committeeName: '재정경제기획위원회', proposerTitle: '재정경제기획위원장', logoKey: 'finance' },
  { committeeName: '교육위원회', proposerTitle: '교육위원장', logoKey: 'edu' },
  { committeeName: '과학기술정보방송통신위원회', proposerTitle: '과학기술정보방송통신위원장', logoKey: 'science' },
  { committeeName: '외교통일위원회', proposerTitle: '외교통일위원장', logoKey: 'uft' },
  { committeeName: '국방위원회', proposerTitle: '국방위원장', logoKey: 'defense' },
  { committeeName: '행정안전위원회', proposerTitle: '행정안전위원장', logoKey: 'adminhom' },
  { committeeName: '문화체육관광위원회', proposerTitle: '문화체육관광위원장', logoKey: 'cst' },
  { committeeName: '농림축산식품해양수산위원회', proposerTitle: '농림축산식품해양수산위원장', logoKey: 'agri' },
  {
    committeeName: '산업통상자원중소벤처기업위원회',
    proposerTitle: '산업통상자원중소벤처기업위원장',
    logoKey: 'industry',
  },
  { committeeName: '보건복지위원회', proposerTitle: '보건복지위원장', logoKey: 'health' },
  { committeeName: '환경노동위원회', proposerTitle: '환경노동위원장', logoKey: 'environment' },
  { committeeName: '기후에너지환경노동위원회', proposerTitle: '기후에너지환경노동위원장', logoKey: 'environment' },
  { committeeName: '국토교통위원회', proposerTitle: '국토교통위원장', logoKey: 'ltc' },
  { committeeName: '정보위원회', proposerTitle: '정보위원장', logoKey: 'intelligence' },
  { committeeName: '여성가족위원회', proposerTitle: '여성가족위원장', logoKey: 'women' },
  { committeeName: '성평등가족위원회', proposerTitle: '성평등가족위원장', logoKey: 'women' },
  { committeeName: '예산결산특별위원회', proposerTitle: '예산결산특별위원장', logoKey: 'budget' },
  { committeeName: '윤리특별위원회', proposerTitle: '윤리특별위원장', logoKey: 'moral' },
];

const normalizeCommitteeText = (value?: string | null) => value?.replace(/\s+/g, '').trim() ?? '';

export function isChairmanProposerKind(proposerKind?: string | null): boolean {
  return proposerKind === 'CHAIRMAN' || proposerKind === '위원장';
}

export function isChairmanBill({
  proposerKind,
  proposerText,
}: {
  proposerKind?: string | null;
  proposerText?: string | null;
}): boolean {
  if (isChairmanProposerKind(proposerKind)) {
    return true;
  }

  return normalizeCommitteeText(proposerText).endsWith('위원장');
}

function getCommitteeLogoDefinition({
  committee,
  proposerText,
}: {
  committee?: string | null;
  proposerText?: string | null;
}): CommitteeLogoDefinition | null {
  const normalizedCommittee = normalizeCommitteeText(committee);
  const normalizedProposer = normalizeCommitteeText(proposerText);

  return (
    COMMITTEE_LOGOS.find(
      ({ committeeName, proposerTitle }) =>
        normalizeCommitteeText(committeeName) === normalizedCommittee ||
        normalizeCommitteeText(proposerTitle) === normalizedProposer,
    ) ?? null
  );
}

export function getChairmanProposerInfo({
  proposerKind,
  proposerText,
  committee,
}: {
  proposerKind?: string | null;
  proposerText?: string | null;
  committee?: string | null;
}): ChairmanProposerInfo | null {
  if (!isChairmanBill({ proposerKind, proposerText })) {
    return null;
  }

  const logoDefinition = getCommitteeLogoDefinition({ committee, proposerText });
  const committeeName = committee?.trim() || logoDefinition?.committeeName || '';
  const proposerTitle = proposerText?.trim() || logoDefinition?.proposerTitle || committeeName || '위원장';
  const logoKey = logoDefinition?.logoKey ?? (committeeName.includes('특별위원회') ? 'spc' : 'committee');

  return {
    committeeName,
    proposerTitle,
    logoSrc: `${COMMITTEE_LOGO_BASE_PATH}/${logoKey}.jpg`,
    logoAlt: `${committeeName || proposerTitle} 로고`,
    accentColor: COMMITTEE_ACCENT_COLOR,
  };
}
