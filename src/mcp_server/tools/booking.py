"""
MCP Tool wrapper for Travliaq Booking Scrapper API.
Uses HTTP calls to the deployed Railway API instead of direct code imports.
"""
import httpx
from typing import Dict, Any, List, Optional
import os

# API Base URL - can be overridden via environment variable
BOOKING_API_URL = os.getenv(
    "BOOKING_API_URL", 
    "https://travliaq-booking-scrapper-production.up.railway.app"
)

# Default timeout for HTTP requests (3 minutes)
DEFAULT_TIMEOUT = 180.0


async def search_hotels(
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
) -> Dict[str, Any]:
    """
    Search for hotels on Booking.com via the REST API.
    
    Args:
        city: Destination city (e.g., "[City Name]")
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults (default: 2)
        children: Number of children (default: 0)
        rooms: Number of rooms (default: 1)
        max_results: Maximum number of results (default: 10)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        min_review_score: Minimum review score 0-10 (optional)
        star_rating: List of star ratings to filter (e.g., [3, 4, 5])
        
    Returns:
        Dict containing 'total_found' and list 'hotels' with search results
    """
    # Build query parameters
    params = {
        "city": city,
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "children": children,
        "rooms": rooms,
    }
    
    # Add optional filters
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    if min_review_score is not None:
        params["min_review_score"] = min_review_score
    if star_rating is not None:
        # Convert list to comma-separated string if needed by API
        params["star_rating"] = star_rating
    
    # Make HTTP request
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{BOOKING_API_URL}/api/v1/search_hotels",
            params=params
        )
        response.raise_for_status()
        return response.json()


async def get_hotel_details(
    hotel_id: str,
    country_code: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 2,
    rooms: int = 1,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific hotel from Booking.com via the REST API.
    
    Args:
        hotel_id: Hotel identifier or URL slug
        country_code: Country code for the URL (e.g., "fr", "gb", "us")
        checkin: Check-in date (YYYY-MM-DD, optional)
        checkout: Check-out date (YYYY-MM-DD, optional)
        adults: Number of adults (default: 2)
        rooms: Number of rooms (default: 1)
        
    Returns:
        Dict containing complete hotel details (description, amenities, rooms, reviews, etc.)
    """
    # Build query parameters
    params = {
        "hotel_id": hotel_id,
        "country_code": country_code,
        "adults": adults,
        "rooms": rooms,
    }
    
    # Add optional parameters
    if checkin:
        params["checkin"] = checkin
    if checkout:
        params["checkout"] = checkout
    
    # Make HTTP request
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.get(
            f"{BOOKING_API_URL}/api/v1/hotel_details",
            params=params
        )
        response.raise_for_status()
        return response.json()
