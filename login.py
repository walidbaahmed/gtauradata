import streamlit as st
from db import verify_user

st.set_page_config(page_title="Login", layout="wide")

def show_login_page():
    st.markdown("""
        <style>
        :root { --brand:#000060; }

        .stApp { 
            background: linear-gradient(180deg, #f4f6ff 0%, #eef1ff 100%);
        }

        div[data-testid="stForm"]{
            background-color: #f2f2f2;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 16px 40px rgba(0,0,96,0.12);
        }

        div[data-testid="stForm"] input:focus {
            outline: none !important;
            border-color: var(--brand) !important;
            box-shadow: 0 0 0 4px rgba(0,0,96,0.12) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        _, col_logo, _ = st.columns([2.2,2,2])
        with col_logo:
            st.image("assets/logo.png", width=200)

        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
                <h2 style="
                    text-align: center;
                    font-family: 'Times new roman';
                    font-size: 30px;
                    font-weight: 700;
                    color: #000060;
                    text-shadow: 1px 1px 4px rgba(0,0,0,0.2);
                ">Connexion</h2>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            email = st.text_input("📧 Email")
            password = st.text_input("🗝️ Mot de passe", type="password")
            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Se connecter")

        if submitted:
            try:
                user = verify_user(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = user["email"]
                    st.session_state.username = user["name"]
                    st.session_state.user_id = user["id"]
                    st.session_state.role = user.get("role", "consultant")
                    st.success("Connexion réussie ✅")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects ou utilisateur inexistant.")
            except Exception as e:
                st.error(f"❌ Erreur de connexion à la base : {e}")
