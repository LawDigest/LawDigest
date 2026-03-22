import { FollowingCongressmanResponse } from '@/types';
import CongressmanItem from './CongressmanItem';

export default function CongressmanList({ congressmanList }: { congressmanList: FollowingCongressmanResponse }) {
  return (
    <ul className="flex w-full gap-3 lg:flex-col lg:gap-2 xl:gap-4">
      {congressmanList.map((congressman) => (
        <CongressmanItem {...congressman} key={congressman.congressman_id} />
      ))}
    </ul>
  );
}
