"""
Vehicle Routing Problem solver using Google OR-Tools.

CRITICAL: time_limit_seconds defaults to 55. Vercel's serverless cap is 60s.
Do not lower this — the solver needs all available time for near-optimal results.
"""
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def solve_vrp(
    distance_matrix: list,
    num_vehicles: int,
    depot_index: int = 0,
    time_limit_seconds: int = 55,
    duration_matrix: list = None,
) -> dict:
    """
    Solve the VRP for the given distance matrix using GUIDED_LOCAL_SEARCH.

    Returns routes as lists of node indices with the depot at start and end.
    Gap fix: accepts duration_matrix and returns total_duration_seconds so the
    cost calculator can compute driver time costs for the optimized solution.
    """
    n = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(n, num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    # OR-Tools requires integer distances
    int_matrix = [[int(d) for d in row] for row in distance_matrix]

    def distance_callback(from_index, to_index):
        return int_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.seconds = time_limit_seconds
    params.log_search = False

    solution = routing.SolveWithParameters(params)

    if not solution:
        return {
            "success": False,
            "routes": [],
            "total_distance_meters": 0,
            "route_distances_meters": [],
            "total_duration_seconds": 0.0,
            "route_durations_seconds": [],
            "dropped_nodes": list(range(1, n)),
            "solver_status": "NO_SOLUTION",
            "error": "OR-Tools found no feasible solution",
        }

    routes = []
    route_distances = []
    route_durations = []

    for vehicle_id in range(num_vehicles):
        route = []
        route_dist = 0
        route_dur = 0.0
        index = routing.Start(vehicle_id)

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            next_index = solution.Value(routing.NextVar(index))
            next_node = manager.IndexToNode(next_index)
            route_dist += int_matrix[node][next_node]
            if duration_matrix:
                route_dur += duration_matrix[node][next_node]
            index = next_index

        route.append(manager.IndexToNode(index))  # close route at depot

        # Skip vehicles with no stops assigned (depot → depot only)
        if len(route) > 2:
            routes.append(route)
            route_distances.append(int(route_dist))
            route_durations.append(route_dur)

    return {
        "success": True,
        "routes": routes,
        "total_distance_meters": sum(route_distances),
        "route_distances_meters": route_distances,
        "total_duration_seconds": sum(route_durations),
        "route_durations_seconds": route_durations,
        "dropped_nodes": [],
        "solver_status": "ROUTING_SUCCESS",
        "error": None,
    }


def format_routes_readable(routes: list, locations: list) -> list[str]:
    """
    Format routes as human-readable strings for logging.
    e.g. "Vehicle 1: Depot -> 3600 N Clark St -> 1724 W Division St -> Depot"
    """
    lines = []
    for i, route in enumerate(routes):
        parts = []
        for j, node in enumerate(route):
            if j == 0 or j == len(route) - 1:
                parts.append("Depot")
            elif node < len(locations):
                addr = locations[node]["address"]
                # Trim to first 35 chars for readability
                parts.append(addr[:35] + ("..." if len(addr) > 35 else ""))
            else:
                parts.append(f"Stop {node}")
        lines.append(f"Vehicle {i + 1}: " + " -> ".join(parts))
    return lines


if __name__ == "__main__":
    # Test with a simple 5-location symmetric distance matrix
    test_matrix = [
        [0,   1200, 3000, 2100, 1500],
        [1200, 0,   2000, 1800, 2400],
        [3000, 2000, 0,   1300, 2800],
        [2100, 1800, 1300, 0,   1600],
        [1500, 2400, 2800, 1600, 0  ],
    ]
    test_locs = [
        {"address": "Depot", "lat": 41.9, "lon": -87.7, "success": True},
        {"address": "Stop A", "lat": 41.91, "lon": -87.71, "success": True},
        {"address": "Stop B", "lat": 41.92, "lon": -87.69, "success": True},
        {"address": "Stop C", "lat": 41.89, "lon": -87.68, "success": True},
        {"address": "Stop D", "lat": 41.88, "lon": -87.72, "success": True},
    ]

    print("Testing VRP solver with 4 stops, 1 vehicle:")
    result = solve_vrp(test_matrix, num_vehicles=1, time_limit_seconds=5)
    print(f"  Status: {result['solver_status']}")
    print(f"  Total distance: {result['total_distance_meters']}m")
    for line in format_routes_readable(result["routes"], test_locs):
        print(f"  {line}")

    print("\nTesting VRP solver with 4 stops, 2 vehicles:")
    result2 = solve_vrp(test_matrix, num_vehicles=2, time_limit_seconds=5)
    print(f"  Status: {result2['solver_status']}")
    print(f"  Routes: {len(result2['routes'])}")
    for line in format_routes_readable(result2["routes"], test_locs):
        print(f"  {line}")
