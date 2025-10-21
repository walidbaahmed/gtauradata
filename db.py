import psycopg2
import hashlib
import streamlit as st

# ✅ Connexion à Supabase PostgreSQL (SSL obligatoire)
def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"],
            sslmode="require"  # Supabase exige SSL
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base : {e}")
        raise

# ✅ Fonction de hachage (sécurisée SHA-256)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ Initialisation de la base
def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # --- TABLE USERS ---
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

        # --- TABLE ROLES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                user_id INTEGER PRIMARY KEY,
                role TEXT CHECK (role IN ('consultant', 'rh', 'admin')) DEFAULT 'consultant',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # --- TABLE FEUILLE TEMPS ---
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

        # --- TABLE ABSENCES ---
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

        # --- TABLE VALIDATION ABSENCE ---
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

        # --- TABLE FEUILLE TEMPS STATUT ---
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

        # --- TABLE PROJETS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projets (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL,
                outil TEXT NOT NULL,
                heures_prevues INTEGER
            )
        """)

        # --- TABLE ATTRIBUTION PROJET ---
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

        # --- TABLE HEURES SAISIES ---
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

        # --- TABLE PARAMÈTRES CONGÉS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parametres_conges (
                annee INTEGER PRIMARY KEY,
                cp_total INTEGER NOT NULL,
                rtt_total INTEGER NOT NULL
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        st.success("✅ Base initialisée avec succès.")
    except Exception as e:
        st.error(f"❌ Erreur lors de l'initialisation : {e}")
