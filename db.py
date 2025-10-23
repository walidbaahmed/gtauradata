import hashlib
import psycopg2
import streamlit as st

# --- Hash mot de passe ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Connexion PostgreSQL (Supabase) ---
def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"],
            sslmode="require",  # Supabase demande SSL
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base : {e}")
        return None

def safe_close(conn, cur=None):
    try:
        if cur:
            cur.close()
    except Exception:
        pass
    try:
        if conn:
            conn.close()
    except Exception:
        pass

# --- Initialisation du schéma ---
def init_db():
    conn = get_connection()
    if not conn:
        st.error("Impossible de se connecter à la base de données.")
        return
    cur = conn.cursor()

    # UTILISATEURS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hashed TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            activated_once BOOLEAN DEFAULT FALSE
        );
    """)

    # ROLES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            role TEXT CHECK (role IN ('consultant','rh','admin')) DEFAULT 'consultant'
        );
    """)

    # FEUILLE DE TEMPS (jour par jour)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feuille_temps (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            statut_jour TEXT CHECK (statut_jour IN ('travail','télétravail','congé','maladie','RTT')) DEFAULT 'travail',
            valeur REAL CHECK (valeur IN (0, 0.5, 1)) DEFAULT 1,
            UNIQUE(user_id, date)
        );
    """)

    # ABSENCES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS absences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type_absence TEXT NOT NULL,
            date_debut DATE NOT NULL,
            date_fin DATE NOT NULL,
            commentaire TEXT,
            statut TEXT CHECK (statut IN ('En attente','Approuvée','Rejetée')) DEFAULT 'En attente',
            date_demande DATE DEFAULT CURRENT_DATE,
            justificatif TEXT
        );
    """)

    # VALIDATION ABSENCE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS validation_absence (
            id SERIAL PRIMARY KEY,
            absence_id INTEGER NOT NULL REFERENCES absences(id) ON DELETE CASCADE,
            validateur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date_validation DATE,
            statut TEXT CHECK (statut IN ('Approuvée','Rejetée')),
            commentaire TEXT
        );
    """)

    # STATUT MENSUEL DE FEUILLE DE TEMPS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feuille_temps_statut (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            annee INTEGER NOT NULL,
            mois INTEGER NOT NULL CHECK (mois BETWEEN 1 AND 12),
            statut TEXT CHECK (statut IN ('brouillon','en attente','validée','rejetée')) DEFAULT 'brouillon',
            motif_refus TEXT,
            PRIMARY KEY (user_id, annee, mois)
        );
    """)

    # PROJETS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projets (
            id SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            outil TEXT NOT NULL,
            heures_prevues INTEGER
        );
    """)

    # ATTRIBUTION PROJETS (avec date_fin attendue par ton code)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attribution_projet (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            projet_id INTEGER NOT NULL REFERENCES projets(id) ON DELETE CASCADE,
            date_debut DATE DEFAULT CURRENT_DATE,
            date_fin DATE,
            UNIQUE(user_id, projet_id)
        );
    """)

    # HEURES SAISIES PAR PROJET/JOUR
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heures_saisie (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            projet_id INTEGER NOT NULL REFERENCES projets(id) ON DELETE CASCADE,
            date_jour DATE NOT NULL,
            heures REAL NOT NULL DEFAULT 0,
            UNIQUE(user_id, projet_id, date_jour)
        );
    """)

    # PARAMETRES CP/RTT
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parametres_conges (
            annee INTEGER PRIMARY KEY,
            cp_total INTEGER NOT NULL,
            rtt_total INTEGER NOT NULL
        );
    """)

    # Index utiles (perf)
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_feuille_temps_user_date ON feuille_temps(user_id, date);""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_absences_user_dates ON absences(user_id, date_debut, date_fin);""")
    cur.execute("""CREATE INDEX IF NOT EXISTS idx_heures_user_date ON heures_saisie(user_id, date_jour);""")

    conn.commit()
    safe_close(conn, cur)
