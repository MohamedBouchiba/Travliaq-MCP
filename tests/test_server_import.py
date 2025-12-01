import sys
import os
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

def test_server_import():
    print("Testing server.py import...")
    try:
        from mcp_server.server import create_mcp
        mcp = create_mcp()
        print("[OK] Successfully imported create_mcp and created instance")
        
        # Verify some tools are registered
        tools = [t.name for t in mcp._tools] # Accessing internal list if available, or just checking if no error
        print(f"[OK] Server created. Tools registered: {len(tools) if hasattr(mcp, '_tools') else 'Unknown'}")
        
    except ImportError as e:
        print(f"[FAIL] ImportError: {e}")
    except SyntaxError as e:
        print(f"[FAIL] SyntaxError: {e}")
    except Exception as e:
        print(f"[FAIL] Exception: {e}")

if __name__ == "__main__":
    test_server_import()
