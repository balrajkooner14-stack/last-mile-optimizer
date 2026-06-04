"use client"

import { useState } from "react"
import dynamic from "next/dynamic"
import ScenarioLoader from "./components/ScenarioLoader"
import AddressForm from "./components/AddressForm"
import ProgressBar from "./components/ProgressBar"
import SavingsPanel from "./components/SavingsPanel"
import HowItWorks from "./components/HowItWorks"
import { FormData, OptimizeResult, ProgressEvent } from "./types"

// Leaflet requires browser APIs — must be loaded client-side only
const RouteMap = dynamic(() => import("./components/RouteMap"), { ssr: false })

const DEFAULT_FORM: FormData = {
  depot: "",
  stops: "",
  city: "",
  state: "",
  num_vehicles: 2,
  vehicle_type: "van",
  fuel_type: "gasoline",
}

type AppStage = "idle" | "loading" | "complete" | "error"

export default function Home() {
  const [formData, setFormData] = useState<FormData>(DEFAULT_FORM)
  const [appStage, setAppStage] = useState<AppStage>("idle")
  const [progressStage, setProgressStage] = useState<string>("")
  const [events, setEvents] = useState<ProgressEvent[]>([])
  const [result, setResult] = useState<OptimizeResult | null>(null)
  const [mapView, setMapView] = useState<"optimized" | "naive">("optimized")
  const [errorMsg, setErrorMsg] = useState<string>("")

  function updateForm(patch: Partial<FormData>) {
    setFormData((prev) => ({ ...prev, ...patch }))
  }

  async function handleSubmit() {
    setAppStage("loading")
    setEvents([])
    setProgressStage("geocoding")
    setResult(null)
    setErrorMsg("")

    const stops = formData.stops
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean)

    try {
      const res = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          depot: formData.depot.trim(),
          stops,
          city: formData.city.trim(),
          state: formData.state,
          num_vehicles: formData.num_vehicles,
          vehicle_type: formData.vehicle_type,
          fuel_type: formData.fuel_type,
        }),
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue
          try {
            const ev: ProgressEvent = JSON.parse(trimmed)
            setEvents((prev) => [...prev, ev])
            setProgressStage(ev.stage)

            if (ev.stage === "complete" && ev.data) {
              setResult(ev.data as unknown as OptimizeResult)
              setAppStage("complete")
            } else if (ev.stage === "error") {
              setErrorMsg(ev.message)
              setAppStage("error")
            }
          } catch {
            // malformed NDJSON line — skip
          }
        }
      }

      if (appStage === "loading") {
        setAppStage("error")
        setErrorMsg("Stream ended without a result")
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Network error")
      setAppStage("error")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              US Last-Mile Delivery Optimizer
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Google OR-Tools VRP · Real road distances · BLS/EIA cost data
            </p>
          </div>
          <span className="hidden sm:block text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-full font-medium">
            Portfolio Project
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panel — inputs */}
        <div className="space-y-5">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
            <ScenarioLoader onLoad={updateForm} />
            <AddressForm
              formData={formData}
              onChange={updateForm}
              onSubmit={handleSubmit}
              loading={appStage === "loading"}
            />
          </div>
          <HowItWorks />
        </div>

        {/* Right panel — results */}
        <div className="lg:col-span-2 space-y-5">
          {/* Progress / status */}
          {(appStage === "loading" || appStage === "error" || events.length > 0) && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Pipeline Progress</h2>
              <ProgressBar events={events} stage={progressStage} />
              {appStage === "error" && (
                <p className="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                  {errorMsg}
                </p>
              )}
            </div>
          )}

          {/* Savings report */}
          {appStage === "complete" && result && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Cost Savings Report</h2>
                <SavingsPanel report={result.savings_report} />
              </div>

              {/* Map */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-gray-700">Route Map</h2>
                  <div className="flex rounded-lg overflow-hidden border border-gray-200 text-xs">
                    <button
                      onClick={() => setMapView("optimized")}
                      className={`px-3 py-1.5 font-medium transition-colors ${
                        mapView === "optimized"
                          ? "bg-indigo-600 text-white"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      Optimized
                    </button>
                    <button
                      onClick={() => setMapView("naive")}
                      className={`px-3 py-1.5 font-medium transition-colors border-l border-gray-200 ${
                        mapView === "naive"
                          ? "bg-indigo-600 text-white"
                          : "bg-white text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      Naive Baseline
                    </button>
                  </div>
                </div>
                <RouteMap
                  mapData={mapView === "optimized" ? result.optimized_map : result.naive_map}
                  title={mapView === "optimized" ? "OR-Tools Optimized Routes" : "Naive Sequential Routes"}
                />
              </div>
            </>
          )}

          {/* Empty state */}
          {appStage === "idle" && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="text-4xl mb-3">🗺️</div>
              <h2 className="text-lg font-semibold text-gray-700 mb-2">
                Load a scenario or enter addresses
              </h2>
              <p className="text-sm text-gray-400 max-w-sm mx-auto">
                The optimizer will geocode your stops, build a real driving-distance matrix via OSRM,
                and solve the VRP with Google OR-Tools — then show you the cost savings.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
