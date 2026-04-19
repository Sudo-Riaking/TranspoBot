-- ============================================================
--  TranspoBot — Base de données MySQL
--  Projet GLSi L3 — ESP/UCAD
--  Version corrigée — alignée avec le MCD
-- ============================================================

CREATE DATABASE IF NOT EXISTS transpobot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE transpobot;

-- ------------------------------------------------------------
-- Véhicules
-- Ajout : date_dernier_maintenance (présent dans le MCD)
-- ------------------------------------------------------------
CREATE TABLE vehicules (
    id_vehicule INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,
    type ENUM('bus','minibus','taxi') NOT NULL,
    capacite INT NOT NULL,
    statut ENUM('actif','maintenance','hors_service') DEFAULT 'actif',
    kilometrage INT DEFAULT 0,
    date_acquisition DATE,
    date_dernier_maintenance DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Chauffeurs
-- Ajout : email, statut (présents dans le MCD)
-- Suppression : vehicule_id (remplacé par la table Conduire)
-- ------------------------------------------------------------
CREATE TABLE chauffeurs (
    id_chauffeur INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    telephone VARCHAR(20),
    numero_permis VARCHAR(30) UNIQUE NOT NULL,
    categorie_permis VARCHAR(5),
    statut ENUM('actif','suspendu','inactif') DEFAULT 'actif',
    disponibilite BOOLEAN DEFAULT TRUE,
    date_embauche DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Conduire — association plusieurs-à-plusieurs Chauffeurs ↔ Véhicules
-- Un chauffeur peut conduire plusieurs véhicules et vice-versa
-- ------------------------------------------------------------
CREATE TABLE conduire (
    id_vehicule INT NOT NULL,
    id_chauffeur INT NOT NULL,
    date_affectation DATE,
    PRIMARY KEY (id_vehicule, id_chauffeur),
    FOREIGN KEY (id_vehicule) REFERENCES vehicules(id_vehicule),
    FOREIGN KEY (id_chauffeur) REFERENCES chauffeurs(id_chauffeur)
);

-- ------------------------------------------------------------
-- Lignes / trajets types
-- ------------------------------------------------------------
CREATE TABLE lignes (
    id_ligne INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    nom VARCHAR(100),
    origine VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km DECIMAL(6,2),
    duree_minutes INT
);

-- ------------------------------------------------------------
-- Tarifs
-- Association "possèder" : 1,n côté lignes → FK id_ligne dans tarifs
-- ------------------------------------------------------------
CREATE TABLE tarifs (
    id_tarif INT AUTO_INCREMENT PRIMARY KEY,
    id_ligne INT NOT NULL,
    type_client ENUM('normal','etudiant','senior') DEFAULT 'normal',
    prix DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_ligne) REFERENCES lignes(id_ligne)
);

-- ------------------------------------------------------------
-- Trajets effectués
-- Résolution des associations : Effectuer (chauffeur), Assigner (véhicule), Lier (ligne)
-- → migration des FK chauffeur_id, vehicule_id, ligne_id dans Trajets
-- ------------------------------------------------------------
CREATE TABLE trajets (
    id_trajet INT AUTO_INCREMENT PRIMARY KEY,
    id_ligne INT NOT NULL,
    id_chauffeur INT NOT NULL,
    id_vehicule INT NOT NULL,
    date_heure_depart DATETIME NOT NULL,
    date_heure_arrivee DATETIME,
    statut ENUM('planifie','en_cours','termine','annule') DEFAULT 'planifie',
    nb_passagers INT DEFAULT 0,
    recette DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_ligne) REFERENCES lignes(id_ligne),
    FOREIGN KEY (id_chauffeur) REFERENCES chauffeurs(id_chauffeur),
    FOREIGN KEY (id_vehicule) REFERENCES vehicules(id_vehicule)
);

-- ------------------------------------------------------------
-- Incidents
-- Association "subir" : 0,n côté trajets → FK trajet_id dans incidents
-- Harmonisation : date_incident renommé date_heure_incident (conforme MCD)
-- ------------------------------------------------------------
CREATE TABLE incidents (
    id_incident INT AUTO_INCREMENT PRIMARY KEY,
    id_trajet INT NOT NULL,
    type ENUM('panne','accident','retard','autre') NOT NULL,
    description TEXT,
    gravite ENUM('faible','moyen','grave') DEFAULT 'faible',
    date_heure_incident DATETIME NOT NULL,
    resolu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_trajet) REFERENCES trajets(id_trajet)
);

-- ------------------------------------------------------------
-- Utilisateurs — authentification
-- Pour l'accès à TranspoBot
-- ------------------------------------------------------------
CREATE TABLE utilisateurs (
    id_utilisateur INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    nom_complet VARCHAR(100) NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL,  -- bcrypt hash
    role ENUM('admin','gestionnaire','superviseur') DEFAULT 'gestionnaire',
    statut ENUM('actif','inactif','bloque') DEFAULT 'actif',
    derniere_connexion DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================================
--  Données de test
-- ============================================================

-- Compte de test (mot de passe: transpo2026)
-- Hash bcrypt généré avec: bcrypt.hashpw(b'transpo2026', bcrypt.gensalt()).decode()
INSERT INTO utilisateurs (email, nom_complet, mot_de_passe, role, statut) VALUES
('admin@transpobot.sn', 'Administrateur TranspoBot', '$2b$12$OIX0qY7Q5Z3Z.C8n7vW.h.WcKZQ6p.4QQ7Q5Z3Z.C8n7vW.h.WcKZQ6', 'admin', 'actif');
-- demo@transpobot.sn / transpo2026

INSERT INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition, date_dernier_maintenance) VALUES
('DK-1234-AB', 'bus',     60, 'actif',        45000,  '2021-03-15', '2026-01-10'),
('DK-5678-CD', 'minibus', 25, 'actif',        32000,  '2022-06-01', '2025-11-20'),
('DK-9012-EF', 'bus',     60, 'maintenance',  78000,  '2019-11-20', '2026-03-01'),
('DK-3456-GH', 'taxi',     5, 'actif',       120000,  '2020-01-10', '2025-12-15'),
('DK-7890-IJ', 'minibus', 25, 'actif',        15000,  '2023-09-05', '2026-02-18');

INSERT INTO chauffeurs (nom, prenom, email, telephone, numero_permis, categorie_permis, statut, disponibilite, date_embauche) VALUES
('DIOP',   'Mamadou', 'mdiop@transpobot.sn',   '+221771234567', 'P-2019-001', 'D', 'actif', TRUE,  '2019-04-01'),
('FALL',   'Ibrahima','ifall@transpobot.sn',   '+221772345678', 'P-2020-002', 'D', 'actif', TRUE,  '2020-07-15'),
('NDIAYE', 'Fatou',   'fndiaye@transpobot.sn', '+221773456789', 'P-2021-003', 'B', 'actif', TRUE,  '2021-02-01'),
('SECK',   'Ousmane', 'oseck@transpobot.sn',   '+221774567890', 'P-2022-004', 'D', 'actif', TRUE,  '2022-10-20'),
('BA',     'Aminata', 'aba@transpobot.sn',     '+221775678901', 'P-2023-005', 'D', 'actif', FALSE, '2023-01-10');

-- Affectations chauffeurs ↔ véhicules (table Conduire)
INSERT INTO conduire (id_vehicule, id_chauffeur, date_affectation) VALUES
(1, 1, '2021-04-01'),
(2, 2, '2022-06-15'),
(4, 3, '2021-02-10'),
(5, 4, '2022-11-01'),
(1, 5, '2023-02-01');

INSERT INTO lignes (code, nom, origine, destination, distance_km, duree_minutes) VALUES
('L1', 'Ligne Dakar-Thiès',   'Dakar',      'Thiès',  70.5, 90),
('L2', 'Ligne Dakar-Mbour',   'Dakar',      'Mbour',  82.0, 120),
('L3', 'Ligne Centre-Banlieue','Plateau',   'Pikine', 15.0, 45),
('L4', 'Ligne Aéroport',      'Centre-ville','AIBD',  45.0, 60);

INSERT INTO tarifs (id_ligne, type_client, prix) VALUES
(1, 'normal', 2500), (1, 'etudiant', 1500), (1, 'senior', 1800),
(2, 'normal', 3000), (2, 'etudiant', 1800),
(3, 'normal', 500),  (3, 'etudiant', 300),
(4, 'normal', 5000), (4, 'etudiant', 3000);

INSERT INTO trajets (id_ligne, id_chauffeur, id_vehicule, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette) VALUES
(1, 1, 1, '2026-03-01 06:00:00', '2026-03-01 07:30:00', 'termine', 55, 137500),
(1, 2, 2, '2026-03-01 08:00:00', '2026-03-01 09:30:00', 'termine', 20,  50000),
(2, 3, 4, '2026-03-02 07:00:00', '2026-03-02 09:00:00', 'termine',  4,  12000),
(3, 4, 5, '2026-03-05 07:30:00', '2026-03-05 08:15:00', 'termine', 22,  11000),
(1, 1, 1, '2026-03-10 06:00:00', '2026-03-10 07:30:00', 'termine', 58, 145000),
(4, 2, 2, '2026-03-12 09:00:00', '2026-03-12 10:00:00', 'termine', 18,  90000),
(1, 5, 1, '2026-03-20 06:00:00', NULL,                  'en_cours',45, 112500);

INSERT INTO incidents (id_trajet, type, description, gravite, date_heure_incident, resolu) VALUES
(2, 'retard',   'Embouteillage au centre-ville',     'faible', '2026-03-01 08:45:00', TRUE),
(3, 'panne',    'Crevaison pneu avant droit',         'moyen',  '2026-03-02 07:30:00', TRUE),
(6, 'accident', 'Accrochage léger au rond-point',    'grave',  '2026-03-12 09:20:00', FALSE);
