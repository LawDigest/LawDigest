/**
 * 분야(category) taxonomy 미러 — 백엔드 category 코드와 1:1.
 * 진실원: output/tab-prototypes/FIELD_TAXONOMY.md (v4), services/ai/.../category_taxonomy.py
 */
export interface CategoryMeta {
  code: string;
  label: string;
  icon: string; // Material Symbols Outlined 아이콘명
}

export const CATEGORIES: CategoryMeta[] = [
  { code: 'economy', label: '경제·세금', icon: 'payments' },
  { code: 'housing', label: '부동산·주거', icon: 'apartment' },
  { code: 'transport', label: '교통·물류', icon: 'commute' },
  { code: 'labor', label: '일자리·노동', icon: 'work' },
  { code: 'environment', label: '환경·기후·에너지', icon: 'eco' },
  { code: 'welfare', label: '복지·연금', icon: 'volunteer_activism' },
  { code: 'health', label: '보건·의료', icon: 'health_and_safety' },
  { code: 'education', label: '교육', icon: 'school' },
  { code: 'family', label: '가족·청소년', icon: 'family_restroom' },
  { code: 'industry', label: '산업·중소기업', icon: 'factory' },
  { code: 'tech', label: '과학·디지털·AI', icon: 'smart_toy' },
  { code: 'agriculture', label: '농림·축산·수산', icon: 'agriculture' },
  { code: 'culture', label: '문화·예술·체육', icon: 'palette' },
  { code: 'safety', label: '안전·재난·치안', icon: 'emergency' },
  { code: 'politics', label: '정치·행정', icon: 'how_to_vote' },
  { code: 'diplomacy', label: '외교·국방', icon: 'public' },
  { code: 'justice', label: '사법·범죄', icon: 'gavel' },
];

export const UNKNOWN_CATEGORY: CategoryMeta = { code: 'unknown', label: '미분류', icon: 'help' };

const CATEGORY_MAP: Record<string, CategoryMeta> = Object.fromEntries(
  [...CATEGORIES, UNKNOWN_CATEGORY].map((c) => [c.code, c]),
);

export const getCategoryMeta = (code?: string | null): CategoryMeta => {
  if (!code) return UNKNOWN_CATEGORY;
  return CATEGORY_MAP[code] ?? { code, label: code, icon: 'category' };
};
