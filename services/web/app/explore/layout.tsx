import { Layout } from '@/components';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '탐색 페이지',
  description: '생활 분야별로 법안을 탐색합니다.',
};

export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav logo notification>
      {children}
    </Layout>
  );
}
