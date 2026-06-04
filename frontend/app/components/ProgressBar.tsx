"use client"

import { ProgressEvent } from "../types"

interface ProgressBarProps {
  events: ProgressEvent[]
  stage: string
}

const STAGES = [
  { key: "geocoding", label: "Geocoding" },
  { key: "matrix", label: "Distance Matrix" },
  { key: "solving", label: "Solving VRP" },
  { key: "complete", label: "Done" },
]

function stageIndex(key: string): number {
  if (key === "error") return -1
  return STAGES.findIndex((s) => s.key === key)
}

export default function ProgressBar({ events, stage }: ProgressBarProps) {
  const currentIdx = stageIndex(stage)
  const isError = stage === "error"

  return (
    <div className="space-y-3">
      {/* Step indicators */}
      <div className="flex items-center gap-1">
        {STAGES.map((s, idx) => {
          const done = currentIdx > idx || stage === "complete"
          const active = currentIdx === idx && !isError
          return (
            <div key={s.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                    isError && active
                      ? "bg-red-500 text-white"
                      : done
                      ? "bg-green-500 text-white"
                      : active
                      ? "bg-indigo-600 text-white animate-pulse"
                      : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {done ? "✓" : idx + 1}
                </div>
                <span className="text-xs text-gray-500 mt-1 text-center">{s.label}</span>
              </div>
              {idx < STAGES.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-1 mb-4 transition-colors ${
                    currentIdx > idx ? "bg-green-400" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Event log */}
      <div className="bg-gray-50 rounded-lg p-3 max-h-40 overflow-y-auto space-y-1">
        {events.map((ev, i) => (
          <p
            key={i}
            className={`text-xs font-mono ${
              ev.stage === "error" ? "text-red-600" : "text-gray-600"
            }`}
          >
            <span className="text-gray-400 mr-1.5">[{ev.stage}]</span>
            {ev.message}
          </p>
        ))}
        {events.length === 0 && (
          <p className="text-xs text-gray-400 italic">Waiting for pipeline output…</p>
        )}
      </div>
    </div>
  )
}
