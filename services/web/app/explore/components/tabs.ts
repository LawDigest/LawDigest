export type ExploreTab = 'field' | 'assembly' | 'stats';

export interface ExploreTabMeta {
  key: ExploreTab;
  label: string;
  icon: string; // Material Symbols Outlined 아이콘명
}

export const EXPLORE_TABS: ExploreTabMeta[] = [
  { key: 'field', label: '분야', icon: 'tag' },
  { key: 'assembly', label: '국회', icon: 'account_balance' },
  { key: 'stats', label: '통계', icon: 'monitoring' },
];
