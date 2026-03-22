import Image from 'next/image';

export default function GPTSummary() {
  return (
    <div className="flex justify-center items-center gap-[11px] opacity-30 text-xs font-semibold">
      <p>Summarized by</p>
      <Image src="/images/gpt.png" alt="gpt-logo" width={25} height={25} priority loader={({ src }) => `${src}`} />
      <p>GPT-4o</p>
    </div>
  );
}
