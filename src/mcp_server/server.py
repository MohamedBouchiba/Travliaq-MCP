from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
from fastmcp import FastMCP, Context
from .tools import weather as w
from .tools import image_generation as imgs


def create_mcp() -> FastMCP:
    mcp = FastMCP(
        name="TravliaqMCP",
        version="1.0.0"
    )

    @mcp.tool(name="weather.by_coords")
    async def weather_by_coords(
        lat: float, 
        lon: float, 
        timezone: str = "auto", 
        days: int = 7,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Prévisions et conditions actuelles par coordonnées. Retourne {mode, coords, current, daily[]}."""
        try:
            if ctx:
                await ctx.info(f"Fetching weather for coordinates: {lat}, {lon}")
            
            result = w.weather_by_coords_core(lat, lon, timezone, days)
            
            if ctx:
                await ctx.info("Weather data retrieved successfully")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Weather fetch failed: {str(e)}")
            raise

    @mcp.tool(name="weather.brief")
    async def weather_brief(
        lat: float, 
        lon: float, 
        timezone: str = "auto",
        ctx: Context = None
    ) -> str:
        """Résumé court: actuel + aperçu 7 jours."""
        try:
            if ctx:
                await ctx.info(f"Generating weather brief for {lat}, {lon}")
            
            result = w.weather_brief_from_coords_core(lat, lon, timezone)
            
            if ctx:
                await ctx.info("Weather brief generated")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Weather brief generation failed: {str(e)}")
            raise

    @mcp.tool(name="weather.by_period")
    async def weather_by_period(
        lat: float, 
        lon: float, 
        start_date: str, 
        end_date: str, 
        timezone: str = "auto",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Météo quotidienne sur une période AAAA-MM-JJ → AAAA-MM-JJ. Retourne {mode, coords, period, daily[]}."""
        try:
            if ctx:
                await ctx.info(f"Fetching weather for period {start_date} to {end_date}")
            
            result = w.weather_by_period_core(lat, lon, timezone, start_date, end_date)
            
            if ctx:
                await ctx.info("Period weather data retrieved")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Period weather fetch failed: {str(e)}")
            raise

    @mcp.tool(name="health.ping")
    async def ping(ctx: Context = None) -> str:
        """Vérifie que le serveur répond."""
        if ctx:
            await ctx.info("Ping received")
        return "pong"

    @mcp.tool(name="images.hero")
    async def images_hero(
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
        ctx: Context = None
    ) -> str:
        """Génère l'image HÉRO 1920x1080 et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        try:
            if ctx:
                await ctx.info(f"Generating hero image for {city}, {country}")
            
            result = imgs.tool_generate_hero(
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
            
            if ctx:
                await ctx.info("Hero image generated and uploaded successfully")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Hero image generation failed: {str(e)}")
            raise

    @mcp.tool(name="images.background")
    async def images_background(
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
        ctx: Context = None
    ) -> str:
        """Génère le BACKGROUND 1920x1080 et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        try:
            if ctx:
                await ctx.info(f"Generating background image for activity: {activity} in {city}, {country}")
            
            result = imgs.tool_generate_background(
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
            
            if ctx:
                await ctx.info("Background image generated and uploaded successfully")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Background image generation failed: {str(e)}")
            raise

    @mcp.tool(name="images.slider")
    async def images_slider(
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
        ctx: Context = None
    ) -> str:
        """Génère un SLIDER 800x600 (5:4 → crop 4:3) et l'upload dans Supabase/TRIPS/<trip_folder>/ ; retourne l'URL (string)."""
        try:
            if ctx:
                await ctx.info(f"Generating slider image: {subject} at {place}, {city}")
            
            result = imgs.tool_generate_slider(
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
            
            if ctx:
                await ctx.info("Slider image generated and uploaded successfully")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Slider image generation failed: {str(e)}")
            raise

    @mcp.tool(name="debug.ls")
    async def debug_ls(path: str = ".", ctx: Context = None) -> str:
        """Liste les fichiers dans un dossier (pour debug)."""
        import os
        try:
            if ctx:
                await ctx.info(f"Listing directory: {path}")
            
            p = Path(path).resolve()
            if not p.exists():
                error_msg = f"Path not found: {p}"
                if ctx:
                    await ctx.error(error_msg)
                return error_msg
            
            lines = [f"Listing {p}:"]
            for item in p.iterdir():
                type_char = "D" if item.is_dir() else "F"
                lines.append(f"[{type_char}] {item.name}")
            
            if ctx:
                await ctx.info(f"Listed {len(lines)-1} items")
            
            return "\n".join(lines)
        except Exception as e:
            error_msg = f"Error: {e}"
            if ctx:
                await ctx.error(f"Directory listing failed: {str(e)}")
            return error_msg

    from .resources import register_resources
    register_resources(mcp)

    return mcp


mcp = create_mcp()
