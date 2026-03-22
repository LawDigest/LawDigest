import '@/styles/globals.css';
import { Metadata, Viewport } from 'next';
import { siteConfig } from '@/config/site';
import { fontSans } from '@/config/fonts';
import clsx from 'clsx';
import { Suspense } from 'react';
import { QueryClientProvider, NextUIProvider, NextThemesProvider, RecoilRootProvider } from '@/lib/provider';
import { GoToTopButton, Loading, Snackbar } from '@/components';
import SearchModal from '@/components/common/SearchBar/SearchModal';
import Nav from '@/components/Layout/Nav/Nav';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: siteConfig.title,
  description: siteConfig.description,
  keywords: [...siteConfig.keywords],
  icons: {
    icon: '/images/favicon.ico',
    shortcut: '/images/favicon-16x16.png',
    apple: '/images/apple-icon-180x180.png',
  },
  verification: {
    google: siteConfig.verification.google,
    other: {
      'naver-site-verification': siteConfig.verification.naver,
    },
  },
  openGraph: {
    siteName: siteConfig.title,
    title: siteConfig.title,
    description: siteConfig.description,
    type: siteConfig.type,
    locale: 'ko_KR',
    url: siteConfig.url,
    images: {
      url: siteConfig.ogImage,
      alt: `${siteConfig.title} 로고`,
      type: 'image/png',
      width: '1200',
      height: '630',
    },
  },
  twitter: {
    title: siteConfig.title,
    description: siteConfig.description,
    images: {
      url: siteConfig.ogImage,
      alt: `${siteConfig.title} 로고`,
      type: 'image/png',
      width: '1200',
      height: '630',
    },
  },
};

function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
      </head>
      <body
        className={clsx(
          'text-black bg-white dark:bg-dark-b dark:lg:bg-dark-pb dark:text-white font-sans antialiased',
          fontSans.variable,
        )}>
        <RecoilRootProvider>
          <QueryClientProvider>
            <NextThemesProvider>
              <NextUIProvider>
                <div className="relative flex flex-col h-auto min-h-[100dvh] min-w-[360px]">
                  <main className="flex items-center justify-center w-full h-full ">
                    <Suspense fallback={<Loading />}>
                      {children}
                      <SearchModal />
                      <Snackbar />
                      <GoToTopButton />
                    </Suspense>
                  </main>
                  {/* Nav는 모든 페이지 전환에서 유지되도록 루트 레이아웃에 배치 */}
                  <Nav />
                </div>
              </NextUIProvider>
            </NextThemesProvider>
          </QueryClientProvider>
        </RecoilRootProvider>
      </body>
    </html>
  );
}

export default RootLayout;
