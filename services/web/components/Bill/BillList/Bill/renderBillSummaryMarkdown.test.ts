import { describe, expect, it } from 'vitest';
import { renderBillSummaryMarkdown } from './renderBillSummaryMarkdown';

describe('renderBillSummaryMarkdown', () => {
  it('마크다운 단락명을 제목 태그로 렌더링한다', () => {
    const html = renderBillSummaryMarkdown('## 쉬운 요약\n- **핵심** 설명\n### 1) 변화\n<mark>중요</mark>');

    expect(html).toContain('<h2');
    expect(html).toContain('쉬운 요약');
    expect(html).toContain('<h3');
    expect(html).toContain('1) 변화');
    expect(html).toContain('<strong>핵심</strong>');
    expect(html).toContain('<mark>중요</mark>');
  });

  it('허용하지 않은 HTML은 이스케이프한다', () => {
    const html = renderBillSummaryMarkdown('## 제목\n<script>alert(1)</script>');

    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;script&gt;alert(1)&lt;/script&gt;');
  });
});
