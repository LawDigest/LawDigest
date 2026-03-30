/** @type {import('next').NextConfig} */
const imageHostname = process.env.NEXT_PUBLIC_HOSTNAME;

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
      allowedOrigins: ['dev.lawdigest.net', 'https://dev.lawdigest.net', 'test.lawdigest.net', 'https://test.lawdigest.net'],
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
