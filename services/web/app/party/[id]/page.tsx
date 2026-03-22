import { dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { SubHeader } from '@/components';
import getQueryClient from '@/lib/getQueryClient';
import { getMetadata } from '@/utils';
import { Metadata } from 'next';
import { PARTY_POSITION, PARTY_NAME_KO } from '@/constants/party';
import PartyContainer from './components';
import { getPartyDetail } from './apis';

export const generateMetadata = async ({ params: { id } }: { params: { id: string } }): Promise<Metadata> => {
  const queryClient = getQueryClient();
  const { data } = await queryClient.fetchQuery({
    queryKey: ['/party/detail', id],
    queryFn: () => getPartyDetail(Number(id)),
  });

  return getMetadata({
    title: `${data.party_name}`,
    description: `${data.party_name} 상세 페이지, ${PARTY_POSITION[data.party_name as keyof typeof PARTY_NAME_KO]}, 지역구 ${data.district_congressman_count} 석, 비례대표 ${data.proportional_congressman_count} 석`,
    asPath: `/party/${id}`,
  });
};

export default async function Party({ params: { id } }: { params: { id: string } }) {
  const queryClient = getQueryClient();

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <section className="flex flex-col gap-10">
        <SubHeader title="정당 프로필" />
        <PartyContainer id={id} />
      </section>
    </HydrationBoundary>
  );
}
