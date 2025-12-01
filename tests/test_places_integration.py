import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from mcp_server.tools import places  # noqa: E402


@pytest.fixture(autouse=True)
def mock_place_http(monkeypatch):
    sample_place = {
        "name": "Paris",
        "country": "France",
        "admin1": "Ile-de-France",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "timezone": "Europe/Paris",
        "population": 2148000,
    }
    climate_payload = {
        "daily": {
            "time": ["2024-06-01", "2024-06-02", "2024-06-03"],
            "temperature_2m_mean": [18.5, 20.1, 19.7],
        }
    }

    def fake_http_get(url: str, params: dict, timeout: int = 15):
        if "geocoding" in url:
            return {"results": [sample_place]}
        if "climate" in url:
            return climate_payload
        raise AssertionError(f"Unexpected URL {url}")

    def fake_load_airports():
        return [
            {
                "name": "Charles de Gaulle International Airport",
                "iata": "CDG",
                "icao": "LFPG",
                "lat": 49.0097,
                "lon": 2.5479,
                "city": "Paris",
                "country": "FR",
            },
            {
                "name": "Paris-Orly Airport",
                "iata": "ORY",
                "icao": "LFPO",
                "lat": 48.7233,
                "lon": 2.3794,
                "city": "Paris",
                "country": "FR",
            },
        ]

    monkeypatch.setattr(places, "_http_get", fake_http_get)
    monkeypatch.setattr(places, "_load_airports", fake_load_airports)


def test_geocode_text_returns_basic_place_data():
    results = places.geocode_text("Paris", count=1)
    assert results, "Expected at least one geocoding result"
    top = results[0]
    for field in ["name", "country", "latitude", "longitude", "timezone"]:
        assert field in top, f"Missing field {field} in geocode result"
    assert isinstance(top["latitude"], (int, float))
    assert isinstance(top["longitude"], (int, float))


def test_nearest_airport_for_place_finds_iata():
    airport = places.nearest_airport_for_place("Paris")
    assert airport.get("iata") == "ORY" or airport.get("iata") == "CDG"
    assert "distance_km" in airport and airport["distance_km"] > 0
    assert "place" in airport and airport["place"].get("name")


def test_climate_mean_temperature_for_place_has_average_and_daily():
    data = places.climate_mean_temperature_for_place(
        "Paris",
        start_date="2024-06-01",
        end_date="2024-06-07",
    )
    assert data.get("average_temperature_c") is not None, "Average temperature should be computed"
    daily = data.get("daily") or []
    assert daily, "Expected daily climate records"
    assert all("date" in r for r in daily)
    assert data["average_temperature_c"] == pytest.approx(19.433, rel=1e-3)


def test_place_overview_combines_geocode_airport_climate():
    overview = places.place_overview(
        "Paris",
        start_date="2024-06-01",
        end_date="2024-06-07",
    )
    assert overview.get("place"), "Place block missing"
    assert overview.get("airport", {}).get("iata"), "Nearest airport missing IATA"
    climate = overview.get("climate")
    assert climate and climate.get("average_temperature_c") is not None
    assert climate.get("place", {}).get("name")
