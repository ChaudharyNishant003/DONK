import type { NextConfig } from "next";

// The app ships as static files inside the Android APK (Capacitor), so there is
// no server: everything is exported to web/out at build time.
const nextConfig: NextConfig = {
  output: "export",
  // Matches the 1.1.0-test1 layout: /today/index.html, /life/money/index.html, ...
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
