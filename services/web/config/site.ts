import { IconFollowing, IconHome, IconMyPage, IconTimeline } from '@/public/svgs';

export type SiteConfig = typeof siteConfig;

export const siteConfig = {
  title: '모두의입법',
  description: '자연어 처리 기술을 이용한 법률 개정안 요약 플랫폼',
  url: 'https://www.lawdigest.net/',
  ogImage: '/images/opengraph-image.png',
  links: {
    github: 'https://github.com/LawDigest',
  },
  type: 'website',
  keywords: ['AI', 'ChatGPT', 'LLM', '법률개정안', '법안', '입법', '국회', '국회의원', '의원', '법률', '정치', '정당'],
  verification: {
    google: 'dZCjlUZB_k_xyVehj8-rN4-U2CpoKlcpvA66JxQbFz0',
    naver: '1ec7cb320c5300b98dc49b84b0a03004f571e7b1',
  },
  navItems: [
    {
      label: '피드',
      href: '/',
      IconComponent: IconHome,
    },
    {
      label: '타임라인',
      href: '/timeline',
      IconComponent: IconTimeline,
    },
    {
      label: '팔로잉',
      href: '/following',
      IconComponent: IconFollowing,
    },
    {
      label: '마이페이지',
      href: '/mypage',
      IconComponent: IconMyPage,
    },
  ],
  stageTabs: [
    { label: '접수', value: 'reception' },
    { label: '위원회 심사', value: 'committeeJudge' },
    { label: '본회의 심의', value: 'review' },
    { label: '공포', value: 'promulgation' },
  ],
  feedTabs: [
    { label: '시간순', value: 'sortedByLatest' },
    { label: 'HOT', value: 'sortedByPopularity' },
  ],
  billTabs: [
    { label: '대표발의한 법안', value: 'representProposer' },
    { label: '공동발의한 법안', value: 'publicProposer' },
  ],
} as const;
