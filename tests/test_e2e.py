"""
End-to-end pipeline test using a small synthetic dataset.

No real network calls — all HTTP is mocked. Exercises the full
geocode → distance matrix → VRP → naive → cost → map pipeline.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from geocoder import geocode_addresses
from distance_matrix import build_distance_matrix
from vrp_solver import solve_vrp
from naive_router import solve_naive
from cost_calculator import calculate_savings_report
from route_visualizer import build_map_data

# ---------------------------------------------------------------------------
# Synthetic test data
# ---------------------------------------------------------------------------

RAW_ADDRESSES = [
    "Depot 1 Chicago IL",
    "Stop A Chicago IL",
    "Stop B Chicago IL",
    "Stop C Chicago IL",
    "Stop D Chicago IL",
]

GEOCODE_RESULTS = [
    {"address": addr, "lat": 41.90 + i * 0.01, "lon": -87.70 - i * 0.01, "success": True}
    for i, addr in enumerate(RAW_ADDRESSES)
]

N = len(RAW_ADDRESSES)
DIST_MATRIX = [[float(abs(i - j) * 1500) for j in range(N)] for i in range(N)]
DUR_MATRIX  = [[float(abs(i - j) * 180)  for j in range(N)] for i in range(N)]

OSRM_TABLE_RESP = MagicMock()
OSRM_TABLE_RESP.raise_for_status = MagicMock()
OSRM_TABLE_RESP.json.return_value = {
    "code": "Ok",
    "distances": DIST_MATRIX,
    "durations": DUR_MATRIX,
}

OSRM_ROUTE_RESP = MagicMock()
OSRM_ROUTE_RESP.raise_for_status = MagicMock()
OSRM_ROUTE_RESP.json.return_value = {
    "code": "Ok",
    "routes": [{
        "geometry": {
            "coordinates": [[-87.70, 41.90], [-87.71, 41.91], [-87.70, 41.90]]
        }
    }]
}


def _run_pipeline(num_vehicles=2):
    """Run the full pipeline with mocked HTTP calls. Returns all stage outputs."""
    # Stage 1: geocoding (already mocked above — use prebuilt results)
    locations = GEOCODE_RESULTS

    # Stage 2: distance matrix
    with patch("distance_matrix.requests.get", return_value=OSRM_TABLE_RESP):
        matrix_result = build_distance_matrix(locations)

    valid_locations = matrix_result["locations"]

    # Stage 3: VRP solve
    vrp_result = solve_vrp(
        matrix_result["distance_matrix"],
        num_vehicles=num_vehicles,
        time_limit_seconds=5,
        duration_matrix=matrix_result["duration_matrix"],
    )

    # Stage 4: naive baseline
    naive_result = solve_naive(
        valid_locations,
        num_vehicles=num_vehicles,
        distance_matrix=matrix_result["distance_matrix"],
        duration_matrix=matrix_result["duration_matrix"],
    )

    # Stage 5: cost report
    savings = calculate_savings_report(
        naive_result=naive_result,
        optimized_result=vrp_result,
        city="Chicago",
        state="IL",
        num_stops=len(valid_locations) - 1,
    )

    # Stage 6: map data
    with patch("route_visualizer.requests.get", return_value=OSRM_ROUTE_RESP):
        with patch("route_visualizer.time.sleep"):
            map_data = build_map_data(valid_locations, vrp_result)
            naive_map = build_map_data(valid_locations, naive_result)

    return {
        "valid_locations": valid_locations,
        "vrp_result": vrp_result,
        "naive_result": naive_result,
        "savings": savings,
        "map_data": map_data,
        "naive_map": naive_map,
    }


class TestFullPipeline:
    def setup_method(self):
        self.out = _run_pipeline(num_vehicles=2)

    def test_all_stops_covered_by_vrp(self):
        visited = set()
        for route in self.out["vrp_result"]["routes"]:
            visited.update(n for n in route if n != 0)
        expected = set(range(1, N))
        assert visited == expected

    def test_all_stops_covered_by_naive(self):
        visited = set()
        for route in self.out["naive_result"]["routes"]:
            visited.update(n for n in route if n != 0)
        assert visited == set(range(1, N))

    def test_savings_report_has_required_keys(self):
        savings = self.out["savings"]
        for key in ("savings_usd", "savings_pct", "annual_savings_usd",
                    "distance_saved_miles", "co2_saved_lbs", "breakdown"):
            assert key in savings

    def test_map_data_has_correct_marker_count(self):
        # One marker per valid location (depot + 4 stops)
        assert len(self.out["map_data"]["markers"]) == N

    def test_map_has_depot_marker(self):
        depots = [m for m in self.out["map_data"]["markers"] if m["is_depot"]]
        assert len(depots) == 1

    def test_map_center_within_bounds(self):
        center = self.out["map_data"]["center"]
        assert 25 < center["lat"] < 50
        assert -130 < center["lon"] < -60

    def test_polylines_have_color(self):
        for poly in self.out["map_data"]["polylines"]:
            assert poly["color"].startswith("#")

    def test_naive_map_has_markers(self):
        assert len(self.out["naive_map"]["markers"]) == N

    def test_vrp_better_or_equal_to_naive(self):
        # Optimized total distance should be <= naive total distance
        assert (self.out["vrp_result"]["total_distance_meters"]
                <= self.out["naive_result"]["total_distance_meters"])

    def test_valid_locations_count(self):
        assert len(self.out["valid_locations"]) == N
