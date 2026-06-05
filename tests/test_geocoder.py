"""Unit tests for src/geocoder.py — all HTTP calls are mocked."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from geocoder import geocode_address, geocode_addresses


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestGeocodeAddress:
    def test_returns_lat_lon_on_success(self):
        payload = [{"lat": "41.8827", "lon": "-87.6233"}]
        with patch("geocoder.requests.get", return_value=_mock_response(payload)):
            result = geocode_address("233 S Wacker Dr Chicago IL")
        assert result is not None
        lat, lon = result
        assert abs(lat - 41.8827) < 0.001
        assert abs(lon - (-87.6233)) < 0.001

    def test_returns_none_on_empty_response(self):
        with patch("geocoder.requests.get", return_value=_mock_response([])):
            result = geocode_address("Nonexistent Address XYZ")
        assert result is None

    def test_returns_none_on_request_exception(self):
        with patch("geocoder.requests.get", side_effect=Exception("timeout")):
            result = geocode_address("233 S Wacker Dr Chicago IL")
        assert result is None


class TestGeocodeAddresses:
    def test_successful_batch(self):
        payloads = [
            [{"lat": "41.88", "lon": "-87.63"}],
            [{"lat": "41.89", "lon": "-87.62"}],
        ]
        call_count = 0

        def fake_get(*args, **kwargs):
            nonlocal call_count
            resp = _mock_response(payloads[call_count % len(payloads)])
            call_count += 1
            return resp

        addresses = ["Address A", "Address B"]
        with patch("geocoder.requests.get", side_effect=fake_get):
            with patch("geocoder.time.sleep"):  # skip rate-limit delay in tests
                results = geocode_addresses(addresses)

        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert results[0]["lat"] == 41.88
        assert results[1]["lat"] == 41.89

    def test_failed_geocode_marked_as_failure(self):
        def fake_get(*args, **kwargs):
            return _mock_response([])

        with patch("geocoder.requests.get", side_effect=fake_get):
            with patch("geocoder.time.sleep"):
                results = geocode_addresses(["Nowhere Town XYZ"])

        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["lat"] is None

    def test_mixed_success_and_failure(self):
        payloads = [
            [{"lat": "41.88", "lon": "-87.63"}],
            [],
        ]
        call_count = 0

        def fake_get(*args, **kwargs):
            nonlocal call_count
            resp = _mock_response(payloads[call_count])
            call_count += 1
            return resp

        with patch("geocoder.requests.get", side_effect=fake_get):
            with patch("geocoder.time.sleep"):
                results = geocode_addresses(["Good Address", "Bad Address"])

        assert results[0]["success"] is True
        assert results[1]["success"] is False

    def test_preserves_address_in_result(self):
        with patch("geocoder.requests.get", return_value=_mock_response([{"lat": "41.88", "lon": "-87.63"}])):
            with patch("geocoder.time.sleep"):
                results = geocode_addresses(["123 Main St"])

        assert results[0]["address"] == "123 Main St"
