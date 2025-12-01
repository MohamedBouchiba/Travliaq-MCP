import json
from datetime import date

import pytest
from PIL import Image

from mcp_server.tools import booking, flights, image_generation, places, weather


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):  # pragma: no cover - no exception path needed in tests
        return None

    def json(self):
        return self._payload


@pytest.mark.anyio
async def test_geocode_text_maps_fields(monkeypatch):
    payload = {
        "results": [
            {
                "name": "Paris",
                "country": "France",
                "admin1": "Ile-de-France",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timezone": "Europe/Paris",
                "population": 1000,
            }
        ]
    }

    async def fake_http_get(url, params, **kwargs):
        return payload

    monkeypatch.setattr(places, "_http_get", fake_http_get)

    results = await places.geocode_text("Paris", count=1)
    assert results == [
        {
            "name": "Paris",
            "country": "France",
            "admin1": "Ile-de-France",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "timezone": "Europe/Paris",
            "population": 1000,
        }
    ]


@pytest.mark.anyio
async def test_nearest_airport_for_place_combines_results(monkeypatch):
    async def fake_geocode(query, count=1, country=None):
        return [
            {
                "name": "Paris",
                "country": "France",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "timezone": "Europe/Paris",
            }
        ]

    async def fake_nearest(lat, lon):
        return {"name": "CDG", "iata": "CDG", "distance_km": 23.4}

    monkeypatch.setattr(places, "geocode_text", fake_geocode)
    monkeypatch.setattr(places, "nearest_airport", fake_nearest)

    result = await places.nearest_airport_for_place("Paris")
    assert result["place"]["name"] == "Paris"
    assert result["iata"] == "CDG"
    assert result["distance_km"] == 23.4


def test_weather_by_coords_core(monkeypatch):
    response = DummyResponse(
        {
            "current": {
                "temperature_2m": 12.5,
                "relative_humidity_2m": 80,
                "precipitation": 0.0,
                "weather_code": 1,
            },
            "daily": {
                "time": ["2024-01-01", "2024-01-02"],
                "temperature_2m_min": [5.0, 6.0],
                "temperature_2m_max": [10.0, 11.0],
                "precipitation_sum": [0.0, 1.2],
                "weather_code": [1, 2],
            },
        }
    )
    monkeypatch.setattr(weather, "_http_get", lambda *args, **kwargs: response)

    data = weather.weather_by_coords_core(10.0, 20.0, "UTC", days=2)
    assert data["current"]["temperature_c"] == 12.5
    assert data["daily"][0]["condition"] == "Peu nuageux"
    assert data["coords"]["timezone"] == "UTC"


def test_weather_by_period_core_handles_window(monkeypatch):
    today = date(2024, 1, 1)
    response = DummyResponse(
        {
            "daily": {
                "time": ["2024-01-01"],
                "temperature_2m_min": [5.0],
                "temperature_2m_max": [10.0],
                "precipitation_sum": [0.0],
                "weather_code": [0],
            }
        }
    )

    monkeypatch.setattr(weather, "date", type("D", (), {"today": staticmethod(lambda: today)}))
    monkeypatch.setattr(weather, "_http_get", lambda *args, **kwargs: response)

    result = weather.weather_by_period_core(1, 2, "UTC", "2024-01-01", "2024-01-01")
    assert result["period"]["status"] == "ok"
    assert result["daily"][0]["condition"] == "Ciel clair"


def test_get_flight_prices(monkeypatch):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params):
            return DummyResponse({"prices": {"2024-01-01": 123}, "from_cache": True, "stats": {"min": 123}})

    monkeypatch.setattr(flights.httpx, "AsyncClient", FakeClient)

    async def run():
        result = await flights.get_flight_prices("CDG", "JFK", "2024-01-01", "2024-01-10")
        assert result["prices"]["2024-01-01"] == 123
        assert result["from_cache"] is True

    import asyncio

    asyncio.run(run())


def test_booking_tools(monkeypatch):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params):
            if "search_hotels" in url:
                return DummyResponse({"total_found": 1, "hotels": [{"name": "Test Hotel"}]})
            return DummyResponse({"hotel": {"id": "123", "name": "Test Hotel"}})

    monkeypatch.setattr(booking.httpx, "AsyncClient", FakeClient)

    async def run():
        hotels = await booking.search_hotels("Paris", "2024-01-01", "2024-01-02")
        assert hotels["total_found"] == 1
        details = await booking.get_hotel_details("123", "fr")
        assert details["hotel"]["name"] == "Test Hotel"

    import asyncio

    asyncio.run(run())


def test_image_generation_builders_and_tool(monkeypatch):
    monkeypatch.setattr(image_generation, "_require_env", lambda: None)
    monkeypatch.setattr(image_generation, "_unique_id", lambda: "abc123")
    monkeypatch.setattr(image_generation, "_generate_image", lambda *args, **kwargs: Image.new("RGB", (800, 600), "red"))
    monkeypatch.setattr(image_generation, "_supabase_upload", lambda data, key, content_type: f"https://supabase.test/{key}")
    monkeypatch.setattr(image_generation.time, "time", lambda: 1700000000)

    folder = image_generation._build_folder("Mon Voyage", None)
    assert folder.startswith("mon-voyage-abc123")

    url = image_generation.tool_generate_slider(
        "statue",
        "square",
        "Paris",
        "France",
        fmt_site="WEBP",
        seed=42,
    )
    assert url.startswith("https://supabase.test/")
    assert "slider_1700000000" in url
