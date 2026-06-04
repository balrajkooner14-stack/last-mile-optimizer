"use client"

import { useEffect } from "react"
import { MapContainer, TileLayer, Marker as LeafletMarker, Popup, Polyline } from "react-leaflet"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { MapData } from "../types"

// Fix Leaflet default marker icons in Next.js (webpack replaces _getIconUrl)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
})

function makeIcon(color: string, label: string) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="36" viewBox="0 0 28 36">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 9.63 14 22 14 22S28 23.63 28 14C28 6.27 21.73 0 14 0z"
            fill="${color}" stroke="white" stroke-width="2"/>
      <text x="14" y="19" text-anchor="middle" font-size="11" font-weight="bold"
            fill="white" font-family="sans-serif">${label}</text>
    </svg>`
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
  })
}

const DEPOT_ICON = makeIcon("#1e293b", "D")
const VEHICLE_COLORS = ["#E05C3A", "#3AB8A0", "#6C7EF8", "#F0A500", "#C084FC"]

interface RouteMapProps {
  mapData: MapData
  title: string
}

export default function RouteMap({ mapData, title }: RouteMapProps) {
  const center: [number, number] = [mapData.center.lat, mapData.center.lon]

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      <div className="rounded-xl overflow-hidden border border-gray-200" style={{ height: 380 }}>
        <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
          />

          {mapData.polylines.map((poly) => (
            <Polyline
              key={poly.vehicle_index}
              positions={poly.coordinates.map(([lon, lat]) => [lat, lon])}
              color={poly.color}
              weight={3}
              opacity={0.85}
            />
          ))}

          {mapData.markers.map((marker) => {
            const icon = marker.is_depot
              ? DEPOT_ICON
              : makeIcon(VEHICLE_COLORS[marker.vehicle_number % VEHICLE_COLORS.length], String(marker.stop_number))
            return (
              <LeafletMarker
                key={marker.index}
                position={[marker.lat, marker.lon]}
                icon={icon}
              >
                <Popup>
                  <div className="text-xs">
                    {marker.is_depot ? (
                      <strong>Depot</strong>
                    ) : (
                      <>
                        <strong>Stop {marker.stop_number}</strong>
                        <br />
                        Vehicle {marker.vehicle_number + 1}
                      </>
                    )}
                    <br />
                    {marker.address}
                  </div>
                </Popup>
              </LeafletMarker>
            )
          })}
        </MapContainer>
      </div>
    </div>
  )
}
