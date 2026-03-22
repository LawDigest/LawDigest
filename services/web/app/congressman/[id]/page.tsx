import { dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { SubHeader } from '@/components';
import { getMetadata } from '@/utils';
import { Metadata } from 'next';
import getQueryClient from '@/lib/getQueryClient';
import { CongressmanContainer } from './components';
import { getCongressmanDetail } from './apis';

export const generateMetadata = async ({ params: { id } }: { params: { id: string } }): Promise<Metadata> => {
  const queryClient = getQueryClient();
  const { data } = await queryClient.fetchQuery({
    queryKey: ['/congressman/detail', id],
    queryFn: () => getCongressmanDetail(id),
  });

  return getMetadata({
    title: `${data.congressman_name} 의원`,
    description: `${data.party_name} ${data.congressman_name} 의원의 상세 프로필 페이지, ${data.district} ${data.elected}, ${data.commits}`,
    asPath: `/congressman/${id}`,
  });
};

export default async function Congressman({ params: { id } }: { params: { id: string } }) {
  const queryClient = getQueryClient();

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <section className="flex flex-col gap-10">
        <SubHeader title="의원 프로필" />
        <CongressmanContainer id={id} />
      </section>
    </HydrationBoundary>
  );
}
