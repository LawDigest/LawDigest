const escapeHtml = (value: string) => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const escapeHtmlAttribute = (value: string) => escapeHtml(value).replace(/"/g, '&quot;');

const renderInlineMarkdown = (value: string) => {
  const withAllowedMark = escapeHtml(value).replace(
    /&lt;mark&gt;(.+?)&lt;\/mark&gt;/g,
    '<mark class="lawdigest-summary-mark">$1</mark>',
  );

  return withAllowedMark
    .replace(/\{\{([^:{}\n]+):([^{}\n]+)\}\}/g, (_match, term: string, definition: string) => {
      const label = term.trim();
      const tooltip = definition.trim();
      return [
        `<span class="lawdigest-term-tooltip" tabindex="0"`,
        ` aria-label="${escapeHtmlAttribute(`${label}: ${tooltip}`)}"`,
        ` data-definition="${escapeHtmlAttribute(tooltip)}">`,
        label,
        '</span>',
      ].join('');
    })
    .split('**')
    .map((text, index) => (index % 2 === 0 ? text : `<strong>${text}</strong>`))
    .join('');
};

const FEED_SECTION_HEADINGS = new Set(['쉬운 요약', '주요 내용']);

const PARTY_ACCENT_COLORS: Record<string, string> = {
  개혁신당: '#ff7210',
  국민의힘: '#e61e2b',
  기본소득당: '#00d2c3',
  녹색정의당: '#007c36',
  다수: '#2e2e2e',
  더불어민주당: '#152484',
  무소속: '#797c85',
  사회민주당: '#f58400',
  새로운미래: '#45babd',
  조국혁신당: '#0073cf',
  진보당: '#d6001c',
};

export const getPartyAccentColor = (partyName: string) => PARTY_ACCENT_COLORS[partyName] ?? '#e63946';

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

const closeList = (html: string[], inList: boolean) => (inList ? [...html, '</ul>'] : html);

export const renderBillSummaryMarkdown = (markdown: string) => {
  const result = markdown.split('\n').reduce(
    (state, line) => {
      if (line.startsWith('- ')) {
        const shouldOpenList = !state.inList;
        const listClassName = state.isSubsectionBody
          ? 'lawdigest-summary-list lawdigest-summary-subsection-body'
          : 'lawdigest-summary-list';

        return {
          html: [
            ...state.html,
            ...(shouldOpenList ? [`<ul class="${listClassName}">`] : []),
            `<li>${renderInlineMarkdown(line.slice(2))}</li>`,
          ],
          inList: true,
          isSubsectionBody: state.isSubsectionBody,
        };
      }

      const html = closeList(state.html, state.inList);

      if (line.startsWith('### ')) {
        return {
          html: [
            ...html,
            `<h3 class="lawdigest-summary-subheading mt-4 mb-1.5 text-sm font-semibold">${renderInlineMarkdown(line.slice(4))}</h3>`,
          ],
          inList: false,
          isSubsectionBody: true,
        };
      }

      if (line.startsWith('## ')) {
        return {
          html: [
            ...html,
            `<h2 class="lawdigest-summary-heading lawdigest-summary-section-heading mt-6 mb-3 text-lg font-bold">${renderInlineMarkdown(line.slice(3))}</h2>`,
          ],
          inList: false,
          isSubsectionBody: false,
        };
      }

      if (line.trim() === '') {
        return { html, inList: false, isSubsectionBody: state.isSubsectionBody };
      }

      const className = state.isSubsectionBody ? ' class="lawdigest-summary-subsection-body"' : '';

      return {
        html: [...html, `<p${className}>${renderInlineMarkdown(line)}</p>`],
        inList: false,
        isSubsectionBody: state.isSubsectionBody,
      };
    },
    { html: [] as string[], inList: false, isSubsectionBody: false },
  );

  return closeList(result.html, result.inList).join('');
};
