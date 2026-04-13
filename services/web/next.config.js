/** @type {import('next').NextConfig} */
const imageHostname = process.env.NEXT_PUBLIC_HOSTNAME;
const internalApiOrigin = (process.env.INTERNAL_API_ORIGIN || 'https://api.lawdigest.kr').replace(/\/+$/, '');

const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: imageHostname
      ? [
          {
            protocol: 'https',
            hostname: imageHostname,
            port: '',
            pathname: '/**',
          },
        ]
      : [],
    domains: imageHostname ? [imageHostname] : [],
  },
  experimental: {
    serverActions: {
      allowedOrigins: [
        'dev.lawdigest.kr',
        'https://dev.lawdigest.kr',
        'test.lawdigest.kr',
        'https://test.lawdigest.kr',
      ],
    },
  },
  async rewrites() {
    return [
      {
        source: '/v1/:path*',
        destination: `${internalApiOrigin}/v1/:path*`,
      },
      {
        source: '/oauth2/:path*',
        destination: `${internalApiOrigin}/oauth2/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
