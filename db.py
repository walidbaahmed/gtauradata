# db.py
import hashlib
import streamlit as st

# --- Base de données SQL (PostgreSQL via psycopg v3) -------------------------
# Assurez-vous d'avoir dans .streamlit/secrets.toml :
# [database]
# url = "postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require"
try:
    import psycopg
except Exception as e:
    psycopg = None


@st.cache_resource
def get_connection():
    """
    Renvoie une connexion PostgreSQL (psycopg v3) en utilisant st.secrets['database']['url'].
    Cette connexion est mise en cache par Streamlit (une instance par session).
    """
    if psycopg is None:
        raise RuntimeError(
            "Le module psycopg n'est pas disponible. "
            "Ajoutez 'psycopg[binary]' dans requirements.txt et redéployez."
        )
    try:
        dsn = st.secrets["database"]["url"]
    except Exception as e:
        raise RuntimeError(
            "Clé 'database.url' manquante dans .streamlit/secrets.toml"
        ) from e

    # Vous pouvez activer l'autocommit si nécessaire : conn.autocommit = True
    conn = psycopg.connect(dsn)
    return conn


# --- Client Supabase ----------------------------------------------------------
# Assurez-vous d'avoir dans .streamlit/secrets.toml :
# [supabase]
# url = "https://<your-project>.supabase.co"
# key = "<anon-or-service-role-key>"
try:
    from supabase import create_client, Client
except Exception:
    # Permettre à l'app de démarrer même si supabase n'est pas installé
    create_client = None
    Client = None


@st.cache_resource
def init_supabase() -> "Client":
    """
    Initialise le client Supabase et le met en cache.
    """
    if create_client is None:
        raise RuntimeError(
            "Le package 'supabase' n'est pas installé. "
            "Ajoutez 'supabase==2.5.1' dans requirements.txt."
        )
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception as e:
        raise RuntimeError(
            "Clés 'supabase.url' et/ou 'supabase.key' manquantes dans .streamlit/secrets.toml"
        ) from e
    return create_client(url, key)


# Objet client supabase utilisable partout (import depuis d'autres modules)
supabase: "Client" = init_supabase()


# --- Utilitaires d'authentification ------------------------------------------
def hash_password(password: str) -> str:
    """
    Hachage simple SHA-256 (à aligner avec ce que vous stockez dans la table 'users').
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(email: str, password: str) -> bool:
    """
    Vérifie les identifiants contre la table 'users' de Supabase
    (colonnes attendues : email, password_hashed).
    Adaptez ce code si vous utilisez une autre stratégie (GoTrue/Auth, RLS, etc.).
    """
    try:
        pw_hash = hash_password(password)
        resp = (
            supabase.table("users")
            .select("id, email, password_hashed")
            .eq("email", email)
            .eq("password_hashed", pw_hash)
            .limit(1)
            .execute()
        )
        return bool(resp.data)
    except Exception as e:
        # En cas d'erreur (schema, réseau…), on remonte une info claire à l'UI.
        st.error(f"Erreur de vérification utilisateur : {e}")
        return False
