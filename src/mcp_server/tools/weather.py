from __future__ import annotations
from typing import Any, Dict, List
import json, time, requests
from datetime import date, datetime

UA = {"User-Agent": "travliaq-weather-tool/1.1"}
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherError(Exception):
    pass


def _http_get(url: str, params: Dict[str, Any], timeout: int = 15, retries: int = 2,
              backoff: float = 1.5) -> requests.Response:
    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            if attempt == retries:
                break
            time.sleep(backoff ** attempt)
    raise WeatherError(str(last))


def _code_label(code: int) -> str:
    table = {
        0: "Ciel clair", 1: "Peu nuageux", 2: "Nuageux", 3: "Couvert",
        45: "Brouillard", 48: "Brouillard givrant",
        51: "Bruine légère", 53: "Bruine", 55: "Bruine forte",
        61: "Pluie faible", 63: "Pluie", 65: "Pluie forte",
        71: "Neige faible", 73: "Neige", 75: "Fortes chutes de neige",
        80: "Averses faibles", 81: "Averses", 82: "Averses fortes",
        95: "Orages", 96: "Orages avec grésil", 99: "Orages violents",
    }
    try:
        return table.get(int(code), f"wcode {code}")
    except Exception:
        return "n/a"


def _parse_ymd(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def _range_days(a: date, b: date) -> int:
    return (b - a).days + 1


def weather_by_coords_core(lat: float, lon: float, timezone: str = "auto", days: int = 7) -> Dict[str, Any]:
    if lat is None or lon is None:
        raise WeatherError("lat/lon requis")
    params = {
        "latitude": lat, "longitude": lon, "timezone": timezone or "auto",
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": max(1, min(int(days or 7), 16)),
    }
    r = _http_get(OPEN_METEO_URL, params=params)
    j = r.json()
    out: Dict[str, Any] = {
        "mode": "window",
        "coords": {"lat": lat, "lon": lon, "timezone": timezone or "auto"},
        "current": {
            "temperature_c": j.get("current", {}).get("temperature_2m"),
            "humidity_pct": j.get("current", {}).get("relative_humidity_2m"),
            "precip_mm": j.get("current", {}).get("precipitation"),
            "condition": _code_label(j.get("current", {}).get("weather_code", -1)),
        },
        "daily": []
    }
    d = j.get("daily", {})
    times: List[str] = d.get("time", []) or []
    tmins = (d.get("temperature_2m_min") or [])
    tmaxs = (d.get("temperature_2m_max") or [])
    precs = (d.get("precipitation_sum") or [])
    wcodes = (d.get("weather_code") or [])
    for i, dt in enumerate(times):
        out["daily"].append({
            "date": dt,
            "tmin_c": tmins[i] if i < len(tmins) else None,
            "tmax_c": tmaxs[i] if i < len(tmaxs) else None,
            "precip_mm": precs[i] if i < len(precs) else None,
            "condition": _code_label(wcodes[i] if i < len(wcodes) else -1),
        })
    return out


def weather_brief_from_coords_core(lat: float, lon: float, timezone: str = "auto") -> str:
    w = weather_by_coords_core(lat, lon, timezone)
    cur = w["current"]
    days = w["daily"]
    dry = sum(1 for d in days if (d["precip_mm"] or 0) == 0)
    tmins = [d["tmin_c"] for d in days if d["tmin_c"] is not None]
    tmaxs = [d["tmax_c"] for d in days if d["tmax_c"] is not None]
    tmin = min(tmins) if tmins else None
    tmax = max(tmaxs) if tmaxs else None
    return f"Actuel {cur['temperature_c']}°C, {cur['condition']} • 7j: {dry} j secs • Tmin {tmin}°C / Tmax {tmax}°C"


def weather_by_period_core(lat: float, lon: float, timezone: str, start_date: str, end_date: str) -> Dict[str, Any]:
    if lat is None or lon is None:
        raise WeatherError("lat/lon requis")
    start = _parse_ymd(start_date)
    end = _parse_ymd(end_date)
    if end < start:
        raise WeatherError("end_date < start_date")
    today = date.today()
    horizon_max = today.toordinal() + 16
    status = "ok"
    if start.toordinal() > horizon_max or end.toordinal() > horizon_max:
        status = "outside_forecast_window"
    params = {
        "latitude": lat, "longitude": lon, "timezone": timezone or "auto",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    try:
        r = _http_get(OPEN_METEO_URL, params=params)
        j = r.json()
    except Exception as e:
        return {
            "mode": "period",
            "coords": {"lat": lat, "lon": lon, "timezone": timezone or "auto"},
            "period": {"start_date": start.isoformat(), "end_date": end.isoformat(), "days": _range_days(start, end),
                       "status": "error"},
            "error": str(e),
            "daily": []
        }
    out: Dict[str, Any] = {
        "mode": "period",
        "coords": {"lat": lat, "lon": lon, "timezone": timezone or "auto"},
        "period": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "days": _range_days(start, end),
            "status": status
        },
        "current": {"note": "période demandée — pas de temps 'current' utile"},
        "daily": []
    }
    d = j.get("daily", {})
    times: List[str] = d.get("time", []) or []
    tmins = (d.get("temperature_2m_min") or [])
    tmaxs = (d.get("temperature_2m_max") or [])
    precs = (d.get("precipitation_sum") or [])
    wcodes = (d.get("weather_code") or [])
    for i, dt in enumerate(times):
        out["daily"].append({
            "date": dt,
            "tmin_c": tmins[i] if i < len(tmins) else None,
            "tmax_c": tmaxs[i] if i < len(tmaxs) else None,
            "precip_mm": precs[i] if i < len(precs) else None,
            "condition": _code_label(wcodes[i] if i < len(wcodes) else -1),
        })
    return out


def weather_by_coords_json(latlon_str: str) -> str:
    try:
        parts = [p.strip() for p in (latlon_str or "").split(",")]
        if len(parts) < 2:
            raise WeatherError("args attendus: 'lat, lon[, timezone]'")
        lat = float(parts[0]);
        lon = float(parts[1])
        tz = parts[2] if len(parts) >= 3 and parts[2] else "auto"
        return json.dumps(weather_by_coords_core(lat, lon, tz), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def weather_period_json(payload_str: str) -> str:
    try:
        data = json.loads(payload_str or "{}")
        lat = float(data["lat"]);
        lon = float(data["lon"])
        tz = str(data.get("timezone") or "auto")
        start_date = str(data["start_date"]);
        end_date = str(data["end_date"])
        return json.dumps(weather_by_period_core(lat, lon, tz, start_date, end_date), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
