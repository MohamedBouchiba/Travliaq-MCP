# Démarrage local
python -m venv .venv && . .venv/Scripts/activate  # Windows ; ou source .venv/bin/activate
pip install -r requirements.txt
python main_http.py
# Tester : http://127.0.0.1:8000/mcp (endpoint MCP)

# Déploiement AWS Lambda (ZIP rapide)
# 1) Construire un ZIP avec dépendances
#   Windows PowerShell:
#     python -m pip install -r requirements.txt -t build/
#     Copy-Item -Recurse src main_http.py lambda_handler.py build/
#     Compress-Archive -Path build/* -DestinationPath deploy.zip
# 2) Console AWS → Lambda → Create function (Python 3.12) → Upload zip (deploy.zip)
# 3) Configuration → Function URL (Auth: AWS_IAM recommandé) → tester GET/POST sur /mcp
#    URL finale: https://<id>.lambda-url.<region>.on.aws/mcp

# CrewAI
# Ajouter l’URL du serveur dans la config d’agent (transport streamable-http) :
# mcps: ["https://<id>.lambda-url.<region>.on.aws/mcp"]
