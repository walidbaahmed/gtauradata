import streamlit as st
from streamlit_option_menu import option_menu
from login import show_login_page

# --- Configuration de la page principale ---
st.set_page_config(
    page_title="GT Auradata",
    page_icon="assets/favicon.png",
    layout="wide"
)

# --- Style global ---
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

        /* Correction du flex cassé */
        .spacer {
            height: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Authentification ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    show_login_page()
else:
    # --- Barre latérale ---
    with st.sidebar:
        col1, col2, col3 = st.columns([0.5, 2, 0.5])
        with col2:
            st.image("assets/logo.png", width=130)

        st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

        selected = option_menu(
            "",
            [
                "Dashboard",
                "Feuille de temps",
                "Demande d'absence",
                "Validation absence",
                "Validation feuille",
                "", "",
                "Administration",
                "Compte rendu d'activité",
                "Guide utilisateur",
                "Déconnexion",
            ],
            icons=[
                "bar-chart", "clock", "file-earmark-text", "check-circle",
                "check-square", "\u200b", "\u200b", "gear",
                "journal-text", "book", "box-arrow-right"
            ],
            menu_icon="none",
            styles={
                "container": {
                    "background-color": "transparent",
                    "width": "230px",
                    "padding": "0px",
                    "margin": "0px",
                },
                "nav-link": {
                    "font-size": "14px",
                    "font-family": "Segoe UI",
                    "text-align": "left",
                    "padding": "10px",
                    "margin": "0px",
                    "color": "#333333",
                },
                "nav-link-selected": {
                    "background-color": "#080686",
                    "color": "white",
                    "font-weight": "bold",
                },
            },
        )

    # --- Navigation principale ---
    if selected == "Dashboard":
        try:
            import dashboard
            dashboard.show_dashboard()
        except Exception as e:
            st.error(f"Erreur chargement Dashboard : {e}")

    elif selected == "Feuille de temps":
        try:
            import feuille_temps
            feuille_temps.show_feuille_temps()
        except Exception as e:
            st.error(f"Erreur chargement Feuille de temps : {e}")

    elif selected == "Demande d'absence":
        try:
            import demande_absence
            demande_absence.show_demande_absence()
        except Exception as e:
            st.error(f"Erreur chargement Demande d'absence : {e}")

    elif selected == "Validation absence":
        try:
            import validation_absence
            validation_absence.show_validation_absence()
        except Exception as e:
            st.error(f"Erreur chargement Validation absence : {e}")

    elif selected == "Validation feuille":
        try:
            import validation_feuille
            validation_feuille.show_validation_feuille()
        except Exception as e:
            st.error(f"Erreur chargement Validation feuille : {e}")

    elif selected == "Administration":
        try:
            import admin
            admin.show_admin()
        except Exception as e:
            st.error(f"Erreur chargement Administration : {e}")

    elif selected == "Compte rendu d'activité":
        try:
            import compte_rendu_activite
            compte_rendu_activite.show_compte_rendu_activite()
        except Exception as e:
            st.error(f"Erreur chargement Compte rendu : {e}")

    elif selected == "Guide utilisateur":
        try:
            import guide_utilisateur
            guide_utilisateur.show_guide_utilisateur()
        except Exception as e:
            st.error(f"Erreur chargement Guide utilisateur : {e}")

    elif selected == "Déconnexion":
        st.session_state.logged_in = False
        st.success("Vous avez été déconnecté.")
        st.rerun()
