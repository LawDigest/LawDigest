interface SectionContainerProps {
  title?: string;
  children: React.ReactNode;
}

export default function SectionContainer({ title, children }: SectionContainerProps) {
  return (
    <section className="flex flex-col gap-6">
      <h3 className="text-2xl font-semibold">{title}</h3>
      {children}
    </section>
  );
}
