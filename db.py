import psycopg2
import hashlib
import socket
import streamlit as st

# ✅ Connexion directe à Supabase PostgreSQL (IPv4 + SSL)
def get_connection():
    try:
        # ⚙️ Tes infos Supabase (modifie ici si besoin)
        host = "db.bzospgaanewvvcmzjpgj.supabase.co"
        database = "postgres"
        user = "postgres.bzospgaanewvvcmzjpgj"
        password = "Auradata@2025"  # 🔒 change si besoin
        port = "5432"

        # ✅ Forcer IPv4 (évite l’erreur gaierror / IPv6)
        ipv4_host = socket.gethostbyname(host)

        # ✅ Connexion sécurisée SSL
        conn = psycopg2.connect(
            host=ipv4_host,
            dbname=database,
            user=user,
            password=password,
            port=port,
            sslmode="require"
        )
        return conn

    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base : {e}")
        return None


# ✅ Hachage de mot de passe
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ✅ Vérifier un utilisateur
def verify_user(email, password):
    conn = get_connection()
    if not conn:
        return None

    hashed = hash_password(password)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.name, u.password_hashed, r.role
            FROM users u
            JOIN roles r ON u.id = r.user_id
            WHERE u.email = %s AND u.password_hashed = %s
        """, (email, hashed))
        user = cursor.fetchone()
        conn.close()
        return user

    except Exception as e:
        st.error(f"Erreur de base de données : {e}")
        return None


# ✅ Créer un utilisateur (admin, consultant, etc.)
def create_user(email, name, password, role="admin"):
    conn = get_connection()
    if not conn:
        return False

    hashed = hash_password(password)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, name, password_hashed, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (email, name, hashed))
        user_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO roles (user_id, role)
            VALUES (%s, %s)
        """, (user_id, role))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Erreur lors de la création de l’utilisateur : {e}")
        return False
