import { Metadata } from 'next';
import { Layout } from '@/components';

export const metadata: Metadata = {
  title: '회원가입 페이지',
  description: '회원가입 페이지',
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout nav theme goBack>
      {children}
    </Layout>
  );
}
