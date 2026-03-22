import { Layout } from '@/components';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '팔로잉 페이지',
  description: '내가 정보한 정보들을 자세히 확인할 수 있는 페이지',
};

export default function FollowingLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav logo notification>
      {children}
    </Layout>
  );
}
