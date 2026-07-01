/**
 * 분야(category) taxonomy 미러 — 백엔드 category 코드와 1:1.
 * 진실원: output/tab-prototypes/FIELD_TAXONOMY.md (v4), services/ai/.../category_taxonomy.py
 */
export interface CategoryMeta {
  code: string;
  label: string;
  icon: string; // Material Symbols Outlined 아이콘명
  color: string; // 분야 고유 색 (hex) — 아이콘/도넛/차트에 공통 사용
}

export const CATEGORIES: CategoryMeta[] = [
  { code: 'economy', label: '경제·세금', icon: 'payments', color: '#0088FF' },
  { code: 'housing', label: '부동산·주거', icon: 'apartment', color: '#F59E0B' },
  { code: 'transport', label: '교통·물류', icon: 'commute', color: '#0EA5E9' },
  { code: 'labor', label: '일자리·노동', icon: 'work', color: '#16A34A' },
  { code: 'environment', label: '환경·기후·에너지', icon: 'eco', color: '#059669' },
  { code: 'welfare', label: '복지·연금', icon: 'volunteer_activism', color: '#14B8A6' },
  { code: 'health', label: '보건·의료', icon: 'health_and_safety', color: '#DB2777' },
  { code: 'education', label: '교육', icon: 'school', color: '#7C3AED' },
  { code: 'family', label: '가족·청소년', icon: 'family_restroom', color: '#F97316' },
  { code: 'industry', label: '산업·중소기업', icon: 'factory', color: '#2563EB' },
  { code: 'tech', label: '과학·디지털·AI', icon: 'smart_toy', color: '#0891B2' },
  { code: 'agriculture', label: '농림·축산·수산', icon: 'agriculture', color: '#65A30D' },
  { code: 'culture', label: '문화·예술·체육', icon: 'palette', color: '#C026D3' },
  { code: 'safety', label: '안전·재난·치안', icon: 'emergency', color: '#DC2626' },
  { code: 'politics', label: '정치·행정', icon: 'how_to_vote', color: '#4F46E5' },
  { code: 'diplomacy', label: '외교·국방', icon: 'public', color: '#475569' },
  { code: 'justice', label: '사법·범죄', icon: 'gavel', color: '#0D9488' },
];

export const UNKNOWN_CATEGORY: CategoryMeta = {
  code: 'unknown',
  label: '미분류',
  icon: 'help',
  color: '#999999',
};

const CATEGORY_MAP: Record<string, CategoryMeta> = Object.fromEntries(
  [...CATEGORIES, UNKNOWN_CATEGORY].map((c) => [c.code, c]),
);

export const getCategoryMeta = (code?: string | null): CategoryMeta => {
  if (!code) return UNKNOWN_CATEGORY;
  return CATEGORY_MAP[code] ?? { code, label: code, icon: 'category', color: '#0088FF' };
};
