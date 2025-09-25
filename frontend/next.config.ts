import type { NextConfig } from 'next';

const isGhPages = process.env.GH_PAGES === 'true';
const basePath = isGhPages ? '/Precipice' : '';
const assetPrefix = isGhPages ? 'https://retailxai.github.io/Precipice/' : undefined;

const nextConfig: NextConfig = {
  output: 'export',
  basePath,
  assetPrefix,
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
