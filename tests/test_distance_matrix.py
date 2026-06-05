"""Unit tests for src/distance_matrix.py — all HTTP calls are mocked."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from distance_matrix import build_distance_matrix, _haversine, meters_to_miles, seconds_to_hours


VALID_LOCATIONS = [
    {"address": "Depot", "lat": 41.90, "lon": -87.70, "success": True},
    {"address": "Stop A", "lat": 41.91, "lon": -87.71, "success": True},
    {"address": "Stop B", "lat": 41.92, "lon": -87.69, "success": True},
]


def _osrm_response(n):
    """Build a minimal OSRM Table API response for n locations."""
    dist = [[float(abs(i - j) * 1000) for j in range(n)] for i in range(n)]
    dur = [[float(abs(i - j) * 120) for j in range(n)] for i in range(n)]
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"code": "Ok", "distances": dist, "durations": dur}
    return resp


class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine(41.9, -87.7, 41.9, -87.7) == 0.0

    def test_known_distance(self):
        # Chicago to Milwaukee is ~134 km straight-line (Haversine)
        d = _haversine(41.85, -87.65, 43.04, -87.91)
        assert 125_000 < d < 145_000


class TestUnitConversions:
    def test_meters_to_miles(self):
        assert abs(meters_to_miles(1609.344) - 1.0) < 0.001

    def test_seconds_to_hours(self):
        assert seconds_to_hours(3600) == 1.0
        assert seconds_to_hours(1800) == 0.5


class TestBuildDistanceMatrix:
    def test_returns_correct_shape(self):
        with patch("distance_matrix.requests.get", return_value=_osrm_response(3)):
            result = build_distance_matrix(VALID_LOCATIONS)

        matrix = result["distance_matrix"]
        assert len(matrix) == 3
        assert all(len(row) == 3 for row in matrix)

    def test_diagonal_is_zero(self):
        with patch("distance_matrix.requests.get", return_value=_osrm_response(3)):
            result = build_distance_matrix(VALID_LOCATIONS)

        matrix = result["distance_matrix"]
        for i in range(3):
            assert matrix[i][i] == 0.0

    def test_filters_out_failed_locations(self):
        locs = VALID_LOCATIONS + [
            {"address": "Bad", "lat": None, "lon": None, "success": False}
        ]
        with patch("distance_matrix.requests.get", return_value=_osrm_response(3)):
            result = build_distance_matrix(locs)

        assert len(result["locations"]) == 3
        assert result["locations"][-1]["address"] != "Bad"

    def test_fallback_on_osrm_error(self):
        with patch("distance_matrix.requests.get", side_effect=Exception("unreachable")):
            result = build_distance_matrix(VALID_LOCATIONS)

        assert result["fallback"] is True
        assert result["success"] is True
        matrix = result["distance_matrix"]
        assert len(matrix) == 3

    def test_fallback_fills_none_cells(self):
        n = 3
        dist = [[float(abs(i - j) * 1000) for j in range(n)] for i in range(n)]
        dur = [[float(abs(i - j) * 120) for j in range(n)] for i in range(n)]
        dist[0][2] = None  # simulate unreachable pair
        dur[0][2] = None

        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"code": "Ok", "distances": dist, "durations": dur}

        with patch("distance_matrix.requests.get", return_value=resp):
            result = build_distance_matrix(VALID_LOCATIONS)

        assert result["distance_matrix"][0][2] is not None
        assert result["duration_matrix"][0][2] is not None
