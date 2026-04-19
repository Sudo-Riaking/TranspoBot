#!/bin/bash
# Script pour démarrer le serveur FastAPI TranspoBot

echo "🚀 Démarrage du serveur TranspoBot..."

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que les dépendances sont installées
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI n'est pas installé"
    echo "💡 Exécutez: pip install -r requirements.txt"
    exit 1
fi

# Charger les variables d'environnement depuis .env si le fichier existe (développement local)
if [ -f .env ]; then
    echo "⚙️  Chargement des variables depuis .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Déterminer le mode (dev avec reload si DEV_MODE=true, sinon production)
RELOAD_FLAG=""
if [ "$DEV_MODE" = "true" ]; then
    RELOAD_FLAG="--reload"
fi

# Utiliser la variable PORT de Railway, ou 8000 par défaut
PORT=${PORT:-8000}

# Démarrer le serveur
echo "📡 Serveur démarrant sur http://localhost:$PORT"
echo "📖 Docs API: http://localhost:$PORT/docs"
echo "🧪 Tests: http://localhost:$PORT/redoc"
echo "💬 Chat: http://localhost:$PORT"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur..."
echo ""

python3 -m uvicorn app:app --host 0.0.0.0 --port $PORT $RELOAD_FLAG
