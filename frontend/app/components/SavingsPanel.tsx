"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { SavingsReport } from "../types"

interface SavingsPanelProps {
  report: SavingsReport
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
      <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function SavingsPanel({ report }: SavingsPanelProps) {
  const costData = [
    {
      name: "Before (Naive)",
      Driver: report.breakdown.naive_driver_cost,
      Fuel: report.breakdown.naive_fuel_cost,
    },
    {
      name: "After (Optimized)",
      Driver: report.breakdown.optimized_driver_cost,
      Fuel: report.breakdown.optimized_fuel_cost,
    },
  ]

  const distData = [
    { name: "Before", Miles: report.naive_distance_miles },
    { name: "After", Miles: report.optimized_distance_miles },
  ]

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat
          label="Cost saved today"
          value={`$${report.savings_usd.toFixed(2)}`}
          sub={`${report.savings_pct}% reduction`}
        />
        <Stat
          label="Annual savings"
          value={`$${report.annual_savings_usd.toLocaleString()}`}
          sub="250 working days"
        />
        <Stat
          label="Miles saved"
          value={`${report.distance_saved_miles} mi`}
          sub={`${report.naive_distance_miles} → ${report.optimized_distance_miles}`}
        />
        <Stat
          label="CO₂ avoided"
          value={`${report.co2_saved_lbs} lbs`}
          sub={`${report.vehicle_type} @ ${report.mpg} mpg`}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-600 mb-3">Cost Breakdown ($)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={costData} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => typeof v === "number" ? `$${v.toFixed(2)}` : v} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Driver" fill="#6C7EF8" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Fuel" fill="#3AB8A0" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-xs font-semibold text-gray-600 mb-3">Distance (miles)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={distData} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => typeof v === "number" ? `${v.toFixed(1)} mi` : v} />
              <Bar dataKey="Miles" fill="#E05C3A" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-50 rounded-xl p-3 text-xs text-gray-500 space-y-0.5">
        <p>
          <span className="font-medium text-gray-700">Driver wage:</span>{" "}
          ${report.driver_wage_used}/hr (BLS SOC 53-3031)
        </p>
        <p>
          <span className="font-medium text-gray-700">Fuel price:</span>{" "}
          ${report.fuel_price_used}/gal (EIA 2024 state average)
        </p>
        <p>
          <span className="font-medium text-gray-700">Stops optimized:</span>{" "}
          {report.num_stops}
        </p>
      </div>
    </div>
  )
}
