# Démarrage local

python -m venv .venv && . .venv/Scripts/activate # Windows ; ou source .venv/bin/activate
pip install -r requirements.txt
python main_http.py

# Tester : http://127.0.0.1:8000 (endpoint SSE à la racine)

# Déploiement AWS Lambda (ZIP rapide)

# Note: Lambda nécessite une configuration différente pour SSE.

# Pour SSE, préférer un déploiement conteneurisé (Railway, Render, Fly.io)

# CrewAI

# Ajouter l'URL du serveur dans la config d'agent (transport SSE) :

# L'URL pointe vers l'endpoint SSE

# Dans pipeline.py: MCP_SERVER_URL = "https://travliaq-mcp-production.up.railway.app/sse"

# Accès via UI (MCP Inspector)

# Vous pouvez utiliser l'inspecteur MCP pour tester et interagir avec le serveur déployé via une interface graphique.

#

# 1. Assurez-vous d'avoir Node.js installé.

# 2. Lancez l'inspecteur en pointant vers l'URL de production (endpoint SSE) :

#

# ```bash

# npx @modelcontextprotocol/inspector https://travliaq-mcp-production.up.railway.app/sse

# ```

#

# Cela ouvrira une interface web locale connectée à votre serveur distant.
