import {
  ElectionCandidateDetailResponse,
  ElectionCandidateId,
  ElectionCandidateListResponse,
  ElectionId,
  ElectionMapResponse,
  ElectionOverviewResponse,
  ElectionRegionCode,
  ElectionRegionPanelResponse,
  ElectionRegionResolveRequest,
  ElectionRegionResolveResponse,
  ElectionRegionType,
  ElectionSelectorResponse,
  ElectionViewMode,
  BaseResponse,
} from '@/types';

const ok = <T>(data: T): BaseResponse<T> => ({
  code: 'SUCCESS',
  message: 'test election mock fallback',
  data,
});

const ELECTIONS: ElectionSelectorResponse['elections'] = [
  { election_id: 'assembly-2028', election_name: '23대 국회의원 선거', election_date: '2028-04-12', upcoming: true },
  { election_id: 'local-2026', election_name: '9회 지방선거', election_date: '2026-06-03', upcoming: true },
  { election_id: 'president-2025', election_name: '21대 대통령 선거', election_date: '2025-06-03', upcoming: false },
  { election_id: 'assembly-2024', election_name: '22대 국회의원 선거', election_date: '2024-04-10', upcoming: false },
  { election_id: 'local-2022', election_name: '8회 지방선거', election_date: '2022-06-01', upcoming: false },
  { election_id: 'president-2022', election_name: '20대 대통령 선거', election_date: '2022-03-09', upcoming: false },
  { election_id: 'assembly-2020', election_name: '21대 국회의원 선거', election_date: '2020-04-15', upcoming: false },
];

const resolveComparisonElectionId = (electionId: ElectionId): ElectionId => {
  switch (electionId) {
    case 'assembly-2028':
      return 'assembly-2024';
    case 'local-2026':
      return 'local-2022';
    case 'president-2025':
      return 'president-2022';
    case 'assembly-2024':
      return 'assembly-2020';
    default:
      return electionId;
  }
};

const resolveUiTemplate = (electionId: ElectionId) => (electionId.startsWith('president-') ? 'CANDIDATE' : 'REGIONAL');

const resolveRegionName = (regionCode: ElectionRegionCode, depth: ElectionRegionType) => {
  if (depth === 'NATIONAL') {
    return '대한민국';
  }

  if (depth === 'PROVINCE') {
    if (regionCode === '11') return '서울특별시';
    if (regionCode === '26') return '부산광역시';
    return '선택한 시도';
  }

  if (depth === 'COUNTY') {
    if (regionCode === '11680') return '서울특별시 강남구';
    if (regionCode === '11740') return '서울특별시 강동구';
    return '선택한 지역';
  }

  if (depth === 'DISTRICT') {
    if (regionCode === '11680-gap') return '서울 강남갑';
    if (regionCode === '11740-gap') return '서울 강동갑';
    return '선택한 선거구';
  }

  return '선택한 지역';
};

const buildMapRegions = (depth: ElectionRegionType, regionCode: ElectionRegionCode): ElectionMapResponse['regions'] => {
  if (depth === 'NATIONAL') {
    return [
      { region_code: '11', region_name: '서울특별시', value: '54.2' },
      { region_code: '26', region_name: '부산광역시', value: '48.1' },
      { region_code: '27', region_name: '대구광역시', value: '51.9' },
    ];
  }

  if (depth === 'PROVINCE') {
    return [
      { region_code: '11680', region_name: '강남구', value: '61.2' },
      { region_code: '11740', region_name: '강동구', value: '54.8' },
      { region_code: '11440', region_name: '마포구', value: '49.7' },
    ];
  }

  if (depth === 'COUNTY') {
    return [
      {
        region_code: regionCode === '11740' ? '11740-gap' : '11680-gap',
        region_name: regionCode === '11740' ? '강동갑' : '강남갑',
        value: '52.4',
      },
      {
        region_code: regionCode === '11740' ? '11740-eul' : '11680-eul',
        region_name: regionCode === '11740' ? '강동을' : '강남을',
        value: '47.6',
      },
    ];
  }

  return [{ region_code: regionCode, region_name: resolveRegionName(regionCode, depth), value: '50.0' }];
};

const buildCandidates = (electionId: ElectionId, regionCode: ElectionRegionCode, officeType?: string | null) => {
  const regionalOffice = officeType ?? (electionId.startsWith('local-') ? '광역단체장' : null);

  if (electionId.startsWith('president-')) {
    return [
      {
        candidate_id: 'candidate-president-1',
        candidate_name: '홍길동',
        party_name: '미래개혁당',
        candidate_image_url: 'https://example.com/candidate-president-1.png',
      },
      {
        candidate_id: 'candidate-president-2',
        candidate_name: '김민주',
        party_name: '국민연합',
        candidate_image_url: 'https://example.com/candidate-president-2.png',
      },
    ];
  }

  return [
    {
      candidate_id: `${regionCode}-candidate-1`,
      candidate_name: regionalOffice === '교육감' ? '이교육' : '홍길동',
      party_name: regionalOffice === '교육감' ? '무소속' : '미래개혁당',
      candidate_image_url: 'https://example.com/candidate-1.png',
    },
    {
      candidate_id: `${regionCode}-candidate-2`,
      candidate_name: regionalOffice === '교육감' ? '박배움' : '김민주',
      party_name: regionalOffice === '교육감' ? '무소속' : '국민연합',
      candidate_image_url: 'https://example.com/candidate-2.png',
    },
  ];
};

export const getMockElectionSelector = (): BaseResponse<ElectionSelectorResponse> =>
  ok({
    default_election_id: 'local-2026',
    elections: ELECTIONS,
  });

export const getMockElectionOverview = (
  electionId: ElectionId,
  regionType: ElectionRegionType,
  regionCode: ElectionRegionCode,
): BaseResponse<ElectionOverviewResponse> =>
  ok({
    selected_election_id: electionId,
    ui_template: resolveUiTemplate(electionId),
    default_result_card: {
      source_election_id: resolveComparisonElectionId(electionId),
      region_type: regionType,
      region_code: regionCode,
      title: electionId,
    },
  });

export const getMockElectionMap = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  viewMode: ElectionViewMode,
): BaseResponse<ElectionMapResponse> =>
  ok({
    selected_election_id: electionId,
    depth,
    region_code: regionCode,
    view_mode: viewMode,
    regions: buildMapRegions(depth, regionCode),
  });

export const getMockElectionRegionPanel = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
): BaseResponse<ElectionRegionPanelResponse> =>
  ok({
    selected_election_id: electionId,
    depth,
    region_code: regionCode,
    office_type: officeType ?? null,
    region_name: resolveRegionName(regionCode, depth),
    result_card: {
      source_election_id: resolveComparisonElectionId(electionId),
      region_type: depth,
      region_code: regionCode,
      title: electionId,
    },
  });

export const getMockElectionCandidates = (
  electionId: ElectionId,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
): BaseResponse<ElectionCandidateListResponse> =>
  ok({
    selected_election_id: electionId,
    region_code: regionCode,
    office_type: officeType ?? null,
    candidates: buildCandidates(electionId, regionCode, officeType),
  });

export const getMockElectionCandidateDetail = (
  electionId: ElectionId,
  candidateId: ElectionCandidateId,
): BaseResponse<ElectionCandidateDetailResponse> => {
  const candidate =
    buildCandidates(electionId, '11680', null).find((item) => item.candidate_id === candidateId) ??
    buildCandidates(electionId, '11680', null)[0];

  return ok({
    selected_election_id: electionId,
    candidate_id: candidateId,
    candidate_name: candidate.candidate_name,
    party_name: candidate.party_name,
    candidate_image_url: candidate.candidate_image_url,
    manifesto_summary: '교통, 주거, 교육 개혁을 중심으로 한 공개 공약입니다.',
    manifesto_items: ['GTX 노선 확대', '청년 주거 지원', '지역 교육 인프라 강화'],
  });
};

export const postMockElectionRegionResolve = (
  body: ElectionRegionResolveRequest,
): BaseResponse<ElectionRegionResolveResponse> => {
  if (body.permission_status === 'denied' || body.permission_status === 'idle') {
    return ok({
      election_id: body.election_id,
      state: 'manual-required',
      confirmation_required: false,
      suggested_region_type: null,
      suggested_region_code: null,
      suggested_region_name: null,
      manual_correction_available: true,
      deny_available: false,
    });
  }

  return ok({
    election_id: body.election_id,
    state: 'gps-suggested',
    confirmation_required: true,
    suggested_region_type: body.election_id.startsWith('assembly-') ? 'DISTRICT' : 'COUNTY',
    suggested_region_code: body.election_id.startsWith('assembly-') ? '11680-gap' : '11680',
    suggested_region_name: body.election_id.startsWith('assembly-') ? '서울 강남갑' : '서울특별시 강남구',
    manual_correction_available: true,
    deny_available: true,
  });
};

export const postMockElectionRegionConfirm = (
  body: ElectionRegionResolveRequest,
): BaseResponse<ElectionRegionResolveResponse> =>
  ok({
    election_id: body.election_id,
    state: 'confirmed',
    confirmation_required: false,
    suggested_region_type: body.region_type ?? (body.election_id.startsWith('assembly-') ? 'DISTRICT' : 'COUNTY'),
    suggested_region_code: body.region_code ?? (body.election_id.startsWith('assembly-') ? '11680-gap' : '11680'),
    suggested_region_name:
      body.region_name ?? (body.election_id.startsWith('assembly-') ? '서울 강남갑' : '서울특별시 강남구'),
    manual_correction_available: true,
    deny_available: false,
  });
