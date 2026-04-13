const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // CRITICAL — produces .next/standalone/ which the production Dockerfile
  // copies into the runner image. Without this flag the standalone
  // directory is never created, the Docker COPY silently copies nothing,
  // and the deployed site renders with no CSS, broken images, and the
  // wrong server entry point.
  output: 'standalone',

  // In a pnpm monorepo, Next.js needs an explicit trace root or it will
  // guess wrong about where the workspace begins. Pinning to two levels
  // up from this config (apps/web → /repo-root) makes the standalone
  // output land at <root>/.next/standalone/ deterministically, both
  // locally and inside the Docker builder.
  experimental: {
    outputFileTracingRoot: path.join(__dirname, '../../'),
  },
}

module.exports = nextConfig
