const summaryParagraphs = [
  '권향엽의원 등 10명에 의해 발의된 국회법 일부개정법률안입니다.',
  '상임위원회가 전반기와 후반기 임기 종료 시점에 활동 결과보고서를 의무적으로 제출하도록 규정합니다.',
  '보고서에는 국정감사의 주요 실시 내용을 포함하도록 해, 채택되지 않은 감사 내용도 국가기관의 공식 기록으로 보존할 수 있게 합니다.',
  '입법부의 기록 보존과 대국민 투명성을 높이려는 취지입니다.',
];

const changeCards = [
  {
    label: '보고 의무',
    title: '상임위 활동 보고서 제출',
    body: '위원회 활동 결과를 임기 종료 시점에 의무 제출하도록 국회법에 명시합니다.',
  },
  {
    label: '기록 범위',
    title: '국정감사 주요 내용 포함',
    body: '감사 결과가 공식 채택되지 않아도 주요 실시 내용은 보고서에 남길 수 있습니다.',
  },
  {
    label: '공개 효과',
    title: '국가기록과 시민 접근성 강화',
    body: '국회 내부 활동 기록을 시민과 언론이 확인할 수 있는 공식 자료로 남깁니다.',
  },
];

const impactRows = [
  ['상임위원회', '활동 결과보고서를 정해진 시점에 제출해야 합니다.'],
  ['국정감사 대상 기관', '주요 지적과 처리 요구가 공식 기록에 남을 가능성이 커집니다.'],
  ['시민·언론', '위원회 활동과 감사 내용을 사후에 확인할 자료가 늘어납니다.'],
];

const progressSteps = [
  { label: 'STEP 01', title: '접수', active: true },
  { label: 'STEP 02', title: '위원회 심사', active: false },
  { label: 'STEP 03', title: '체계자구 심사', active: false },
  { label: 'STEP 04', title: '본회의 심의', active: false },
  { label: 'STEP 05', title: '정부 이송', active: false },
  { label: 'STEP 06', title: '공포', active: false },
];

const evidenceRows = [
  ['열린국회정보', '의안 원문·발의자·심사 단계', '확인'],
  ['국가법령정보센터', '국회법 현행 조문', '대조'],
  ['법제처', '법령 체계·개정 대상', '대조'],
];

const relatedBills = [
  [
    '무제한토론 운영의 합리화와 본회의 의사진행 효율성을 높이는 국회법 일부개정법률안',
    '본회의 심의',
    '민형배의원 등 11인',
  ],
  ['복수 법안심사소위 설치 의무화를 위한 국회법 일부개정법률안', '위원회 심사', '권칠승의원 등 11인'],
];

function getEvidenceTone(status: string) {
  return status === '확인' ? 'bg-black text-white dark:bg-white dark:text-black' : 'bg-theme-info text-black';
}

function ProgressDot({ active, index }: { active: boolean; index: number }) {
  return (
    <span
      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
        active ? 'bg-theme-alert text-white' : 'bg-gray-1 text-white dark:bg-dark-l'
      }`}>
      {index}
    </span>
  );
}

export default function BillVisualReportMockupPage() {
  return (
    <section className="w-full bg-white pb-28 text-black dark:bg-dark-b dark:text-white">
      <div className="mx-auto w-full max-w-[1180px]">
        <header className="relative flex h-[58px] items-center justify-center border-b border-gray-0.5 px-5 dark:border-dark-l">
          <span className="material-symbols-outlined absolute left-5 text-[22px]" aria-hidden="true">
            arrow_back
          </span>
          <h1 className="text-base font-semibold">의안 자세히 보기</h1>
        </header>

        <div className="flex flex-col md:flex-row md:items-start">
          <article className="w-full md:w-[calc(100%-340px)] md:border-r md:border-gray-0.5 dark:md:border-dark-l lg:w-[calc(100%-530px)]">
            <section className="px-5 pb-8 pt-6">
              <div className="flex items-center gap-1 text-sm text-gray-2">
                <span className="material-symbols-outlined text-[18px]" aria-hidden="true">
                  schedule
                </span>
                <span>23일 전</span>
              </div>

              <h2 className="mt-4 break-keep text-[26px] font-semibold leading-[1.35] md:text-[28px]">
                상임위원회의 활동 결과보고서 제출을 의무화하고 국정감사 주요 내용을 포함하여 국가기관의 공식 기록으로
                남기기 위한 국회법 일부개정법률안
              </h2>

              <p className="mt-4 text-sm text-gray-2 dark:text-gray-3">국회법 일부개정법률안</p>

              <div className="mt-7 space-y-2 text-[15px] leading-7">
                {summaryParagraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>

              <div className="mt-10 flex items-center justify-between text-sm text-gray-2">
                <div className="flex items-center gap-4">
                  <span className="inline-flex items-center gap-1">
                    <span className="material-symbols-outlined text-[22px]" aria-hidden="true">
                      bookmark
                    </span>
                    스크랩 0
                  </span>
                  <span>조회수 26</span>
                </div>
                <span className="material-symbols-outlined text-[22px]" aria-hidden="true">
                  ios_share
                </span>
              </div>

              <div className="mt-9 flex flex-col items-center gap-4 border-t border-gray-0.5 pt-7 text-center dark:border-dark-l">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-2">
                  <span>Summarized by</span>
                  <span className="material-symbols-outlined text-[24px]" aria-hidden="true">
                    network_intelligence
                  </span>
                  <span>GPT-4o</span>
                </div>
                <p className="text-xs font-semibold text-theme-alert">
                  AI 기반의 요약은 내용이 불완전할 수 있습니다. 꼭 원문을 확인해주세요 !
                </p>
                <button
                  type="button"
                  className="h-14 w-[242px] rounded-full bg-primary-3 text-sm font-semibold text-white dark:bg-gray-0.5 dark:text-black">
                  원문 확인하기
                </button>
              </div>
            </section>

            <section className="border-t border-gray-0.5 px-5 py-8 dark:border-dark-l">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-2">AI 시각 리포트</p>
                  <h2 className="mt-2 text-2xl font-semibold">쟁점과 변경점</h2>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold">
                  <span className="rounded-full bg-primary-1 px-3 py-1.5 dark:bg-dark-pb">JSON 블록 7개</span>
                  <span className="rounded-full bg-theme-info px-3 py-1.5 text-black">출처 대조형</span>
                </div>
              </div>

              <div className="mt-6 border border-gray-0.5 bg-primary-1 p-5 dark:border-dark-l dark:bg-dark-pb">
                <div className="flex flex-col gap-4 md:flex-row md:items-start">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-black text-white dark:bg-white dark:text-black">
                    <span className="material-symbols-outlined text-[22px]" aria-hidden="true">
                      summarize
                    </span>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-2">핵심 요약</p>
                    <h3 className="mt-2 break-keep text-xl font-semibold leading-snug">
                      상임위 활동과 국정감사 내용을 정례 기록으로 남기는 법안입니다.
                    </h3>
                    <p className="mt-3 text-sm leading-6 text-gray-3 dark:text-gray-2">
                      기존 긴 요약문은 유지하되, 개정 전후와 영향 대상을 블록으로 분리해 첫 화면 아래에서 바로 읽게
                      합니다.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-5 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
                <section className="border border-gray-0.5 p-5 dark:border-dark-l">
                  <h3 className="text-lg font-semibold">현행과 개정안</h3>
                  <div className="mt-5 grid gap-3">
                    <div className="border-l-4 border-gray-1 bg-gray-50 px-4 py-3 dark:border-dark-l dark:bg-dark-pb">
                      <p className="text-xs font-semibold text-gray-2">현행</p>
                      <p className="mt-2 text-sm leading-6">
                        상임위원회 활동 결과보고서 제출 의무가 분명하지 않고, 감사 내용이 기록에 남지 않는 경우가
                        있습니다.
                      </p>
                    </div>
                    <div className="border-l-4 border-theme-info bg-theme-info/20 px-4 py-3">
                      <p className="text-xs font-semibold text-gray-3 dark:text-gray-2">개정안</p>
                      <p className="mt-2 text-sm leading-6">
                        활동 결과보고서를 제출하고 국정감사 주요 실시 내용을 포함하도록 합니다.
                      </p>
                    </div>
                  </div>
                </section>

                <section className="border border-gray-0.5 p-5 dark:border-dark-l">
                  <h3 className="text-lg font-semibold">달라지는 점</h3>
                  <div className="mt-5 divide-y divide-gray-0.5 dark:divide-dark-l">
                    {changeCards.map((item, index) => (
                      <div key={item.label} className="grid gap-3 py-4 first:pt-0 last:pb-0 md:grid-cols-[40px_1fr]">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-black text-sm font-semibold text-white dark:bg-white dark:text-black">
                          {index + 1}
                        </span>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-semibold">{item.title}</p>
                            <span className="text-xs font-semibold text-gray-2">{item.label}</span>
                          </div>
                          <p className="mt-1 text-sm leading-6 text-gray-3 dark:text-gray-2">{item.body}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <section className="mt-5 border border-gray-0.5 p-5 dark:border-dark-l">
                <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                  <h3 className="text-lg font-semibold">영향 대상</h3>
                  <p className="text-sm text-gray-2">찬반 평가 없이 제도 변화만 표시</p>
                </div>

                <div className="mt-5 grid border border-gray-0.5 dark:border-dark-l">
                  {impactRows.map(([target, effect]) => (
                    <div
                      key={target}
                      className="grid gap-2 border-b border-gray-0.5 p-4 last:border-b-0 dark:border-dark-l md:grid-cols-[150px_1fr]">
                      <p className="font-semibold">{target}</p>
                      <p className="text-sm leading-6 text-gray-3 dark:text-gray-2">{effect}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="mt-5 border border-gray-0.5 p-5 dark:border-dark-l">
                <h3 className="text-lg font-semibold">변화 강도</h3>
                <div className="mt-5 space-y-4">
                  {[
                    ['기록 의무', '강함', 'w-[92%]'],
                    ['국정감사 공개성', '보통', 'w-[68%]'],
                    ['예산·조직 영향', '낮음', 'w-[32%]'],
                  ].map(([label, value, width]) => (
                    <div key={label} className="grid gap-2 md:grid-cols-[130px_1fr_52px] md:items-center">
                      <p className="text-sm font-semibold">{label}</p>
                      <div className="h-2 overflow-hidden rounded-full bg-gray-1 dark:bg-dark-l">
                        <div className={`h-full rounded-full bg-theme-info ${width}`} />
                      </div>
                      <p className="text-sm text-gray-2">{value}</p>
                    </div>
                  ))}
                </div>
              </section>
            </section>

            <section className="border-t border-gray-0.5 px-5 py-8 dark:border-dark-l">
              <h2 className="text-2xl font-semibold">국회법 일부개정법률안의 다른 개정안 보기</h2>
              <div className="mt-6 grid gap-4">
                {relatedBills.map(([title, stage, proposer]) => (
                  <div
                    key={title}
                    className="border border-party-minjoo p-4 shadow-[0_10px_24px_rgba(21,36,132,0.08)] dark:bg-dark-pb">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="break-keep text-base font-semibold leading-7">{title}</p>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-2">
                          <span className="rounded bg-gray-50 px-2 py-1 dark:bg-dark-l">{stage}</span>
                          <span>{proposer}</span>
                        </div>
                      </div>
                      <span className="text-right text-sm font-bold text-party-minjoo">더불어민주당</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </article>

          <aside className="w-full md:w-[340px] lg:w-[530px]">
            <div className="flex flex-col gap-[34px] px-5 pb-10 pt-4">
              <section className="border border-party-minjoo px-[18px] py-4 shadow-sm dark:bg-dark-pb">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-1 text-sm font-semibold">
                      권
                    </div>
                    <div>
                      <p className="font-semibold">권향엽 의원</p>
                      <p className="text-xs text-gray-2">권향엽의원 등 10인</p>
                    </div>
                  </div>
                  <p className="text-right text-lg font-bold text-party-minjoo">더불어민주당</p>
                </div>
              </section>

              <section className="flex flex-col gap-6">
                <h3 className="text-2xl font-semibold">발의자 명단</h3>
                <div className="text-sm leading-7">
                  <p className="font-semibold">권향엽 등 10인</p>
                  <p className="mt-5 text-gray-3 dark:text-gray-2">
                    권향엽 김윤 문진석 박광온 박지원 염태영 이기헌 이주희 장종태 채현일
                  </p>
                </div>
              </section>

              <div className="hidden h-[1px] w-full bg-gray-1 dark:bg-dark-l md:block" />

              <section className="flex flex-col gap-6">
                <h3 className="text-2xl font-semibold">심사 진행 단계</h3>
                <ol className="ml-0 flex flex-col gap-4 md:ml-10 lg:ml-[150px]">
                  {progressSteps.map((step, index) => (
                    <li
                      key={step.label}
                      className={`grid grid-cols-[28px_68px_1fr] items-center gap-2 text-sm ${
                        step.active ? 'text-black dark:text-white' : 'text-gray-1 dark:text-dark-l'
                      }`}>
                      <ProgressDot active={step.active} index={index + 1} />
                      <span className="font-semibold">{step.label}</span>
                      <span>{step.title}</span>
                    </li>
                  ))}
                </ol>
              </section>

              <div className="hidden h-[1px] w-full bg-gray-1 dark:bg-dark-l md:block" />

              <section className="flex flex-col gap-6">
                <h3 className="text-2xl font-semibold">법안 처리 결과</h3>
                <p className="text-center text-sm text-gray-2">투표 정보가 없습니다.</p>
              </section>

              <div className="hidden h-[1px] w-full bg-gray-1 dark:bg-dark-l md:block" />

              <section className="flex flex-col gap-5">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-2xl font-semibold">리포트 근거</h3>
                  <span className="rounded-full bg-primary-1 px-3 py-1 text-xs font-semibold dark:bg-dark-pb">
                    MCP 조회
                  </span>
                </div>

                <div className="divide-y divide-gray-0.5 border border-gray-0.5 dark:divide-dark-l dark:border-dark-l">
                  {evidenceRows.map(([source, item, status]) => (
                    <div key={source} className="p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{source}</p>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getEvidenceTone(status)}`}>
                          {status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-gray-2">{item}</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
