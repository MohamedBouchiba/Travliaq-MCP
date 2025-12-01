import math
from typing import Any, Dict, List, Optional

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
CLIMATE_URL = "https://climate-api.open-meteo.com/v1/climate"
AIRPORTS_DATA_URL = "https://raw.githubusercontent.com/mwgg/Airports/master/airports.json"
USER_AGENT = {"User-Agent": "travliaq-geo-tool/1.0"}
NO_PROXY = {"http": None, "https": None}

_AIRPORTS: List[Dict[str, Any]] | None = None


class GeoError(Exception):
    pass


def _http_get(url: str, params: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
    r = requests.get(
        url,
        params=params,
        headers=USER_AGENT,
        timeout=timeout,
        proxies=NO_PROXY,
    )
    r.raise_for_status()
    return r.json()


def geocode_text(query: str, count: int = 5, country: Optional[str] = None) -> List[Dict[str, Any]]:
    if not query:
        raise GeoError("query required")
    params = {"name": query, "count": max(1, min(count, 10))}
    if country:
        params["country"] = country
    data = _http_get(GEOCODE_URL, params)
    results = data.get("results") or []
    out: List[Dict[str, Any]] = []
    for item in results:
        out.append(
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "admin1": item.get("admin1"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
                "population": item.get("population"),
            }
        )
    return out


def _load_airports() -> List[Dict[str, Any]]:
    global _AIRPORTS
    if _AIRPORTS is not None:
        return _AIRPORTS
    data = requests.get(
        AIRPORTS_DATA_URL,
        headers=USER_AGENT,
        timeout=30,
        proxies=NO_PROXY,
    )
    data.raise_for_status()
    j = data.json()
    airports = []
    for _code, info in j.items():
        if not info.get("iata"):
            continue
        airports.append(
            {
                "name": info.get("name"),
                "iata": info.get("iata"),
                "icao": info.get("icao"),
                "lat": info.get("lat"),
                "lon": info.get("lon"),
                "city": info.get("city"),
                "country": info.get("country"),
            }
        )
    _AIRPORTS = airports
    return airports


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_airport(lat: float, lon: float) -> Dict[str, Any]:
    airports = _load_airports()
    best = None
    best_dist = float("inf")
    for ap in airports:
        try:
            d = _haversine_km(lat, lon, float(ap["lat"]), float(ap["lon"]))
        except Exception:
            continue
        if d < best_dist:
            best = ap
            best_dist = d
    if not best:
        raise GeoError("No airport found")
    out = dict(best)
    out["distance_km"] = round(best_dist, 2)
    return out


def nearest_airport_for_place(query: str, country: Optional[str] = None) -> Dict[str, Any]:
    results = geocode_text(query, count=1, country=country)
    if not results:
        raise GeoError("place not found")
    coords = results[0]
    ap = nearest_airport(coords["latitude"], coords["longitude"])
    ap["place"] = coords
    return ap


def climate_mean_temperature(lat: float, lon: float, start_date: str, end_date: str, timezone: str = "UTC") -> Dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean",
        "timezone": timezone,
    }
    data = _http_get(CLIMATE_URL, params)
    daily = data.get("daily", {})
    times = daily.get("time") or []
    temps = daily.get("temperature_2m_mean") or []
    records: List[Dict[str, Any]] = []
    for i, dt in enumerate(times):
        records.append({"date": dt, "tmean_c": temps[i] if i < len(temps) else None})
    avg = None
    if temps:
        vals = [t for t in temps if t is not None]
        if vals:
            avg = sum(vals) / len(vals)
    return {
        "coords": {"lat": lat, "lon": lon, "timezone": timezone},
        "period": {"start_date": start_date, "end_date": end_date},
        "average_temperature_c": avg,
        "daily": records,
    }


def climate_mean_temperature_for_place(query: str, start_date: str, end_date: str, country: Optional[str] = None,
                                       timezone: str = "auto") -> Dict[str, Any]:
    results = geocode_text(query, count=1, country=country)
    if not results:
        raise GeoError("place not found")
    coords = results[0]
    tz = coords.get("timezone") or timezone
    data = climate_mean_temperature(coords["latitude"], coords["longitude"], start_date, end_date, tz)
    data["place"] = coords
    return data


def place_overview(
    query: str,
    *,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timezone: str = "auto",
) -> Dict[str, Any]:
    """Return geocode, nearest airport, and optional climate block for a place name."""

    geo_results = geocode_text(query, count=1, country=country)
    if not geo_results:
        raise GeoError("place not found")

    place = geo_results[0]
    lat, lon = place["latitude"], place["longitude"]

    airport = nearest_airport(lat, lon)
    airport["place"] = {"name": place.get("name"), "country": place.get("country")}

    climate = None
    if start_date and end_date:
        tz = place.get("timezone") or timezone
        climate = climate_mean_temperature(lat, lon, start_date, end_date, tz)
        climate["place"] = place

    return {
        "place": place,
        "airport": airport,
        "climate": climate,
    }
