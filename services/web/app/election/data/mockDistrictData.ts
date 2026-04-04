// services/web/app/election/data/mockDistrictData.ts

export interface MockCandidate {
  id: string;
  name: string;
  partyName: string;
  partyColor: string;
  slogan: string;
  supportPct: number;
  career: string[];
  pledges: string[];
  imageUrl?: string;
}

export interface MockDistrict {
  regionCode: string;
  regionName: string;
  officeName: string;
  candidates: MockCandidate[];
}

export const MOCK_DISTRICT: MockDistrict = {
  regionCode: '11',
  regionName: '서울특별시',
  officeName: '서울특별시장',
  candidates: [
    {
      id: 'c1',
      name: '홍길동',
      partyName: '더불어민주당',
      partyColor: '#152484',
      slogan: '함께 만드는 서울의 미래',
      supportPct: 47.3,
      career: ['전 서울시 경제부시장', '전 국회의원 (19대)', '서울대학교 경제학과 졸업'],
      pledges: ['청년 공공임대주택 5만 호 공급', '대중교통 요금 동결', '소상공인 임대료 안정 지원'],
    },
    {
      id: 'c2',
      name: '이순신',
      partyName: '국민의힘',
      partyColor: '#C9151E',
      slogan: '강한 서울, 행복한 시민',
      supportPct: 43.1,
      career: ['전 행정안전부 장관', '전 서울시 행정1부시장', '연세대학교 행정학과 졸업'],
      pledges: ['서울 경제 활성화 3대 프로젝트', '안전한 서울 만들기', '서울형 돌봄 서비스 확대'],
    },
    {
      id: 'c3',
      name: '강감찬',
      partyName: '조국혁신당',
      partyColor: '#6A3FA0',
      slogan: '새로운 서울의 시작',
      supportPct: 7.2,
      career: ['전 시민단체 대표', '전 서울시의원 (3선)', '고려대학교 법학과 졸업'],
      pledges: ['투명한 서울시정 실현', '기후위기 대응 그린 뉴딜', '교육 격차 해소 프로그램'],
    },
  ],
};
