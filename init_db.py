#!/usr/bin/env python3
"""
Script d'initialisation pour Railway
Crée les tables et insère les données de test
"""

import mysql.connector
import os

# Railway fournit automatiquement ces variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'port': int(os.getenv('MYSQL_PORT', 3306))
}

print("📌 Configuration MySQL Railway")
print(f"Host: {DB_CONFIG['host']}")
print(f"Database: {DB_CONFIG['database']}")
print(f"User: {DB_CONFIG['user']}")

# Votre SQL d'initialisation (copié depuis schema.sql)
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
    statut ENUM('actif', 'suspendu', 'inactif') DEFAULT 'actif',
    disponibilite BOOLEAN DEFAULT TRUE,
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

-- Données de test
INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition) VALUES
    ('DK-1234-AB', 'bus', 60, 'actif', 45000, '2021-03-15'),
    ('DK-5678-CD', 'minibus', 25, 'actif', 32000, '2022-06-01'),
    ('DK-9012-EF', 'bus', 60, 'maintenance', 78000, '2019-11-20'),
    ('DK-3456-GH', 'taxi', 5, 'actif', 120000, '2020-01-10'),
    ('DK-7890-IJ', 'minibus', 25, 'actif', 15000, '2023-09-05');

INSERT INTO chauffeurs (nom, prenom, email, telephone, numero_permis, categorie_permis, statut, disponibilite, date_embauche) VALUES
    ('DIOP', 'Mamadou', 'mdiop@transpobot.sn', '+221771234567', 'P-2019-001', 'D', 'actif', TRUE, '2019-04-01'),
    ('FALL', 'Ibrahima', 'ifall@transpobot.sn', '+221772345678', 'P-2020-002', 'D', 'actif', TRUE, '2020-07-15'),
    ('NDIAYE', 'Fatou', 'fndiaye@transpobot.sn', '+221773456789', 'P-2021-003', 'B', 'actif', TRUE, '2021-02-01'),
    ('SECK', 'Ousmane', 'oseck@transpobot.sn', '+221774567890', 'P-2022-004', 'D', 'actif', TRUE, '2022-10-20'),
    ('BA', 'Aminata', 'aba@transpobot.sn', '+221775678901', 'P-2023-005', 'D', 'actif', FALSE, '2023-01-10');

INSERT INTO conduire (id_vehicule, id_chauffeur, date_affectation) VALUES
    (1, 1, '2021-04-01'),
    (2, 2, '2022-06-15'),
    (4, 3, '2021-02-10'),
    (5, 4, '2022-11-01'),
    (1, 5, '2023-02-01');

INSERT INTO lignes (code, nom, origine, destination, distance_km, duree_minutes) VALUES
    ('L1', 'Dakar - Thiès', 'Dakar', 'Thiès', 70.5, 90),
    ('L2', 'Dakar - Mbour', 'Dakar', 'Mbour', 82.0, 120),
    ('L3', 'Centre - Banlieue', 'Plateau', 'Pikine', 15.0, 45),
    ('L4', 'Aéroport', 'Centre-ville', 'AIBD', 45.0, 60);

INSERT INTO tarifs (id_ligne, type_client, prix) VALUES
    (1, 'normal', 2500), (1, 'etudiant', 1500),
    (2, 'normal', 3000), (2, 'etudiant', 1800),
    (3, 'normal', 500), (3, 'etudiant', 300),
    (4, 'normal', 5000), (4, 'etudiant', 3000);

INSERT INTO trajets (id_ligne, id_chauffeur, id_vehicule, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette) VALUES
    (1, 1, 1, NOW(), DATE_ADD(NOW(), INTERVAL 90 MINUTE), 'termine', 55, 137500),
    (1, 2, 2, NOW(), DATE_ADD(NOW(), INTERVAL 90 MINUTE), 'termine', 20, 50000),
    (2, 3, 4, NOW(), DATE_ADD(NOW(), INTERVAL 120 MINUTE), 'termine', 4, 12000),
    (3, 4, 5, NOW(), DATE_ADD(NOW(), INTERVAL 45 MINUTE), 'termine', 22, 11000),
    (1, 1, 1, NOW(), DATE_ADD(NOW(), INTERVAL 90 MINUTE), 'en_cours', 45, 112500);

INSERT INTO incidents (id_trajet, type, description, gravite, date_heure_incident, resolu) VALUES
    (1, 'retard', 'Embouteillage au centre-ville', 'faible', NOW(), TRUE),
    (2, 'panne', 'Crevaison pneu avant droit', 'moyen', NOW(), TRUE);
"""

def init_database():
    try:
        print("🔧 Connexion à MySQL Railway...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🗂️ Création des tables...")
        for statement in SQL_INIT.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        
        # Vérification
        cursor.execute("SELECT COUNT(*) FROM vehicules")
        v_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chauffeurs")
        c_count = cursor.fetchone()[0]
        
        print(f"\n✅ Base de données initialisée avec succès!")
        print(f"📊 Véhicules: {v_count}, Chauffeurs: {c_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    init_database()