"""
Builds a real driving distance and duration matrix using the OSRM Table API.
Falls back to Haversine straight-line distances if OSRM is unavailable.
"""
import math
import requests

OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving/{coordinates}"
REQUEST_TIMEOUT = 30
ROAD_FACTOR = 1.3    # multiply straight-line by this to estimate road distance
AVG_SPEED_MS = 13.4  # ~30 mph in m/s for duration estimate when OSRM is down


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles."""
    return meters * 0.000621371


def seconds_to_hours(seconds: float) -> float:
    """Convert seconds to hours."""
    return seconds / 3600.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance between two points in meters (Haversine formula)."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _haversine_fallback(locations: list[dict], error: str) -> dict:
    n = len(locations)
    dist = [[0.0] * n for _ in range(n)]
    dur = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d = _haversine(
                    locations[i]["lat"], locations[i]["lon"],
                    locations[j]["lat"], locations[j]["lon"],
                ) * ROAD_FACTOR
                dist[i][j] = d
                dur[i][j] = d / AVG_SPEED_MS
    return {
        "distance_matrix": dist,
        "duration_matrix": dur,
        "locations": locations,
        "success": True,
        "error": error,
        "fallback": True,
    }


def build_distance_matrix(locations: list[dict]) -> dict:
    """
    Build an N×N driving distance (meters) and duration (seconds) matrix via OSRM.

    Only successful geocode results are used. The returned 'locations' list is
    the filtered subset — use these indices when calling the VRP solver.
    Falls back to Haversine if OSRM is unreachable.
    """
    valid = [loc for loc in locations if loc.get("success")]
    n = len(valid)
    print(f"Building distance matrix for {n} locations...")

    # OSRM requires lon,lat order (longitude first)
    coords = ";".join(f"{loc['lon']},{loc['lat']}" for loc in valid)

    try:
        response = requests.get(
            OSRM_TABLE_URL.format(coordinates=coords),
            params={"annotations": "distance,duration"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok":
            raise ValueError(f"OSRM error code: {data.get('code')}")

        dist_matrix = data["distances"]
        dur_matrix = data["durations"]

        # OSRM returns None for unreachable pairs — fill with Haversine estimate
        for i in range(n):
            for j in range(n):
                if dist_matrix[i][j] is None or dur_matrix[i][j] is None:
                    d = _haversine(
                        valid[i]["lat"], valid[i]["lon"],
                        valid[j]["lat"], valid[j]["lon"],
                    ) * ROAD_FACTOR
                    dist_matrix[i][j] = d
                    dur_matrix[i][j] = d / AVG_SPEED_MS

        print(f"Distance matrix built via OSRM ({n}x{n})")
        return {
            "distance_matrix": dist_matrix,
            "duration_matrix": dur_matrix,
            "locations": valid,
            "success": True,
            "error": None,
            "fallback": False,
        }

    except Exception as e:
        print(f"OSRM unavailable ({e}), using Haversine fallback")
        return _haversine_fallback(valid, str(e))
