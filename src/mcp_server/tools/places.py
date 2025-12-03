import asyncio
import math
from typing import Any, Dict, List, Optional

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
CLIMATE_URL = "https://climate-api.open-meteo.com/v1/climate"
AIRPORTS_DATA_URL = "https://raw.githubusercontent.com/mwgg/Airports/master/airports.json"
USER_AGENT = {"User-Agent": "travliaq-geo-tool/1.0"}
NO_PROXY = {"http": None, "https": None}

_AIRPORTS: List[Dict[str, Any]] | None = None


class GeoError(Exception):
    pass


async def _http_get(
    url: str,
    params: Dict[str, Any],
    *,
    timeout: float = 15.0,
    retries: int = 2,
    backoff: float = 1.5,
) -> Dict[str, Any]:
    """HTTP GET with retries and detailed error messages."""
    last_err: Exception | None = None
    async with httpx.AsyncClient(
        headers=USER_AGENT,
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
        trust_env=False,
    ) as client:
        for attempt in range(retries + 1):
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                # ✅ VALIDATION: Vérifier que l'API a retourné vraiment des données
                if not data or (isinstance(data, dict) and not data.get("results")):
                    # Si aucun résultat, ce n'est pas une erreur côté serveur
                    return data if data else {}
                
                return data
            except httpx.HTTPStatusError as exc:
                # Erreurs HTTP 4xx/5xx
                status = exc.response.status_code
                last_err = GeoError(
                    f"API HTTP {status}: {exc.response.text[:200]}. "
                    f"URL: {url}. Params: {params}"
                )
                if attempt == retries:
                    break
                await asyncio.sleep(backoff**attempt)
            except httpx.TimeoutException as exc:
                # Timeout réseau
                last_err = GeoError(
                    f"Timeout après {timeout}s. "
                    f"L'API météo est peut-être surchargée. URL: {url}"
                )
                if attempt == retries:
                    break
                await asyncio.sleep(backoff**attempt)
            except Exception as exc:
                # Autres erreurs (réseau, JSON, etc.)
                last_err = GeoError(
                    f"Erreur inattendue: {type(exc).__name__}: {str(exc)}. "
                    f"URL: {url}"
                )
                if attempt == retries:
                    break
                await asyncio.sleep(backoff**attempt)
    
    # Lever l'erreur finale avec le message détaillé
    raise last_err if last_err else GeoError("Unknown error")


async def geocode_text(query: str, count: int = 5, country: Optional[str] = None) -> List[Dict[str, Any]]:
    """Géocode un nom de lieu en coordonnées GPS.
    
    Args:
        query: Nom du lieu (ex: "Paris", "Tokyo Tower", "Lisbon, Portugal")
        count: Nombre maximum de résultats (1-10)
        country: Code pays ISO-2 optionnel pour filtrer (ex: "FR", "PT", "JP")
    
    Returns:
        Liste de lieux avec name, country, latitude, longitude, etc.
        
    Raises:
        GeoError: Si le lieu n'est pas trouvé ou erreur API
    """
    if not query or not query.strip():
        raise GeoError(
            "❌ Query vide. "
            "Exemples valides: 'Paris', 'Tokyo Tower', 'Lisbon Portugal'"
        )
    
    query = query.strip()
    params = {"name": query, "count": max(1, min(count, 10))}
    if country:
        params["country"] = country.upper()[:2]  # Normaliser le code pays
    
    try:
        data = await _http_get(GEOCODE_URL, params)
    except GeoError:
        raise  # Relayer l'erreur avec le message détaillé
    
    results = data.get("results") or []
    
    # ✅ MEILLEUR MESSAGE: Si aucun résultat trouvé
    if not results:
        suggestion = (
            f"Lieu '{query}' introuvable. "
            f"Suggestions: Essayez un nom plus simple (ex: 'Lisbon' au lieu de 'Lisbonne'), "
            f"ou ajoutez le pays (ex: 'Lisbon, Portugal')"
        )
        if country:
            suggestion += f". Code pays utilisé: {country.upper()}"
        raise GeoError(suggestion)
    
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


async def _load_airports() -> List[Dict[str, Any]]:
    global _AIRPORTS
    if _AIRPORTS is not None:
        return _AIRPORTS
    j = await _http_get(AIRPORTS_DATA_URL, {}, timeout=30)
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


async def nearest_airport(lat: float, lon: float) -> Dict[str, Any]:
    airports = await _load_airports()
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


async def nearest_airport_for_place(query: str, country: Optional[str] = None) -> Dict[str, Any]:
    results = await geocode_text(query, count=1, country=country)
    if not results:
        raise GeoError("place not found")
    coords = results[0]
    ap = await nearest_airport(coords["latitude"], coords["longitude"])
    ap["place"] = coords
    return ap


async def climate_mean_temperature(lat: float, lon: float, start_date: str, end_date: str, timezone: str = "UTC") -> Dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean",
        "timezone": timezone,
    }
    data = await _http_get(CLIMATE_URL, params)
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


async def climate_mean_temperature_for_place(query: str, start_date: str, end_date: str, country: Optional[str] = None,
                                       timezone: str = "auto") -> Dict[str, Any]:
    results = await geocode_text(query, count=1, country=country)
    if not results:
        raise GeoError("place not found")
    coords = results[0]
    tz = coords.get("timezone") or timezone
    data = await climate_mean_temperature(coords["latitude"], coords["longitude"], start_date, end_date, tz)
    data["place"] = coords
    return data


async def place_overview(
    query: str,
    *,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timezone: str = "auto",
) -> Dict[str, Any]:
    """Return geocode, nearest airport, and optional climate block for a place name."""

    geo_results = await geocode_text(query, count=1, country=country)
    if not geo_results:
        raise GeoError("place not found")

    place = geo_results[0]
    lat, lon = place["latitude"], place["longitude"]

    airport = await nearest_airport(lat, lon)
    airport["place"] = {"name": place.get("name"), "country": place.get("country")}

    climate = None
    if start_date and end_date:
        tz = place.get("timezone") or timezone
        climate = await climate_mean_temperature(lat, lon, start_date, end_date, tz)
        climate["place"] = place

    return {
        "place": place,
        "airport": airport,
        "climate": climate,
    }
