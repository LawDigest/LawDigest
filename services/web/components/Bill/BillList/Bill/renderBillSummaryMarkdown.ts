const escapeHtml = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const renderInlineMarkdown = (value: string) => {
  const withAllowedMark = escapeHtml(value).replace(/&lt;mark&gt;(.+?)&lt;\/mark&gt;/g, '<mark>$1</mark>');

  return withAllowedMark
    .split('**')
    .map((text, index) => (index % 2 === 0 ? text : `<strong>${text}</strong>`))
    .join('');
};

const FEED_SECTION_HEADINGS = new Set(['쉬운 요약', '주요 내용']);

export const getFeedSummaryMarkdown = (markdown: string) => {
  const result = markdown.split('\n').reduce(
    (state, line) => {
      if (state.done) {
        return state;
      }

      const { feedLines, foundFeedSection, isFeedSection } = state;

      if (!line.startsWith('## ')) {
        return isFeedSection ? { ...state, feedLines: [...feedLines, line] } : state;
      }

      const heading = line.slice(3).trim();

      if (!FEED_SECTION_HEADINGS.has(heading)) {
        return foundFeedSection ? { ...state, done: true } : { ...state, isFeedSection: false };
      }

      return {
        done: state.done,
        feedLines: [...feedLines, line],
        foundFeedSection: true,
        isFeedSection: true,
      };
    },
    {
      done: false,
      feedLines: [] as string[],
      foundFeedSection: false,
      isFeedSection: false,
    },
  );

  return result.foundFeedSection ? result.feedLines.join('\n').trim() : markdown;
};

export const getSummaryVisibilityClassNames = ({ detail, expanded }: { detail: boolean; expanded: boolean }) => ({
  moreButtonClassName: detail || expanded ? 'hidden' : 'text-gray-2 dark:text-gray-3',
  summaryClassName: detail || expanded ? '' : 'line-clamp-[8]',
});

export const renderBillSummaryMarkdown = (markdown: string) =>
  markdown
    .split('\n')
    .map((line) => {
      if (line.startsWith('### ')) {
        return `<h3 class="mt-4 mb-2 text-base font-semibold">${renderInlineMarkdown(line.slice(4))}</h3>`;
      }

      if (line.startsWith('## ')) {
        return `<h2 class="mt-5 mb-2 text-lg font-semibold">${renderInlineMarkdown(line.slice(3))}</h2>`;
      }

      if (line.trim() === '') {
        return '';
      }

      return `<p>${renderInlineMarkdown(line)}</p>`;
    })
    .join('');
