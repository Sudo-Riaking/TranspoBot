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

# Vérifier le fichier .env
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé"
    echo "💡 Créez-le à partir de .env.example:"
    echo "   cp .env.example .env"
    echo "   Puis complétez les variables d'environnement"
    exit 1
fi

# Charger les variables d'environnement
export $(cat .env | grep -v '^#' | xargs)

# Démarrer le serveur
echo "📡 Serveur démarrant sur http://localhost:8000"
echo "📖 Docs API: http://localhost:8000/docs"
echo "🧪 Tests: http://localhost:8000/redoc"
echo "💬 Chat: http://localhost:8000"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur..."
echo ""

python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
