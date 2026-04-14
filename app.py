"""
TranspoBot — Squelette Backend FastAPI
Projet GLSi L3 — ESP/UCAD
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Literal, Optional
import mysql.connector
import os
import re
import httpx
from datetime import datetime

# Charger les variables du .env manuellement
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

app = FastAPI(title="TranspoBot API", version="1.0.0") #Instance de l'application FastAPI

app.add_middleware(         
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
) #Configurer les CORS pour permettre les requêtes depuis n'importe quelle origine

# ── Configuration ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "transpobot"),
}

LLM_API_KEY  = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

# ── Schéma de la base (pour le prompt système) ─────────────────
DB_SCHEMA = """
Tables MySQL disponibles :

vehicules(id_vehicule, immatriculation, type[bus/minibus/taxi], capacite, statut[actif/maintenance/hors_service], kilometrage, date_acquisition, date_dernier_maintenance)
chauffeurs(id_chauffeur, nom, prenom, email, telephone, numero_permis, categorie_permis, statut[actif/suspendu/inactif], disponibilite, date_embauche)
conduire(id_vehicule, id_chauffeur, date_affectation) -- association chauffeurs ↔ véhicules
lignes(id_ligne, code, nom, origine, destination, distance_km, duree_minutes)
tarifs(id_tarif, id_ligne, type_client[normal/etudiant/senior], prix)
trajets(id_trajet, id_ligne, id_chauffeur, id_vehicule, date_heure_depart, date_heure_arrivee, statut[planifie/en_cours/termine/annule], nb_passagers, recette)
incidents(id_incident, id_trajet, type[panne/accident/retard/autre], description, gravite[faible/moyen/grave], date_heure_incident, resolu)
"""

SYSTEM_PROMPT = f"""Tu es TranspoBot, l'assistant intelligent de la compagnie de transport.
Tu aides les gestionnaires à interroger la base de données en langage naturel.

{DB_SCHEMA}

RÈGLES IMPORTANTES :
1. Génère UNIQUEMENT des requêtes SELECT (pas de INSERT, UPDATE, DELETE, DROP).
2. Réponds TOUJOURS en JSON avec ce format :
   {{"sql": "SELECT ...", "explication": "Ce que fait la requête"}}
3. Si la question ne peut pas être répondue avec SQL, réponds :
   {{"sql": null, "explication": "Explication de pourquoi"}}
4. Utilise des alias clairs dans les requêtes.
5. Limite les résultats à 100 lignes maximum avec LIMIT.
"""

# ── Connexion MySQL ────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(**DB_CONFIG) 

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
    """Vérifier qu'une entité existe avant de l'utiliser en FK"""
    try:
        result = execute_query(f"SELECT 1 FROM {table} WHERE {id_col} = {id_value} LIMIT 1")
        return len(result) > 0
    except:
        return False

def validate_trajet_fks(id_ligne: int, id_chauffeur: int, id_vehicule: int) -> tuple[bool, str]:
    """Valide toutes les FK pour un trajet"""
    if not check_fk_exists("lignes", "id_ligne", id_ligne):
        return False, f"Ligne {id_ligne} inexistante"
    if not check_fk_exists("chauffeurs", "id_chauffeur", id_chauffeur):
        return False, f"Chauffeur {id_chauffeur} inexistant"
    if not check_fk_exists("vehicules", "id_vehicule", id_vehicule):
        return False, f"Véhicule {id_vehicule} inexistant"
    return True, ""

def validate_incident_fk(id_trajet: int) -> tuple[bool, str]:
    """Valide la FK pour un incident"""
    if not check_fk_exists("trajets", "id_trajet", id_trajet):
        return False, f"Trajet {id_trajet} inexistant"
    return True, ""

# ── Appel LLM ─────────────────────────────────────────────────
async def ask_llm(question: str) -> dict: #Envoyer la question au LLM et récupérer la réponse
    async with httpx.AsyncClient() as client: #Créer un client HTTP asynchrone pour faire la requête à l'API du LLM
        response = await client.post( #Faire une requête POST à l'endpoint de chat completions de l'API du LLM
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
        content = response.json()["choices"][0]["message"]["content"]
        # Extraire le JSON de la réponse
        import json
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("Réponse LLM invalide")

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

        # ⚠️ SÉCURITÉ : Vérifier que le SQL commence bien par SELECT
        if not sql.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Requête non autorisée — seules les lectures (SELECT) sont permises")

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
    """Tableau de bord — statistiques rapides"""
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
        SELECT i.id_incident, i.type, i.description, i.gravite, i.date_heure_incident as date,
               i.resolu, t.id_trajet, l.nom as ligne, 
               CONCAT(ch.nom, ' ', ch.prenom) as chauffeur
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
        SELECT l.id_ligne, l.code, l.nom, l.origine, l.destination, 
               l.distance_km, l.duree_minutes
        FROM lignes l
        ORDER BY l.code
    """)

# ── Modèles POST ──────────────────────────────────────────────
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

# ── POST Endpoints ────────────────────────────────────────────
@app.post("/api/vehicules")
def create_vehicule(vehicule: VehiculeInput):
    """Créer un new véhicule"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            vehicule.immatriculation, vehicule.type, vehicule.capacite, 
            vehicule.statut, vehicule.kilometrage, vehicule.date_acquisition
        ))
        conn.commit()
        vehicule_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": vehicule_id, "message": "Véhicule créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chauffeurs")
def create_chauffeur(chauffeur: ChauffeurInput):
    """Créer un nouveau chauffeur"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            INSERT INTO chauffeurs (nom, prenom, email, telephone, numero_permis, 
                                   categorie_permis, statut, disponibilite, date_embauche)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            chauffeur.nom, chauffeur.prenom, chauffeur.email, chauffeur.telephone,
            chauffeur.numero_permis, chauffeur.categorie_permis, chauffeur.statut,
            chauffeur.disponibilite, chauffeur.date_embauche
        ))
        conn.commit()
        chauffeur_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": chauffeur_id, "message": "Chauffeur créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/trajets")
def create_trajet(trajet: TrajetInput):
    """Créer un nouveau trajet"""
    try:
        # Validation des clés étrangères
        valid, msg = validate_trajet_fks(trajet.id_ligne, trajet.id_chauffeur, trajet.id_vehicule)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            INSERT INTO trajets (id_ligne, id_chauffeur, id_vehicule, date_heure_depart, 
                                nb_passagers, recette, statut)
            VALUES (%s, %s, %s, %s, %s, %s, 'planifie')
        """
        cursor.execute(sql, (
            trajet.id_ligne, trajet.id_chauffeur, trajet.id_vehicule,
            trajet.date_heure_depart, trajet.nb_passagers, trajet.recette
        ))
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
    """Créer un nouvel incident"""
    try:
        # Validation de la clé étrangère
        valid, msg = validate_incident_fk(incident.id_trajet)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        
        # Utiliser la date actuelle si elle n'est pas fournie
        date_incident = incident.date_heure_incident or datetime.now().isoformat()
        
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            INSERT INTO incidents (id_trajet, type, description, gravite, 
                                  date_heure_incident, resolu)
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """
        cursor.execute(sql, (
            incident.id_trajet, incident.type, incident.description,
            incident.gravite, date_incident
        ))
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

# ── Lancement ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
