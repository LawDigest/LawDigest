import { Layout } from '@/components';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '정당 페이지',
  description: '정당을 자세히 확인할 수 있는 페이지',
};

export default function PartyLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav goBack search title="정당 프로필">
      {children}
    </Layout>
  );
}
