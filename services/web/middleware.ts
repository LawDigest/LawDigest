import { NextRequest, NextResponse } from 'next/server';

const BLOCKED_BOT_PATTERN = /(GPTBot|OAI-SearchBot)/i;
const TARGET_PATHS = ['/bill/', '/party/', '/congressman/', '/search', '/_next/data/'];

const shouldBlock = (userAgent: string | null, pathname: string): boolean => {
  if (!userAgent || !BLOCKED_BOT_PATTERN.test(userAgent)) return false;
  if (pathname.startsWith('/_next/data/') || pathname.startsWith('/search')) return true;

  return TARGET_PATHS.some((pathPrefix) => pathname.startsWith(pathPrefix));
};

export function middleware(request: NextRequest) {
  const userAgent = request.headers.get('user-agent');
  const pathname = request.nextUrl.pathname;

  if (!shouldBlock(userAgent, pathname)) return NextResponse.next();

  return new NextResponse('Too Many Requests', {
    status: 429,
    headers: {
      'Retry-After': '120',
      'Content-Type': 'text/plain; charset=utf-8',
    },
  });
}

export const config = {
  matcher: [
    '/bill/:path*',
    '/party/:path*',
    '/congressman/:path*',
    '/search/:path*',
    '/_next/data/:path*',
  ],
};
