import Image from 'next/image';
import Link from 'next/link';
import { useTheme } from 'next-themes';

interface VoteResultBoardProps {
  party_vote_list: {
    party_info: {
      party_id: number;
      party_name: string;
      party_image_url: string;
    };
    party_approval_count: number;
  }[];
}

export default function VoteResultBoard({ party_vote_list }: VoteResultBoardProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="grid w-full grid-cols-2 gap-y-4 gap-x-4">
      {party_vote_list
        .sort((a, b) => b.party_approval_count - a.party_approval_count)
        .map(({ party_info: { party_id, party_name, party_image_url }, party_approval_count }) => (
          <div key={party_id} className="flex items-center justify-between w-[130px]">
            <Link
              href={`/party/${party_id}`}
              className={`flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 ${party_name}`}>
              {party_name === '무소속' ? (
                <div className="text-xs font-medium text-black">무</div>
              ) : (
                <Image
                  src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_image_url.replace('wide', 'dark') : party_image_url}`}
                  width={20}
                  height={20}
                  alt={`${party_name} 로고 이미지`}
                />
              )}
            </Link>
            <Link href={`/party/${party_id}`}>
              <p className="text-xs font-semibold text-gray-2 dark:text-gray-1">{party_name}</p>
            </Link>
            <p className="text-xs font-medium w-[32px]">
              {party_approval_count}
              <span className="font-light">표</span>
            </p>
          </div>
        ))}
    </div>
  );
}
