import hashlib
import psycopg2
import streamlit as st

# --- Fonction de hash du mot de passe ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# --- Connexion à la base Supabase PostgreSQL ---
def get_connection():
    try:
        conn = psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["dbname"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"],
            sslmode="require"  # 🔒 obligatoire pour Supabase
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base : {e}")
        return None


# --- Initialisation des tables ---
def init_db():
    conn = get_connection()
    if not conn:
        st.error("Impossible de se connecter à la base de données.")
        return

    cursor = conn.cursor()

    # ✅ TABLE users
    cursor.execute("""
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

    # ✅ TABLE roles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            role TEXT CHECK (role IN ('consultant', 'rh', 'admin')) DEFAULT 'consultant'
        );
    """)

    # ✅ TABLE feuille_temps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feuille_temps (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            date DATE NOT NULL,
            statut_jour TEXT CHECK (statut_jour IN ('travail', 'télétravail', 'congé', 'maladie', 'RTT')) DEFAULT 'travail',
            valeur REAL CHECK (valeur IN (0, 0.5, 1)) DEFAULT 1,
            UNIQUE(user_id, date)
        );
    """)

    # ✅ TABLE absences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absences (
