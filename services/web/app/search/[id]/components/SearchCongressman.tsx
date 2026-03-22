import Link from 'next/link';
import { Avatar } from '@nextui-org/avatar';
import { SearchCongressmanPartyProps } from '@/types';
import { EnterButton } from '@/components';

export default function SearchCongressman({
  congressman_id,
  congressman_image_url,
  congressman_name,
  party_name,
}: SearchCongressmanPartyProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex gap-6">
        <Avatar
          src={process.env.NEXT_PUBLIC_IMAGE_URL + congressman_image_url}
          size="lg"
          className={`border ${party_name}`}
        />
        <div className="flex flex-col ">
          <p className="text-lg font-semibold">{congressman_name}</p>
          <p className="text-sm font-medium text-gray-2 dark:text-gray-3">{party_name}</p>
        </div>
      </div>
      <Link href={`/congressman/${congressman_id}`}>
        <EnterButton />
      </Link>
    </div>
  );
}
