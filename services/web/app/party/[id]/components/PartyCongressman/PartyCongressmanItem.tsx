import Link from 'next/link';
import { PartyCongressmanProps } from '@/types';
import { Avatar } from '@nextui-org/avatar';

export default function PartyCongressmanItem({
  congressman_id,
  congressman_name,
  congressman_image_url,
}: PartyCongressmanProps) {
  return (
    <Link href={`/congressman/${congressman_id}`} className="flex flex-col items-center gap-2">
      <Avatar
        size="lg"
        className="border-2 dark:border-dark-l"
        src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${congressman_image_url}`}
      />
      <div className="flex flex-col items-center">
        <p className="text-sm text-gray-3 dark:text-gray-2">의원</p>
        <p className="font-medium">{congressman_name}</p>
      </div>
    </Link>
  );
}
