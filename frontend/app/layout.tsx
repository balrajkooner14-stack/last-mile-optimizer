import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "US Last-Mile Delivery Optimizer",
  description: "Real-world VRP optimization with OR-Tools, OSRM road distances, and BLS/EIA cost data",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
