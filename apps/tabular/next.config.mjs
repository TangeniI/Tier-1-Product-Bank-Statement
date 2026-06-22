/** @type {import('next').NextConfig} */
const nextConfig = {
  // Compile the shared workspace packages (they ship raw TS/TSX source).
  transpilePackages: [
    "@tabular/ui",
    "@tabular/auth",
    "@tabular/billing",
    "@tabular/analytics",
  ],
};

export default nextConfig;
