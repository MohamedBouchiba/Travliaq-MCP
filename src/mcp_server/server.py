from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
from fastmcp import FastMCP, Context
from .tools import weather as w
from .tools import image_generation as imgs
from .tools import booking as b
from .tools import flights as f
from .tools import places as g


def create_mcp() -> FastMCP:
    mcp = FastMCP(
        name="TravliaqMCP",
        version="1.0.0"
    )

    @mcp.tool(name="geo.text_to_place")
    async def geo_text_to_place(query: str, country: str | None = None, max_results: int = 5, ctx: Context = None):
        """Geocode un texte (ville/région) vers des coordonnées. Retourne une liste."""
        try:
            if ctx:
                await ctx.info(f"Geocoding query: {query}")
            return g.geocode_text(query, max_results, country)
        except Exception as e:
            if ctx:
                await ctx.error(f"Geocoding failed: {str(e)}")
            raise

    @mcp.tool(name="places.overview")
    async def places_overview(
        query: str,
        country: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        timezone: str = "auto",
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Retourne pour un lieu: géoloc, aéroport le plus proche, et climat (si dates fournies)."""
        try:
            if ctx:
                await ctx.info(f"Place overview for {query}")
            return g.place_overview(
                query,
                country=country,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
            )
        except Exception as e:
            if ctx:
                await ctx.error(f"Place overview failed: {str(e)}")
            raise

    @mcp.tool(name="airports.nearest")
    async def airports_nearest(city: str | None = None, country: str | None = None,
                               lat: float | None = None, lon: float | None = None, ctx: Context = None):
        """Trouve l'aéroport le plus proche d'une ville ou de coordonnées."""
        try:
            if lat is not None and lon is not None:
                if ctx:
                    await ctx.info(f"Searching nearest airport for coords {lat},{lon}")
                return g.nearest_airport(lat, lon)
            if not city:
                raise ValueError("city or lat/lon required")
            if ctx:
                await ctx.info(f"Searching nearest airport for {city}")
            return g.nearest_airport_for_place(city, country)
        except Exception as e:
            if ctx:
                await ctx.error(f"Airport lookup failed: {str(e)}")
            raise

    @mcp.tool(name="climate.avg_temperature")
    async def climate_avg_temperature(city: str | None = None, start_date: str = "", end_date: str = "",
                                      country: str | None = None, lat: float | None = None,
                                      lon: float | None = None, timezone: str = "auto",
                                      ctx: Context = None):
        """Température moyenne quotidienne pour une période (date AAAA-MM-JJ)."""
        try:
            if lat is not None and lon is not None:
                if ctx:
                    await ctx.info(f"Climate stats by coords {lat},{lon}")
                return g.climate_mean_temperature(lat, lon, start_date, end_date, timezone)
            if not city:
                raise ValueError("city or lat/lon required")
            if ctx:
                await ctx.info(f"Climate stats for {city}")
            return g.climate_mean_temperature_for_place(city, start_date, end_date, country, timezone)
        except Exception as e:
            if ctx:
                await ctx.error(f"Climate stats failed: {str(e)}")
            raise

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
        style_preset: Optional[str] = None,
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
                style_preset=style_preset,
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
        style_preset: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        fmt: Literal["JPEG", "WEBP"] = "JPEG",
        max_kb: int = 400,
        quality: int = 80,
        shots: int = 1,
        seed: int = 0,
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
                style_preset=style_preset,
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
        style_preset: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        fmt_site: Literal["WEBP", "JPEG"] = "WEBP",
        max_kb: int = 150,
        quality: int = 80,
        shots: int = 1,
        seed: int = 0,
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
                style_preset=style_preset,
                trip_name=trip_name,
                trip_folder=trip_folder,
                width=width,
                height=height,
                fmt_site=fmt_site,
                max_kb=max_kb,
                quality=quality,
                shots=shots,
                seed=seed,
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
        start_date: str,
        end_date: str,
        force_refresh: bool = False,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Scrape les prix des vols sur Google Flights pour une période donnée.
        
        Args:
            origin: Code IATA de l'aéroport de départ (ex: "CDG").
            destination: Code IATA de l'aéroport d'arrivée (ex: "JFK").
            start_date: Date de début de recherche (YYYY-MM-DD).
            end_date: Date de fin de recherche (YYYY-MM-DD).
            force_refresh: Forcer le re-scraping même si en cache (défaut: False).
            
        Returns:
            Dictionnaire contenant:
            - stats: {min, max, avg, count}
            - prices: Dictionnaire {date: prix} pour chaque jour trouvé.
            - from_cache: bool - Si les données viennent du cache
        """
        try:
            if ctx:
                await ctx.info(f"Scraping flight prices from {origin} to {destination} ({start_date} to {end_date})")
            
            result = await f.get_flight_prices(
                origin=origin,
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh
            )
            
            if ctx:
                price_count = len(result.get('prices', {}))
                await ctx.info(f"Found {price_count} flight prices")
            
            return result
        except Exception as e:
            if ctx:
                await ctx.error(f"Flight scraping failed: {str(e)}")
            raise

    from .resources import register_resources
    register_resources(mcp)

    return mcp


mcp = create_mcp()
