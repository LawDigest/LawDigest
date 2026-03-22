import { GoBackButton } from '@/components/common';

export default function SubHeader({ title }: { title: string }) {
  return (
    <section className="relative items-center hidden pb-3 mt-5 font-medium lg:flex border-b-1 dark:border-dark-l">
      <div className="absolute">
        <GoBackButton />
      </div>
      <div className="mx-auto">{title}</div>
    </section>
  );
}
