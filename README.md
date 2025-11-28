# Travliaq MCP Server

> **Serveur MCP (Model Context Protocol) pour Travliaq** - Fournit des outils météo et de génération d'images pour la planification de voyages.

[![FastMCP](https://img.shields.io/badge/FastMCP-v2.0-blue)](https://gofastmcp.com)
[![Python](https://img.shields.io/badge/Python-3.12+-green)](https://www.python.org/)

## 📋 Table des Matières

- [À Propos](#à-propos)
- [Outils Disponibles](#outils-disponibles)
- [Installation Locale](#installation-locale)
- [Déploiement en Production](#déploiement-en-production)
- [Accès au Serveur](#accès-au-serveur)
- [Configuration](#configuration)
- [Bonnes Pratiques Implémentées](#bonnes-pratiques-implémentées)

## 🎯 À Propos

Travliaq-MCP est un serveur MCP construit avec [fastMCP v2](https://gofastmcp.com) qui expose des outils pour :

- 🌤️ Récupérer des données météorologiques (Open-Meteo API)
- 🖼️ Générer des images pour les voyages (héros, backgrounds, sliders)
- 📚 Accéder à une base de connaissances de documentation

Le serveur suit toutes les **meilleures pratiques fastMCP v2** :

- ✅ Support async/await complet
- ✅ Context MCP pour logging et observabilité
- ✅ Gestion d'erreurs structurée
- ✅ ASGI-ready pour production

## 🛠️ Outils Disponibles

### Météo

| Outil               | Description                                            |
| ------------------- | ------------------------------------------------------ |
| `weather.by_coords` | Prévisions et conditions actuelles par coordonnées GPS |
| `weather.brief`     | Résumé court : température actuelle + aperçu 7 jours   |
| `weather.by_period` | Météo quotidienne sur une période définie (AAAA-MM-JJ) |

### Images

| Outil               | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `images.hero`       | Génère une image héro 1920x1080 pour une destination    |
| `images.background` | Génère un background 1920x1080 pour une activité        |
| `images.slider`     | Génère une image slider 800x600 pour un lieu spécifique |

### Utilitaires

| Outil         | Description                                |
| ------------- | ------------------------------------------ |
| `health.ping` | Vérifie que le serveur répond              |
| `debug.ls`    | Liste les fichiers dans un dossier (debug) |

## 💻 Installation Locale

### Prérequis

- Python 3.12+
- pip

### Étapes

```bash
# 1. Cloner le repository
git clone <votre-repo>
cd Travliaq-MCP

# 2. Créer un environnement virtuel
python -m venv .venv

# 3. Activer l'environnement
# Windows :
.venv\Scripts\activate
# Linux/Mac :
source .venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Configurer les variables d'environnement (optionnel)
# Créez un fichier .env à la racine
PORT=8005

# 6. Démarrer le serveur
python main_http.py
```

Le serveur sera accessible à : **http://localhost:8005**

## 🚀 Déploiement en Production

### Option 1 : Railway / Render / Fly.io (Recommandé)

Le serveur est conçu pour être déployé sur des plateformes avec support HTTP/SSE :

**Railway** :

```bash
# Le fichier Procfile ou commande de démarrage :
uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Configuration requise** :

- Variable d'environnement : `PORT` (automatique sur Railway)
- Build command : `pip install -r requirements.txt`
- Start command : `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Option 2 : Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8005
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8005"]
```

```bash
docker build -t travliaq-mcp .
docker run -p 8005:8005 travliaq-mcp
```

### Option 3 : AWS Lambda

> ⚠️ **Note** : Lambda nécessite une configuration API Gateway pour SSE. Préférez Railway/Render pour SSE natif.

Le fichier `lambda_handler.py` est fourni mais nécessite une configuration API Gateway appropriée.

## 🌐 Accès au Serveur

### En Production avec Nom de Domaine

Une fois déployé, votre serveur MCP sera accessible via un nom de domaine. Voici les différents endpoints :

#### Endpoints Disponibles

| Endpoint | Type | Description                    | URL Exemple                     |
| -------- | ---- | ------------------------------ | ------------------------------- |
| `/mcp`   | HTTP | Point d'accès principal MCP    | `https://votre-domaine.com/mcp` |
| `/sse`   | SSE  | Server-Sent Events (streaming) | `https://votre-domaine.com/sse` |
| `/`      | HTTP | Redirection vers `/mcp`        | `https://votre-domaine.com/`    |

#### Configuration avec Nom de Domaine Personnalisé

**Railway** :

1. Déployez votre application sur Railway
2. Dans Settings → Domains, ajoutez votre domaine personnalisé
3. Configurez vos DNS :
   - Type : `CNAME`
   - Name : `mcp` (ou sous-domaine de votre choix)
   - Value : `<votre-app>.up.railway.app`

**Résultat** : Votre serveur sera accessible à `https://mcp.votre-domaine.com/mcp`

### Intégration dans CrewAI

Pour utiliser le serveur MCP dans vos agents CrewAI :

```python
# Dans votre pipeline.py ou configuration d'agent
from crewai import Agent
from crewai.knowledge.source.mcp_knowledge_source import MCPKnowledgeSource

# URL de production avec votre domaine
MCP_SERVER_URL = "https://mcp.votre-domaine.com/mcp"

# Créer la source de connaissance MCP
mcp_source = MCPKnowledgeSource(
    server_url=MCP_SERVER_URL,
    timeout=30
)

# Utiliser dans un agent
agent = Agent(
    role="Expert en météo",
    goal="Fournir des prévisions précises",
    knowledge_sources=[mcp_source]
)
```

### Test avec MCP Inspector

L'inspecteur MCP permet de tester graphiquement tous vos outils :

```bash
# Avec domaine de production
npx @modelcontextprotocol/inspector https://mcp.votre-domaine.com/mcp

# Avec Railway (URL par défaut)
npx @modelcontextprotocol/inspector https://travliaq-mcp-production.up.railway.app/mcp
```

Cela ouvrira une interface web locale (`http://localhost:5173`) connectée à votre serveur distant.

### Exemple de Requête HTTP

```bash
# Ping le serveur
curl https://mcp.votre-domaine.com/mcp

# Appeler un outil (via MCP Inspector ou client MCP)
# Le protocole MCP utilise SSE pour les communications
```

## ⚙️ Configuration

### Variables d'Environnement

| Variable | Description                    | Valeur par Défaut |
| -------- | ------------------------------ | ----------------- |
| `PORT`   | Port d'écoute du serveur       | `8005`            |
| `MCP_*`  | Variables de configuration MCP | -                 |

### Fichier `.env` (exemple)

```env
PORT=8005
# Ajoutez vos clés API si nécessaire
# OPENAI_API_KEY=xxx
# SUPABASE_URL=xxx
```

## ✨ Bonnes Pratiques Implémentées

Ce serveur suit toutes les **meilleures pratiques fastMCP v2** :

### 1. Context MCP

```python
@mcp.tool(name="weather.by_coords")
async def weather_by_coords(..., ctx: Context = None):
    if ctx:
        await ctx.info("Fetching weather...")
```

Avantages :

- 🔍 Logs visibles dans les clients MCP
- ⚠️ Gestion d'erreurs observable
- 📊 Reporting de progression

### 2. Async/Await

```python
@mcp.tool(name="weather.brief")
async def weather_brief(...):
    # Fonction async pour I/O non-bloquant
```

Avantages :

- ⚡ Performance améliorée
- 🔄 Support natif par fastMCP
- 🚀 Scalabilité

### 3. Gestion d'Erreurs

```python
try:
    result = await fetch_data()
    return result
except Exception as e:
    await ctx.error(f"Error: {e}")
    raise
```

Avantages :

- 🛡️ Robustesse accrue
- 📝 Messages d'erreur descriptifs
- 🔧 Debugging facilité

### 4. Structure ASGI

```python
# app.py
from src.mcp_server.server import mcp
app = mcp.http_app()  # ASGI app pour uvicorn
```

Avantages :

- 🏭 Production-ready
- 🎯 Compatible uvicorn/gunicorn
- 📈 Scalable

## 📚 Ressources

- [Documentation FastMCP](https://gofastmcp.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [CrewAI Documentation](https://docs.crewai.com)

## 📝 Licence

MIT

---

**Développé pour Travliaq** 🌍✈️
