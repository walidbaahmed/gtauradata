# db.py
import hashlib
import streamlit as st

# --- Connexion PostgreSQL (pour accès direct à la base si besoin) -------------
try:
    import psycopg
except Exception:
    psycopg = None


@st.cache_resource
def get_connection():
    """
    Renvoie une connexion PostgreSQL (psycopg v3) en utilisant st.secrets['database']['url'].
    Compatible avec Supabase PostgreSQL.
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

    conn = psycopg.connect(dsn)
    return conn


# --- Connexion Supabase (API REST) -------------------------------------------
try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None


@st.cache_resource
def init_supabase() -> "Client":
    """
    Initialise et met en cache un client Supabase Python.
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
            "⚠️ Clés 'supabase.url' et/ou 'supabase.key' manquantes dans .streamlit/secrets.toml"
        ) from e

    return create_client(url, key)


supabase: "Client" = init_supabase()


# --- Authentification --------------------------------------------------------
def hash_password(password: str) -> str:
    """Retourne un hachage SHA-256 du mot de passe."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(email: str, password: str):
    """
    Vérifie les identifiants d’un utilisateur dans la table 'users'.
    Retourne un dictionnaire {id, email, name, role} si OK, sinon None.
    """
    try:
        pw_hash = hash_password(password)
        resp = (
            supabase.table("users")
            .select("id, email, name, password_hashed, roles(role)")
            .eq("email", email)
            .eq("password_hashed", pw_hash)
            .limit(1)
            .execute()
        )

        if resp.data and len(resp.data) > 0:
            return resp.data[0]  # ✅ retourne un objet user complet
        return None

    except Exception as e:
        st.error(f"Erreur de vérification utilisateur : {e}")
        return None


def create_user(email, name, password, role="consultant"):
    """
    Crée un nouvel utilisateur dans Supabase avec un rôle associé.
    """
    try:
        hashed = hash_password(password)
        insert = supabase.table("users").insert({
            "email": email,
            "name": name,
            "password_hashed": hashed,
            "is_active": True
        }).execute()

        if not insert or not insert.data:
            st.error("❌ Insertion utilisateur échouée.")
            return False

        user_id = insert.data[0].get("id")
        if not user_id:
            st.error("❌ Aucun ID utilisateur retourné.")
            return False

        supabase.table("roles").insert({
            "user_id": user_id,
            "role": role
        }).execute()

        st.success(f"✅ Utilisateur {email} créé avec succès.")
        return True

    except Exception as e:
        st.error(f"Erreur lors de la création de l’utilisateur : {e}")
        return False
