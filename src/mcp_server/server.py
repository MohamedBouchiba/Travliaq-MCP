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

    @mcp.tool(name="geo.city")
    async def geo_city(query: str, country: str | None = None, max_results: int = 5, ctx: Context = None):
        """🏙️ Géocode une VILLE ou un PAYS en coordonnées GPS.
        
        📋 **QUAND UTILISER:**
        - Pour obtenir GPS d'une ville: "Paris", "Tokyo", "Lisbon"
        - Pour une région/province: "Provence, France", "Hokkaido, Japan"
        - Pour un pays entier: "Portugal", "Japan", "Belgium"
        - Avant d'appeler weather, flights, climate, ou airports tools
        
        ✅ **EXEMPLES D'UTILISATION:**
        
        1. Simple ville:
           geo.city(query="Tokyo")
           → {"name": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503}
        
        2. Ville + pays (RECOMMANDÉ pour éviter ambiguïté):
           geo.city(query="Lisbon, Portugal")
           → {"name": "Lisbon", "country": "Portugal", "latitude": 38.7223, "longitude": -9.1393}
        
        3. Avec filtre pays (ISO-2):
           geo.city(query="Springfield", country="US", max_results=3)
           → Limite résultats aux USA uniquement
        
        ⚠️ **NE PAS UTILISER POUR:**
        - ❌ Monuments (ex: "Atomium") → Utiliser geo.place
        - ❌ Attractions spécifiques (ex: "Tokyo Skytree") → Utiliser geo.place
        - ❌ Restaurants, musées, POIs → Utiliser geo.place
        
        📤 **FORMAT DE RETOUR:**
        [
          {
            "name": "Lisbon",
            "country": "Portugal",
            "admin1": "Lisboa",
            "latitude": 38.7223,
            "longitude": -9.1393,
            "timezone": "Europe/Lisbon",
            "population": 517802
          }
        ]
        
        💡 **ASTUCE:** Utilise TOUJOURS le premier résultat [0] sauf si tu cherches parmi plusieurs villes homonymes.
        """
        try:
            if ctx:
                await ctx.info(f"🏙️ Geocoding ville/pays: '{query}'" + (f" (country={country})" if country else ""))
            results = await g.geocode_text(query, max_results, country)
            if ctx:
                await ctx.info(f"✅ Trouvé {len(results)} résultat(s)")
            return results
        except Exception as e:
            error_msg = f"❌ Geocoding ville/pays échoué pour '{query}': {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise Exception(error_msg) from e

    @mcp.tool(name="geo.place")
    async def geo_place(query: str, country: str | None = None, max_results: int = 3, ctx: Context = None):
        """🎯 Géocode un LIEU SPÉCIFIQUE (monument, attraction, POI, restaurant) via OpenStreetMap.
        
        📋 **QUAND UTILISER:**
        - Pour obtenir GPS EXACT d'un monument: "Atomium, Brussels"
        - Pour une attraction touristique: "Tokyo Skytree, Tokyo"
        - Pour un musée: "Louvre Museum, Paris"
        - Pour un temple/sanctuaire: "Senso-ji Temple, Asakusa, Tokyo"
        - Pour un restaurant célèbre: "Sukiyabashi Jiro, Ginza, Tokyo"
        - Pour tout POI (point d'intérêt) spécifique
        
        ✅ **EXEMPLES ULTRA-PRÉCIS:**
        
        1. Monument avec ville et pays:
           geo.place(query="Atomium, Laken, Brussels, Belgium")
           → GPS EXACT: {lat: 50.8948, lon: 4.3418}
           → "display_name": "Atomium, Laken, Bruxelles-Capitale, Belgique"
        
        2. Attraction touristique avec quartier:
           geo.place(query="Tokyo Skytree, Sumida, Tokyo, Japan")
           → GPS EXACT: {lat: 35.7101, lon: 139.8107}
        
        3. Temple avec quartier:
           geo.place(query="Senso-ji Temple, Asakusa, Tokyo")
           → GPS EXACT du temple
        
        4. Tour/Monument célèbre:
           geo.place(query="Eiffel Tower, Paris, France")
           → GPS EXACT de la tour
        
        5. Restaurant étoilé:
           geo.place(query="Sukiyabashi Jiro, Ginza, Tokyo")
           → GPS EXACT du restaurant
        
        💡 **ASTUCES POUR MAXIMUM DE PRÉCISION:**
        - ✅ Inclure le quartier: "Senso-ji, Asakusa, Tokyo" (meilleur que juste "Senso-ji, Tokyo")
        - ✅ Inclure le pays: "Atomium, Brussels, Belgium" (évite confusion)
        - ✅ Nom complet: "Tokyo Skytree" au lieu de "Skytree"
        - ✅ Nom local + anglais: "Tour Eiffel" ou "Eiffel Tower" marchent tous les deux
        
        📤 **FORMAT DE RETOUR:**
        [
          {
            "name": "Atomium",
            "display_name": "Atomium, Laken, Bruxelles-Capitale, 1020, Belgique",
            "latitude": 50.8948,
            "longitude": 4.3418,
            "type": "attraction",
            "category": "tourism",
            "importance": 0.801,
            "osm_id": 123456789,
            "address": {...}
          }
        ]
        
        ⚠️ **LIMITATIONS:**
        - Délai de 1 seconde entre chaque requête (politique Nominatim OSM)
        - Si lieu introuvable, vérifier l'orthographe ou simplifier la query
        
        🔄 **SI ÉCHEC:**
        - Essaye sans le pays: "Atomium, Brussels" au lieu de "Atomium, Brussels, Belgium"
        - Essaye nom anglais: "Eiffel Tower" au lieu de "Tour Eiffel"
        - Essaye nom local: "東京スカイツリー" ou "Tokyo Skytree" marchent
        """
        try:
            if ctx:
                await ctx.info(f"🎯 Geocoding lieu spécifique: '{query}'" + (f" (country={country})" if country else ""))
            results = await g.geocode_specific_place(query, country, max_results)
            if ctx:
                await ctx.info(f"✅ Trouvé {len(results)} lieu(x) spécifique(s)")
            return results
        except Exception as e:
            error_msg = f"❌ Geocoding lieu spécifique échoué pour '{query}': {str(e)}"
            if ctx:
                await ctx.error(error_msg)
            raise Exception(error_msg) from e


    @mcp.tool(name="places.overview")
    async def places_overview(
        query: str,
        country: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        timezone: str = "auto",
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Enchaîne géocodage + aéroport proche (+ climat optionnel).

        - Fournir `query` (+ `country` éventuel). Ajoute un bloc `climate` si `start_date`/`end_date` (AAAA-MM-JJ) sont fournis.
        - Retour : {place, nearest_airport, climate?} pour résumer rapidement un lieu.
        """
        try:
            if ctx:
                await ctx.info(f"Place overview for {query}")
            return await g.place_overview(
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
        """Trouve l'aéroport le plus proche d'une ville ou de coordonnées.

        - Priorité : passer `lat` + `lon` si déjà connus ; sinon `city` (+ `country` optionnel) pour chercher et inclure le bloc `place`.
        - Retour : aéroport (IATA/ICAO, distance_km) et, pour la recherche ville, le lieu correspondant.
        """
        try:
            if lat is not None and lon is not None:
                if ctx:
                    await ctx.info(f"Searching nearest airport for coords {lat},{lon}")
                return await g.nearest_airport(lat, lon)
            if not city:
                raise ValueError("city or lat/lon required")
            if ctx:
                await ctx.info(f"Searching nearest airport for {city}")
            return await g.nearest_airport_for_place(city, country)
        except Exception as e:
            if ctx:
                await ctx.error(f"Airport lookup failed: {str(e)}")
            raise

    @mcp.tool(name="climate.avg_temperature")
    async def climate_avg_temperature(city: str | None = None, start_date: str = "", end_date: str = "",
                                      country: str | None = None, lat: float | None = None,
                                      lon: float | None = None, timezone: str = "auto",
                                      ctx: Context = None):
        """Température moyenne quotidienne pour une période.

        - Dates au format AAAA-MM-JJ. Préférer `lat`/`lon` ; sinon `city` (+ `country`).
        - Retour : `average_temperature_c` et `daily[]`; `period.status` précise si la fenêtre dépasse les prévisions.
        """
        try:
            if lat is not None and lon is not None:
                if ctx:
                    await ctx.info(f"Climate stats by coords {lat},{lon}")
                return await g.climate_mean_temperature(lat, lon, start_date, end_date, timezone)
            if not city:
                raise ValueError("city or lat/lon required")
            if ctx:
                await ctx.info(f"Climate stats for {city}")
            return await g.climate_mean_temperature_for_place(city, start_date, end_date, country, timezone)
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
        """Prévisions + conditions actuelles par coordonnées.

        - Arguments : `lat`/`lon` obligatoires ; `days` (<=16) et `timezone` optionnel.
        - Retour : {mode, coords, current, daily[]} incluant températures, humidité, précipitations.
        """
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
        """Résumé texte court météo pour 7 jours.

        - Fournir `lat`/`lon`; `timezone` optionnel (auto par défaut).
        - Retour : phrase compacte (« Actuel X°C ... + tendance 7j ») prête à répondre à l'utilisateur.
        """
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
        """Météo quotidienne sur une période AAAA-MM-JJ → AAAA-MM-JJ.

        - Fournir `lat`/`lon` + `start_date`/`end_date`; `timezone` optionnel.
        - Retour : {mode, coords, period, daily[]}. Si la période dépasse la fenêtre de prévision (~16j), `period.status` = `outside_forecast_window`.
        """
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
        """Ping simple pour vérifier la disponibilité ; répond "pong"."""
        if ctx:
            await ctx.info("Ping received")
        return "pong"

    @mcp.tool(name="images.hero")
    async def images_hero(
        trip_code: str,
        prompt: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Génère l'image principale (Hero) du voyage. Format 1920x1080.

        Cette image est la bannière principale. Elle doit être spectaculaire, inspirante et de très haute qualité.
        
        Args:
            trip_code: Le code unique du voyage (ex: "JP_TOKYO_2025"). Sert à organiser les fichiers dans le stockage.
            prompt: Description VISUELLE détaillée de la scène.
                    DOIT inclure le LIEU (Ville, Pays) et l'AMBIANCE générale du voyage.
                    EXEMPLE: "Vue panoramique époustouflante du Mont Fuji au lever du soleil, Japon, cerisiers en fleurs au premier plan, lumière dorée."
        
        Returns:
            Dict contenant l'URL de l'image générée.
        """
        try:
            if ctx:
                await ctx.info(f"Generating hero image (Trip: {trip_code})")

            url = imgs.generate_hero(trip_code, prompt)

            if ctx:
                await ctx.info(f"Hero image generated: {url}")

            return {
                "url": url,
                "type": "hero",
                "usage": "main_image"
            }
        except Exception as e:
            if ctx:
                await ctx.error(f"Hero image generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate hero image: {str(e)}")

    @mcp.tool(name="images.background")
    async def images_background(
        trip_code: str,
        prompt: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Génère une image d'arrière-plan (1920x1080).

        Cette image servira de fond pour une étape. Elle sera affichée avec de l'opacité.
        
        Args:
            trip_code: Le code unique du voyage.
            prompt: Description du LIEU SPÉCIFIQUE de l'étape et de l'ambiance.
                    EXEMPLE: "Temple Senso-ji à Tokyo, atmosphère spirituelle, texture de bois rouge et lanternes, flou artistique."
                    IMPORTANT: L'image doit être sombre ou peu contrastée pour servir de fond.
            
        Returns:
            Dict contenant l'URL de l'image générée.
        """
        try:
            if ctx:
                await ctx.info(f"Generating background image (Trip: {trip_code})")

            url = imgs.generate_background(trip_code, prompt)

            if ctx:
                await ctx.info(f"Background image generated: {url}")

            return {
                "url": url,
                "type": "background",
                "usage": "step_main_image"
            }
        except Exception as e:
            if ctx:
                await ctx.error(f"Background image generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate background image: {str(e)}")

    @mcp.tool(name="images.slider")
    async def images_slider(
        trip_code: str,
        prompt: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """Génère une image illustrative pour un carrousel (800x600).

        Utilisé pour illustrer des activités spécifiques ou des détails.
        
        Args:
            trip_code: Le code unique du voyage.
            prompt: Description de l'activité ou du lieu spécifique.
                    DOIT inclure le LIEU.
                    EXEMPLE: "Gros plan sur un bol de ramen fumant à Tokyo, éclairage chaleureux."
            
        Returns:
            Dict contenant l'URL de l'image générée.
        """
        try:
            if ctx:
                await ctx.info(f"Generating slider image (Trip: {trip_code})")
            
            url = imgs.generate_slider(trip_code, prompt)
            
            if ctx:
                await ctx.info(f"Slider image generated: {url}")
            
            return {
                "url": url,
                "type": "slider",
                "usage": "carousel"
            }
        except Exception as e:
            if ctx:
                await ctx.error(f"Slider image generation failed: {str(e)}")
            raise

    @mcp.tool(name="debug.ls")
    async def debug_ls(path: str = ".", ctx: Context = None) -> str:
        """Liste un dossier (debug uniquement). Retourne une chaîne multi-lignes."""
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
        """Recherche Booking.com avec filtres.

        - Requis : `city`, `checkin`, `checkout` (AAAA-MM-JJ). Optionnels : `adults`, `children`, `rooms`, `max_results`, filtres de prix/note (`min_price`, `max_price`, `min_review_score`, `star_rating`).
        - Retour : liste d'hôtels, `total_found`, et champs prix/notes prêts à trier côté agent.
        """
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
        """Détails Booking.com pour un hôtel.

        - Requis : `hotel_id` ou slug Booking. Optionnels : `checkin`/`checkout` (AAAA-MM-JJ), `adults`, `rooms`, `country_code` pour choisir le domaine.
        - Retour : description, équipements, chambres, photos et avis consolidés.
        """
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
