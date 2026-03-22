import { Layout } from '@/components';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '타임라인 페이지',
  description: '법안들의 타임라인을 날짜별로 자세히 확인할 수 있는 페이지',
};

export default function TimelineLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav logo notification>
      {children}
    </Layout>
  );
}
