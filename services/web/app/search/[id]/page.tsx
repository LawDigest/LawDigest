import SearchResultClient from './SearchResultClient';

type SearchResultPageProps = {
  params: Promise<{ id: string }>;
};

export default async function SearchResultPage({ params }: SearchResultPageProps) {
  const { id } = await params;

  return <SearchResultClient id={id} />;
}
