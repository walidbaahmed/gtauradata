import streamlit as st
from supabase import create_client
import hashlib

# ✅ Initialisation Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# ✅ Hachage de mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ Vérifier un utilisateur
def verify_user(email, password):
    hashed = hash_password(password)
    try:
        response = (
            supabase.table("users")
            .select("id, email, name, password_hashed, roles(role)")
            .eq("email", email)
            .eq("password_hashed", hashed)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erreur Supabase : {e}")
        return None

# ✅ Créer un utilisateur
def create_user(email, name, password, role="admin"):
    hashed = hash_password(password)
    try:
        user_insert = supabase.table("users").insert({
            "email": email,
            "name": name,
            "password_hashed": hashed,
            "is_active": True
        }).execute()

        user_id = user_insert.data[0]["id"]

        supabase.table("roles").insert({
            "user_id": user_id,
            "role": role
        }).execute()
        return True

    except Exception as e:
        st.error(f"Erreur lors de la création de l’utilisateur : {e}")
        return False
