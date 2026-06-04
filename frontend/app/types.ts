export interface Marker {
  index: number
  address: string
  lat: number
  lon: number
  is_depot: boolean
  vehicle_number: number
  stop_number: number
}

export interface Polyline {
  vehicle_index: number
  color: string
  coordinates: [number, number][]
}

export interface MapData {
  center: { lat: number; lon: number }
  markers: Marker[]
  polylines: Polyline[]
}

export interface SavingsReport {
  naive_total_cost: number
  optimized_total_cost: number
  savings_usd: number
  savings_pct: number
  naive_distance_miles: number
  optimized_distance_miles: number
  distance_saved_miles: number
  naive_duration_hours: number
  optimized_duration_hours: number
  time_saved_hours: number
  annual_savings_usd: number
  co2_saved_lbs: number
  driver_wage_used: number
  fuel_price_used: number
  vehicle_type: string
  mpg: number
  num_stops: number
  breakdown: {
    naive_driver_cost: number
    naive_fuel_cost: number
    optimized_driver_cost: number
    optimized_fuel_cost: number
  }
}

export interface OptimizeResult {
  savings_report: SavingsReport
  optimized_map: MapData
  naive_map: MapData
  locations: { address: string; lat: number; lon: number; success: boolean }[]
}

export interface ProgressEvent {
  stage: string
  message: string
  data?: Record<string, unknown>
}

export interface FormData {
  depot: string
  stops: string
  city: string
  state: string
  num_vehicles: number
  vehicle_type: string
  fuel_type: string
}
