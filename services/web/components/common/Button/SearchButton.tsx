import { IconSearch } from '@/public/svgs';
import Link from 'next/link';

export default function SearchButton({ onClick }: { onClick: () => void }) {
  return (
    <Link href="#" onClick={onClick}>
      <IconSearch />
    </Link>
  );
}
