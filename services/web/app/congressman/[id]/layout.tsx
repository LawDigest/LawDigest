import { Layout } from '@/components';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '의원 페이지',
  description: '의원을 자세히 확인할 수 있는 페이지',
};

export default function CongressmanLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav goBack search title="의원 프로필">
      {children}
    </Layout>
  );
}
