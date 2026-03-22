import Link from 'next/link';
import { Avatar } from '@nextui-org/avatar';
import { FollowingCongressmanType } from '@/types';

export default function CongressmanItem({
  congressman_id,
  congressman_name,
  congressman_image_url,
  party_name,
}: FollowingCongressmanType) {
  return (
    <Link href={`/congressman/${congressman_id}`} className="flex flex-col items-center gap-1">
      <Avatar
        size="lg"
        src={process.env.NEXT_PUBLIC_IMAGE_URL + congressman_image_url}
        className={`border-1.5 ${party_name}`}
      />
      <div className="flex flex-col items-center">
        <p className="text-xs font-medium text-gray-2 dark:text-[#999999]">{party_name}</p>
        <p className="text-sm font-medium">{congressman_name}</p>
      </div>
    </Link>
  );
}
