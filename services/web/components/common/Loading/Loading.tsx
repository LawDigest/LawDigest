import { Logo } from '@/components/Layout';
import { Spinner } from '@nextui-org/spinner';

export default function Loading() {
  return (
    <section className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[90%] mx-auto h-full flex flex-col justify-center items-center gap-20">
      <Logo width={222} height={37} />
      <Spinner />
      <p>로딩 중입니다.</p>
    </section>
  );
}
