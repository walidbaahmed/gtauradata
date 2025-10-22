import streamlit as st
from streamlit_option_menu import option_menu
from db import verify_user, create_user
 
st.set_page_config(page_title="GT Auradata", page_icon="assets/favicon.png", layout="wide")
 
# --- Custom CSS ---
st.markdown("""
<style>
        [data-testid="stSidebar"] > div:first-child {
            overflow-y: hidden;
        }
        .nav-link:has(span:not(:empty)):hover {
            background-color: blue !important;
            cursor: pointer;
        }
        .nav-link:has(span:empty):hover {
            background-color: transparent !important;
            cursor: default;
        }
</style>
""", unsafe_allow_html=True)
 
 
# --- Login Page ---
def show_login_page():
    st.title("🔐 Connexion - GT Auradata")
 
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
 
        if submitted:
            user = verify_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Bienvenue {user['name']} 👋")
                st.rerun()
            else:
                st.error("❌ Email ou mot de passe incorrect.")
 
 
# --- Sidebar Menu ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    show_login_page()
else:
    with st.sidebar:
        col1, col2, col3 = st.columns([0.5, 2, 0.5])
        with col2:
            st.image("assets/logo.png", width=130)
 
        selected = option_menu(
            "",
            ["Dashboard", "Feuille de temps", "Demande d'absence", "Validation absence",
             "Validation feuille", "", "", "Administration", "Compte rendu d'activité",
             "Guide utilisateur", "Déconnexion"],
            icons=["bar-chart", "clock", "file-earmark-text", "check-circle", "check-square",
                   "\u200b", "\u200b", "gear", "journal-text", "book", "box-arrow-right"],
            menu_icon="none",
            styles={
                "container": {"background-color": "transparent", "width": "230px", "padding": "0px", "margin": "0px"},
                "nav-link": {"font-size": "14px", "font-family": "Segoe UI", "text-align": "left",
                             "padding": "10px", "margin": "0px", "color": "#333333"},
                "nav-link-selected": {"background-color": "#080686", "color": "white", "font-weight": "bold"},
            }
        )
 
    if selected == "Dashboard":
        st.title("📊 Tableau de bord")
        st.info("Section du dashboard à venir.")
 
    elif selected == "Feuille de temps":
        st.title("🕓 Feuille de temps")
        st.info("Module Feuille de temps à venir.")
 
    elif selected == "Demande d'absence":
        st.title("📄 Demande d'absence")
        st.info("Module Demande d'absence à venir.")
 
    elif selected == "Validation absence":
        st.title("✅ Validation des absences")
        st.info("Module Validation absence à venir.")
 
    elif selected == "Validation feuille":
        st.title("🧾 Validation des feuilles")
        st.info("Module Validation feuille à venir.")
 
    elif selected == "Administration":
        st.title("⚙️ Administration")
        st.info("Module Administration à venir.")
 
    elif selected == "Compte rendu d'activité":
        st.title("🧭 Compte rendu d'activité")
        st.info("Module Compte rendu à venir.")
 
    elif selected == "Guide utilisateur":
        st.title("📘 Guide utilisateur")
        st.info("Guide utilisateur à venir.")
 
    elif selected == "Déconnexion":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
