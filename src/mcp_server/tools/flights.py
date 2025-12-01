"""
MCP Tool wrapper for Travliaq Google Flights Scrapper API.
Uses HTTP calls to the deployed Railway API instead of direct code imports.
"""
import httpx
from typing import Dict, Any
from datetime import datetime, timedelta
import os

# API Base URL - can be overridden via environment variable
FLIGHTS_API_URL = os.getenv(
    "FLIGHTS_API_URL",
    "https://travliaq-google-flights-scrapper-production.up.railway.app"
)

# Default timeout for HTTP requests (3 minutes)
DEFAULT_TIMEOUT = 180.0


async def get_flight_prices(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Get flight prices from Google Flights for a specific date range via the REST API.
    
    Args:
        origin: IATA code of departure airport (e.g., "CDG")
        destination: IATA code of arrival airport (e.g., "JFK")
        start_date: Start date for the search (YYYY-MM-DD)
        end_date: End date for the search (YYYY-MM-DD)
        force_refresh: Force re-scraping even if cached data exists (default: False)
        
    Returns:
        Dict containing:
        - stats: {min, max, avg, count} - Price statistics
        - prices: Dict[date, price] - Prices for each day in the range
        - from_cache: bool - Whether data was retrieved from cache
    """
    # Build query parameters
    params = {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "start_date": start_date,
        "end_date": end_date,
        "force_refresh": force_refresh,
    }
    
    # Make HTTP request
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{FLIGHTS_API_URL}/api/v1/calendar-prices",
            params=params
        )
        response.raise_for_status()
        return response.json()
