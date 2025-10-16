import streamlit as st
from db import get_connection, hash_password

st.set_page_config(page_title="Login", layout="wide")

def authenticate(email, password):
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
    conn.close()
    return user

def show_login_page():

    st.markdown("""
        <style>
        :root { --brand:#000060; }

        .stApp { 
            background: linear-gradient(180deg, #f4f6ff 0%, #eef1ff 100%);
        }

        /* Carte/encadré du formulaire */
        div[data-testid="stForm"]{
            background-color: #f2f2f2;
            
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 16px 40px rgba(0,0,96,0.12);
        }

        /* Inputs : focus visible et propre */
        div[data-testid="stForm"] input:focus {
            outline: none !important;
            border-color: var(--brand) !important;
            box-shadow: 0 0 0 4px rgba(0,0,96,0.12) !important;
        }

        </style>
    """, unsafe_allow_html=True)

    # Centrage
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        _, col_logo, _ = st.columns([2.2,2,2])
        with col_logo:
            st.image("assets/logo.png", width=200)
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        # --- FORMULAIRE ENCADRÉ (pas de div markdown !) ---
        with st.form("login_form", clear_on_submit=False):

            st.markdown("""
                <h2 style="
                    text-align: center;
                    font-family: 'Times new roman';
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

        # Gestion de la soumission
        if submitted:
            user = authenticate(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = user[1]
                st.session_state.username = user[2] if user[2] else user[1]
                st.session_state.user_id = user[0]
                st.session_state.role = user[4]
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Identifiants incorrects.")



# import streamlit as st
# import hashlib
# from db import get_connection, hash_password

# # Flag de développement (à désactiver en production)
# DEV_MODE = True

# def authenticate(email, password):
#     hashed = hash_password(password)
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT u.id, u.email, u.name, u.password_hashed, r.role
#         FROM users u
#         JOIN roles r ON u.id = r.user_id
#         WHERE u.email = ? AND u.password_hashed = ?
#     """, (email, hashed))
#     user = cursor.fetchone()
#     conn.close()
#     return user

# def dev_auto_login():
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT u.id, u.email, u.name, u.password_hashed, r.role
#         FROM users u
#         JOIN roles r ON u.id = r.user_id
#         WHERE u.email = ?
#     """, ("daniella.rakotondratsimba@auradata.fr",))
#     user = cursor.fetchone()
#     conn.close()

#     if user:
#         st.session_state.logged_in = True
#         st.session_state.user_email = user[1]
#         st.session_state.username = user[2] if user[2] else user[1]
#         st.session_state.user_id = user[0]
#         st.session_state.role = user[4]
#         st.rerun()

# def show_login_page():
#     st.title("Connexion 🔐")

#     # Connexion automatique en dev
#     if DEV_MODE and 'logged_in' not in st.session_state:
#         dev_auto_login()

#     email = st.text_input("Email")
#     password = st.text_input("Mot de passe", type="password")

#     if st.button("Se connecter"):
#         user = authenticate(email, password)
#         if user:
#             st.session_state.logged_in = True
#             st.session_state.user_email = user[1]
#             st.session_state.username = user[2] if user[2] else user[1]
#             st.session_state.user_id = user[0]
#             st.session_state.role = user[4]

#             st.success("Connexion réussie !")
#             st.rerun()
#         else:
#             st.error("Identifiants incorrects.")
