/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In local dev, proxy /api/* to the FastAPI server on port 8001
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: "http://localhost:8001/api/:path*",
        },
      ]
    }
    return []
  },
}

export default nextConfig
