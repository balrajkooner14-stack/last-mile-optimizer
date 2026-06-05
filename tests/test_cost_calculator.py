"""Unit tests for src/cost_calculator.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from cost_calculator import (
    calculate_route_cost,
    calculate_savings_report,
    get_driver_wage,
    get_fuel_price,
    _meters_to_miles,
    _seconds_to_hours,
    BLS_NATIONAL_FALLBACK_WAGE,
    EIA_NATIONAL_GAS_FALLBACK,
    MPG,
)


class TestUnitConversions:
    def test_meters_to_miles(self):
        assert abs(_meters_to_miles(1609.344) - 1.0) < 0.001

    def test_seconds_to_hours(self):
        assert _seconds_to_hours(3600) == 1.0


class TestGetDriverWage:
    def test_returns_float(self):
        wage = get_driver_wage("Chicago", "IL")
        assert isinstance(wage, float)
        assert wage > 0

    def test_chicago_il_found_in_data(self):
        wage = get_driver_wage("Chicago", "IL")
        # Chicago BLS wage is $22.89 — should not fall back to national average
        assert wage != BLS_NATIONAL_FALLBACK_WAGE

    def test_unknown_city_returns_fallback(self):
        wage = get_driver_wage("Nonexistent City", "ZZ")
        assert wage == BLS_NATIONAL_FALLBACK_WAGE


class TestGetFuelPrice:
    def test_returns_float(self):
        price = get_fuel_price("IL")
        assert isinstance(price, float)
        assert price > 0

    def test_il_found_in_data(self):
        price = get_fuel_price("IL", "gasoline")
        assert price != EIA_NATIONAL_GAS_FALLBACK

    def test_unknown_state_returns_fallback(self):
        price = get_fuel_price("ZZ")
        assert price == EIA_NATIONAL_GAS_FALLBACK

    def test_diesel_type(self):
        price = get_fuel_price("TX", "diesel")
        assert isinstance(price, float)
        assert price > 0


class TestCalculateRouteCost:
    def test_returns_required_keys(self):
        result = calculate_route_cost(
            distance_meters=16093.44,
            duration_seconds=3600,
            city="Chicago",
            state="IL",
        )
        for key in ("driver_cost_usd", "fuel_cost_usd", "total_cost_usd",
                    "distance_miles", "duration_hours", "cost_per_mile"):
            assert key in result

    def test_driver_plus_fuel_equals_total(self):
        result = calculate_route_cost(16093.44, 3600, "Chicago", "IL")
        assert abs(result["driver_cost_usd"] + result["fuel_cost_usd"]
                   - result["total_cost_usd"]) < 0.01

    def test_zero_distance_cost_per_mile(self):
        result = calculate_route_cost(0, 3600, "Chicago", "IL")
        assert result["cost_per_mile"] == 0.0

    def test_mpg_affects_fuel_cost(self):
        van = calculate_route_cost(16093.44, 3600, "Chicago", "IL", vehicle_type="van")
        truck = calculate_route_cost(16093.44, 3600, "Chicago", "IL", vehicle_type="truck")
        # Truck has lower mpg so higher fuel cost
        assert truck["fuel_cost_usd"] > van["fuel_cost_usd"]


class TestCalculateSavingsReport:
    NAIVE = {
        "total_distance_meters": 50_000,
        "total_duration_seconds": 7200,
    }
    OPTIMIZED = {
        "total_distance_meters": 35_000,
        "total_duration_seconds": 5000,
    }

    def test_savings_positive_when_optimized_is_better(self):
        report = calculate_savings_report(
            self.NAIVE, self.OPTIMIZED, "Chicago", "IL", num_stops=10
        )
        assert report["savings_usd"] > 0
        assert report["savings_pct"] > 0

    def test_annual_savings_is_250x_daily(self):
        report = calculate_savings_report(
            self.NAIVE, self.OPTIMIZED, "Chicago", "IL", num_stops=10
        )
        assert abs(report["annual_savings_usd"] - report["savings_usd"] * 250) < 1.0

    def test_distance_saved_correct(self):
        report = calculate_savings_report(
            self.NAIVE, self.OPTIMIZED, "Chicago", "IL", num_stops=10
        )
        expected = _meters_to_miles(50_000) - _meters_to_miles(35_000)
        assert abs(report["distance_saved_miles"] - round(expected, 2)) < 0.01

    def test_breakdown_keys_present(self):
        report = calculate_savings_report(
            self.NAIVE, self.OPTIMIZED, "Chicago", "IL", num_stops=10
        )
        for key in ("naive_driver_cost", "naive_fuel_cost",
                    "optimized_driver_cost", "optimized_fuel_cost"):
            assert key in report["breakdown"]

    def test_co2_saved_positive(self):
        report = calculate_savings_report(
            self.NAIVE, self.OPTIMIZED, "Chicago", "IL", num_stops=10
        )
        assert report["co2_saved_lbs"] > 0

    def test_zero_savings_when_equal(self):
        report = calculate_savings_report(
            self.NAIVE, self.NAIVE, "Chicago", "IL", num_stops=10
        )
        assert report["savings_usd"] == 0.0
        assert report["savings_pct"] == 0.0
