"use client"

import { useState } from "react"

const STEPS = [
  {
    num: "01",
    title: "Geocoding via Nominatim",
    body: "Each address is resolved to latitude/longitude coordinates using the OpenStreetMap Nominatim API. Failed geocodes are skipped with a warning.",
  },
  {
    num: "02",
    title: "Distance Matrix via OSRM",
    body: "A real driving distance and travel-time matrix is built using the OSRM Table API. All N×N pairs of actual road distances are computed in one call.",
  },
  {
    num: "03",
    title: "VRP Solving via OR-Tools",
    body: "Google OR-Tools solves the multi-vehicle routing problem using PATH_CHEAPEST_ARC for initial routes and GUIDED_LOCAL_SEARCH metaheuristic for 55 seconds to find near-optimal routes.",
  },
  {
    num: "04",
    title: "Naive Baseline",
    body: "A naive baseline is computed by splitting stops sequentially across vehicles — mimicking how most small businesses plan routes without optimization software.",
  },
  {
    num: "05",
    title: "Cost Calculation",
    body: "Real costs use BLS OES driver wages (SOC 53-3031) for the metro area and EIA 2024 state-average retail fuel prices. Cost = driver time × hourly wage + miles × (fuel price ÷ MPG).",
  },
]

export default function HowItWorks() {
  const [open, setOpen] = useState(false)

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <span>How it works</span>
        <span className="text-gray-400 text-base">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
          {STEPS.map((s) => (
            <div key={s.num} className="flex gap-3">
              <span className="text-xs font-bold text-indigo-500 mt-0.5 shrink-0">{s.num}</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">{s.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{s.body}</p>
              </div>
            </div>
          ))}
          <div className="mt-2 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-400">
              Data sources: BLS Occupational Employment Statistics (2023), EIA Weekly Retail Gasoline &amp; Diesel Prices (2024 annual average), OpenStreetMap contributors.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
