import {
  ElectionFamily,
  ElectionRegionResolveState,
  ElectionRegionType,
  ElectionSelectorItem,
  ElectionUiTemplate,
} from '@/types';

export const inferElectionFamilyFromId = (electionId: string): ElectionFamily => {
  if (electionId.startsWith('president')) {
    return 'president';
  }

  if (electionId.startsWith('assembly')) {
    return 'assembly';
  }

  return 'local';
};

export const getElectionFamilyLabel = (family: ElectionFamily) => {
  if (family === 'assembly') {
    return '국회의원 선거';
  }

  if (family === 'president') {
    return '대통령 선거';
  }

  return '지방선거';
};

export const getElectionHeadline = (election: ElectionSelectorItem | null) => {
  if (!election) {
    return '선거 셸';
  }

  return election.election_name;
};

export const getElectionOptionDescription = (election: ElectionSelectorItem) => {
  const formattedDate = election.election_date.replace(/-/g, '.');
  const suffix = election.upcoming ? '예정' : '지난 선거';

  return `${election.election_name} · ${formattedDate} · ${suffix}`;
};

export const getResolveStateMessage = (state?: ElectionRegionResolveState | null) => {
  switch (state) {
    case 'requesting-permission':
      return '위치 권한을 허용하면 현재 지역을 기준으로 지역별 선거 템플릿을 바로 열 수 있습니다.';
    case 'manual-required':
      return '현재 위치를 확인할 수 없어 직접 지역을 선택해야 합니다.';
    case 'gps-suggested':
      return '추천된 지역을 확인하거나 직접 수정할 수 있습니다.';
    case 'confirmed':
      return '지역이 확인되었습니다.';
    default:
      return '현재 위치를 사용하거나 직접 지역을 선택해 지역별 선거 결과 셸을 시작하세요.';
  }
};

export const getRegionTypeLabel = (regionType: ElectionRegionType) => {
  switch (regionType) {
    case 'NATIONAL':
      return '전국';
    case 'PROVINCE':
      return '시도';
    case 'DISTRICT':
      return '선거구';
    case 'COUNTY':
      return '시군구';
    default:
      return regionType;
  }
};

export const getTemplateLabel = (template: ElectionUiTemplate) => {
  if (template === 'CANDIDATE') {
    return '후보 중심';
  }

  return '지역 중심';
};
