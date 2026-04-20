"""
TranspoBot — Backend FastAPI
Projet GLSi L3 — ESP/UCAD
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Literal, Optional
import mysql.connector
import os
import re
import json
import httpx
import bcrypt
from datetime import datetime

# Railway utilise la variable d'environnement PORT
PORT = int(os.environ.get("PORT", 8080))

# ── Chargement du .env ────────────────────────────────────────
env_path = Path(__file__).resolve().parent / '.env'
if env_path.exists():
    with env_path.open('r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

app = FastAPI(title="TranspoBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialise TOUTES les tables et données de test au démarrage"""
    try:
        # D'abord, essayer de créer la base de données si elle n'existe pas
        config = get_db_config()
        db_name = config['database']

        # Connexion sans spécifier la base de données
        temp_config = config.copy()
        del temp_config['database']

        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()

        # Créer la base de données si elle n'existe pas
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.close()
        conn.close()

        # Maintenant se connecter à la base de données
        conn = get_db()
        cursor = conn.cursor()

        # Lire et exécuter le fichier schema.sql complet
        with open('schema.sql', 'r') as f:
            sql_script = f.read()

        # Exécuter chaque instruction SQL (CREATE TABLE, INSERT, etc.)
        for statement in sql_script.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # Ignorer les erreurs "table already exists"
                    if "already exists" not in str(e).lower():
                        print(f"Warning: {e}")

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Base de données complète initialisée avec succès!")
    except Exception as e:
        print(f"⚠️ Erreur init BD: {e}")
        print(f"Config DB: {get_db_config()}")

# ── Configuration ──────────────────────────────────────────────
import re

# Configuration base de données pour Railway
def get_db_config():
    # Vérifier d'abord MYSQL_URL (variable Railway), puis DATABASE_URL
    database_url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")
    
    if database_url:
        # Parse l'URL: mysql://user:password@host:port/database
        match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
        if match:
            return {
                "host": match.group(3),
                "user": match.group(1),
                "password": match.group(2),
                "database": match.group(5),
                "port": int(match.group(4))
            }
    
    # Fallback pour le développement local
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "transpobot"),
        "port": 3306
    }

# Utilisez cette fonction dans get_db()
def get_db():
    config = get_db_config()
    return mysql.connector.connect(**config)

LLM_API_KEY  = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

# ── Schéma de la base (pour le prompt système) ─────────────────
DB_SCHEMA = """
Tables MySQL disponibles :

vehicules(id_vehicule, immatriculation, type[bus/minibus/taxi], capacite, statut[actif/maintenance/hors_service], kilometrage, date_acquisition, date_dernier_maintenance)
chauffeurs(id_chauffeur, nom, prenom, email, telephone, numero_permis, categorie_permis, statut[actif/suspendu/inactif], disponibilite (BOOLEAN), date_embauche)
conduire(id_vehicule, id_chauffeur, date_affectation) -- association chauffeurs ↔ véhicules
lignes(id_ligne, code, nom, origine, destination, distance_km, duree_minutes)
tarifs(id_tarif, id_ligne, type_client[normal/etudiant/senior], prix)
trajets(id_trajet, id_ligne, id_chauffeur, id_vehicule, date_heure_depart, date_heure_arrivee, statut[planifie/en_cours/termine/annule], nb_passagers, recette)
incidents(id_incident, id_trajet, type[panne/accident/retard/autre], description, gravite[faible/moyen/grave], date_heure_incident, resolu)
"""

SYSTEM_PROMPT = f"""
Tu es TranspoBot, l'assistant intelligent d'une compagnie de transport
urbain au Sénégal (similaire à Dakar Dem Dikk).
Tu aides les gestionnaires à interroger la base de données en langage
naturel, en français ou en anglais.

{DB_SCHEMA}

════════════════════════════════════════════════════════════════
 RÈGLES DE SÉCURITÉ — ABSOLUMENT OBLIGATOIRES
════════════════════════════════════════════════════════════════

RÈGLE 1 — SELECT UNIQUEMENT :
Tu ne dois JAMAIS générer autre chose qu'une requête SELECT.
Les mots-clés suivants sont STRICTEMENT INTERDITS :
INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, GRANT, REVOKE.
Si la question demande une modification, tu réponds :
{{"sql": null, "explication": "Je suis uniquement autorisé à consulter les données, pas à les modifier. Veuillez contacter un administrateur."}}

RÈGLE 2 — LIMIT OBLIGATOIRE :
Toute requête SELECT doit inclure LIMIT 100 maximum.

RÈGLE 3 — COLONNES EXACTES :
Utilise UNIQUEMENT les noms de colonnes du schéma ci-dessus.
Les clés primaires sont id_vehicule, id_chauffeur, id_ligne, id_tarif,
id_trajet, id_incident — JAMAIS juste 'id'.

RÈGLE 4 — JOINTURES CORRECTES :
Utilise toujours les bonnes clés FK définies dans les relations.
Pour relier chauffeurs ↔ véhicules, passe par la table 'conduire'.

════════════════════════════════════════════════════════════════
 FORMAT DE RÉPONSE — TOUJOURS CE FORMAT JSON
════════════════════════════════════════════════════════════════

Tu réponds TOUJOURS et UNIQUEMENT avec du JSON valide :
{{"sql": "SELECT ...", "explication": "Réponse claire en français"}}

Si question hors sujet :
{{"sql": null, "explication": "Je suis spécialisé dans la gestion de transport. Posez-moi une question sur les véhicules, chauffeurs, trajets ou incidents."}}

Règles de style :
- Toujours en français
- Montants en FCFA
- Utiliser CONCAT(c.prenom, ' ', c.nom) pour les noms complets
- Alias clairs : AS total, AS nb_incidents, AS recette_totale

════════════════════════════════════════════════════════════════
 EXEMPLES few-shot — alignés sur le vrai schéma
════════════════════════════════════════════════════════════════

--- EXEMPLE 1 ---
Question : "Combien de trajets ont été effectués cette semaine ?"
Réponse :
{{"sql": "SELECT COUNT(*) AS total FROM trajets WHERE date_heure_depart >= DATE_SUB(NOW(), INTERVAL 7 DAY) AND statut = 'termine'", "explication": "Cette semaine, il y a eu [total] trajets terminés."}}

--- EXEMPLE 2 ---
Question : "Quel chauffeur a le plus d'incidents ce mois-ci ?"
Réponse :
{{"sql": "SELECT CONCAT(c.prenom, ' ', c.nom) AS chauffeur, COUNT(i.id_incident) AS nb_incidents FROM incidents i JOIN trajets t ON i.id_trajet = t.id_trajet JOIN chauffeurs c ON t.id_chauffeur = c.id_chauffeur WHERE MONTH(i.date_heure_incident) = MONTH(NOW()) AND YEAR(i.date_heure_incident) = YEAR(NOW()) GROUP BY c.id_chauffeur, c.nom, c.prenom ORDER BY nb_incidents DESC LIMIT 1", "explication": "Le chauffeur avec le plus d'incidents ce mois-ci est [prénom NOM] avec [nb] incidents."}}

--- EXEMPLE 3 ---
Question : "Quels véhicules sont en maintenance ?"
Réponse :
{{"sql": "SELECT immatriculation, type, kilometrage, date_dernier_maintenance FROM vehicules WHERE statut = 'maintenance' ORDER BY immatriculation LIMIT 100", "explication": "Voici les véhicules actuellement en maintenance."}}

--- EXEMPLE 4 ---
Question : "Quelle est la recette totale du mois de mars 2026 ?"
Réponse :
{{"sql": "SELECT SUM(recette) AS recette_totale, COUNT(*) AS nb_trajets FROM trajets WHERE MONTH(date_heure_depart) = 3 AND YEAR(date_heure_depart) = 2026 AND statut = 'termine'", "explication": "La recette totale de mars 2026 est de [recette_totale] FCFA pour [nb_trajets] trajets terminés."}}

--- EXEMPLE 5 ---
Question : "Liste les chauffeurs disponibles avec leur véhicule"
Réponse :
{{"sql": "SELECT CONCAT(c.prenom, ' ', c.nom) AS chauffeur, c.telephone, v.immatriculation AS vehicule FROM chauffeurs c LEFT JOIN conduire co ON c.id_chauffeur = co.id_chauffeur LEFT JOIN vehicules v ON co.id_vehicule = v.id_vehicule WHERE c.disponibilite = TRUE AND c.statut = 'actif' ORDER BY c.nom LIMIT 100", "explication": "Voici les chauffeurs disponibles avec leur véhicule assigné."}}

--- EXEMPLE 6 ---
Question : "Liste les incidents graves non résolus"
Réponse :
{{"sql": "SELECT i.id_incident, i.type, i.description, i.date_heure_incident, CONCAT(c.prenom, ' ', c.nom) AS chauffeur FROM incidents i JOIN trajets t ON i.id_trajet = t.id_trajet JOIN chauffeurs c ON t.id_chauffeur = c.id_chauffeur WHERE i.gravite = 'grave' AND i.resolu = FALSE ORDER BY i.date_heure_incident DESC LIMIT 100", "explication": "Voici les incidents graves non encore résolus."}}

--- EXEMPLE 7 ---
Question : "Supprime tous les trajets annulés"
Réponse :
{{"sql": null, "explication": "Je suis uniquement autorisé à consulter les données, pas à les modifier. Veuillez contacter un administrateur."}}

--- EXEMPLE 8 ---
Question : "Quel temps fait-il à Dakar ?"
Réponse :
{{"sql": null, "explication": "Je suis spécialisé dans la gestion de transport. Je peux vous aider sur les véhicules, chauffeurs, trajets et incidents de votre flotte."}}

════════════════════════════════════════════════════════════════
 RAPPELS TECHNIQUES IMPORTANTS
════════════════════════════════════════════════════════════════

- Clés primaires TOUJOURS préfixées : id_vehicule, id_chauffeur, id_trajet, etc.
- Pour lier chauffeurs ↔ véhicules : passer par la table 'conduire'
- Colonne date : 'date_heure_incident' (pas 'date_incident')
- chauffeurs.disponibilite est un BOOLEAN (TRUE/FALSE)
- vehicules a 'date_dernier_maintenance'
- Pour les noms : CONCAT(c.prenom, ' ', c.nom) AS chauffeur
- Pour les montants : préciser FCFA dans l'explication
- Toujours GROUP BY toutes les colonnes non-agrégées
- Toujours LIMIT 100 maximum
"""

# ── Connexion MySQL ────────────────────────────────────────────
def get_db():
    config = get_db_config()  # Utilisez la fonction que vous avez créée
    return mysql.connector.connect(**config)

def execute_query(sql: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

# ── Validation des Clés Étrangères ────────────────────────────
def check_fk_exists(table: str, id_col: str, id_value: int) -> bool:
    # Note: table et id_col sont toujours des valeurs internes, jamais de l'input utilisateur
    try:
        result = execute_query(f"SELECT 1 FROM {table} WHERE {id_col} = {id_value} LIMIT 1")
        return len(result) > 0
    except:
        return False

def validate_trajet_fks(id_ligne: int, id_chauffeur: int, id_vehicule: int) -> tuple[bool, str]:
    if not check_fk_exists("lignes", "id_ligne", id_ligne):
        return False, f"Ligne {id_ligne} inexistante"
    if not check_fk_exists("chauffeurs", "id_chauffeur", id_chauffeur):
        return False, f"Chauffeur {id_chauffeur} inexistant"
    if not check_fk_exists("vehicules", "id_vehicule", id_vehicule):
        return False, f"Véhicule {id_vehicule} inexistant"
    return True, ""

def validate_incident_fk(id_trajet: int) -> tuple[bool, str]:
    if not check_fk_exists("trajets", "id_trajet", id_trajet):
        return False, f"Trajet {id_trajet} inexistant"
    return True, ""

# ── Appel LLM ─────────────────────────────────────────────────
async def ask_llm(question: str) -> dict:
    if not LLM_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Clé API LLM non configurée. Ajoutez OPENAI_API_KEY dans le .env."
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": question},
                    ],
                    "temperature": 0,
                },
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Erreur LLM {exc.response.status_code}: {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Erreur réseau vers l'API LLM: {str(exc)}"
            )

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise HTTPException(status_code=502, detail=f"Réponse LLM invalide: {str(exc)}")

        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=502, detail=f"JSON LLM invalide: {str(exc)}")

        raise HTTPException(status_code=502, detail="Réponse LLM ne contient pas de JSON.")

# ── Routes API ─────────────────────────────────────────────────
class ChatMessage(BaseModel):
    question: str

@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """Point d'entrée principal : question → SQL → résultats"""
    try:
        llm_response = await ask_llm(msg.question)
        sql = llm_response.get("sql")
        explication = llm_response.get("explication", "")

        if not sql:
            return {"answer": explication, "data": [], "sql": None}

        # Sécurité : uniquement les SELECT autorisés
        if not sql.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Requête non autorisée — seules les lectures (SELECT) sont permises"
            )

        data = execute_query(sql)
        return {
            "answer": explication,
            "data": data,
            "sql": sql,
            "count": len(data),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    stats = {}
    queries = {
        "total_trajets":    "SELECT COUNT(*) as n FROM trajets WHERE statut='termine'",
        "trajets_en_cours": "SELECT COUNT(*) as n FROM trajets WHERE statut='en_cours'",
        "vehicules_actifs": "SELECT COUNT(*) as n FROM vehicules WHERE statut='actif'",
        "incidents_ouverts":"SELECT COUNT(*) as n FROM incidents WHERE resolu=FALSE",
        "recette_totale":   "SELECT COALESCE(SUM(recette),0) as n FROM trajets WHERE statut='termine'",
    }
    for key, sql in queries.items():
        result = execute_query(sql)
        stats[key] = result[0]["n"] if result else 0
    return stats

@app.get("/api/vehicules")
def get_vehicules():
    return execute_query("SELECT * FROM vehicules ORDER BY immatriculation")

@app.get("/api/chauffeurs")
def get_chauffeurs():
    return execute_query("""
        SELECT DISTINCT c.id_chauffeur, c.nom, c.prenom, c.email, c.telephone,
               c.numero_permis, c.categorie_permis, c.statut, c.disponibilite,
               c.date_embauche, GROUP_CONCAT(v.immatriculation) as immatriculations
        FROM chauffeurs c
        LEFT JOIN conduire co ON c.id_chauffeur = co.id_chauffeur
        LEFT JOIN vehicules v ON co.id_vehicule = v.id_vehicule
        GROUP BY c.id_chauffeur
        ORDER BY c.nom, c.prenom
    """)

@app.get("/api/trajets")
def get_trajets():
    return execute_query("""
        SELECT t.id_trajet, t.date_heure_depart as date, t.date_heure_arrivee, t.statut,
               t.nb_passagers as passagers, t.recette, l.nom as ligne,
               CONCAT(ch.nom, ' ', ch.prenom) as chauffeur, v.immatriculation
        FROM trajets t
        JOIN lignes l ON t.id_ligne = l.id_ligne
        JOIN chauffeurs ch ON t.id_chauffeur = ch.id_chauffeur
        JOIN vehicules v ON t.id_vehicule = v.id_vehicule
        ORDER BY t.date_heure_depart DESC
        LIMIT 50
    """)

@app.get("/api/incidents")
def get_incidents():
    return execute_query("""
        SELECT i.id_incident, i.type, i.description, i.gravite,
               i.date_heure_incident as date, i.resolu, t.id_trajet,
               l.nom as ligne, CONCAT(ch.nom, ' ', ch.prenom) as chauffeur
        FROM incidents i
        JOIN trajets t ON i.id_trajet = t.id_trajet
        JOIN lignes l ON t.id_ligne = l.id_ligne
        JOIN chauffeurs ch ON t.id_chauffeur = ch.id_chauffeur
        ORDER BY i.date_heure_incident DESC
        LIMIT 50
    """)

@app.get("/api/lignes")
def get_lignes():
    return execute_query("""
        SELECT id_ligne, code, nom, origine, destination, distance_km, duree_minutes
        FROM lignes ORDER BY code
    """)

# ── Modèles Pydantic ──────────────────────────────────────────
class VehiculeInput(BaseModel):
    immatriculation: str
    type: Literal["bus", "minibus", "taxi"]
    capacite: int
    statut: Literal["actif", "maintenance", "hors_service"] = "actif"
    kilometrage: int = 0
    date_acquisition: Optional[str] = None

class ChauffeurInput(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    numero_permis: str
    categorie_permis: str
    statut: Literal["actif", "suspendu", "inactif"] = "actif"
    disponibilite: bool = True
    date_embauche: Optional[str] = None

class TrajetInput(BaseModel):
    id_ligne: int
    id_chauffeur: int
    id_vehicule: int
    date_heure_depart: str
    nb_passagers: int
    recette: float = 0

class IncidentInput(BaseModel):
    id_trajet: int
    type: Literal["panne", "accident", "retard", "autre"]
    description: Optional[str] = None
    gravite: Literal["faible", "moyen", "grave"] = "faible"
    date_heure_incident: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user: dict
    token: str

# ── Authentification ──────────────────────────────────────────
@app.post("/api/login")
async def login(req: LoginRequest):
    """Authentification utilisateur"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_utilisateur, email, nom_complet, mot_de_passe, role, statut FROM utilisateurs WHERE email = %s",
            (req.email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Identifiants incorrects")

        # Vérifier le mot de passe avec bcrypt
        if not bcrypt.checkpw(req.password.encode('utf-8'), user['mot_de_passe'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")

        if user['statut'] != 'actif':
            raise HTTPException(status_code=403, detail="Compte désactivé")

        # Mettre à jour la dernière connexion
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE utilisateurs SET derniere_connexion = NOW() WHERE id_utilisateur = %s",
            (user['id_utilisateur'],)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "user": {
                "id": user['id_utilisateur'],
                "email": user['email'],
                "nom": user['nom_complet'],
                "role": user['role']
            },
            "token": f"token_{user['id_utilisateur']}_{int(datetime.now().timestamp())}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── POST Endpoints ────────────────────────────────────────────
@app.post("/api/vehicules")
def create_vehicule(vehicule: VehiculeInput):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (vehicule.immatriculation, vehicule.type, vehicule.capacite,
              vehicule.statut, vehicule.kilometrage, vehicule.date_acquisition))
        conn.commit()
        vehicule_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": vehicule_id, "message": "Véhicule créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chauffeurs")
def create_chauffeur(chauffeur: ChauffeurInput):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chauffeurs (nom, prenom, email, telephone, numero_permis,
                                   categorie_permis, statut, disponibilite, date_embauche)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (chauffeur.nom, chauffeur.prenom, chauffeur.email, chauffeur.telephone,
              chauffeur.numero_permis, chauffeur.categorie_permis, chauffeur.statut,
              chauffeur.disponibilite, chauffeur.date_embauche))
        conn.commit()
        chauffeur_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": chauffeur_id, "message": "Chauffeur créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trajets")
def create_trajet(trajet: TrajetInput):
    try:
        valid, msg = validate_trajet_fks(trajet.id_ligne, trajet.id_chauffeur, trajet.id_vehicule)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trajets (id_ligne, id_chauffeur, id_vehicule, date_heure_depart,
                                nb_passagers, recette, statut)
            VALUES (%s, %s, %s, %s, %s, %s, 'planifie')
        """, (trajet.id_ligne, trajet.id_chauffeur, trajet.id_vehicule,
              trajet.date_heure_depart, trajet.nb_passagers, trajet.recette))
        conn.commit()
        trajet_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": trajet_id, "message": "Trajet créé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/incidents")
def create_incident(incident: IncidentInput):
    try:
        valid, msg = validate_incident_fk(incident.id_trajet)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        date_incident = incident.date_heure_incident or datetime.now().isoformat()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incidents (id_trajet, type, description, gravite,
                                  date_heure_incident, resolu)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (incident.id_trajet, incident.type, incident.description,
              incident.gravite, date_incident))
        conn.commit()
        incident_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": incident_id, "message": "Incident créé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok", "app": "TranspoBot"}

@app.get("/test")
async def test():
    """Route de test simple"""
    return {"status": "ok", "message": "API is working"}

@app.get("/")
async def read_root():
    """Route racine - retourne le statut de l'API"""
    try:
        if os.path.exists("index.html"):
            return FileResponse("index.html")
        else:
            # Si index.html n'existe pas, retourner un JSON de test
            return {
                "status": "ok",
                "message": "TranspoBot API is running",
                "endpoints": {
                    "health": "/health",
                    "test": "/test",
                    "docs": "/docs",
                    "login": "/api/login"
                }
            }
    except Exception as e:
        print(f"Erreur dans read_root: {e}")
        return {"error": str(e), "message": "Erreur serveur"}

# @app.get("/api/init")
# async def init_tables():
#     """Initialise les tables et données de test"""
#     try:
#         conn = get_db()
#         cursor = conn.cursor()
#         
#         # Lecture du fichier schema.sql
#         with open('schema.sql', 'r') as f:
#             sql_content = f.read()
#         
#         # Exécuter chaque requête
#         for statement in sql_content.split(';'):
#             statement = statement.strip()
#             if statement and not statement.startswith('--'):
#                 try:
#                     cursor.execute(statement)
#                 except Exception as e:
#                     print(f"Warning: {e}")
#         
#         conn.commit()
#         cursor.close()
#         conn.close()
#         
#         return {"status": "success", "message": "Base de données initialisée avec succès!"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# ── Lancement ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    # reload=False pour la production (Railway), True pour le développement local
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=dev_mode)