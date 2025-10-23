# db.py
import hashlib
import psycopg2
import streamlit as st

# --- Hash de mot de passe ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Connexion DB (respecte STRICTEMENT secrets.toml) ---
def get_connection():
    """
    Utilise EXCLUSIVEMENT [postgres] dans .streamlit/secrets.toml :
      host, port, dbname, user, password, (optionnel) hostaddr pour forcer l'IPv4.
    Ne teste aucun autre host/port/user en arrière-plan.
    """
    if "postgres" not in st.secrets:
        st.error("❌ Section [postgres] manquante dans secrets.toml.")
        st.stop()

    cfg = st.secrets["postgres"]
    required = ("host", "port", "dbname", "user", "password")
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        st.error(f"❌ secrets.toml incomplet. Clés manquantes: {', '.join(missing)}")
        st.stop()

    kwargs = dict(
        host=cfg["host"],
        port=int(cfg["port"]),
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
        sslmode="require",
    )
    # Optionnel : forcer IPv4 si ton runtime casse en IPv6
    if cfg.get("hostaddr"):
        kwargs["hostaddr"] = cfg["hostaddr"]

    try:
        conn = psycopg2.connect(**kwargs)
        return conn
    except Exception as e:
        st.error("❌ Échec de connexion PostgreSQL. Vérifie secrets.toml (host/port/user/db/password) et, si besoin, renseigne hostaddr (IPv4).")
        st.exception(e)
        st.stop()

# --- Schéma minimal (cohérent avec password_hashed) ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            role TEXT CHECK (role IN ('consultant', 'rh', 'admin')) DEFAULT 'consultant'
        );
    """)

    conn.commit()
    conn.close()
