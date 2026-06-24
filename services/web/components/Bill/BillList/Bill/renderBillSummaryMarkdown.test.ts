import { describe, expect, it } from 'vitest';
import {
  getFeedSummaryMarkdown,
  getPartyAccentColor,
  getSummaryVisibilityClassNames,
  renderBillSummaryMarkdown,
} from './renderBillSummaryMarkdown';

describe('renderBillSummaryMarkdown', () => {
  it('마크다운 단락명을 제목 태그로 렌더링한다', () => {
    const html = renderBillSummaryMarkdown('## 쉬운 요약\n- **핵심** 설명\n### 1) 변화\n<mark>중요</mark>');

    expect(html).toContain(
      '<h2 class="lawdigest-summary-heading lawdigest-summary-section-heading mt-6 mb-3 text-lg font-bold">',
    );
    expect(html).toContain('쉬운 요약');
    expect(html).toContain('<ul class="lawdigest-summary-list">');
    expect(html).toContain('<li><strong>핵심</strong> 설명</li>');
    expect(html).toContain('<h3 class="lawdigest-summary-subheading mt-4 mb-1.5 text-base font-semibold">');
    expect(html).toContain('1) 변화');
    expect(html).toContain('<strong>핵심</strong>');
    expect(html).toContain('<mark class="lawdigest-summary-mark">중요</mark>');
  });

  it('허용하지 않은 HTML은 이스케이프한다', () => {
    const html = renderBillSummaryMarkdown('## 제목\n<script>alert(1)</script>');

    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
  });

  it('법령용어 툴팁 표기를 점선 밑줄 span으로 렌더링한다', () => {
    const html = renderBillSummaryMarkdown('- {{청문:행정청이 처분 전에 당사자의 의견을 직접 듣는 절차}}을 거쳐요.');

    expect(html).toContain('class="lawdigest-term-tooltip"');
    expect(html).toContain('tabindex="0"');
    expect(html).toContain('aria-label="청문: 행정청이 처분 전에 당사자의 의견을 직접 듣는 절차"');
    expect(html).toContain('data-definition="행정청이 처분 전에 당사자의 의견을 직접 듣는 절차"');
    expect(html).toContain('>청문</span>을 거쳐요.');
  });

  it('법령용어 툴팁 정의 안의 HTML은 이스케이프한다', () => {
    const html = renderBillSummaryMarkdown('{{청문:<script>alert(1)</script>}}');

    expect(html).not.toContain('<script>');
    expect(html).toContain('&amp;lt;script&amp;gt;alert(1)&amp;lt;/script&amp;gt;');
  });

  it('하위 제목 아래 본문과 목록에 들여쓰기 클래스를 붙인다', () => {
    const html = renderBillSummaryMarkdown('## 무엇이 달라지나\n### 1) 변상금 원칙 유지\n본문 설명\n- 세부 설명');

    expect(html).toContain('<h3 class="lawdigest-summary-subheading mt-4 mb-1.5 text-base font-semibold">');
    expect(html).toContain('<p class="lawdigest-summary-subsection-body">본문 설명</p>');
    expect(html).toContain('<ul class="lawdigest-summary-list lawdigest-summary-subsection-body">');
  });
});

describe('getFeedSummaryMarkdown', () => {
  it('피드에서는 쉬운 요약과 주요 내용 섹션만 남긴다', () => {
    const markdown = [
      '<mark>아직 통과하지 않았어요.</mark>',
      '',
      '## 쉬운 요약',
      '- 첫 요약',
      '',
      '## 주요 내용',
      '- **핵심** 내용',
      '',
      '## 왜 나왔나',
      '상세 배경',
      '',
      '## 무엇이 달라지나',
      '### 1) 세부 변화',
      '상세 변화',
    ].join('\n');

    const feedMarkdown = getFeedSummaryMarkdown(markdown);

    expect(feedMarkdown).toContain('## 쉬운 요약');
    expect(feedMarkdown).toContain('## 주요 내용');
    expect(feedMarkdown).not.toContain('아직 통과하지 않았어요');
    expect(feedMarkdown).not.toContain('## 왜 나왔나');
    expect(feedMarkdown).not.toContain('## 무엇이 달라지나');
    expect(feedMarkdown).not.toContain('### 1) 세부 변화');
  });

  it('대상 섹션이 없으면 원문을 유지한다', () => {
    const markdown = '기존 한 줄 요약';

    expect(getFeedSummaryMarkdown(markdown)).toBe(markdown);
  });
});

describe('getSummaryVisibilityClassNames', () => {
  it('피드 접힘 상태에서는 본문을 줄이고 더 보기 버튼을 보인다', () => {
    expect(getSummaryVisibilityClassNames({ detail: false, expanded: false })).toEqual({
      moreButtonClassName: 'text-gray-2 dark:text-gray-3',
      summaryClassName: 'line-clamp-[8]',
    });
  });

  it('피드 펼침 상태와 상세 화면에서는 더 보기 버튼을 숨긴다', () => {
    expect(getSummaryVisibilityClassNames({ detail: false, expanded: true })).toEqual({
      moreButtonClassName: 'hidden',
      summaryClassName: '',
    });
    expect(getSummaryVisibilityClassNames({ detail: true, expanded: false })).toEqual({
      moreButtonClassName: 'hidden',
      summaryClassName: '',
    });
  });
});

describe('getPartyAccentColor', () => {
  it('대표발의자 정당명을 요약 리스트 포인트 컬러로 변환한다', () => {
    expect(getPartyAccentColor('더불어민주당')).toBe('#152484');
    expect(getPartyAccentColor('국민의힘')).toBe('#e61e2b');
    expect(getPartyAccentColor('개혁신당')).toBe('#ff7210');
  });

  it('알 수 없는 정당명은 기본 포인트 컬러를 쓴다', () => {
    expect(getPartyAccentColor('알 수 없는 정당')).toBe('#e63946');
  });
});
