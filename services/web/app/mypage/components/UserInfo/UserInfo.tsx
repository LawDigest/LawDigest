import { Avatar } from '@nextui-org/avatar';
import { QueryClient } from '@tanstack/react-query';
import Image from 'next/image';
import { useGetUserInfo } from '../../apis';
import LogoutButton from './LogoutButton';

export default async function UserInfo({ queryClient }: { queryClient: QueryClient }) {
  const { data: userInfo } = await useGetUserInfo(queryClient);
  const { user_name, user_image_url, user_email } = userInfo;

  return (
    <section className="flex items-center px-[30px] justify-between h-[200px] shadow-md rounded-b-xl md:rounded-xl bg-white pt-3 pb-7 md:py-6 dark:bg-primary-3 lg:bg-gray-0.5 lg:shadow-none md:h-[300px] md:w-[708px] md:mt-10 md:bg-gray-4 md:dark:bg-dark-pb md:text-white lg:text-black lg:dark:text-white lg:h-[260px] lg:w-[200px] lg:justify-center lg:relative">
      <div className="flex items-center w-full lg:flex-col lg:gap-5">
        <div className="relative">
          <Image
            src="/images/profileBorder.png"
            width={100}
            height={100}
            alt="프로필 사진 테두리"
            priority
            loader={({ src }) => `${src}`}
            className="absolute z-10"
          />
          <Avatar src={`${user_image_url}`} className="w-[100px] h-[100px] mr-4 lg:mr-0" />
        </div>

        <div className="flex flex-col w-full gap-3 lg:items-center">
          <div className="flex items-center justify-between">
            <p className="text-3xl font-semibold">{user_name}</p>
            <div className="lg:absolute lg:-bottom-[50px]">
              <LogoutButton />
            </div>
          </div>
          <p className="text-[#999999] text-xs dark:text-gray-2">{user_email}</p>
        </div>
      </div>
    </section>
  );
}
