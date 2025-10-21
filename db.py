import psycopg2
import socket
import hashlib
import streamlit as st


# ✅ Hachage du mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ✅ Connexion à Supabase PostgreSQL (IPv4 + SSL)
def get_connection():
    host = st.secrets["postgres"]["host"]
    ipv4_host = socket.gethostbyname(host)

    conn = psycopg2.connect(
        host=ipv4_host,
        database=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
        sslmode="require"
    )
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hashed TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            activated_once BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY,
            role TEXT CHECK (role IN ('consultant', 'rh', 'admin')) DEFAULT 'consultant',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feuille_temps (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            statut_jour TEXT CHECK (statut_jour IN ('travail', 'télétravail', 'congé', 'maladie', 'RTT')) DEFAULT 'travail',
            valeur REAL CHECK (valeur IN (0, 0.5, 1)) DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type_absence TEXT NOT NULL,
            date_debut DATE NOT NULL,
            date_fin DATE NOT NULL,
            commentaire TEXT,
            statut TEXT CHECK (statut IN ('En attente', 'Approuvée', 'Rejetée')) DEFAULT 'En attente',
            date_demande DATE,
            justificatif TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_absence (
            id SERIAL PRIMARY KEY,
            absence_id INTEGER NOT NULL,
            validateur_id INTEGER NOT NULL,
            date_validation DATE,
            statut TEXT CHECK (statut IN ('Approuvée', 'Rejetée')),
            commentaire TEXT,
            FOREIGN KEY(absence_id) REFERENCES absences(id),
            FOREIGN KEY(validateur_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feuille_temps_statut (
            user_id INTEGER NOT NULL,
            annee INTEGER NOT NULL,
            mois INTEGER NOT NULL,
            statut TEXT CHECK (statut IN ('brouillon', 'en attente', 'validée', 'rejetée')) DEFAULT 'brouillon',
            motif_refus TEXT,
            PRIMARY KEY(user_id, annee, mois),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projets (
            id SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            outil TEXT NOT NULL,
            heures_prevues INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attribution_projet (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            projet_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(projet_id) REFERENCES projets(id),
            UNIQUE(user_id, projet_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heures_saisie (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            projet_id INTEGER NOT NULL,
            date_jour DATE NOT NULL,
            heures REAL NOT NULL,
            UNIQUE(user_id, projet_id, date_jour)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres_conges (
            annee INTEGER PRIMARY KEY,
            cp_total INTEGER NOT NULL,
            rtt_total INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()
