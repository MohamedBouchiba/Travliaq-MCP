import sys
import os
from pathlib import Path
import asyncio

# Setup paths to mimic the server environment
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

print(f"Project Root: {PROJECT_ROOT}")
print(f"Src Dir: {SRC_DIR}")

async def test_imports():
    print("\n--- Testing Imports ---")
    try:
        from mcp_server.tools import booking
        print("[OK] Successfully imported booking tool")
    except ImportError as e:
        print(f"[FAIL] Failed to import booking tool: {e}")
        # return # Don't return, try the next one

    try:
        from mcp_server.tools import flights
        print("[OK] Successfully imported flights tool")
    except ImportError as e:
        print(f"[FAIL] Failed to import flights tool: {e}")
        # return

    print("\n--- Testing Instantiation (Mock) ---")
    # We won't actually run the scrapers as they require browsers, but we check if we can access the functions
    
    if hasattr(booking, 'search_hotels'):
        print("[OK] booking.search_hotels exists")
    else:
        print("[FAIL] booking.search_hotels missing")

    if hasattr(flights, 'get_flight_prices'):
        print("[OK] flights.get_flight_prices exists")
    else:
        print("[FAIL] flights.get_flight_prices missing")

if __name__ == "__main__":
    asyncio.run(test_imports())
