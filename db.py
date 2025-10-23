import socket
import hashlib
import psycopg2
import streamlit as st

PROJECT_REF = "bzospgaanewvvcmzjpgj"

# --- Fonction de hash du mot de passe ---
def hash_password(password: str) -> str:
    """Retourne le hash SHA256 du mot de passe."""
    return hashlib.sha256(password.encode()).hexdigest()


# --- Résolution IPv4 ---
def _ipv4(hostname: str) -> str | None:
    try:
        infos = socket.getaddrinfo(hostname, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        return infos[0][4][0] if infos else None
    except Exception:
        return None


# --- Connexion à la base Supabase ---
def get_connection():
    if "postgres" not in st.secrets:
        st.error("❌ [secrets.toml] section [postgres] manquante.")
        st.stop()

    cfg = st.secrets["postgres"]
    pwd = cfg.get("password", "")
    if not pwd:
        st.error("❌ Mot de passe PostgreSQL manquant (ne pas utiliser la clé anon/service).")
        st.stop()

    hosts = [
        cfg.get("host", "aws-1-eu-central-1.pooler.supabase.com"),
        "aws-0-eu-central-1.pooler.supabase.com"
    ]
    users = [f"postgres.{PROJECT_REF}", "postgres"]

    for host in hosts:
        for user in users:
            for ipv4 in (False, True):
                try:
                    conn = psycopg2.connect(
                        host=host,
                        port=6543,
                        dbname="postgres",
                        user=user,
                        password=pwd,
                        sslmode="require",
                        hostaddr=_ipv4(host) if ipv4 else None
                    )
                    st.info(f"✅ Connecté via pooler : {host} ({user}) IPv4={ipv4}")
                    return conn
                except Exception as e:
                    st.warning(f"⚠️ Échec pooler {host} ({user}) IPv4={ipv4} → {e}")

    # fallback direct
    direct = f"db.{PROJECT_REF}.supabase.co"
    for ipv4 in (False, True):
        try:
            conn = psycopg2.connect(
                host=direct,
                port=5432,
                dbname="postgres",
                user="postgres",
                password=pwd,
                sslmode="require",
                hostaddr=_ipv4(direct) if ipv4 else None
            )
            st.info(f"✅ Connecté en direct (IPv4={ipv4})")
            return conn
        except Exception as e:
            st.warning(f"⚠️ Échec direct IPv4={ipv4} → {e}")

    st.error("❌ Impossible de se connecter à Supabase.")
    st.stop()


# --- Initialisation DB ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # TABLE users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hashed TEXT NOT NULL,  -- ✅ cohérence
            is_active BOOLEAN DEFAULT TRUE,
            must_change_password BOOLEAN DEFAULT FALSE,
            activated_once BOOLEAN DEFAULT FALSE
        );
    """)

    # TABLE roles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            role TEXT CHECK (role IN ('consultant', 'rh', 'admin')) DEFAULT 'consultant'
        );
    """)

    conn.commit()
    conn.close()
