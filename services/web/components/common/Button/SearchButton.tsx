import { IconSearch } from '@/public/svgs';
import Link from 'next/link';

export default function SearchButton({ onClick }: { onClick: () => void }) {
  return (
    // eslint-disable-next-line jsx-a11y/anchor-is-valid
    <Link href="#" onClick={onClick}>
      <IconSearch />
    </Link>
  );
}
