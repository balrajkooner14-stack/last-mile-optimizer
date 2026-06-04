"""
Naive sequential router — the "before" baseline.

Splits delivery stops evenly across vehicles in the order they appear in the
input list. This mirrors how most small businesses actually plan routes:
first call gets stop 1, second call gets stop 2, and so on.
"""


def calculate_route_distance(route_indices: list, distance_matrix: list) -> int:
    """Total route distance in meters for a sequence of node indices (depot-to-depot)."""
    total = 0
    for i in range(len(route_indices) - 1):
        total += int(distance_matrix[route_indices[i]][route_indices[i + 1]])
    return total


def calculate_route_duration(route_indices: list, duration_matrix: list) -> float:
    """Total route duration in seconds for a sequence of node indices."""
    total = 0.0
    for i in range(len(route_indices) - 1):
        total += duration_matrix[route_indices[i]][route_indices[i + 1]]
    return total


def solve_naive(
    locations: list,
    num_vehicles: int,
    distance_matrix: list,
    duration_matrix: list = None,
) -> dict:
    """
    Generate the naive sequential baseline routes.

    Stops (indices 1..n) are split as evenly as possible across vehicles in
    sequential order. Depot is always index 0.
    Gap fix: accepts duration_matrix and returns total_duration_seconds to
    match solve_vrp's return structure for cost comparison.
    """
    num_stops = len(locations) - 1  # depot is index 0
    all_stops = list(range(1, num_stops + 1))

    # Distribute stops as evenly as possible
    base, remainder = divmod(num_stops, num_vehicles)
    vehicle_stops = []
    start = 0
    for v in range(num_vehicles):
        count = base + (1 if v < remainder else 0)
        vehicle_stops.append(all_stops[start : start + count])
        start += count

    routes = []
    route_distances = []
    route_durations = []

    for stop_list in vehicle_stops:
        if not stop_list:
            continue
        route = [0] + stop_list + [0]  # depot -> stops -> depot
        dist = calculate_route_distance(route, distance_matrix)
        dur = calculate_route_duration(route, duration_matrix) if duration_matrix else 0.0
        routes.append(route)
        route_distances.append(dist)
        route_durations.append(dur)

    return {
        "success": True,
        "routes": routes,
        "total_distance_meters": sum(route_distances),
        "route_distances_meters": route_distances,
        "total_duration_seconds": sum(route_durations),
        "route_durations_seconds": route_durations,
        "dropped_nodes": [],
        "solver_status": "NAIVE_SEQUENTIAL",
        "error": None,
    }
