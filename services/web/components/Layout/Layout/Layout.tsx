import { Header } from '../Header';

interface LayoutProps {
  logo?: boolean;
  goBack?: boolean;
  title?: string;
  setting?: boolean;
  search?: boolean;
  notification?: boolean;
  nav?: boolean;
  theme?: boolean;
  children: React.ReactNode;
}

export default function Layout({
  logo,
  goBack,
  title,
  setting,
  search,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  nav: _nav,
  notification,
  theme,
  children,
}: LayoutProps) {
  return (
    <section className="w-full h-full flex flex-col items-center lg:w-full min-w-[360px]">
      <Header
        logo={logo}
        goBack={goBack}
        title={title}
        setting={setting}
        search={search}
        notification={notification}
        theme={theme}
      />
      <section className="w-full h-full md:max-w-[768px] lg:max-w-[1280px]">{children}</section>
    </section>
  );
}
