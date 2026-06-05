"""Unit tests for src/vrp_solver.py and src/naive_router.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from vrp_solver import solve_vrp, format_routes_readable
from naive_router import solve_naive, calculate_route_distance, calculate_route_duration

# Small symmetric distance matrix (5 nodes: depot + 4 stops)
MATRIX_5 = [
    [0,    1200, 3000, 2100, 1500],
    [1200, 0,    2000, 1800, 2400],
    [3000, 2000, 0,    1300, 2800],
    [2100, 1800, 1300, 0,    1600],
    [1500, 2400, 2800, 1600, 0   ],
]

DURATION_5 = [
    [0,   120, 300, 210, 150],
    [120, 0,   200, 180, 240],
    [300, 200, 0,   130, 280],
    [210, 180, 130, 0,   160],
    [150, 240, 280, 160, 0  ],
]

LOCATIONS_5 = [
    {"address": "Depot",  "lat": 41.90, "lon": -87.70},
    {"address": "Stop A", "lat": 41.91, "lon": -87.71},
    {"address": "Stop B", "lat": 41.92, "lon": -87.69},
    {"address": "Stop C", "lat": 41.89, "lon": -87.68},
    {"address": "Stop D", "lat": 41.88, "lon": -87.72},
]


class TestSolveVrp:
    def test_single_vehicle_visits_all_stops(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        assert result["success"] is True
        visited = set()
        for route in result["routes"]:
            visited.update(n for n in route if n != 0)
        assert visited == {1, 2, 3, 4}

    def test_routes_start_and_end_at_depot(self):
        result = solve_vrp(MATRIX_5, num_vehicles=2, time_limit_seconds=5)
        assert result["success"] is True
        for route in result["routes"]:
            assert route[0] == 0
            assert route[-1] == 0

    def test_total_distance_positive(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        assert result["total_distance_meters"] > 0

    def test_duration_returned_when_matrix_provided(self):
        result = solve_vrp(
            MATRIX_5, num_vehicles=1, time_limit_seconds=5, duration_matrix=DURATION_5
        )
        assert result["total_duration_seconds"] > 0

    def test_duration_zero_without_matrix(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        assert result["total_duration_seconds"] == 0.0

    def test_two_vehicles_split_stops(self):
        result = solve_vrp(MATRIX_5, num_vehicles=2, time_limit_seconds=5)
        assert result["success"] is True
        assert len(result["routes"]) >= 1  # at least one non-empty vehicle

    def test_returns_correct_keys(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        for key in ("success", "routes", "total_distance_meters", "total_duration_seconds",
                    "route_distances_meters", "route_durations_seconds", "dropped_nodes",
                    "solver_status", "error"):
            assert key in result

    def test_solver_status_on_success(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        assert result["solver_status"] == "ROUTING_SUCCESS"


class TestFormatRoutesReadable:
    def test_output_contains_depot(self):
        result = solve_vrp(MATRIX_5, num_vehicles=1, time_limit_seconds=5)
        lines = format_routes_readable(result["routes"], LOCATIONS_5)
        assert any("Depot" in line for line in lines)

    def test_one_line_per_vehicle(self):
        result = solve_vrp(MATRIX_5, num_vehicles=2, time_limit_seconds=5)
        lines = format_routes_readable(result["routes"], LOCATIONS_5)
        assert len(lines) == len(result["routes"])


class TestNaiveRouter:
    def test_all_stops_assigned(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=2,
                             distance_matrix=MATRIX_5, duration_matrix=DURATION_5)
        visited = set()
        for route in result["routes"]:
            visited.update(n for n in route if n != 0)
        assert visited == {1, 2, 3, 4}

    def test_routes_start_and_end_at_depot(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=2,
                             distance_matrix=MATRIX_5)
        for route in result["routes"]:
            assert route[0] == 0
            assert route[-1] == 0

    def test_total_distance_matches_sum(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=1,
                             distance_matrix=MATRIX_5)
        assert result["total_distance_meters"] == sum(result["route_distances_meters"])

    def test_duration_returned_with_matrix(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=1,
                             distance_matrix=MATRIX_5, duration_matrix=DURATION_5)
        assert result["total_duration_seconds"] > 0

    def test_duration_zero_without_matrix(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=1, distance_matrix=MATRIX_5)
        assert result["total_duration_seconds"] == 0.0

    def test_solver_status(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=1, distance_matrix=MATRIX_5)
        assert result["solver_status"] == "NAIVE_SEQUENTIAL"

    def test_sequential_assignment_order(self):
        # With 1 vehicle all 4 stops go to that vehicle in order 1,2,3,4
        result = solve_naive(LOCATIONS_5, num_vehicles=1, distance_matrix=MATRIX_5)
        route = result["routes"][0]
        stops_in_route = [n for n in route if n != 0]
        assert stops_in_route == [1, 2, 3, 4]

    def test_returns_correct_keys(self):
        result = solve_naive(LOCATIONS_5, num_vehicles=1, distance_matrix=MATRIX_5)
        for key in ("success", "routes", "total_distance_meters", "total_duration_seconds",
                    "route_distances_meters", "route_durations_seconds", "dropped_nodes",
                    "solver_status", "error"):
            assert key in result


class TestCalculateRouteHelpers:
    def test_route_distance_depot_to_stop_a(self):
        # depot(0) -> stop_a(1) -> depot(0): 1200 + 1200 = 2400
        assert calculate_route_distance([0, 1, 0], MATRIX_5) == 2400

    def test_route_duration(self):
        assert calculate_route_duration([0, 1, 0], DURATION_5) == 240.0
