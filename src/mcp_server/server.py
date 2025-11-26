from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
from fastmcp import FastMCP
from .tools import weather as w
from .tools import image_generation as imgs


def create_mcp() -> FastMCP:
    mcp = FastMCP(name="TravliaqMCP")

    @mcp.tool(name="weather.by_coords")
    def weather_by_coords(lat: float, lon: float, timezone: str = "auto", days: int = 7) -> Dict[str, Any]:
        """Prévisions et conditions actuelles par coordonnées. Retourne {mode, coords, current, daily[]}."""
        return w.weather_by_coords_core(lat, lon, timezone, days)

    @mcp.tool(name="weather.brief")
    def weather_brief(lat: float, lon: float, timezone: str = "auto") -> str:
        """Résumé court: actuel + aperçu 7 jours."""
        return w.weather_brief_from_coords_core(lat, lon, timezone)

    @mcp.tool(name="weather.by_period")
    def weather_by_period(lat: float, lon: float, start_date: str, end_date: str, timezone: str = "auto") -> Dict[str, Any]:
        """Météo quotidienne sur une période AAAA-MM-JJ → AAAA-MM-JJ. Retourne {mode, coords, period, daily[]}."""
        return w.weather_by_period_core(lat, lon, timezone, start_date, end_date)

    @mcp.tool(name="health.ping")
    def ping() -> str:
        """Vérifie que le serveur répond."""
        return "pong"

    @mcp.tool(name="images.hero")
    def images_hero(
        city: str,
        country: str,
        theme_keywords: Optional[List[str]] = None,
        trip_name: Optional[str] = None,
        trip_folder: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        fmt: Literal["JPEG", "WEBP"] = "JPEG",
        max_kb: int = 500,
        quality: int = 85,
        shots: int = 1,
        seed: int = 0,
    ) -> str:
        """Génère l'image HÉRO 1920x1080 et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        return imgs.tool_generate_hero(
            city=city,
            country=country,
            theme_keywords=theme_keywords,
            trip_name=trip_name,
            trip_folder=trip_folder,
            width=width,
            height=height,
            fmt=fmt,
            max_kb=max_kb,
            quality=quality,
            shots=shots,
            seed=seed,
        )

    @mcp.tool(name="images.background")
    def images_background(
        activity: str,
        city: str,
        country: str,
        mood_keywords: Optional[List[str]] = None,
        trip_name: Optional[str] = None,
        trip_folder: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        fmt: Literal["JPEG", "WEBP"] = "JPEG",
        max_kb: int = 400,
        quality: int = 80,
        shots: int = 1,
        seed: int = 0,
        style_preset: str = "photographic",
    ) -> str:
        """Génère le BACKGROUND 1920x1080 et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        return imgs.tool_generate_background(
            activity=activity,
            city=city,
            country=country,
            mood_keywords=mood_keywords,
            trip_name=trip_name,
            trip_folder=trip_folder,
            width=width,
            height=height,
            fmt=fmt,
            max_kb=max_kb,
            quality=quality,
            shots=shots,
            seed=seed,
            style_preset=style_preset,
        )

    @mcp.tool(name="images.slider")
    def images_slider(
        subject: str,
        place: str,
        city: str,
        country: str,
        trip_name: Optional[str] = None,
        trip_folder: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        fmt_site: Literal["WEBP", "JPEG"] = "WEBP",
        max_kb: int = 150,
        quality: int = 80,
        shots: int = 1,
        seed: int = 0,
        style_preset: str = "photographic",
    ) -> str:
        """Génère un SLIDER 800x600 (5:4 → crop 4:3) et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        return imgs.tool_generate_slider(
            subject=subject,
            place=place,
            city=city,
            country=country,
            trip_name=trip_name,
            trip_folder=trip_folder,
            width=width,
            height=height,
            fmt_site=fmt_site,
            max_kb=max_kb,
            quality=quality,
            shots=shots,
            seed=seed,
            style_preset=style_preset,
        )

    @mcp.tool(name="debug.ls")
    def debug_ls(path: str = ".") -> str:
        """Liste les fichiers dans un dossier (pour debug)."""
        import os
        try:
            p = Path(path).resolve()
            if not p.exists():
                return f"Path not found: {p}"
            
            lines = [f"Listing {p}:"]
            for item in p.iterdir():
                type_char = "D" if item.is_dir() else "F"
                lines.append(f"[{type_char}] {item.name}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    from .resources import register_resources
    register_resources(mcp)

    return mcp


mcp = create_mcp()
