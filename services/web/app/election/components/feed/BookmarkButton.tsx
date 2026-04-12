'use client';

import { useAddElectionBookmark, useRemoveElectionBookmark } from '../../apis/queries';

interface BookmarkButtonProps {
  feedType: string;
  feedItemId: string;
  bookmarked: boolean;
}

export default function BookmarkButton({ feedType, feedItemId, bookmarked }: BookmarkButtonProps) {
  const addMutation = useAddElectionBookmark();
  const removeMutation = useRemoveElectionBookmark();
  const isPending = addMutation.isPending || removeMutation.isPending;

  function handleClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (bookmarked) {
      removeMutation.mutate({ feedType, feedItemId });
    } else {
      addMutation.mutate({ feedType, feedItemId });
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isPending}
      aria-label={bookmarked ? '북마크 해제' : '북마크 추가'}
      className="p-1 rounded-full text-gray-400 hover:text-indigo-500 transition-colors disabled:opacity-40">
      <span
        className="material-symbols-outlined text-[18px]"
        style={{ fontVariationSettings: bookmarked ? "'FILL' 1" : "'FILL' 0" }}>
        bookmark
      </span>
    </button>
  );
}
