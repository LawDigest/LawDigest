const LEE_ADMINISTRATION_START_DATE = '2025-06-03';

export function isGovernmentProposerKind(proposerKind?: string | null): boolean {
  return proposerKind === 'GOVERNMENT' || proposerKind === '정부';
}

export function getGovernmentAdministrationName(proposeDate?: string | null): string {
  if (!proposeDate) {
    return '대한민국 정부';
  }

  return proposeDate >= LEE_ADMINISTRATION_START_DATE ? '이재명 정부' : '대한민국 정부';
}
