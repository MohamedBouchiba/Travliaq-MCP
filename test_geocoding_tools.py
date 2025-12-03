"""
Test script pour valider les nouveaux outils de geocodage.

Teste:
- geo.city: Villes et pays
- geo.place: Lieux specifiques (monuments, attractions, etc.)
"""
import asyncio
import sys
import io

# Fix Unicode pour Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, "src")

from mcp_server.tools import places as g

def safe_print(text):
    """Print avec gestion Unicode robuste."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: remplacer caractères problématiques
        print(text.encode('ascii', errors='replace').decode('ascii'))

async def test_geo_city():
    """Test geo.city pour villes/pays."""
    print("TEST geo.city - Villes et Pays")
    print("=" * 60)
    
    # Test 1: Ville simple
    print("\n1. Ville simple: Tokyo")
    result = await g.geocode_text("Tokyo", count=1)
    print(f"   OK: {result[0]['name']}, {result[0]['country']}")
    print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    
    # Test 2: Ville + pays
    print("\n2. Ville + pays: Lisbon, Portugal")
    result = await g.geocode_text("Lisbon, Portugal", count=1)
    print(f"   OK: {result[0]['name']}, {result[0]['country']}")
    print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    
    # Test 3: Avec country filter
    print("\n3. Avec filtre pays: Brussels (BE)")
    result = await g.geocode_text("Brussels", country="BE", count=1)
    print(f"   OK: {result[0]['name']}, {result[0]['country']}")
    print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")


async def test_geo_place():
    """Test geo.place pour lieux specifiques (Nominatim OSM)."""
    print("\n\nTEST geo.place - Lieux Specifiques (Nominatim OSM)")
    print("=" * 60)
    
    # Test 1: Monument celebre
    print("\n1. Monument: Atomium, Brussels, Belgium")
    result = await g.geocode_specific_place("Atomium, Brussels, Belgium", max_results=1)
    print(f"   OK: {result[0]['name']}")
    print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    print(f"   Type: {result[0]['category']}/{result[0]['type']}")
    print(f"   Adresse: {result[0]['display_name'][:80]}...")
    
    # Delai pour respecter Nominatim (1 req/sec)
    await asyncio.sleep(1)
    
    # Test 2: Attraction touristique
    safe_print("\n2. Attraction: Tokyo Skytree, Tokyo, Japan")
    result = await g.geocode_specific_place("Tokyo Skytree, Tokyo, Japan", max_results=1)
    safe_print(f"   OK: {result[0]['name']}")
    safe_print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    safe_print(f"   Type: {result[0]['category']}/{result[0]['type']}")
    safe_print(f"   Adresse: {result[0]['display_name'][:80]}...")
    
    await asyncio.sleep(1)
    
    # Test 3: Temple
    safe_print("\n3. Temple: Senso-ji Temple, Asakusa, Tokyo")
    result = await g.geocode_specific_place("Senso-ji Temple, Asakusa, Tokyo", max_results=1)
    safe_print(f"   OK: {result[0]['name']}")
    safe_print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    safe_print(f"   Type: {result[0]['category']}/{result[0]['type']}")
    safe_print(f"   Adresse: {result[0]['display_name'][:80]}...")
    
    await asyncio.sleep(1)
    
    # Test 4: Tour Eiffel
    print("\n4. Monument: Eiffel Tower, Paris, France")
    result = await g.geocode_specific_place("Eiffel Tower, Paris, France", max_results=1)
    print(f"   OK: {result[0]['name']}")
    print(f"   GPS: {result[0]['latitude']}, {result[0]['longitude']}")
    print(f"   Type: {result[0]['category']}/{result[0]['type']}")
    print(f"   Adresse: {result[0]['display_name'][:80]}...")


async def main():
    try:
        await test_geo_city()
        await test_geo_place()
        
        print("\n\n" + "=" * 60)
        print("SUCCESS - TOUS LES TESTS PASSES!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n\nERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
