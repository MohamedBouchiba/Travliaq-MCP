import os
from pathlib import Path
from typing import List
from fastmcp import FastMCP

# Configuration
# Configuration
# On pourrait déplacer ça dans des variables d'env ou config
# En prod (Docker), le code est dans /app, donc on scanne /app ou un sous-dossier
# En local, on peut vouloir scanner tout le repo
default_root = Path("/app") if os.path.exists("/app") else Path("e:/CrewTravliaq")
ROOT_DIR = Path(os.getenv("MCP_RESOURCES_ROOT", default_root))
IGNORE_DIRS = {
    ".git",
    ".venv",
    ".idea",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "output",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "site-packages",
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
    
    # On scanne récursivement ROOT_DIR
    # Attention: sur un gros repo ça peut être long, ici on suppose une taille raisonnable
    # ou on cible des dossiers spécifiques si besoin (ex: ROOT_DIR / "docs")
    
    print(f"Scanning resources in {ROOT_DIR}...")
    
    for root, dirs, files in os.walk(ROOT_DIR):
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
                    rel_path = file_path.relative_to(ROOT_DIR)
                except ValueError:
                    rel_path = file_path
                
                description = f"Documentation file: {rel_path}"

                # Enregistrement de la ressource
                # FastMCP gère la lecture via le décorateur ou on peut passer une fonction
                # Ici on utilise une closure pour capturer le path
                
                @mcp.resource(uri=uri, name=name, description=description)
                def read_file(uri: str = uri) -> str:
                    """Lit le contenu du fichier de documentation."""
                    # On extrait le path de l'URI si besoin, mais ici on a capturé file_path
                    # Attention: l'argument uri est passé par FastMCP lors de l'appel
                    # Il faut parser l'URI pour retrouver le fichier si on n'utilise pas la closure directement
                    # Mais FastMCP semble matcher l'URI.
                    # Pour être sûr, on re-parse l'URI ou on utilise le path capturé.
                    # Le path capturé est plus sûr ici car 'read_file' est défini pour CETTE ressource.
                    
                    # Petit hack: pour éviter des soucis de closure dans la boucle, 
                    # on peut utiliser un default argument ou une factory.
                    # FastMCP enregistre la fonction.
                    
                    # Re-parsing propre de l'URI pour la sécurité (vérifier que c'est bien ce fichier)
                    path_str = uri.replace("file:///", "")
                    p = Path(path_str)
                    if not p.exists():
                        return f"Error: File not found at {p}"
                    return p.read_text(encoding="utf-8", errors="replace")

    print("Resources registration complete.")
