"use client"

import { FormData } from "../types"

interface AddressFormProps {
  formData: FormData
  onChange: (data: Partial<FormData>) => void
  onSubmit: () => void
  loading: boolean
}

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
  "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
  "VA","WA","WV","WI","WY","DC",
]

export default function AddressForm({ formData, onChange, onSubmit, loading }: AddressFormProps) {
  const stopCount = formData.stops.split("\n").filter((s) => s.trim()).length

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Depot address
        </label>
        <input
          type="text"
          value={formData.depot}
          onChange={(e) => onChange({ depot: e.target.value })}
          placeholder="2158 N Milwaukee Ave Chicago IL 60647"
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Delivery stops{" "}
          <span className="text-gray-400 font-normal">(one address per line)</span>
        </label>
        <textarea
          value={formData.stops}
          onChange={(e) => onChange({ stops: e.target.value })}
          rows={6}
          placeholder={"3600 N Clark St Chicago IL 60613\n1724 W Division St Chicago IL 60622\n5240 N Clark St Chicago IL 60640"}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-y"
        />
        <p className="text-xs text-gray-400 mt-1">{stopCount} stop{stopCount !== 1 ? "s" : ""} entered</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
          <input
            type="text"
            value={formData.city}
            onChange={(e) => onChange({ city: e.target.value })}
            placeholder="Chicago"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
          <select
            value={formData.state}
            onChange={(e) => onChange({ state: e.target.value })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            <option value="">Select…</option>
            {US_STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vehicles</label>
          <input
            type="number"
            min={1}
            max={10}
            value={formData.num_vehicles}
            onChange={(e) => onChange({ num_vehicles: parseInt(e.target.value) || 1 })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Vehicle type</label>
          <select
            value={formData.vehicle_type}
            onChange={(e) => onChange({ vehicle_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            <option value="van">Van (18 mpg)</option>
            <option value="truck">Truck (12 mpg)</option>
            <option value="car">Car (28 mpg)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Fuel type</label>
          <select
            value={formData.fuel_type}
            onChange={(e) => onChange({ fuel_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
          >
            <option value="gasoline">Gasoline</option>
            <option value="diesel">Diesel</option>
          </select>
        </div>
      </div>

      <button
        onClick={onSubmit}
        disabled={loading || !formData.depot.trim() || stopCount === 0}
        className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors text-sm"
      >
        {loading ? "Optimizing…" : "Optimize Routes"}
      </button>
    </div>
  )
}
