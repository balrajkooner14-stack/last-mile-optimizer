"use client"

import { useEffect, useState } from "react"
import { FormData } from "../types"

interface Scenario {
  name: string
  display_name: string
  depot: string
  num_stops: number
}

interface ScenarioLoaderProps {
  onLoad: (data: Partial<FormData>) => void
}

const CITY_STATE: Record<string, { city: string; state: string }> = {
  chicago_florist: { city: "Chicago", state: "IL" },
  austin_pharmacy: { city: "Austin", state: "TX" },
  brooklyn_grocery: { city: "Brooklyn", state: "NY" },
}

export default function ScenarioLoader({ onLoad }: ScenarioLoaderProps) {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/scenarios")
      .then((r) => r.json())
      .then((d) => setScenarios(d.scenarios ?? []))
      .catch(() => {})
  }, [])

  async function loadScenario(name: string) {
    setLoading(true)
    setActive(name)
    try {
      const res = await fetch(`/api/scenario/${name}`)
      const data = await res.json()
      const { city, state } = CITY_STATE[name] ?? { city: "", state: "" }
      onLoad({
        depot: data.depot,
        stops: data.stops.join("\n"),
        city,
        state,
      })
    } catch {
      // silently fail — user can enter manually
    }
    setLoading(false)
  }

  if (scenarios.length === 0) return null

  return (
    <div className="mb-4">
      <p className="text-sm font-medium text-gray-600 mb-2">Load a sample scenario:</p>
      <div className="flex flex-wrap gap-2">
        {scenarios.map((s) => (
          <button
            key={s.name}
            onClick={() => loadScenario(s.name)}
            disabled={loading}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              active === s.name
                ? "bg-indigo-600 text-white border-indigo-600"
                : "bg-white text-gray-700 border-gray-200 hover:border-indigo-400 hover:text-indigo-600"
            }`}
          >
            {s.display_name}
            <span className="ml-1.5 text-xs opacity-60">{s.num_stops} stops</span>
          </button>
        ))}
      </div>
    </div>
  )
}
