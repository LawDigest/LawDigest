import { Metadata } from 'next';
import { HydrationBoundary, dehydrate } from '@tanstack/react-query';
import { SubHeader } from '@/components';
import getQueryClient from '@/lib/getQueryClient';
import { getMetadata } from '@/utils';
import { BillContainer } from './components';
import { useGetBillDetail, usePatchViewCount } from './apis';

export const generateMetadata = async ({ params: { id } }: { params: { id: string } }): Promise<Metadata> => {
  const queryClient = getQueryClient();
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { data } = await useGetBillDetail(id, queryClient);

  return getMetadata({
    title: data.bill_info_dto.brief_summary,
    description: `${data.bill_info_dto.propose_date} 발의, 현재 ${data.bill_info_dto.bill_stage} 단계, '${data.bill_info_dto.bill_name}' 관련 발의안`,
    asPath: `/bill/${id}`,
  });
};

export default async function BillDetail({ params: { id } }: { params: { id: string } }) {
  const queryClient = getQueryClient();
  const viewCount = await usePatchViewCount(id).then((res) => res.data.view_count);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <section className="flex flex-col">
        <SubHeader title="의안 자세히 보기" />
        <BillContainer id={id} viewCount={viewCount} />
      </section>
    </HydrationBoundary>
  );
}
