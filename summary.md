# TranspoBot — Rapport de Synthèse

## 📋 Vue d'ensemble

**TranspoBot** est une application web de gestion de transport urbain qui intègre un assistant conversationnel intelligent. Elle permet aux gestionnaires d'une société de transport d'interroger leurs données opérationnelles en langage naturel, sans avoir à écrire de requêtes SQL manuellement.

Le projet a été développé comme un travail académique (Projet GLSi L3 — ESP/UCAD).

---

## 🛠️ Stack Technologique

### Backend
- **Framework** : FastAPI 0.104.1
- **Serveur ASGI** : Uvicorn 0.24.0
- **Validation des données** : Pydantic 2.8.0
- **Langage** : Python 3.x

### Base de données
- **SGBDR** : MySQL
- **Connecteur** : mysql-connector-python 8.2.0

### Authentification & Sécurité
- **Hachage de mots de passe** : bcrypt 4.1.1

### Intégrations externes
- **Client HTTP** : httpx 0.25.2 (pour les appels aux APIs)
- **Traitement des formulaires** : python-multipart 0.0.6

### Frontend
- **Markup** : HTML5
- **Langage de balisage** : Vanilla JavaScript

### Déploiement
- **Plateforme** : Railway
- **Configuration** : Procfile pour orchestration des processus

---

## 💾 Structure de la base de données

La base de données TranspoBot est organisée autour des tables suivantes :

### Entités principales
- **Véhicules** : Gestion des bus, minibus et taxis avec statut, kilométrage et maintenance
- **Chauffeurs** : Profils des chauffeurs avec permis, disponibilité et historique d'embauche
- **Lignes** : Trajets types avec origine, destination, distance et durée estimée
- **Tarifs** : Tarification segmentée (normal, étudiant, senior) par ligne

### Associations
- **Conduire** : Relation plusieurs-à-plusieurs entre chauffeurs et véhicules
- **Trajets** : Enregistrement des trajets effectués avec statut, passagers et recette

---

## ✨ Fonctionnalités

### Gestion opérationnelle
- Suivi des véhicules (statut, maintenance, kilométrage)
- Gestion des chauffeurs et de leurs affectations
- Enregistrement des trajets effectués
- Calcul des recettes par trajet

### Intelligence conversationnelle
- **Assistant LLM** : Interrogation des données en langage naturel
- **Requêtes dynamiques** : Génération de queries SQL à partir de questions en français/anglais
- **Accès simplifié** : Interface sans besoin de connaissances SQL

---

## 🏗️ Architecture

```
TranspoBot/
├── app.py              # Backend FastAPI avec routes API
├── index.html          # Interface utilisateur web
├── schema.sql          # Structure et données initiales de la BD
├── requirements.txt    # Dépendances Python
├── Procfile           # Configuration Railway
├── run.sh             # Script de lancement
└── README.md          # Documentation
```

### Initiative côté serveur
- Initialisation automatique de la base de données au démarrage
- Gestion adaptative de la configuration (MySQL_URL pour Railway)
- Middleware CORS pour les appels cross-origin

---

## 🚀 Déploiement

L'application est configurée pour fonctionner sur **Railway**, une plateforme de déploiement cloud moderne. La configuration utilise des variables d'environnement pour adapter le comportement à l'environnement d'exécution.

---

## 📝 Notes de développement

Le projet a été développé avec l'assistance de GitHub Copilot pour l'optimisation du code et la résolution de problèmes de compatible, ce qui a permis d'accélérer le processus de développement tout en maintenant la qualité du code.

---

**Date** : Avril 2026  
**Statut** : Production-ready  
**Licence** : Projet académique — ESP/UCAD
