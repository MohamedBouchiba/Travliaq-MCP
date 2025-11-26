import os
from pathlib import Path
from typing import List
from fastmcp import FastMCP

# Configuration
# Configuration
# On cible uniquement le dossier knowledge-base situé à côté de ce script
# Structure: src/mcp_server/resources.py -> src/mcp_server/knowledge-base/
KB_DIR = Path(__file__).parent / "knowledge-base"

IGNORE_DIRS = {
    ".git",
    ".venv",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
INCLUDE_EXTENSIONS = {".md", ".txt"}


def _is_ignored(path: Path) -> bool:
    """Vérifie si un chemin doit être ignoré."""
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    return False


def register_resources(mcp: FastMCP) -> None:
    """Scanne et enregistre les fichiers de documentation comme ressources MCP."""
    
    if not KB_DIR.exists():
        print(f"Warning: Knowledge base directory not found at {KB_DIR}")
        return

    print(f"Scanning resources in {KB_DIR}...")
    
    for root, dirs, files in os.walk(KB_DIR):
        # Filtrage des dossiers in-place pour os.walk
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in INCLUDE_EXTENSIONS:
                if _is_ignored(file_path):
                    continue
                
                # URI unique pour la ressource
                # On utilise file:/// pour être standard
                uri = f"file:///{file_path.as_posix()}"
                
                # Nom lisible
                name = f"{file_path.name} ({file_path.parent.name})"
                
                # Description (optionnel, on met le chemin relatif)
                try:
                    rel_path = file_path.relative_to(KB_DIR)
                except ValueError:
                    rel_path = file_path
                
                description = f"Documentation file: {rel_path}"

                # Enregistrement de la ressource
                # FastMCP gère la lecture via le décorateur.
                # Pour éviter que FastMCP ne pense que c'est un template (à cause d'arguments),
                # on définit une fonction sans argument qui capture les variables via une factory.
                
                def make_reader(p: Path):
                    def read_content() -> str:
                        """Lit le contenu du fichier."""
                        if not p.exists():
                            return f"Error: File not found at {p}"
                        return p.read_text(encoding="utf-8", errors="replace")
                    return read_content

                mcp.resource(uri=uri, name=name, description=description)(make_reader(file_path))

    print("Resources registration complete.")
