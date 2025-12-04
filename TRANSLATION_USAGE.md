# Exemples d'Utilisation - Outil text.translate

## Test Basique

```python
# Dans un agent CrewAI ou directement via MCP

# 1. Traduction simple EN → FR
result = await mcp_tools.call_tool(
    "text.translate",
    text="Hello, welcome to Paris!",
    source_language="EN",
    target_language="FR"
)
# → {"success": true, "translated_text": "Bonjour, bienvenue à Paris !", "target_language": "fra_Latn"}

# 2. Traduction titre voyage FR → ES
result = await mcp_tools.call_tool(
    "text.translate",
    text="Découvrez les temples cachés de Tokyo",
    source_language="FR",
    target_language="ES"
)
# → {"success": true, "translated_text": "Descubre los templos escondidos de Tokio", ...}

# 3. Description longue EN → DE
result = await mcp_tools.call_tool(
    "text.translate",
    text="Visit the ancient Senso-ji temple, Tokyo's oldest Buddhist temple founded in 628. Walk through Nakamise shopping street with traditional crafts.",
    source_language="EN",
    target_language="DE"
)
# → {"success": true, "translated_text": "Besuchen Sie den antiken Senso-ji-Tempel...", ...}
```

## Utilisation dans un Agent CrewAI

```python
from crewai import Agent, Task

translation_agent = Agent(
    role="Traducteur de Contenu Voyage",
    goal="Traduire itinéraires dans langue utilisateur",
    tools=["text.translate"],  # Outil MCP disponible
    backstory="Expert en traduction de contenu touristique multilingue"
)

translate_task = Task(
    description="""
    Traduire TOUS les titres et descriptions de l'itinéraire
    du français vers {target_language}.

    Utilise l'outil text.translate pour chaque champ:
    - title → traduit
    - subtitle → traduit
    - description → traduit
    - tips → traduit

    Itinéraire: {itinerary_json}
    Langue cible: {target_language}
    """,
    agent=translation_agent,
    expected_output="JSON de l'itinéraire avec tous champs traduits"
)
```

## Gestion des Erreurs

```python
result = await mcp_tools.call_tool(
    "text.translate",
    text="Bonjour",
    source_language="FR",
    target_language="XX"  # Code invalide
)

if result.get("success"):
    translated = result["translated_text"]
    print(f"Traduction: {translated}")
else:
    error = result["error"]
    print(f"Erreur: {error}")
    # → "Translation service returned error 400: Unsupported language code: XX"
```

## Langues Supportées (Codes Courts)

| Code | Langue      | Exemple            |
| ---- | ----------- | ------------------ |
| EN   | Anglais     | "Hello world"      |
| FR   | Français    | "Bonjour le monde" |
| ES   | Espagnol    | "Hola mundo"       |
| DE   | Allemand    | "Hallo Welt"       |
| IT   | Italien     | "Ciao mondo"       |
| PT   | Portugais   | "Olá mundo"        |
| NL   | Néerlandais | "Hallo wereld"     |
| RU   | Russe       | "Привет мир"       |
| AR   | Arabe       | "مرحبا بالعالم"    |
| ZH   | Chinois     | "你好世界"         |

**Note:** Pour codes NLLB complets (200 langues), utiliser format `xxx_Xxxx` (ex: `hin_Deva` pour Hindi, `jpn_Jpan` pour Japonais).

## Configuration Service

L'URL du service est configurée dans `translation.py`:

```python
TRANSLATE_SERVICE_URL = "https://travliaq-translate-production.up.railway.app"
```

Pour changer (développement local):

```python
TRANSLATE_SERVICE_URL = "http://localhost:8000"
```

## Performance

- Traduction courte (< 50 mots): **200-500ms**
- Traduction moyenne (100-200 mots): **500ms-1s**
- Traduction longue (300-400 mots): **1-2s**

**Timeout:** 30 secondes par défaut
