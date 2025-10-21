import psycopg2
import hashlib
import streamlit as st

# ✅ Connexion à Supabase PostgreSQL (SSL requis)
def get_connection():
    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
        sslmode="require"  # Supabase exige SSL
    )
    return conn


# ✅ Fonction de hachage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ✅ Initialisation de la base
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

    # ... (le reste de tes CREATE TABLE ici sans changer la logique) ...

    conn.commit()
    conn.close()
