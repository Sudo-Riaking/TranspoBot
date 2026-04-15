# 🧪 Guide de Test Manuel - TranspoBot

Guide complet pour tester manuellement l'API TranspoBot sans tests automatisés.

## ✅ Prérequis

- MySQL en cours d'exécution
- Python 3.8+ 
- Dépendances installées: `pip install -r requirements.txt`
- Environnement `.env` configuré
- Base de données initialisée: `python3 init_db.py`

## 🚀 Démarrage du serveur

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le serveur
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Résultat attendu:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## 🌐 Accéder à l'interface

- **Frontend**: http://localhost:8000
- **API Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 Test via cURL

Testez chaque endpoint dans un terminal séparé:

### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Résultat attendu:**
```json
{"status":"ok","app":"TranspoBot"}
```

### 2. Récupérer les statistiques
```bash
curl http://localhost:8000/api/stats
```
**Résultat attendu:**
```json
{
  "total_trajets": 6,
  "trajets_en_cours": 1,
  "vehicules_actifs": 4,
  "incidents_ouverts": 1,
  "recette_totale": 5452.0
}
```

### 3. Récupérer les véhicules
```bash
curl http://localhost:8000/api/vehicules
```

### 4. Récupérer les chauffeurs
```bash
curl http://localhost:8000/api/chauffeurs
```

### 5. Récupérer les trajets
```bash
curl http://localhost:8000/api/trajets
```

### 6. Récupérer les incidents
```bash
curl http://localhost:8000/api/incidents
```

### 7. Récupérer les lignes
```bash
curl http://localhost:8000/api/lignes
```

---

## ➕ Test des POST endpoints

### Créer un véhicule
```bash
curl -X POST http://localhost:8000/api/vehicules \
  -H "Content-Type: application/json" \
  -d '{
    "immatriculation": "SN-TEST-001",
    "type": "bus",
    "capacite": 50,
    "statut": "actif",
    "kilometrage": 5000,
    "date_acquisition": "2024-01-15"
  }'
```

**Test validation enum (doit échouer):**
```bash
curl -X POST http://localhost:8000/api/vehicules \
  -H "Content-Type: application/json" \
  -d '{
    "immatriculation": "SN-BAD-001",
    "type": "voiture",
    "capacite": 50,
    "statut": "actif"
  }'
```
**Résultat attendu:** Erreur 422 (validation enum échouée)

### Créer un chauffeur
```bash
curl -X POST http://localhost:8000/api/chauffeurs \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@test.com",
    "telephone": "77123456",
    "numero_permis": "FR123456",
    "categorie_permis": "D",
    "statut": "actif",
    "disponibilite": true,
    "date_embauche": "2024-01-10"
  }'
```

### Créer un trajet
```bash
# Récupérez d'abord un id_ligne, id_chauffeur et id_vehicule existants
curl -X POST http://localhost:8000/api/trajets \
  -H "Content-Type: application/json" \
  -d '{
    "id_ligne": 1,
    "id_chauffeur": 1,
    "id_vehicule": 1,
    "date_heure_depart": "2024-04-15T08:00:00",
    "nb_passagers": 35,
    "recette": 1200.50
  }'
```

**Test FK validation (doit échouer):**
```bash
curl -X POST http://localhost:8000/api/trajets \
  -H "Content-Type: application/json" \
  -d '{
    "id_ligne": 999,
    "id_chauffeur": 999,
    "id_vehicule": 999,
    "date_heure_depart": "2024-04-15T08:00:00",
    "nb_passagers": 35,
    "recette": 1200.50
  }'
```
**Résultat attendu:** Erreur 400 "Ligne 999 inexistante"

### Créer un incident
```bash
# Récupérez d'abord un id_trajet existant
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "id_trajet": 1,
    "type": "retard",
    "description": "Incident test",
    "gravite": "faible",
    "date_heure_incident": "2024-04-15T10:00:00"
  }'
```

---

## 🤖 Test du Chat IA (endpoint /api/chat)

**Important:** Requiert une clé OpenAI valide dans `.env`

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combien de trajets sont en cours?"
  }'
```

**Résultat attendu:**
```json
{
  "answer": "Il y a actuellement 1 trajet en cours.",
  "data": [{"n": 1}],
  "sql": "SELECT COUNT(*) as n FROM trajets WHERE statut='en_cours'",
  "count": 1
}
```

### Tests de sécurité du chat:

**Test 1: Tentative d'INSERT (doit être rejetée)**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Insère un nouveau véhicule"
  }'
```
**Résultat attendu:** Erreur 400 "Requête non autorisée"

---

## 🖥️ Interface Web (tests manuels)

### Tableau de bord
1. Allez sur http://localhost:8000
2. Vérifiez que les statistiques s'affichent
3. Vérifiez que tous les nombres sont correctes

### Gestion des véhicules
1. Cliquez sur **Véhicules**
2. Vérifiez que la liste s'affiche
3. Testez le bouton **+ Ajouter**:
   - Remplissez le formulaire
   - Essayez un type invalide (doit être rejeté)
   - Soumettez avec un type valide

### Gestion des chauffeurs
1. Cliquez sur **Chauffeurs**
2. Vérifiez la liste
3. Testez l'ajout de nouveau chauffeur

### Gestion des trajets
1. Cliquez sur **Trajets**
2. Vérifiez la liste (max 50 derniers)
3. Testez l'ajout avec validations FK

### Gestion des incidents
1. Cliquez sur **Incidents**
2. Vérifiez la liste (max 50 derniers)
3. Testez l'ajout d'un incident

### Chat IA
1. Cliquez sur **Chat**
2. Posez diverses questions:
   - "Combien de véhicules actifs?"
   - "Lister tous les chauffeurs"
   - "Quels sont les trajets terminés?"
3. Vérifiez que:
   - Les réponses sont cohérentes
   - Le SQL affiché est valide
   - Les résultats correspondent

---

## 🔍 Checklist de test complet

### GET Endpoints
- [ ] `/health` retourne `{"status":"ok"}`
- [ ] `/api/stats` retourne tous les compteurs
- [ ] `/api/vehicules` retourne la liste
- [ ] `/api/chauffeurs` retourne la liste
- [ ] `/api/trajets` retourne max 50
- [ ] `/api/incidents` retourne max 50
- [ ] `/api/lignes` retourne la liste

### POST Endpoints (création)
- [ ] Véhicule créé avec succès
- [ ] Chauffeur créé avec succès
- [ ] Trajet créé avec succès
- [ ] Incident créé avec succès

### Validations (doivent échouer)
- [ ] Type véhicule invalide → erreur 422
- [ ] FK ligne inexistante → erreur 400
- [ ] FK chauffeur inexistant → erreur 400
- [ ] FK véhicule inexistant → erreur 400
- [ ] FK trajet inexistant → erreur 400

### Chat IA
- [ ] Question valide retourne SQL + réponse
- [ ] INSERT rejeté (sécurité)
- [ ] DELETE rejeté (sécurité)
- [ ] UPDATE rejeté (sécurité)

### Interface Web
- [ ] Dashboard charge et affiche stats
- [ ] Listes se chargent correctement
- [ ] Formulaires créent des entités
- [ ] Chat répond aux questions
- [ ] Validations frontend fonctionnent

---

## 🐛 Dépannage

**Problème:** "Connection refused" sur port 8000
- **Solution:** Vérifiez que le serveur est lancé avec `uvicorn`

**Problème:** "Database connection error"
- **Solution:** Vérifiez que MySQL fonctionne et `.env` est correctement configuré

**Problème:** Chat ne répond pas
- **Solution:** Vérifiez que `OPENAI_API_KEY` est défini dans `.env`

**Problème:** FK validation failing
- **Solution:** Assurez-vous que les IDs référencés existent dans la BD (lancez `init_db.py`)
