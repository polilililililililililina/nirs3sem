const nextConfig = {
  reactStrictMode: true,
  compiler: {
    emotion: true,
  },
  env: {
    API_HOST: process.env.API_HOST,
    SOCKET: process.env.SOCKET,
  },
}

module.exports = nextConfig
