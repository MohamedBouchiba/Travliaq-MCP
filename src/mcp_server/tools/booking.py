import sys
import os
from pathlib import Path
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Add Booking Scrapper to path
# Assuming the directory structure is:
# e:\CrewTravliaq\Travliaq-MCP\src\mcp_server\tools\booking.py
# We need to reach e:\CrewTravliaq\Travliaq-Booking-Scrapper
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent  # src -> mcp_server -> tools -> booking.py -> ...
BOOKING_SCRAPPER_PATH = PROJECT_ROOT / "Travliaq-Booking-Scrapper"

if str(BOOKING_SCRAPPER_PATH) not in sys.path:
    sys.path.append(str(BOOKING_SCRAPPER_PATH))

try:
    from src.scrapers.search import SearchScraper
    from src.scrapers.details import DetailsScraper
    from src.models.search import HotelSearchRequest, PropertyType
    from src.models.hotel import HotelDetailsRequest
except ImportError as e:
    # This might happen if dependencies are missing in the MCP environment
    # For now we assume the environment is set up correctly or we will handle it at runtime
    print(f"Warning: Could not import Booking Scrapper modules: {e}")


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
    star_rating: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Search for hotels using the Booking Scrapper.
    
    Args:
        city: City name to search for
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults
        children: Number of children
        rooms: Number of rooms
        max_results: Maximum number of results to return
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_review_score: Minimum review score (0-10)
        star_rating: List of star ratings to filter by (e.g. [3, 4, 5])
    """
    try:
        # Convert dates
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date()
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date()
        
        request = HotelSearchRequest(
            city=city,
            checkin=checkin_date,
            checkout=checkout_date,
            adults=adults,
            children=children,
            rooms=rooms,
            max_results=max_results,
            min_price=min_price,
            max_price=max_price,
            min_review_score=min_review_score,
            star_rating=star_rating
        )
        
        scraper = SearchScraper()
        result = await scraper.search_hotels(request)
        
        # Convert result to dict for JSON serialization
        hotels_data = []
        for hotel in result.hotels:
            hotels_data.append({
                "hotel_id": hotel.hotel_id,
                "name": hotel.name,
                "price": hotel.price,
                "currency": hotel.currency,
                "review_score": hotel.review_score,
                "url": hotel.url
            })
            
        return {
            "total_found": result.total_found,
            "hotels": hotels_data,
            "search_params": {
                "city": city,
                "checkin": checkin,
                "checkout": checkout
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


async def get_hotel_details(
    hotel_id: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 2,
    rooms: int = 1,
    country_code: str = "fr"
) -> Dict[str, Any]:
    """
    Get detailed information about a specific hotel.
    
    Args:
        hotel_id: The hotel ID or URL part
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        adults: Number of adults
        rooms: Number of rooms
        country_code: Country code for URL construction (default: fr)
    """
    try:
        # Convert dates if provided
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d").date() if checkin else None
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d").date() if checkout else None
        
        request = HotelDetailsRequest(
            hotel_id=hotel_id,
            checkin=checkin_date,
            checkout=checkout_date,
            adults=adults,
            rooms=rooms,
            country_code=country_code
        )
        
        scraper = DetailsScraper()
        async with scraper:
            details, reviews = await scraper.get_hotel_details(request)
            
        # Convert to dict
        details_dict = {
            "hotel_id": details.hotel_id,
            "name": details.name,
            "address": details.address.full_address if details.address else None,
            "coordinates": {
                "lat": details.address.latitude,
                "lon": details.address.longitude
            } if details.address else None,
            "description": details.description,
            "stars": details.star_rating,
            "review_score": details.review_score,
            "review_count": details.review_count,
            "amenities": details.amenities,
            "popular_amenities": details.popular_amenities,
            "images": details.images[:10], # Limit images
            "main_image": details.main_image,
            "cheapest_price": details.cheapest_price,
            "rooms": [
                {
                    "type": r.room_type,
                    "price": r.price,
                    "capacity": r.capacity,
                    "bed": r.bed_type,
                    "cancellation": r.cancellation_policy
                } for r in details.rooms
            ]
        }
        
        return details_dict
        
    except Exception as e:
        return {"error": str(e)}
