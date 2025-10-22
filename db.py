from supabase import create_client, Client

import streamlit as st

import hashlib
 
# ✅ Initialize Supabase connection

@st.cache_resource

def init_supabase() -> Client:

    url = st.secrets["supabase"]["url"]

    key = st.secrets["supabase"]["key"]

    return create_client(url, key)
 
supabase = init_supabase()
 
# ✅ Password hashing

def hash_password(password: str) -> str:

    return hashlib.sha256(password.encode()).hexdigest()
 
# ✅ Authentication helper

def verify_user(email, password):

    hashed = hash_password(password)

    response = supabase.table("users").select("*").eq("email", email).eq("password_hashed", hashed).execute()

    if response.data and len(response.data) > 0:

        return response.data[0]

    return None
 
# ✅ Create user (only once, for admin initialization)

def create_user(email, name, password, role="admin"):

    hashed = hash_password(password)

    supabase.table("users").insert({

        "email": email,

        "name": name,

        "password_hashed": hashed,

        "is_active": True

    }).execute()

    user = supabase.table("users").select("id").eq("email", email).execute().data[0]

    supabase.table("roles").insert({

        "user_id": user["id"],

        "role": role

    }).execute()

    return True

 
