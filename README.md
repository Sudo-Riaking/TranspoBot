# 🚌 TranspoBot

> **Intelligence artificielle pour la gestion de transport urbain**  
> Un assistant conversationnel qui transforme vos données opérationnelles en insights en langage naturel.

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.2-4479A1?style=flat-square&logo=mysql)](https://www.mysql.com)
[![Groq](https://img.shields.io/badge/Groq%20API-LLM-FF6B35?style=flat-square)](https://groq.com)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python)](https://python.org)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D17?style=flat-square&logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/License-Academic%20Project-green?style=flat-square)](LICENSE)

[🚀 Déploiement Live](#-déploiement-live) • [📋 Fonctionnalités](#-fonctionnalités-clés) • [🛠️ Stack Technique](#-stack-technique) • [📖 Documentation Complète](summary.md)

</div>

---

## 📸 Démonstration

> ![alt text](20260421-0115-07.9845655.gif)

Utilisateurs en train d'interroger la base de données :
```
👤 Utilisateur : "Combien de trajets ont été effectués cette semaine ?"
🤖 TranspoBot : "Cette semaine, il y a eu 0 trajets terminés."

👤 Utilisateur : "Quel est le chauffeur avec le plus de revenus cette année ?"
🤖 TranspoBot : "Mamadou Diop avec 847500 FCFA."
```

---

## 🚀 Déploiement Live

L'application est déployée et accessible en production :

🔗 **[TranspoBot en ligne](https://transpobot-production-3025.up.railway.app/)**  

---

## ✨ Fonctionnalités Clés

### 🤖 Assistant Conversationnel Intelligent
- **Requêtes en langage naturel** : Interrogez vos données en français ou anglais
- **Génération SQL dynamique** : L'IA transforme les questions en requêtes SQL optimisées
- **Réponses intelligentes** : Récupération et formatage automatique des résultats

### 📊 Gestion Complète du Transport
- **Véhicules** : Suivi des bus, minibus et taxis (stato, kilométrage, maintenance)
- **Chauffeurs** : Gestion des profils, permis, disponibilité et affectations
- **Trajets** : Enregistrement en temps réel avec statut, passagers et recette
- **Incidents** : Suivi des pannes, accidents et retards
- **Tarification** : Gestion des tarifs par client (normal, étudiant, senior)

### 🔒 Sécurité & Contrôle
- **Accès en lecture seule** : Aucune modification accidentelle de données
- **Validation stricte** : Vérifications d'intégrité sur chaque requête
- **API robuste** : Gestion d'erreurs et authentification

### 📈 Rapports & Analyses
- **Métriques opérationnelles** : Recettes par ligne, etc.
- **Historique complet** : Traçabilité de tous les trajets et incidents
- **Requêtes personnalisées** : Créez vos propres analyses en langage naturel

---

## 🛠️ Stack Technique

### Backend
| Composant | Technologie | Version | Rôle |
|-----------|-------------|---------|------|
| **Framework Web** | FastAPI | 0.104.1 | API REST haute performance |
| **Serveur ASGI** | Uvicorn | 0.24.0 | Serveur application |
| **Validation** | Pydantic | 2.8.0 | Validation des données |
| **LLM** | Groq API | - | Inférence IA (llama-3.3-70b) |
| **Sécurité** | bcrypt | 4.1.1 | Hachage de mots de passe |

### Données
| Composant | Technologie |
|-----------|-------------|
| **SGBDR** | MySQL 8.2+ |
| **Connecteur** | mysql-connector-python 8.2.0 |
| **Initialisation** | SQL schema automatisé |

### Frontend
| Composant | Technologie |
|-----------|-------------|
| **Interface** | HTML5 + Vanilla JavaScript |
| **Communication** | Fetch API / CORS |
| **Styling** | CSS3 |

### Déploiement
| Composant | Technologie |
|-----------|-------------|
| **Plateforme** | Railway |
| **Configuration** | Procfile, variables d'environnement |
| **Intégrations** | MYSQL_URL, OPENAI_API_KEY, LLM_* |

---

## 🏗️ Architecture

```
TranspoBot/
├── app.py                    # Backend FastAPI + routes API
├── index.html               # Interface web utilisateur
├── schema.sql               # Structure & données DB
├── requirements.txt         # Dépendances Python
├── Procfile                 # Configuration Railway
├── run.sh                   # Script de lancement
├── .env                     # Variables d'environnement (local)
├── README.md               # Cette documentation (vitrine)
└── summary.md              # Documentation technique complète
```

### Flux de données
```
┌─────────────────┐
│   HTML/JS UI    │
└────────┬────────┘
         │ HTTP/JSON
         ↓
┌─────────────────────────────┐
│   FastAPI Backend           │
│ - Routing                   │ 
│ - Validation (Pydantic)     │
└────────┬────────────────────┘
         │ SQL Queries
         ↓
┌─────────────┐      ┌──────────────┐
│   MySQL DB  │      │  Groq LLM    │
│             │      │  (llama-70b) │
│  7 Tables   │      │              │
└─────────────┘      └──────────────┘
         │                    │
         └────────┬───────────┘
                  │ Insights
                  ↓
            [User Response]
```

---

## 🚀 Installation & Utilisation Locale

### Prérequis
- Python 3.8+
- MySQL 8.0+
- Clés API : Groq (pour le LLM)

### Étapes
```bash
# 1. Cloner le repo
git clone https://github.com/Sudo-Riaking/TranspoBot.git
cd TranspoBot

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos identifiants MySQL et clé Groq

# 5. Lancer l'application
bash run.sh
# ou
python -m uvicorn app:app --reload --port 8080
```

L'app sera accessible sur : **http://localhost:8080**

---

## 📚 Documentation

- **[Documentation Complète](summary.md)** — Architecture détaillée, structure de BD, et notes de développement
- **[Code Source](app.py)** — Backend FastAPI avec tous les endpoints
- **[Schéma DB](schema.sql)** — Structure MySQL complète

---

## 🔌 API Endpoints

### Principal
- `GET /` — Servir l'interface HTML
- `POST /query` — Interroger l'assistant  
  **Body** : `{"question": "Combien de trajets cette semaine ?"}`  
  **Response** : `{"sql": "SELECT ...", "explication": "...", "data": [...]}`

### Santé
- `GET /health` — Vérifier que l'API est accessible

---

## 💡 Exemples d'Utilisation

### Question 1 : Métriques simples
```
Utilisateur : "Combien de trajets ont été effectués cette semaine ?"

TranspoBot génère :
SELECT COUNT(*) AS total 
FROM trajets 
WHERE date_heure_depart >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
  AND statut = 'termine'

Réponse : "Cette semaine, il y a eu 156 trajets terminés."
```

### Question 2 : Analyse comparative
```
Utilisateur : "Quel chauffeur a le plus d'incidents ce mois-ci ?"

TranspoBot génère :
SELECT c.nom, c.prenom, COUNT(i.id_incident) AS nb_incidents
FROM chauffeurs c
JOIN trajets t ON c.id_chauffeur = t.id_chauffeur
JOIN incidents i ON t.id_trajet = i.id_trajet
WHERE MONTH(i.date_heure_incident) = MONTH(NOW())
GROUP BY c.id_chauffeur
ORDER BY nb_incidents DESC
LIMIT 1

Réponse : "Mamadou Ndiaye a 3 incidents signalés en avril."
```

### Question 3 : Requête complexe
```
Utilisateur : "Recette totale par ligne cette semaine, triée"

TranspoBot génère :
SELECT l.code, l.nom, SUM(t.recette) AS recette_totale
FROM lignes l
JOIN trajets t ON l.id_ligne = t.id_ligne
WHERE t.date_heure_depart >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND t.statut = 'termine'
GROUP BY l.id_ligne
ORDER BY recette_totale DESC

Réponse : "Voici la recette par ligne... [tableau]"
```

---

## 🔐 Sécurité & Bonnes Pratiques

✅ **Ce que TranspoBot fait**
- ✓ Génère uniquement des requêtes SELECT
- ✓ Limite les résultats avec LIMIT 100
- ✓ Valide tous les noms de colonnes
- ✓ Échappes les entrées utilisateur
- ✓ Journalise les requêtes sensibles

❌ **Ce qu'il ne peut pas faire**
- ✗ INSERT, UPDATE, DELETE (sécurité par défaut)
- ✗ Accéder à d'autres bases de données
- ✗ Exécuter du code arbitraire
- ✗ Contourner les permissions MySQL

---

## 🎓 Contexte Académique

**TranspoBot** est un projet de fin d'études développé dans le cadre du programme **Génie Logiciel (GLSi) L3** à l'**ESP/UCAD** (École Supérieure Polytechnique / Université Cheikh Anta Diop, Dakar).

**Inspiré par** : Services de transport urbain sénégalais types (Dakar Dem Dikk, Ndiaga Ndiaye, etc.)

---

## 👥 Contribution & Support

Les questions, suggestions et améliorations sont les bienvenues !

- 📧 **Email** : [À configurer]
- 🐛 **Issues** : [GitHub Issues](https://github.com/Sudo-Riaking/TranspoBot/issues)
- 📝 **Pull Requests** : Contributions sont bienvenues

---

## 📖 Notes de Développement

Le projet a bénéficié de l'optimisation des performances et de la résolution de problèmes de compatibilité grâce aux outils de développement modernes, permettant d'accélérer le processus de développement tout en maintenant la qualité du code.

Pour plus de détails techniques, architectural et historique du projet, consultez la [**documentation complète**](summary.md).

---

## 📄 License

Projet académique — ESP/UCAD  
Tous droits réservés © 2026

---

<div align="center">

**Fait avec ❤️ par les étudiants de GLSi L3**

[⬆ Retour au sommet](#-transpobot)

</div>
