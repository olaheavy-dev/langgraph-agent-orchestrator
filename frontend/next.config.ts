import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Standalone output so the Docker image carries only what it needs to run,
  // rather than the whole node_modules tree.
  output: 'standalone',
};

export default nextConfig;
