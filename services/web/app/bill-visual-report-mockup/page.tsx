const changePoints = [
  {
    label: '계획 항목',
    title: '협력체계 구축 방안 명시',
    body: '공공외교 기본계획에 지방자치단체와 민간의 협력체계 구축 방안을 포함하도록 합니다.',
  },
  {
    label: '협력 대상',
    title: '지방·민간 참여 구조화',
    body: '국가 단위 공공외교 계획에서 지방자치단체와 민간을 협력 주체로 더 분명히 다룹니다.',
  },
  {
    label: '정책 효과',
    title: '계획 수립 단계의 누락 보완',
    body: '개별 사업 협력보다 앞선 계획 수립 단계에서 협력 방식을 정리하게 됩니다.',
  },
];

const impactRows = [
  ['외교부', '5년 단위 기본계획에 협력체계 항목을 반영해야 할 수 있습니다.'],
  ['지방자치단체', '공공외교 사업의 협력 파트너로 계획 단계부터 등장할 여지가 커집니다.'],
  ['민간 단체', '지역·민간 외교 활동이 국가 계획과 연결될 근거가 강화될 수 있습니다.'],
];

const timelineSteps = [
  { label: '발의', status: 'done', date: '2025.12' },
  { label: '위원회 심사', status: 'current', date: '확인 중' },
  { label: '본회의', status: 'pending', date: '대기' },
  { label: '공포', status: 'pending', date: '대기' },
];

const evidence = [
  ['열린국회', '의안 상세', '조회 필요'],
  ['국가법령정보센터', '공공외교법 현행 조문', '조회 필요'],
  ['Lawdigest DB', '기존 AI 요약', '확인됨'],
];

function getTimelineTone(status: string) {
  if (status === 'done') return 'bg-theme-info';
  if (status === 'current') return 'bg-black dark:bg-white';
  return 'bg-gray-1';
}

function StatusDot({ status }: { status: string }) {
  const tone = getTimelineTone(status);

  return <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${tone}`} aria-hidden="true" />;
}

export default function BillVisualReportMockupPage() {
  return (
    <section className="w-full min-h-[100dvh] bg-white pb-28 text-black dark:bg-dark-b dark:text-white">
      <div className="mx-auto flex w-full max-w-[1180px] flex-col gap-5 px-4 py-5 md:px-8 md:py-8">
        <header className="flex flex-col gap-5 border-b border-gray-0.5 pb-5 dark:border-dark-l lg:flex-row lg:items-end lg:justify-between">
          <div className="flex max-w-[760px] flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-gray-2">
              <span className="rounded-full border border-gray-0.5 px-3 py-1 dark:border-dark-l">
                모두의입법 리포트
              </span>
              <span className="rounded-full bg-theme-info px-3 py-1 text-black">검수 대기</span>
              <span>v1.0 JSON blocks</span>
            </div>

            <div className="flex h-1.5 w-32 overflow-hidden rounded-full" aria-hidden="true">
              <span className="flex-1 bg-theme-info" />
              <span className="flex-1 bg-theme-alert" />
              <span className="flex-1 bg-party-future" />
              <span className="flex-1 bg-party-basic" />
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold text-gray-2">공공외교법 일부개정법률안</p>
              <h1 className="max-w-[720px] break-keep text-[30px] font-bold leading-tight tracking-normal md:text-[42px]">
                공공외교 기본계획에 지자체·민간 협력체계를 명시
              </h1>
            </div>
          </div>

          <aside className="grid grid-cols-3 overflow-hidden border border-gray-0.5 text-center text-xs dark:border-dark-l md:w-[360px]">
            <div className="border-r border-gray-0.5 px-3 py-3 dark:border-dark-l">
              <p className="text-gray-2">대상</p>
              <p className="mt-1 font-semibold">일반 시민</p>
            </div>
            <div className="border-r border-gray-0.5 px-3 py-3 dark:border-dark-l">
              <p className="text-gray-2">톤</p>
              <p className="mt-1 font-semibold">중립 설명</p>
            </div>
            <div className="px-3 py-3">
              <p className="text-gray-2">근거</p>
              <p className="mt-1 font-semibold">2건 필요</p>
            </div>
          </aside>
        </header>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="flex flex-col gap-5">
            <section className="border border-gray-0.5 bg-primary-1 p-5 dark:border-dark-l dark:bg-dark-pb md:p-7">
              <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
                <div className="space-y-3">
                  <p className="text-xs font-semibold text-gray-2">summary_callout</p>
                  <h2 className="break-keep text-2xl font-bold leading-snug md:text-[32px]">
                    공공외교 계획에 “누구와 어떻게 협력할지”를 쓰게 하는 법안입니다.
                  </h2>
                  <p className="max-w-[650px] text-base leading-7 text-gray-3 dark:text-gray-2">
                    새 리포트는 긴 요약문을 다시 보여주기보다, 사용자가 첫 화면에서 바뀌는 조항과 영향을 바로 훑을 수
                    있게 블록 단위로 정리합니다.
                  </p>
                </div>

                <div className="grid min-w-[180px] grid-cols-2 gap-2 text-sm">
                  <div className="border border-gray-0.5 bg-white p-3 dark:border-dark-l dark:bg-dark-b">
                    <p className="text-xs text-gray-2">블록</p>
                    <p className="mt-1 text-xl font-bold">8</p>
                  </div>
                  <div className="border border-gray-0.5 bg-white p-3 dark:border-dark-l dark:bg-dark-b">
                    <p className="text-xs text-gray-2">출처</p>
                    <p className="mt-1 text-xl font-bold">3</p>
                  </div>
                </div>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-[0.9fr_1.1fr]">
              <div className="border border-gray-0.5 p-5 dark:border-dark-l md:p-6">
                <p className="text-xs font-semibold text-gray-2">before_after</p>
                <h2 className="mt-2 text-xl font-bold">현행과 개정안</h2>

                <div className="mt-5 grid gap-3">
                  <div className="border-l-4 border-gray-1 bg-gray-50 px-4 py-3 dark:border-dark-l dark:bg-dark-pb">
                    <p className="text-xs font-semibold text-gray-2">현행</p>
                    <p className="mt-2 text-sm leading-6">
                      공공외교 기본계획 항목에 협력체계 구축 방안이 직접 드러나지 않습니다.
                    </p>
                  </div>
                  <div className="border-l-4 border-theme-info bg-theme-info/20 px-4 py-3 text-black dark:text-white">
                    <p className="text-xs font-semibold text-gray-3">개정안</p>
                    <p className="mt-2 text-sm leading-6">
                      지방자치단체와 민간의 협력체계 구축 방안을 기본계획에 포함합니다.
                    </p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-0.5 p-5 dark:border-dark-l md:p-6">
                <p className="text-xs font-semibold text-gray-2">change_points</p>
                <h2 className="mt-2 text-xl font-bold">달라지는 점</h2>

                <div className="mt-5 divide-y divide-gray-0.5 dark:divide-dark-l">
                  {changePoints.map((item, index) => (
                    <div key={item.label} className="grid gap-3 py-4 first:pt-0 last:pb-0 md:grid-cols-[48px_1fr]">
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-black text-sm font-bold text-white dark:bg-white dark:text-black">
                        {index + 1}
                      </span>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-base font-bold">{item.title}</p>
                          <span className="text-xs font-semibold text-gray-2">{item.label}</span>
                        </div>
                        <p className="mt-1 text-sm leading-6 text-gray-3 dark:text-gray-2">{item.body}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="border border-gray-0.5 p-5 dark:border-dark-l md:p-6">
              <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-xs font-semibold text-gray-2">impact_list</p>
                  <h2 className="mt-2 text-xl font-bold">누가 영향을 받나</h2>
                </div>
                <p className="text-sm text-gray-2">찬반 평가 없이 제도 변화만 표시</p>
              </div>

              <div className="mt-5 grid border border-gray-0.5 dark:border-dark-l">
                {impactRows.map(([target, effect]) => (
                  <div
                    key={target}
                    className="grid gap-2 border-b border-gray-0.5 p-4 last:border-b-0 dark:border-dark-l md:grid-cols-[160px_1fr]">
                    <p className="font-bold">{target}</p>
                    <p className="text-sm leading-6 text-gray-3 dark:text-gray-2">{effect}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="border border-gray-0.5 p-5 dark:border-dark-l md:p-6">
              <p className="text-xs font-semibold text-gray-2">process_timeline</p>
              <h2 className="mt-2 text-xl font-bold">입법 진행</h2>

              <ol className="mt-6 grid gap-3 md:grid-cols-4">
                {timelineSteps.map((step) => (
                  <li key={step.label} className="border border-gray-0.5 p-4 dark:border-dark-l">
                    <div className="flex items-center gap-2">
                      <StatusDot status={step.status} />
                      <p className="font-bold">{step.label}</p>
                    </div>
                    <p className="mt-3 text-sm text-gray-2">{step.date}</p>
                  </li>
                ))}
              </ol>
            </section>
          </div>

          <aside className="flex flex-col gap-5 lg:sticky lg:top-6 lg:self-start">
            <section className="border border-gray-0.5 p-5 dark:border-dark-l">
              <p className="text-xs font-semibold text-gray-2">evidence</p>
              <h2 className="mt-2 text-xl font-bold">근거 상태</h2>

              <div className="mt-5 divide-y divide-gray-0.5 dark:divide-dark-l">
                {evidence.map(([source, item, state]) => (
                  <div key={source} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-bold">{source}</p>
                      <span
                        className={`text-xs font-semibold ${
                          state === '확인됨' ? 'text-black dark:text-white' : 'text-theme-alert'
                        }`}>
                        {state}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-2">{item}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="border border-gray-0.5 p-5 dark:border-dark-l">
              <p className="text-xs font-semibold text-gray-2">law_links</p>
              <h2 className="mt-2 text-xl font-bold">함께 볼 법</h2>
              <div className="mt-5 flex flex-col gap-2">
                <div className="border border-gray-0.5 px-4 py-3 dark:border-dark-l">
                  <p className="text-sm font-bold">공공외교법</p>
                  <p className="mt-1 text-xs text-gray-2">개정 대상</p>
                </div>
                <div className="border border-gray-0.5 px-4 py-3 dark:border-dark-l">
                  <p className="text-sm font-bold">지방자치법</p>
                  <p className="mt-1 text-xs text-gray-2">협력 주체 확인</p>
                </div>
              </div>
            </section>

            <section className="border border-gray-0.5 bg-black p-5 text-white dark:border-dark-l dark:bg-white dark:text-black">
              <p className="text-xs font-semibold opacity-60">source_notes</p>
              <h2 className="mt-2 text-xl font-bold">공개 전 확인</h2>
              <p className="mt-4 text-sm leading-6 opacity-80">
                의안 상세와 현행 조문 조회가 끝나기 전에는 공개용 리포트로 승격하지 않습니다.
              </p>
            </section>
          </aside>
        </div>
      </div>
    </section>
  );
}
