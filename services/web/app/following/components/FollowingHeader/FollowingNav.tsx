import { Card, CardHeader, CardBody } from '@nextui-org/react';
import { useQueryClient } from '@tanstack/react-query';
import CongressmanList from './CongressmanList';
import { useGetFollowingCongressman } from '../../apis';

export default async function FollowingNav() {
  const queryClient = useQueryClient();
  const { data: congressmanList } = await useGetFollowingCongressman(queryClient);

  return (
    <Card
      classNames={{
        base: ['shadow-[0_4px_6px_-2px_rgba(0,_0,_0,_0.1)] md:shadow-[0_0_6px_rgba(0,_0,_0,_0.1)]'],
      }}
      className=" w-full pl-5 mx-auto lg:mx-0 bg-transparent md:mt-10 md:mb-6 md:h-[200px] md:w-[708px] md:pt-3 md:rounded-xl lg:my-0 lg:rounded-none lg:h-full lg:text-black lg:dark:text-white lg:bg-transparent lg:pt-8 lg:shadow-none md:dark:bg-primary-3 lg:dark:bg-transparent lg:w-[120px] xl:w-[312px] md:border border-b lg:border-none dark:border-dark-l">
      <CardHeader className="pt-2 pb-0 pl-0 lg:hidden">
        <h2 className="text-2xl font-bold md:text-3xl lg:mx-auto">팔로잉</h2>
      </CardHeader>
      <CardBody className="flex flex-row items-center gap-4 pl-0 overflow-x-scroll lg:flex-col scrollbar-hide lg:scrollbar-default">
        <div className="flex flex-col items-center shrink-0 xl:flex-row xl:justify-start xl:w-full xl:gap-2">
          <p className="text-xs font-medium text-gray-2 md:text-sm xl:text-[26px] xl:text-black xl:font-semibold xl:dark:text-white">
            팔로우한 의원
          </p>
          <p className="hidden xl:block text-[26px] font-semibold lg:dark:text-gray-2"> · </p>
          <p className="text-2xl font-semibold xl:text-[26px] xl:text-gray-2 xl:dark:text-gray-3">
            {congressmanList.length}
          </p>
        </div>

        <CongressmanList congressmanList={congressmanList} />
      </CardBody>
    </Card>
  );
}
