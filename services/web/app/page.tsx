import getQueryClient from '@/lib/getQueryClient';
import { cookies } from 'next/headers';
import { Feed, Layout } from '@/components';
import { getBillByStage } from '@/components/Feed/Feed/apis';
import { ACCESS_TOKEN } from '@/constants';
import { NotificationTopThree } from './notification/components';

export default async function Home() {
  const queryClient = getQueryClient();
  const accessToken = cookies().get(ACCESS_TOKEN)?.value;

  await queryClient.prefetchInfiniteQuery({
    queryKey: ['/bill/mainfeed'],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillByStage(pageParam, ''),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
    pages: 3,
  });

  return (
    <Layout nav logo notification>
      <section className="lg:w-[880px] mx-auto ">
        {accessToken ? <NotificationTopThree /> : null}
        <Feed />
      </section>
    </Layout>
  );
}
