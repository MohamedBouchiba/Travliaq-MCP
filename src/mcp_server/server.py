from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
from fastmcp import FastMCP, Context
from .tools import weather as w
from .tools import image_generation as imgs
from .tools import booking as b
from .tools import flights as f


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


    @mcp.tool(name="booking.search")
    async def booking_search(
        city: str,
        checkin: str,
        checkout: str,
        adults: int = 2,
        children: int = 0,
        rooms: int = 1,
        max_results: int = 10,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_review_score: Optional[float] = None,
        star_rating: Optional[List[int]] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Search for hotels on Booking.com."""
        try:
            if ctx:
                await ctx.info(f"Searching hotels in {city} from {checkin} to {checkout}")
            
            result = await b.search_hotels(
                city=city,
                checkin=checkin,
                checkout=checkout,
                adults=adults,
                children=children,
                rooms=rooms,
                max_results=max_results,
                min_price=min_price,
                max_price=max_price,
                min_review_score=min_review_score,
                star_rating=star_rating
            )
            
            if ctx:
                await ctx.info(f"Found {result.get('total_found', 0)} hotels")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Booking search failed: {str(e)}")
            raise

    @mcp.tool(name="booking.details")
    async def booking_details(
        hotel_id: str,
        checkin: Optional[str] = None,
        checkout: Optional[str] = None,
        adults: int = 2,
        rooms: int = 1,
        country_code: str = "fr",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get detailed information about a specific hotel from Booking.com."""
        try:
            if ctx:
                await ctx.info(f"Fetching details for hotel {hotel_id}")
            
            result = await b.get_hotel_details(
                hotel_id=hotel_id,
                checkin=checkin,
                checkout=checkout,
                adults=adults,
                rooms=rooms,
                country_code=country_code
            )
            
            if ctx:
                await ctx.info("Hotel details retrieved")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Booking details failed: {str(e)}")
            raise

    @mcp.tool(name="flights.prices")
    async def flights_prices(
        origin: str,
        destination: str,
        months_ahead: int = 3,
        headless: bool = True,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Get flight prices from Google Flights calendar."""
        try:
            if ctx:
                await ctx.info(f"Scraping flight prices from {origin} to {destination} for {months_ahead} months")
            
            result = await f.get_flight_prices(
                origin=origin,
                destination=destination,
                months_ahead=months_ahead,
                headless=headless
            )
            
            if ctx:
                await ctx.info("Flight prices retrieved")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Flight scraping failed: {str(e)}")
            raise

    from .resources import register_resources
    register_resources(mcp)

    return mcp


mcp = create_mcp()
