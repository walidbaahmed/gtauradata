import streamlit as st
from db import get_connection, hash_password
import psycopg2

# 🧭 Configuration de la page
st.set_page_config(page_title="Login", layout="wide")


# --- AUTHENTIFICATION ---
def authenticate(email, password):
    """Vérifie les identifiants de l'utilisateur dans la base PostgreSQL."""
    try:
        hashed = hash_password(password)
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.email, u.name, u.password_hashed, r.role
            FROM users u
            JOIN roles r ON u.id = r.user_id
            WHERE u.email = %s AND u.password_hashed = %s
        """, (email, hashed))

        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    except psycopg2.Error as e:
        st.error(f"Erreur de base de données : {e.pgerror or e}")
        return None


# --- INTERFACE UTILISATEUR ---
def show_login_page():

    # 🎨 Style CSS global
    st.markdown("""
        <style>
        :root { --brand:#000060; }

        .stApp { 
            background: linear-gradient(180deg, #f4f6ff 0%, #eef1ff 100%);
        }

        /* Carte / encadré du formulaire */
        div[data-testid="stForm"] {
            background-color: #f2f2f2;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 16px 40px rgba(0,0,96,0.12);
            padding: 2rem;
        }

        div[data-testid="stForm"] input:focus {
            outline: none !important;
            border-color: var(--brand) !important;
            box-shadow: 0 0 0 4px rgba(0,0,96,0.12) !important;
        }

        button[kind="primary"] {
            background-color: var(--brand) !important;
            color: white !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 🧭 Centrage du contenu
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo
        _, col_logo, _ = st.columns([2.2, 2, 2])
        with col_logo:
            st.image("assets/logo.png", width=200)
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        # Formulaire de connexion
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
                <h2 style="
                    text-align: center;
                    font-family: 'Times New Roman';
                    font-size: 30px;
                    font-weight: 700;
                    color: #000060;
                    text-shadow: 1px 1px 4px rgba(0,0,0,0.2);
                ">
                Connexion
                </h2>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            email = st.text_input("📧 Email")
            password = st.text_input("🗝️ Mot de passe", type="password")
            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Se connecter")

        # --- Gestion de la soumission ---
        if submitted:
            if not email or not password:
                st.warning("Veuillez entrer un email et un mot de passe.")
            else:
                user = authenticate(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = user[1]
                    st.session_state.username = user[2] if user[2] else user[1]
                    st.session_state.user_id = user[0]
                    st.session_state.role = user[4]
                    st.success("✅ Connexion réussie ! Redirection en cours...")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects ou utilisateur inexistant.")
