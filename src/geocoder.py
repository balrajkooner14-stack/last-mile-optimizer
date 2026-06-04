"""
Geocodes street addresses to (lat, lon) coordinates using Nominatim (OpenStreetMap).
Rate-limited to 1 request/second per Nominatim usage policy.
"""
import time
import requests
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "LastMileOptimizer/1.0 (portfolio project)"}
RATE_LIMIT_DELAY = 1.1
MAX_RETRIES = 3


def geocode_address(address: str) -> Optional[tuple[float, float]]:
    """
    Convert a street address to (latitude, longitude).

    Returns None if the address cannot be geocoded after MAX_RETRIES attempts.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                NOMINATIM_URL,
                params={"q": address, "format": "json", "limit": 1},
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            results = response.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
            return None
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
    return None


def geocode_addresses(addresses: list[str]) -> list[dict]:
    """
    Geocode a list of addresses, respecting the Nominatim rate limit.

    Returns a list of dicts: {address, lat, lon, success, error_message}.
    The first element is treated as the depot by the API layer.
    """
    results = []
    total = len(addresses)

    for i, address in enumerate(addresses):
        print(f"Geocoding {i + 1} of {total}: {address}")
        try:
            coords = geocode_address(address)
            if coords:
                results.append({
                    "address": address,
                    "lat": coords[0],
                    "lon": coords[1],
                    "success": True,
                    "error_message": None,
                })
            else:
                results.append({
                    "address": address,
                    "lat": None,
                    "lon": None,
                    "success": False,
                    "error_message": "No results returned by Nominatim",
                })
        except Exception as e:
            results.append({
                "address": address,
                "lat": None,
                "lon": None,
                "success": False,
                "error_message": str(e),
            })

        if i < total - 1:
            time.sleep(RATE_LIMIT_DELAY)

    successful = sum(1 for r in results if r["success"])
    print(f"Geocoding complete: {successful}/{total} addresses resolved")
    return results


if __name__ == "__main__":
    test_addresses = [
        "2158 N Milwaukee Ave Chicago IL 60647",
        "3600 N Clark St Chicago IL 60613",
        "1724 W Division St Chicago IL 60622",
    ]
    print("Testing geocoder with 3 Chicago addresses:\n")
    results = geocode_addresses(test_addresses)
    print()
    for r in results:
        if r["success"]:
            print(f"  OK  {r['address']}")
            print(f"       -> ({r['lat']:.6f}, {r['lon']:.6f})")
        else:
            print(f"  FAIL {r['address']}: {r['error_message']}")
