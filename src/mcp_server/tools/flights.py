import sys
import os
from pathlib import Path
import asyncio
from typing import Optional, Dict, Any

# Add Google Flights Scrapper to path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent
FLIGHTS_SCRAPPER_PATH = PROJECT_ROOT / "Travliaq-Google-Flights-Scrapper"

if str(FLIGHTS_SCRAPPER_PATH) not in sys.path:
    sys.path.append(str(FLIGHTS_SCRAPPER_PATH))

try:
    from src.scrapers.calendar_scraper import CalendarScraper
except ImportError as e:
    print(f"Warning: Could not import Google Flights Scrapper modules: {e}")


async def get_flight_prices(
    origin: str,
    destination: str,
    months_ahead: int = 3,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Get flight prices from Google Flights calendar for the next N months.
    
    Args:
        origin: IATA code for origin airport (e.g. CDG)
        destination: IATA code for destination airport (e.g. JFK)
        months_ahead: Number of months to scrape (default: 3)
        headless: Whether to run browser in headless mode (default: True)
    """
    try:
        def _run_scraper():
            scraper = CalendarScraper(headless=headless)
            return scraper.scrape(
                origin=origin,
                destination=destination,
                months_ahead=months_ahead
            )

        # Run synchronous Selenium scraper in a separate thread
        prices = await asyncio.to_thread(_run_scraper)
        
        # Calculate statistics
        price_values = list(prices.values())
        stats = {}
        if price_values:
            stats = {
                "min": min(price_values),
                "max": max(price_values),
                "avg": sum(price_values) / len(price_values),
                "count": len(price_values)
            }
            
        return {
            "origin": origin,
            "destination": destination,
            "months_ahead": months_ahead,
            "stats": stats,
            "prices": prices # Dict {date: price}
        }
        
    except Exception as e:
        return {"error": str(e)}
