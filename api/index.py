"""
FastAPI backend for the Last-Mile Delivery Cost Optimizer.
Exposes four endpoints; /api/optimize streams NDJSON progress events.
"""
import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Resolve paths so src/ and data/ work on both local and Vercel
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from geocoder import geocode_addresses
from distance_matrix import build_distance_matrix
from vrp_solver import solve_vrp
from naive_router import solve_naive
from cost_calculator import calculate_savings_report
from route_visualizer import build_map_data

DATA_DIR = ROOT / "data"
SCENARIOS_DIR = DATA_DIR / "sample_scenarios"

app = FastAPI(title="Last-Mile Optimizer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    depot: str
    stops: list[str]
    city: str
    state: str
    num_vehicles: int = 2
    vehicle_type: str = "van"
    fuel_type: str = "gasoline"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@app.get("/api/scenarios")
def list_scenarios():
    """Return metadata for all bundled sample scenarios."""
    scenarios = []
    for csv_path in sorted(SCENARIOS_DIR.glob("*.csv")):
        try:
            with csv_path.open() as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            depot_row = next((r for r in rows if r.get("stop_number") == "0"), rows[0])
            scenarios.append({
                "name": csv_path.stem,
                "display_name": csv_path.stem.replace("_", " ").title(),
                "depot": depot_row.get("address", ""),
                "num_stops": len(rows) - 1,
            })
        except Exception as exc:
            scenarios.append({"name": csv_path.stem, "error": str(exc)})
    return {"scenarios": scenarios}


@app.get("/api/scenario/{name}")
def get_scenario(name: str):
    """Return the depot address + stop list for a named scenario."""
    csv_path = SCENARIOS_DIR / f"{name}.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    try:
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    depot_row = next((r for r in rows if r.get("stop_number") == "0"), rows[0])
    stop_rows = [r for r in rows if r.get("stop_number") != "0"]

    return {
        "name": name,
        "depot": depot_row.get("address", ""),
        "stops": [r["address"] for r in stop_rows],
        "metadata": [
            {
                "customer_name": r.get("customer_name", ""),
                "package_weight_lbs": r.get("package_weight_lbs", ""),
                "delivery_notes": r.get("delivery_notes", ""),
            }
            for r in stop_rows
        ],
    }


# ---------------------------------------------------------------------------
# Optimize — streaming NDJSON
# ---------------------------------------------------------------------------

def _event(stage: str, message: str, data: Optional[dict] = None) -> str:
    payload = {"stage": stage, "message": message}
    if data is not None:
        payload["data"] = data
    return json.dumps(payload) + "\n"


@app.post("/api/optimize")
async def optimize(req: OptimizeRequest):
    """
    Run the full optimization pipeline and stream NDJSON progress events.

    Event sequence:
      geocoding -> matrix -> solving -> complete (or error)
    """
    all_addresses = [req.depot] + req.stops
    num_stops = len(req.stops)

    async def generate():
        try:
            # --- Stage 1: Geocoding ---
            yield _event("geocoding", f"Geocoding {len(all_addresses)} addresses...")
            locations = await asyncio.to_thread(geocode_addresses, all_addresses)

            failed = [loc["address"] for loc in locations if not loc.get("success")]
            if failed:
                yield _event(
                    "geocoding",
                    f"Warning: {len(failed)} address(es) could not be geocoded",
                    {"failed_addresses": failed},
                )

            valid_count = sum(1 for loc in locations if loc.get("success"))
            if valid_count < 2:
                yield _event("error", "Not enough addresses could be geocoded (need at least 2)")
                return

            yield _event("geocoding", f"Geocoded {valid_count}/{len(all_addresses)} addresses successfully")

            # --- Stage 2: Distance Matrix ---
            yield _event("matrix", "Building driving distance matrix via OSRM...")
            matrix_result = await asyncio.to_thread(build_distance_matrix, locations)
            valid_locations = matrix_result["locations"]  # filtered valid-only subset

            fallback_note = " (using straight-line fallback)" if matrix_result.get("fallback") else ""
            yield _event(
                "matrix",
                f"Distance matrix built for {len(valid_locations)} locations{fallback_note}",
            )

            # --- Stage 3: VRP Solve ---
            yield _event("solving", "Running OR-Tools VRP optimizer...")

            vrp_result = await asyncio.to_thread(
                solve_vrp,
                matrix_result["distance_matrix"],
                req.num_vehicles,
                0,    # depot_index
                55,   # time_limit_seconds — never lower (Vercel 60s cap)
                matrix_result["duration_matrix"],
            )

            if not vrp_result["success"]:
                yield _event("error", vrp_result.get("error", "VRP solver failed"))
                return

            naive_result = await asyncio.to_thread(
                solve_naive,
                valid_locations,
                req.num_vehicles,
                matrix_result["distance_matrix"],
                matrix_result["duration_matrix"],
            )

            yield _event(
                "solving",
                f"Optimization complete — {len(vrp_result['routes'])} routes generated",
            )

            # --- Stage 4: Cost Report ---
            savings = calculate_savings_report(
                naive_result=naive_result,
                optimized_result=vrp_result,
                city=req.city,
                state=req.state,
                num_stops=num_stops,
                vehicle_type=req.vehicle_type,
                fuel_type=req.fuel_type,
            )

            # --- Stage 5: Map Data ---
            # CRITICAL: pass valid_locations (matrix_result["locations"]), not raw geocoder output
            map_data = await asyncio.to_thread(build_map_data, valid_locations, vrp_result)
            naive_map_data = await asyncio.to_thread(build_map_data, valid_locations, naive_result)

            # --- Complete ---
            yield _event(
                "complete",
                "Pipeline finished successfully",
                {
                    "savings_report": savings,
                    "optimized_map": map_data,
                    "naive_map": naive_map_data,
                    "vrp_result": {
                        "routes": vrp_result["routes"],
                        "total_distance_meters": vrp_result["total_distance_meters"],
                        "total_duration_seconds": vrp_result["total_duration_seconds"],
                        "solver_status": vrp_result["solver_status"],
                    },
                    "naive_result": {
                        "routes": naive_result["routes"],
                        "total_distance_meters": naive_result["total_distance_meters"],
                        "total_duration_seconds": naive_result["total_duration_seconds"],
                        "solver_status": naive_result["solver_status"],
                    },
                    "locations": valid_locations,
                },
            )

        except Exception as exc:
            yield _event("error", f"Unexpected error: {str(exc)}")

    return StreamingResponse(generate(), media_type="application/x-ndjson")
