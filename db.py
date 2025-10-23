import psycopg2
import streamlit as st
import hashlib

PROJECT_REF = "bzospgaanewvvcmzjpgj"

def hash_password(pw: str) -> str:
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

def _build_cfg():
    cfg = st.secrets["postgres"]
    return {
        "host": cfg["host"],
        "port": int(cfg["port"]),
        "dbname": cfg["dbname"],
        "user": cfg["user"],
        "password": cfg["password"],
    }

def get_connection():
    # 1) Tente ce qui est dans secrets tel quel
    try:
        cfg = _build_cfg()
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            user=cfg["user"],
            password=cfg["password"],
            sslmode="require",
        )
        return conn
    except Exception as e1:
        st.warning(f"⚠️ Connexion échouée sur {st.secrets['postgres']['host']}:{st.secrets['postgres']['port']} en user={st.secrets['postgres']['user']}. Essai fallback…\n{e1}")

    # 2) Si on est sur le pooler mais mauvais user, retenter user suffixé
    try:
        cfg = _build_cfg()
        host = cfg["host"]
        if ".pooler.supabase.com" in host:
            user_try = f"postgres.{PROJECT_REF}"
            conn = psycopg2.connect(
                host=host,
                port=cfg["port"],
                dbname=cfg["dbname"],
                user=user_try,
                password=cfg["password"],
                sslmode="require",
            )
            st.info(f"✅ Connecté via pooler avec user={user_try}")
            return conn
    except Exception as e2:
        st.warning(f"⚠️ Essai pooler avec user suffixé échoué: {e2}")

    # 3) Fallback direct (5432)
    try:
        conn = psycopg2.connect(
            host=f"db.{PROJECT_REF}.supabase.co",
            port=5432,
            dbname="postgres",
            user="postgres",
            password=st.secrets["postgres"]["password"],
            sslmode="require",
        )
        st.info("✅ Connecté en direct (5432) — pensez à repasser au pooler pour la prod.")
        return conn
    except Exception as e3:
        st.error(f"❌ Aucune connexion possible (pooler & direct). Vérifiez host/user/password dans Supabase → Connect.\n{e3}")
        return None
