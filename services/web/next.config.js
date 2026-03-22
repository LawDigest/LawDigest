/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: process.env.NEXT_PUBLIC_HOSTNAME,
        port: '',
        pathname: '/**',
      },
    ],
    domains: [process.env.NEXT_PUBLIC_HOSTNAME],
  },
  experimental: {
    serverActions: {
      allowedOrigins: ['test.lawdigest.net', 'https://test.lawdigest.net'],
    },
  },
  async rewrites() {
    return [
      {
        source: '/v1/:path*',
        destination: 'https://api.lawdigest.net/v1/:path*',
      },
      {
        source: '/oauth2/:path*',
        destination: 'https://api.lawdigest.net/oauth2/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
