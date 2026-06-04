"""
Builds JSON-serializable map data for the Next.js Leaflet frontend.
Fetches actual road geometry from the OSRM Route API for each vehicle's route.
"""
import time
import requests

OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/driving/{coordinates}"
VEHICLE_COLORS = ["#E05C3A", "#3AB8A0", "#6C7EF8", "#F0A500", "#C084FC"]
RATE_LIMIT_DELAY = 1.1
REQUEST_TIMEOUT = 15


def get_route_geometry(locations: list[dict], route_indices: list[int]) -> list:
    """
    Fetch actual road geometry for a vehicle's route from the OSRM Route API.

    Returns a list of [lon, lat] coordinate pairs for the Leaflet polyline.
    Falls back to straight lines between stops if OSRM is unavailable.
    OSRM requires lon,lat order (longitude first).
    """
    # Remove duplicate depot at the end to build the OSRM waypoints
    # e.g. [0, 3, 7, 2, 0] -> [0, 3, 7, 2, 0] (keep trailing depot so OSRM closes the loop)
    coords = ";".join(
        f"{locations[i]['lon']},{locations[i]['lat']}"
        for i in route_indices
    )

    try:
        response = requests.get(
            OSRM_ROUTE_URL.format(coordinates=coords),
            params={"overview": "full", "geometries": "geojson"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError("No route returned by OSRM")

        # GeoJSON coordinates are [lon, lat] pairs
        return data["routes"][0]["geometry"]["coordinates"]

    except Exception:
        # Straight-line fallback: connect stops in order
        return [[locations[i]["lon"], locations[i]["lat"]] for i in route_indices]


def build_map_data(locations: list[dict], routes_result: dict) -> dict:
    """
    Build the full map payload for the Leaflet frontend.

    locations: the valid (successfully geocoded) location list — same list
               that was used to build the distance matrix and solve the VRP.
    routes_result: the dict returned by solve_vrp() or solve_naive().

    Returns a JSON-serializable dict with center, markers, and polylines.
    """
    if not locations:
        return {"center": {"lat": 39.5, "lon": -98.35}, "markers": [], "polylines": []}

    center_lat = sum(loc["lat"] for loc in locations) / len(locations)
    center_lon = sum(loc["lon"] for loc in locations) / len(locations)

    # Build a mapping: node_index -> (vehicle_number, stop_number_within_vehicle)
    routes = routes_result.get("routes", [])
    node_to_vehicle: dict[int, tuple[int, int]] = {}
    for v_idx, route in enumerate(routes):
        stop_count = 0
        for pos, node in enumerate(route):
            # Skip depot appearances (first and last position)
            if node == 0 and (pos == 0 or pos == len(route) - 1):
                continue
            stop_count += 1
            node_to_vehicle[node] = (v_idx, stop_count)

    # Build markers — one per location
    markers = []
    for idx, loc in enumerate(locations):
        is_depot = idx == 0
        v_num, stop_num = node_to_vehicle.get(idx, (0, 0))
        markers.append({
            "index": idx,
            "address": loc["address"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "is_depot": is_depot,
            "vehicle_number": v_num,
            "stop_number": stop_num,
        })

    # Build polylines — one OSRM route call per vehicle
    polylines = []
    for v_idx, route in enumerate(routes):
        if len(route) <= 2:
            continue  # empty vehicle

        coords = get_route_geometry(locations, route)
        polylines.append({
            "vehicle_index": v_idx,
            "color": VEHICLE_COLORS[v_idx % len(VEHICLE_COLORS)],
            "coordinates": coords,
        })

        # Rate limit between OSRM route calls (one per vehicle)
        if v_idx < len(routes) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    return {
        "center": {"lat": round(center_lat, 6), "lon": round(center_lon, 6)},
        "markers": markers,
        "polylines": polylines,
    }
