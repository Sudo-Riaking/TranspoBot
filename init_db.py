#!/usr/bin/env python3
"""
Script d'initialisation de la base de données MySQL
Crée le schéma complet avec données de test
"""

#!/usr/bin/env python3
"""
Script d'initialisation de la base de données MySQL
Crée le schéma complet avec données de test
"""

import mysql.connector
import os
import sys

# Charger les variables du .env manuellement
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

print("\n📌 Configuration MySQL")
print("=" * 50)

# Récupère depuis les variables d'environnement
host = os.getenv('DB_HOST', 'localhost')
user = os.getenv('DB_USER', 'root')
password = os.getenv('DB_PASSWORD', '')
database = os.getenv('DB_NAME', 'transpobot')

# Affiche les valeurs actuelles
print(f"Host:     {host}")
print(f"User:     {user}")
print(f"Password: {'***' if password else '(empty)'}")
print(f"Database: {database}")
print("=" * 50)

# Demande de modification
prompt = input("\nModifier la configuration? (y/n) [n]: ").strip().lower()
if prompt == 'y':
    host = input(f"Host [{host}]: ").strip() or host
    user = input(f"User [{user}]: ").strip() or user
    password = input(f"Password [***]: ").strip() or password
    database = input(f"Database [{database}]: ").strip() or database

DB_CONFIG = {
    'host': host,
    'user': user,
    'password': password,
    'database': database
}

SQL_INIT = """
-- Tables de base
CREATE TABLE IF NOT EXISTS vehicules (
    id_vehicule INT PRIMARY KEY AUTO_INCREMENT,
    immatriculation VARCHAR(20) UNIQUE NOT NULL,
    type ENUM('bus', 'minibus', 'taxi') NOT NULL,
    capacite INT NOT NULL,
    statut ENUM('actif', 'maintenance', 'hors_service') DEFAULT 'actif',
    kilometrage INT DEFAULT 0,
    date_acquisition DATE,
    date_dernier_maintenance DATE
);

CREATE TABLE IF NOT EXISTS chauffeurs (
    id_chauffeur INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    telephone VARCHAR(20),
    numero_permis VARCHAR(20) UNIQUE,
    categorie_permis VARCHAR(10),
    statut ENUM('actif', 'inactive', 'conge') DEFAULT 'actif',
    disponibilite ENUM('disponible', 'occupe', 'en_repos') DEFAULT 'disponible',
    date_embauche DATE
);

CREATE TABLE IF NOT EXISTS conduire (
    id_vehicule INT,
    id_chauffeur INT,
    date_affectation DATETIME DEFAULT NOW(),
    PRIMARY KEY (id_vehicule, id_chauffeur),
    FOREIGN KEY (id_vehicule) REFERENCES vehicules(id_vehicule) ON DELETE CASCADE,
    FOREIGN KEY (id_chauffeur) REFERENCES chauffeurs(id_chauffeur) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lignes (
    id_ligne INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    origine VARCHAR(100),
    destination VARCHAR(100),
    distance_km DECIMAL(10, 2),
    duree_minutes INT
);

CREATE TABLE IF NOT EXISTS tarifs (
    id_tarif INT PRIMARY KEY AUTO_INCREMENT,
    id_ligne INT NOT NULL,
    type_client VARCHAR(50),
    prix DECIMAL(10, 2),
    FOREIGN KEY (id_ligne) REFERENCES lignes(id_ligne) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trajets (
    id_trajet INT PRIMARY KEY AUTO_INCREMENT,
    id_ligne INT NOT NULL,
    id_chauffeur INT NOT NULL,
    id_vehicule INT NOT NULL,
    date_heure_depart DATETIME NOT NULL,
    date_heure_arrivee DATETIME,
    statut ENUM('planifie', 'en_cours', 'termine', 'annule') DEFAULT 'planifie',
    nb_passagers INT DEFAULT 0,
    recette DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (id_ligne) REFERENCES lignes(id_ligne) ON DELETE CASCADE,
    FOREIGN KEY (id_chauffeur) REFERENCES chauffeurs(id_chauffeur) ON DELETE CASCADE,
    FOREIGN KEY (id_vehicule) REFERENCES vehicules(id_vehicule) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS incidents (
    id_incident INT PRIMARY KEY AUTO_INCREMENT,
    id_trajet INT,
    type VARCHAR(50),
    description TEXT,
    gravite ENUM('faible', 'moyen', 'grave') DEFAULT 'moyen',
    date_heure_incident DATETIME DEFAULT NOW(),
    resolu BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_trajet) REFERENCES trajets(id_trajet) ON DELETE CASCADE
);
"""

# Données de test
SQL_SEED = """
-- Insérer des véhicules
INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition)
VALUES 
    ('TN-001-TN', 'bus', 50, 'actif', 45000, '2020-01-15'),
    ('TN-002-TN', 'bus', 50, 'actif', 38000, '2020-06-20'),
    ('TN-003-TN', 'minibus', 25, 'actif', 12000, '2021-03-10'),
    ('TN-004-TN', 'taxi', 5, 'maintenance', 105000, '2018-11-05'),
    ('TN-005-TN', 'minibus', 25, 'actif', 23000, '2021-09-12');

-- Insérer des chauffeurs
INSERT INTO chauffeurs (nom, prenom, email, telephone, numero_permis, categorie_permis, statut, disponibilite, date_embauche)
VALUES 
    ('Traore', 'Moussa', 'moussa.traore@transpobot.tn', '+216-71-234-567', 'TN123456', 'D', 'actif', 'disponible', '2019-02-01'),
    ('Ben Ali', 'Ahmed', 'ahmed.benali@transpobot.tn', '+216-71-345-678', 'TN234567', 'D', 'actif', 'occupe', '2019-05-15'),
    ('Guessous', 'Fatima', 'fatima.guessous@transpobot.tn', '+216-71-456-789', 'TN345678', 'D', 'actif', 'disponible', '2020-01-10'),
    ('Jellane', 'Karim', 'karim.jellane@transpobot.tn', '+216-71-567-890', 'TN456789', 'D', 'conge', 'en_repos', '2020-03-20'),
    ('Mami', 'Salah', 'salah.mami@transpobot.tn', '+216-71-678-901', 'TN567890', 'D', 'actif', 'disponible', '2021-06-15');

-- Insérer les affectations véhicule-chauffeur
INSERT INTO conduire (id_vehicule, id_chauffeur, date_affectation)
VALUES 
    (1, 1, '2023-01-01'),
    (2, 2, '2023-01-05'),
    (3, 3, '2023-02-01'),
    (4, 4, '2023-01-15');

-- Insérer des lignes
INSERT INTO lignes (code, nom, origine, destination, distance_km, duree_minutes)
VALUES 
    ('L1', 'Tunis - Sousse', 'Tunis', 'Sousse', 140, 180),
    ('L2', 'Tunis - Sfax', 'Tunis', 'Sfax', 320, 420),
    ('L3', 'Sousse - Gabès', 'Sousse', 'Gabès', 380, 500),
    ('L4', 'Tunis - Sidi Bouzid', 'Tunis', 'Sidi Bouzid', 250, 320),
    ('L5', 'Sfax - Djerba', 'Sfax', 'Djerba', 250, 340);

-- Insérer les tarifs
INSERT INTO tarifs (id_ligne, type_client, prix)
VALUES 
    (1, 'adulte', 18.5),
    (1, 'enfant', 9.25),
    (2, 'adulte', 35.0),
    (2, 'enfant', 17.5),
    (3, 'adulte', 42.0),
    (3, 'enfant', 21.0),
    (4, 'adulte', 28.0),
    (4, 'enfant', 14.0),
    (5, 'adulte', 28.0),
    (5, 'enfant', 14.0);

-- Insérer des trajets de test
INSERT INTO trajets (id_ligne, id_chauffeur, id_vehicule, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette)
VALUES 
    (1, 1, 1, '2024-04-10 08:00:00', '2024-04-10 11:00:00', 'termine', 48, 888.0),
    (1, 1, 1, '2024-04-10 12:30:00', '2024-04-10 15:30:00', 'termine', 50, 925.0),
    (2, 2, 2, '2024-04-10 07:00:00', '2024-04-10 12:00:00', 'termine', 49, 1715.0),
    (3, 3, 3, '2024-04-11 06:00:00', NULL, 'en_cours', 22, 924.0),
    (4, 1, 1, '2024-04-12 09:00:00', NULL, 'planifie', 0, 0),
    (1, 1, 1, '2024-04-12 14:00:00', NULL, 'planifie', 0, 0);

-- Insérer des incidents
INSERT INTO incidents (id_trajet, type, description, gravite, date_heure_incident, resolu)
VALUES 
    (1, 'retard_depart', 'Embouteillage à Tunis', 'faible', '2024-04-10 08:15:00', TRUE),
    (3, 'panne_moteur', 'Problème de surchauffe moteur', 'grave', '2024-04-10 10:30:00', FALSE),
    (4, 'incident_passager', 'Passager malade', 'moyen', '2024-04-11 08:45:00', TRUE);
"""

def init_database():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données TranspoBot...")
    
    try:
        # Connexion au serveur MySQL (sans base de données)
        print(f"📡 Connexion à MySQL ({DB_CONFIG['host']})...")
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Créer la base de données
        print(f"📦 Création de la base de données '{DB_CONFIG['database']}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']};")
        cursor.execute(f"USE {DB_CONFIG['database']};")
        
        # Créer les tables
        print("🗂️  Création des tables...")
        for statement in SQL_INIT.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        
        # Vérifier si les données existent
        cursor.execute("SELECT COUNT(*) FROM vehicules;")
        count = cursor.fetchone()[0]
        
        # Insérer les données de test si vides
        if count == 0:
            print("🌱 Insertion des données de test...")
            for statement in SQL_SEED.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except mysql.connector.Error as e:
                        # Ignorer les doublons
                        if "Duplicate entry" not in str(e):
                            print(f"⚠️  Avertissement: {e}")
            conn.commit()
        
        # Afficher un résumé
        cursor.execute("SELECT COUNT(*) FROM vehicules;")
        v_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chauffeurs;")
        c_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM trajets;")
        t_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM incidents;")
        i_count = cursor.fetchone()[0]
        
        print("\n✅ Base de données initialisée avec succès!")
        print(f"📊 Résumé:")
        print(f"   • Véhicules: {v_count}")
        print(f"   • Chauffeurs: {c_count}")
        print(f"   • Trajets: {t_count}")
        print(f"   • Incidents: {i_count}\n")
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ Erreur MySQL: {e}")
        print(f"\n💡 Assurez-vous que:")
        print(f"   • MySQL est en cours d'exécution")
        print(f"   • L'utilisateur '{DB_CONFIG['user']}' a les droits nécessaires")
        print(f"   • Vous pouvez vous connecter à '{DB_CONFIG['host']}'")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
