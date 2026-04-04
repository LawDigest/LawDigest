// services/web/app/election/data/mockPartyPollData.ts

export interface PartyPollResult {
  partyName: string;
  color: string;
  nationalPct: number; // 전국 지지율
  regionalPct: Record<string, number>; // 시/도별 지지율
}

export const MOCK_PARTY_POLL_DATA: PartyPollResult[] = [
  {
    partyName: '더불어민주당',
    color: '#152484',
    nationalPct: 47.5,
    regionalPct: {
      서울특별시: 47.3,
      경기도: 50.2,
      인천광역시: 44.8,
      광주광역시: 74.8,
      전북특별자치도: 71.5,
      전라남도: 72.3,
      부산광역시: 39.4,
      대구광역시: 35.2,
      경상남도: 36.7,
      경상북도: 29.8,
      대전광역시: 46.1,
      세종특별자치시: 44.2,
      충청북도: 42.5,
      충청남도: 41.3,
      울산광역시: 40.1,
      강원특별자치도: 41.2,
      제주특별자치도: 52.1,
    },
  },
  {
    partyName: '국민의힘',
    color: '#C9151E',
    nationalPct: 42.8,
    regionalPct: {
      서울특별시: 43.1,
      경기도: 40.5,
      인천광역시: 46.5,
      광주광역시: 16.3,
      전북특별자치도: 19.2,
      전라남도: 18.1,
      부산광역시: 52.8,
      대구광역시: 56.8,
      경상남도: 55.2,
      경상북도: 62.1,
      대전광역시: 44.8,
      세종특별자치시: 47.3,
      충청북도: 49.1,
      충청남도: 50.2,
      울산광역시: 51.3,
      강원특별자치도: 50.6,
      제주특별자치도: 39.4,
    },
  },
  {
    partyName: '조국혁신당',
    color: '#6A3FA0',
    nationalPct: 6.7,
    regionalPct: {
      서울특별시: 7.2,
      경기도: 6.8,
      인천광역시: 6.5,
      광주광역시: 5.8,
      전북특별자치도: 6.1,
      전라남도: 6.0,
      부산광역시: 5.9,
      대구광역시: 5.5,
      경상남도: 5.7,
      경상북도: 5.3,
      대전광역시: 6.3,
      세종특별자치시: 6.0,
      충청북도: 6.0,
      충청남도: 5.9,
      울산광역시: 5.8,
      강원특별자치도: 6.1,
      제주특별자치도: 6.5,
    },
  },
];
