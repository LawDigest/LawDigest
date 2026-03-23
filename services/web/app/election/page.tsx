import { Layout } from '@/components';

export default function Election() {
  return (
    <Layout nav logo>
      <section className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <span className="text-5xl">🗳️</span>
        <h1 className="text-2xl font-bold">선거</h1>
        <p className="text-sm text-gray-500">선거 정보 서비스를 준비 중이에요.</p>
      </section>
    </Layout>
  );
}
