from supabase import create_client, Client
import streamlit as st
import hashlib

# ✅ Connexion à Supabase
@st.cache_resource
def init_supabase() -> Client:
    """
    Initialise la connexion Supabase à partir des secrets Streamlit.
    """
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# ✅ Fonction de hachage de mot de passe
def hash_password(password: str) -> str:
    """
    Hache un mot de passe avec SHA256.
    """
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ Authentification utilisateur
def verify_user(email: str, password: str):
    """
    Vérifie les identifiants d’un utilisateur.
    Retourne l’utilisateur si trouvé, sinon None.
    """
    hashed = hash_password(password)
    response = supabase.table("users").select("*").eq("email", email).eq("password_hashed", hashed).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

# ✅ Création d’un utilisateur (ex: admin au premier lancement)
def create_user(email: str, name: str, password: str, role: str = "admin"):
    """
    Crée un nouvel utilisateur avec son rôle associé.
    """
    hashed = hash_password(password)

    # Crée l'utilisateur
    supabase.table("users").insert({
        "email": email,
        "name": name,
        "password_hashed": hashed,
        "is_active": True
    }).execute()

    # Récupère son id
    user = supabase.table("users").select("id").eq("email", email).execute().data[0]

    # Associe un rôle
    supabase.table("roles").insert({
        "user_id": user["id"],
        "role": role
    }).execute()

    return True
