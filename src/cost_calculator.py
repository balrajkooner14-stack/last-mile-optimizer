"""
Calculates real delivery costs using BLS driver wage data and EIA fuel prices.
All monetary values are in USD.
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

# Fallbacks when the city/state is not found in our CSV data
BLS_NATIONAL_FALLBACK_WAGE = 22.14       # BLS national mean, SOC 53-3031, 2023
EIA_NATIONAL_GAS_FALLBACK = 3.31         # EIA US average, 2024
EIA_NATIONAL_DIESEL_FALLBACK = 3.61      # EIA US average, 2024

MPG = {"van": 18, "truck": 12, "car": 28}
CO2_LBS_PER_MILE = {"van": 0.89, "truck": 1.45, "car": 0.68}

METERS_PER_MILE = 1609.344


def _meters_to_miles(meters: float) -> float:
    return meters / METERS_PER_MILE


def _seconds_to_hours(seconds: float) -> float:
    return seconds / 3600.0


def load_bls_wages() -> pd.DataFrame:
    """Load BLS OES driver wage data."""
    return pd.read_csv(DATA_DIR / "bls_driver_wages.csv")


def load_fuel_prices() -> pd.DataFrame:
    """Load EIA retail fuel price data."""
    return pd.read_csv(DATA_DIR / "fuel_prices.csv")


def get_driver_wage(city: str, state: str) -> float:
    """
    Return the mean hourly wage for Light Truck Drivers (SOC 53-3031) in the
    given metro. Falls back to the BLS national average if not found.
    """
    try:
        df = load_bls_wages()
        mask = (
            df["metro_name"].str.lower().str.contains(city.lower(), na=False)
            & (df["state"].str.upper() == state.upper())
        )
        match = df[mask]
        if not match.empty:
            return float(match.iloc[0]["mean_hourly_wage"])
    except Exception:
        pass
    return BLS_NATIONAL_FALLBACK_WAGE


def get_fuel_price(state: str, fuel_type: str = "gasoline") -> float:
    """
    Return the average 2024 retail fuel price for the given state.
    Falls back to the EIA national average if the state is not found.
    """
    try:
        df = load_fuel_prices()
        col = "avg_gasoline_price_2024" if fuel_type == "gasoline" else "avg_diesel_price_2024"
        match = df[df["state_abbr"].str.upper() == state.upper()]
        if not match.empty:
            return float(match.iloc[0][col])
    except Exception:
        pass
    return EIA_NATIONAL_GAS_FALLBACK if fuel_type == "gasoline" else EIA_NATIONAL_DIESEL_FALLBACK


def calculate_route_cost(
    distance_meters: float,
    duration_seconds: float,
    city: str,
    state: str,
    vehicle_type: str = "van",
    fuel_type: str = "gasoline",
) -> dict:
    """
    Calculate the total cost for a single vehicle's route.

    Cost = driver_cost + fuel_cost
    driver_cost = duration_hours * hourly_wage
    fuel_cost   = distance_miles * (fuel_price / mpg)
    """
    wage = get_driver_wage(city, state)
    fuel_price = get_fuel_price(state, fuel_type)
    mpg = MPG.get(vehicle_type, 18)

    distance_miles = _meters_to_miles(distance_meters)
    duration_hours = _seconds_to_hours(duration_seconds)

    driver_cost = duration_hours * wage
    fuel_cost = distance_miles * (fuel_price / mpg)
    total_cost = driver_cost + fuel_cost

    return {
        "driver_cost_usd": round(driver_cost, 2),
        "fuel_cost_usd": round(fuel_cost, 2),
        "total_cost_usd": round(total_cost, 2),
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 3),
        "cost_per_mile": round(total_cost / distance_miles, 3) if distance_miles > 0 else 0.0,
    }


def calculate_savings_report(
    naive_result: dict,
    optimized_result: dict,
    city: str,
    state: str,
    num_stops: int,
    vehicle_type: str = "van",
    fuel_type: str = "gasoline",
) -> dict:
    """
    Compare naive vs optimized routes and return a full cost savings report.

    Both result dicts must contain total_distance_meters and total_duration_seconds
    (present in both solve_vrp and solve_naive return values).
    """
    wage = get_driver_wage(city, state)
    fuel_price = get_fuel_price(state, fuel_type)
    mpg = MPG.get(vehicle_type, 18)
    co2 = CO2_LBS_PER_MILE.get(vehicle_type, 0.89)

    naive_dist_m = naive_result.get("total_distance_meters", 0)
    naive_dur_s = naive_result.get("total_duration_seconds", 0)
    opt_dist_m = optimized_result.get("total_distance_meters", 0)
    opt_dur_s = optimized_result.get("total_duration_seconds", 0)

    def total_cost(dist_m, dur_s):
        return _seconds_to_hours(dur_s) * wage + _meters_to_miles(dist_m) * (fuel_price / mpg)

    naive_cost = total_cost(naive_dist_m, naive_dur_s)
    opt_cost = total_cost(opt_dist_m, opt_dur_s)
    savings = naive_cost - opt_cost
    savings_pct = (savings / naive_cost * 100) if naive_cost > 0 else 0.0

    naive_dist_mi = _meters_to_miles(naive_dist_m)
    opt_dist_mi = _meters_to_miles(opt_dist_m)
    naive_dur_hr = _seconds_to_hours(naive_dur_s)
    opt_dur_hr = _seconds_to_hours(opt_dur_s)

    # Cost breakdown for the charts
    naive_driver = naive_dur_hr * wage
    naive_fuel = naive_dist_mi * (fuel_price / mpg)
    opt_driver = opt_dur_hr * wage
    opt_fuel = opt_dist_mi * (fuel_price / mpg)

    return {
        "naive_total_cost": round(naive_cost, 2),
        "optimized_total_cost": round(opt_cost, 2),
        "savings_usd": round(savings, 2),
        "savings_pct": round(savings_pct, 1),
        "naive_distance_miles": round(naive_dist_mi, 2),
        "optimized_distance_miles": round(opt_dist_mi, 2),
        "distance_saved_miles": round(naive_dist_mi - opt_dist_mi, 2),
        "naive_duration_hours": round(naive_dur_hr, 3),
        "optimized_duration_hours": round(opt_dur_hr, 3),
        "time_saved_hours": round(naive_dur_hr - opt_dur_hr, 3),
        "annual_savings_usd": round(savings * 250, 2),
        "co2_saved_lbs": round((naive_dist_mi - opt_dist_mi) * co2, 2),
        "driver_wage_used": wage,
        "fuel_price_used": fuel_price,
        "vehicle_type": vehicle_type,
        "mpg": mpg,
        "num_stops": num_stops,
        "breakdown": {
            "naive_driver_cost": round(naive_driver, 2),
            "naive_fuel_cost": round(naive_fuel, 2),
            "optimized_driver_cost": round(opt_driver, 2),
            "optimized_fuel_cost": round(opt_fuel, 2),
        },
    }
