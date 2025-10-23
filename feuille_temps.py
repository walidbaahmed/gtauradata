import streamlit as st
import pandas as pd
import calendar
from datetime import date, datetime, timedelta
from db import get_connection
import holidays
from io import BytesIO
import io
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import plotly.express as px

st.set_page_config(page_title="Feuille de temps", layout="wide")

def show_feuille_temps():

    if "user_id" not in st.session_state:
        st.error("Vous devez être connecté pour accéder à cette page.")
        st.stop()

    user_id = st.session_state["user_id"]

    st.markdown("""
        <div id="title">
            <h4> Feuille de temps </h4>  
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        .stApp {
            background-color: #f2f2f2;     
        }
        .block-container {
            padding-top: 1.5rem !important;
            margin-top: 0 !important;
        }
        .main .block-container {
            margin-top: 0rem !important;
        }
        header {
            visibility: hidden;
            height: 0px;
        }
        .stButton > button, .stDownloadButton > button {
            background-color: #000060;      
            color: white;                   
            font-size: 16px;
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0, 0, 96, 0.3);
            transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background-color: #f0f0f0; 
            color: #000060;
            box-shadow: 0 6px 12px rgba(0, 0, 96, 0.6);
            transform: translateY(-3px);
        }
        .stButton > button:active, .stDownloadButton > button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0, 0, 96, 0.2);
        }
        #title {
            position: fixed;
            top: 0;
            left: 275px;
            background-color: #f2f2f2;
            z-index: 999;
            width:100%;
            padding: 10px 20px;
            margin-bottom: 0px;
        }
        #title h4 {
            font-size: 24px;
            font-weight: 600;
            color: #000060;
            margin: 0;
            font-family: 'New Icon';
            border-bottom: 3px solid #000060;
            padding-bottom: 6px;
            display: inline-block;
        }
        div[data-baseweb="select"] {
            background-color: #f0f0f5;
            color: black;
            border-radius: 8px;
        }
        div[data-baseweb="select"] > div {
            color: #333333;
        }
        .card-box {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 1rem;
        }
        .card-title {
            font-size: 14px;
            font-weight: bold;
            color: #000066;
            margin-bottom: 0.8rem;
            border-bottom: 1px solid #ccc;
            padding-bottom: 0.3rem;
        }
        .month-highlight {
            color: #1a40af;
            font-weight: 700;
            font-family: 'New Icon';
            font-size: 30px;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 20px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
        }
        .status-badge {
            font-size: 13px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 12px;
            color: white;
            display: inline-block;
            min-width: 90px;
            margin-top: 10px;
            padding-bottom: 6px;
        }
        .validée { background-color: #4CAF50 !important; }
        .rejetée { background-color: #F44336 !important; }
        .en-attente { background-color: #FFA500 !important; }
        table {
            width: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #222;
        }
        th {
            background-color: #080686;
            color: white;
            font-weight: 700;
            padding: 10px 12px;
            text-align: center !important;
            user-select: none;
        }
        td {
            background-color: white;
            padding: 10px 12px;
            text-align: center;
            vertical-align: middle;
        }
        .refus-card {
            background-color: #ffcccc;
            padding: 1rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 1rem;
            border: 1px solid #f5c2c7;
        }
        .refus-card h4 {
            margin: 0 0 5px 0;
            font-size: 16px;
            color: #b00020;
        }
        .refus-card p {
            margin: 0;
            font-size: 14px;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Saisie feuille de temps", "Saisie heures", "Mes projets", "Historique de validation"])

    # Saisie feuille
    with tab1:

        col_select, _, col_heures, col_statut = st.columns([2, 1, 1.5, 1.5])

        with col_select:
            conn = get_connection()

            mois_noms = [calendar.month_name[m] for m in range(1, 13)]
            col_mois, col_annee = st.columns(2)
            with col_mois:
                mois_selectionne = st.selectbox("📅 Mois", mois_noms, index=datetime.today().month - 1)
                mois = mois_noms.index(mois_selectionne) + 1
            with col_annee:
                annee = st.selectbox(
                    "📆 Année",
                    list(range(2020, 2031)),
                    index=list(range(2020, 2031)).index(datetime.today().year)
                )
            mois_str = f"{mois:02d}"
            annee_str = str(annee)

            cal = calendar.Calendar(firstweekday=0)
            jours_mois = list(cal.itermonthdates(annee, mois))

            debut_periode = date(annee, mois, 1)
            fin_periode = date(annee, mois, calendar.monthrange(annee, mois)[1])

            df_abs = pd.read_sql_query(
                """
                SELECT date_debut, date_fin, type_absence
                FROM absences
                WHERE user_id = %s AND statut = 'Approuvée'
                AND (
                    (date_debut BETWEEN %s AND %s)
                    OR (date_fin BETWEEN %s AND %s)
                    OR (date_debut <= %s AND date_fin >= %s)
                )
                """,
                conn,
                params=(user_id, debut_periode, fin_periode, debut_periode, fin_periode, debut_periode, fin_periode)
            )

            abs_dict = {}
            for _, row in df_abs.iterrows():
                start = pd.to_datetime(row["date_debut"]).date()
                end = pd.to_datetime(row["date_fin"]).date()
                for i in range((end - start).days + 1):
                    abs_dict[start + timedelta(days=i)] = row["type_absence"]

            emoji_absences = {
                "Maladie": "🤒",
                "Congé payé": "🏖️",
                "RTT": "🕶️",
                "Télétravail": "💻",
                "Congé sans soldes": "🏖️",
            }

            # Unifier l'API jours fériés
            feries = holidays.France(years=[annee])
            feries_dict = {jour: nom for jour, nom in feries.items() if jour.month == mois}

            valeurs_saisies = {}

            df_feuille = pd.read_sql_query(
                """
                SELECT date, valeur FROM feuille_temps
                WHERE user_id = %s 
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(YEAR FROM date) = %s
                """,
                conn,
                params=(user_id, int(mois_str), int(annee_str)),
                parse_dates=["date"]
            )
            df_feuille.set_index("date", inplace=True)

        with col_statut:
            st.markdown("<div style='margin-top:50px;'></div>", unsafe_allow_html=True)  # guillemet corrigé

            cur = conn.cursor()
            cur.execute(
                """
                SELECT statut FROM feuille_temps_statut
                WHERE user_id = %s AND annee = %s AND mois = %s
                """,
                (user_id, annee, mois)
            )
            row_statut = cur.fetchone()
            if row_statut:
                statut_feuille = row_statut[0]
            else:
                statut_feuille = 'brouillon'
                cur.execute(
                    """
                    INSERT INTO feuille_temps_statut (user_id, annee, mois, statut)
                    VALUES (%s, %s, %s, 'brouillon')
                    """,
                    (user_id, annee, mois)
                )
                conn.commit()

            statut_couleurs = {
                "brouillon": ("#fff3cd", "#856404"),
                "rejetée": ("#f8d7da", "#721c24"),
                "en attente": ("#d1ecf1", "#0c5460"),
                "validée": ("#d4edda", "#155724"),
            }

            bg_color, text_color = statut_couleurs.get(statut_feuille, ("#eeeeee", "#333"))

            st.markdown(f"""
                <div style='
                    background-color: {bg_color};
                    color: {text_color};
                    padding: 0.8rem;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                    border-left: 6px solid {text_color}; 
                    text-align: center;
                    margin-bottom: 0.7rem;
                '>
                    Statut actuel de la feuille : <span style='text-transform: capitalize;'>{statut_feuille}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_heures:
            if "mode_modification" not in st.session_state:
                st.session_state["mode_modification"] = True
            total_heures_preview = 0
            for jour, row in df_feuille.iterrows():
                if jour.date().weekday() < 5:
                    val = row["valeur"]
                    if val == 1:
                        total_heures_preview += 8
                    elif val == 0.5:
                        total_heures_preview += 3

            st.markdown(f"""
                <div style='
                    background:#f8f9fa; 
                    padding:1rem; 
                    border-radius:12px; 
                    box-shadow:0 3px 6px rgba(0,0,0,0.1); 
                    text-align:center; 
                    margin-top:0.7rem;
                '>
                    <div style='font-size:1.8rem; font-weight:bold; color:#000066;'>⏱️ {total_heures_preview}</div>
                    <div style='font-size:0.9rem; font-weight:500; color:#666;'>Nombre d'heures travaillées</div>
                </div>
            """, unsafe_allow_html=True)

        if "mois_selectionne" not in st.session_state or st.session_state["mois_selectionne"] != (mois, annee):
            st.session_state["mois_selectionne"] = (mois, annee)
            st.session_state["mode_modification"] = df_feuille.empty

        jours_utiles = [
            jour for jour in jours_mois
            if jour.month == mois and jour.weekday() < 5 and jour not in abs_dict and jour not in feries_dict
        ]
        feuille_complete = all(jour in df_feuille.index.date for jour in jours_utiles)

        if "mode_modification" not in st.session_state:
            st.session_state["mode_modification"] = df_feuille.empty

        can_edit = st.session_state["mode_modification"] and statut_feuille in ['brouillon', 'rejetée']

        style_case = """
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 95px;
            min-width: 85px;
            padding: 8px 6px;
            border-radius: 10px;
            border: 1px solid #ddd;
            font-size: 14px;
            box-sizing: border-box;
            background: #ffffff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        """

        st.markdown(f"""
                <h3 style='
                    color: #000060;
                    font-family: ' New Icon';
                    font-weight: 700;
                    font-size: 28px;
                    margin-bottom: 12px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                '>
                📅 Feuille de temps - <span class='month-highlight'>{mois_selectionne} {annee}</span></h3>
                </h3>
            """, unsafe_allow_html=True)

        jours_du_mois = [jour for jour in jours_mois if jour.month == mois]
        milieu = len(jours_du_mois) // 2
        jours_premiere_ligne = jours_du_mois[:milieu]
        jours_deuxieme_ligne = jours_du_mois[milieu:]

        def nom_jour(jour):
            jours_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
            return jours_fr[jour.weekday()]

        def afficher_jours(jours_ligne):
            cols = st.columns(len(jours_ligne), gap="small")

            for i, jour in enumerate(jours_ligne):
                val_init = 1
                if jour in df_feuille.index:
                    val_init = df_feuille.loc[jour]["valeur"]

                is_weekend = (jour.weekday() >= 5)
                is_absence = (jour in abs_dict)
                is_ferie = (jour in feries_dict)

                with cols[i]:
                    if is_weekend:
                        st.markdown(f"""
                            <div style='{style_case} background:#f0f0f0; color:#999;'>
                                <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                                <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                                <div style='font-size:12px; text-align:center;'>Weekend</div>
                            </div>
                        """, unsafe_allow_html=True)

                    elif is_ferie:
                        nom_ferie = feries_dict[jour]
                        st.markdown(f"""
                            <div style='{style_case} background:#ffe6e6; color:#cc0000;'>
                                <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                                <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                                <div style='font-size:12px; text-align:center;'>{nom_ferie}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    elif is_absence:
                        type_abs = abs_dict[jour]
                        emoji = emoji_absences.get(type_abs, "")
                        st.markdown(f"""
                            <div style='{style_case} background:#fff4e5; color:#cc6600;'>
                                <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                                <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                                <div style='font-size:12px; text-align:center;'>{emoji} {type_abs}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    else:
                        st.markdown(f"""
                            <div style='font-size:12px; color:#666; text-align:center;'>{nom_jour(jour)}</div>
                            <div style='text-align:center; font-weight:600; font-size:18px; color:#000066;'>{jour.day}</div>
                        """, unsafe_allow_html=True)

                        choix = st.selectbox(
                            label=f"{jour}",
                            options=[1, 0.5],
                            index=0 if val_init == 1 else 1,
                            key=str(jour),
                            label_visibility="collapsed",
                            disabled=not can_edit
                        )
                        valeurs_saisies[jour] = choix

        afficher_jours(jours_premiere_ligne)
        afficher_jours(jours_deuxieme_ligne)

        col1, col2, col3 = st.columns(3)
        with col1:
            if can_edit:
                if st.button("Enregistrer la feuille de temps", use_container_width=True):
                    cursor = conn.cursor()
                    for jour, val in valeurs_saisies.items():
                        if jour in abs_dict or jour.weekday() >= 5 or jour in feries_dict:
                            continue
                        cursor.execute("""
                            INSERT INTO feuille_temps (user_id, date, valeur, statut_jour)
                            VALUES (%s, %s, %s, 'travail')
                            ON CONFLICT (user_id, date) DO UPDATE SET valeur = EXCLUDED.valeur
                        """, (user_id, jour.isoformat(), val))

                    if statut_feuille == 'rejetée':
                        cursor.execute("""
                            UPDATE feuille_temps_statut
                            SET statut = 'brouillon'
                            WHERE user_id = %s AND annee = %s AND mois = %s
                        """, (user_id, annee, mois))

                    conn.commit()
                    st.success("Feuille enregistrée.")
                    st.session_state["mode_modification"] = False
                    st.rerun()

        with col2:
            if not st.session_state["mode_modification"] and statut_feuille in ['brouillon', 'rejetée']:
                submit_disabled = not feuille_complete or len(df_feuille) == 0
                if submit_disabled:
                    st.button("Soumettre la feuille", use_container_width=True, disabled=True)
                    st.info("La feuille doit être complète avant soumission.")
                else:
                    if st.button("Soumettre la feuille", use_container_width=True):
                        cur = conn.cursor()
                        cur.execute("""
                            UPDATE feuille_temps_statut
                            SET statut = 'en attente'
                            WHERE user_id = %s AND annee = %s AND mois = %s
                        """, (user_id, annee, mois))
                        conn.commit()
                        st.success("Feuille soumise.")
                        st.session_state["mode_modification"] = False
                        st.rerun()

        with col3:
            if statut_feuille in ['brouillon', 'rejetée'] and not st.session_state["mode_modification"] and not df_feuille.empty:
                if st.button("Modifier la feuille", use_container_width=True):
                    st.session_state["mode_modification"] = True
                    st.rerun()

        # Récapitulatif
        st.markdown("<hr style='margin:2rem 0;'>", unsafe_allow_html=True)
        st.markdown(f"""
                <h3 style='
                    color: #000060;
                    font-family: ' New Icon';
                    font-weight: 700;
                    margin-bottom: 12px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                '>
                🧾 Récapitulatif - <span class='month-highlight'>{mois_selectionne} {annee}</span></h3>
                </h3>
        """, unsafe_allow_html=True)

        df_recap = df_feuille.copy()
        df_recap.index = df_recap.index.date

        def afficher_recap(jours_ligne):
            cols = st.columns(len(jours_ligne), gap="small")
            for i, jour in enumerate(jours_ligne):
                if jour in abs_dict:
                    type_abs = abs_dict[jour]
                    emoji = emoji_absences.get(type_abs, "")
                    cols[i].markdown(f"""
                        <div style='{style_case} background:#fef6e4; color:#b85c00;'>
                            <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                            <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                            <div style='font-size:12px; text-align:center;'>{emoji} {type_abs}</div>
                        </div>
                    """, unsafe_allow_html=True)

                elif jour in feries_dict:
                    cols[i].markdown(f"""
                        <div style='{style_case} background:#fdecea; color:#b80000;'>
                            <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                            <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                            <div style='font-size:12px; text-align:center;'>{feries_dict[jour]}</div>
                        </div>
                    """, unsafe_allow_html=True)

                elif jour.weekday() >= 5:
                    cols[i].markdown(f"""
                        <div style='{style_case} background:#f5f5f5; color:#666;'>
                            <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                            <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                            <div style='font-size:12px; text-align:center;'>Weekend</div>
                        </div>
                    """, unsafe_allow_html=True)

                elif jour in df_recap.index:
                    val = df_recap.loc[jour]["valeur"]
                    couleur = "#cce5ff" if val == 1 else "#d9f0ff"
                    texte = "1" if val == 1 else "0.5"
                    icone = "🕘" if val == 1 else "⏳"
                    cols[i].markdown(f"""
                        <div style='{style_case} background:{couleur}; color:#004085;'>
                            <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                            <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                            <div style='font-size:12px;'>{icone} {texte}</div>
                        </div>
                    """, unsafe_allow_html=True)

                else:
                    cols[i].markdown(f"""
                        <div style='{style_case} background:#f8f9fa; color:#aaa;'>
                            <div style='font-size:12px; color:#666;'>{nom_jour(jour)}</div>
                            <div style='font-weight:600; font-size:18px;'>{jour.day}</div>
                            <div style='font-size:12px;'>Non saisi</div>
                        </div>
                    """, unsafe_allow_html=True)

        afficher_recap(jours_premiere_ligne)
        afficher_recap(jours_deuxieme_ligne)

        # Important : fermer la connexion ouverte au début de l'onglet 1
        try:
            conn.close()
        except Exception:
            pass

    # Historique 
    with tab4:

        col_all, col_refus = st.columns([5,3])

        with col_all:
            st.markdown("""
                <h4 style="
                    background-color: #d6dcf5;
                    padding: 10px 15px;
                    border-radius: 8px;
                    color: #000060;
                    font-weight: 600;
                    border-left: 6px solid #9aa7e5;
                    margin-bottom: 20px;
                ">
                    📝 Toutes les feuilles
                </h4>
            """, unsafe_allow_html=True)

            conn = get_connection()
            try:
                historique_df = pd.read_sql_query(
                    """
                    SELECT fts.annee, fts.mois, fts.statut
                    FROM feuille_temps_statut fts
                    WHERE fts.user_id = %s
                    AND fts.statut IN ('validée', 'rejetée', 'en attente')
                    ORDER BY fts.annee DESC, fts.mois DESC
                    """,
                    conn,
                    params=(user_id,)
                )
            finally:
                conn.close()

            if historique_df.empty:
                st.info("Aucun historique disponible pour le moment.")
            else:
                def calcul_total_heures(row):
                    annee = row["annee"]
                    mois = row["mois"]
                    conn_local = get_connection()
                    try:
                        df = pd.read_sql_query(
                            """
                            SELECT date, valeur FROM feuille_temps
                            WHERE user_id = %s
                            AND EXTRACT(MONTH FROM date) = %s
                            AND EXTRACT(YEAR FROM date) = %s
                            """,
                            conn_local,
                            params=(user_id, mois, annee),
                            parse_dates=["date"]
                        )
                    finally:
                        conn_local.close()

                    if df.empty:
                        return 0
                    total_heures = 0
                    for _, r in df.iterrows():
                        jour = r["date"]
                        if jour.weekday() < 5:
                            val = r["valeur"]
                            total_heures += 8 if val == 1 else 3
                    return total_heures

                historique_df["Total heures"] = historique_df.apply(calcul_total_heures, axis=1)

                historique_df = historique_df.rename(columns={
                    "annee": "Année",
                    "mois": "Mois",
                    "statut": "Statut"
                })

                mois_fr = {
                    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
                }
                historique_df["Mois"] = historique_df["Mois"].map(mois_fr)

                annees_completes = list(range(2020,2031))
                statuts = sorted(historique_df["Statut"].unique())

                col1, col2 = st.columns(2)
                with col1:
                    annee_filtre = st.selectbox("📅 Année", ["Toutes"] + [str(a) for a in annees_completes])
                with col2:
                    statut_filtre = st.selectbox("📌 Statut", ["Tous"] + statuts)

                df_filtre = historique_df.copy()
                if annee_filtre != "Toutes":
                    df_filtre = df_filtre[df_filtre["Année"] == int(annee_filtre)]
                if statut_filtre != "Tous":
                    df_filtre = df_filtre[df_filtre["Statut"] == statut_filtre]

                if df_filtre.empty:
                    st.info("Aucune donnée correspondant aux filtres.")
                else:
                    df_filtre["Statut"] = df_filtre["Statut"].apply(
                        lambda s: f"<span class='status-badge {s.replace(' ', '-')}'>{s.capitalize()}</span>"
                    )
                    display_df = df_filtre[["Année", "Mois", "Total heures", "Statut"]]
                    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    buffer = io.BytesIO()
                    export_df = df_filtre.copy()
                    export_df["Statut"] = export_df["Statut"].str.replace(r"<.*?>", "", regex=True)
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='Historique')
                    buffer.seek(0)

                    nom_fichier = "historique_feuille_" + (annee_filtre if annee_filtre != "Toutes" else "toutes_annees")
                    nom_fichier += "_" + (statut_filtre if statut_filtre != "Tous" else "tous_statuts") + ".xlsx"

                    cols = st.columns([3, 0.9])
                    with cols[-1]:
                        st.download_button(
                            label="Exporter en Excel",
                            data=buffer,
                            file_name=nom_fichier,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        with col_refus:
            conn = get_connection()
            try:
                refus_df = pd.read_sql_query(
                    """
                    SELECT annee, mois, motif_refus
                    FROM feuille_temps_statut
                    WHERE user_id = %s AND statut = 'rejetée'
                    ORDER BY annee DESC, mois DESC
                    """,
                    conn,
                    params=(user_id,)
                )
            finally:
                conn.close()

            if annee_filtre != "Toutes":
                refus_df = refus_df[refus_df["annee"] == int(annee_filtre)]

            st.markdown("""
                <h4 style="
                    background-color: #ffe5e5;
                    padding: 10px 15px;
                    border-radius: 8px;
                    color: #b00020;
                    font-weight: 600;
                    border-left: 6px solid #b00020;
                    margin-bottom: 20px;
                ">
                    📝 Motifs de refus
                </h4>
            """, unsafe_allow_html=True)

            if refus_df.empty:
                st.info("Aucun motif de refus pour l'année sélectionnée.")
            else:
                mois_fr = {
                    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
                }
                refus_df["mois"] = refus_df["mois"].map(mois_fr)

                for _, row in refus_df.iterrows():
                    st.markdown(f"""
                        <div class="refus-card">
                            <h4>{row['mois']} {row['annee']}</h4>
                            <p><strong>Motif :</strong> {row['motif_refus'] or "Non spécifié"}</p>
                        </div>
                    """, unsafe_allow_html=True)

    # Liste projets utilisateur
    with tab3:
        st.markdown("""
            <h4 style='
                background-color: #d6dcf5;
                padding: 10px 15px;
                border-radius: 8px;
                color: #000060;
                font-weight: 600;
                border-left: 6px solid #9aa7e5;
                margin-bottom: 20px;
            '>
                📁 Mes projets
            </h4>
        """, unsafe_allow_html=True)

        user_id_local = st.session_state.get("user_id", None)
        df_projets_user = pd.DataFrame()

        if user_id_local is None:
            st.error("Utilisateur non identifié.")
        else:
            try:
                conn = get_connection()
                df_projets_user = pd.read_sql_query(
                    """
                    SELECT p.id, p.nom AS Projet, p.outil AS Outil
                    FROM projets p
                    INNER JOIN attribution_projet ap ON ap.projet_id = p.id
                    WHERE ap.user_id = %s
                    ORDER BY p.nom
                    """,
                    conn,
                    params=(user_id_local,)
                )
            except Exception as e:
                st.error(f"Erreur lors de la récupération des projets : {e}")
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            if df_projets_user.empty:
                st.info("Aucun projet attribué.")
            else:
                search_text = st.text_input("🔍 Rechercher un projet", key="search_user_proj")
                if search_text:
                    df_filtered_proj = df_projets_user[
                        df_projets_user["Projet"].str.contains(search_text, case=False, na=False) |
                        df_projets_user["Outil"].str.contains(search_text, case=False, na=False)
                    ]
                else:
                    df_filtered_proj = df_projets_user.copy()

                PROJECTS_PER_PAGE = 5
                total = len(df_filtered_proj)
                total_pages = (total - 1) // PROJECTS_PER_PAGE + 1

                if "proj_user_page" not in st.session_state:
                    st.session_state.proj_user_page = 1

                def go_prev_proj():
                    if st.session_state.proj_user_page > 1:
                        st.session_state.proj_user_page -= 1

                def go_next_proj():
                    if st.session_state.proj_user_page < total_pages:
                        st.session_state.proj_user_page += 1

                start_idx = (st.session_state.proj_user_page - 1) * PROJECTS_PER_PAGE
                end_idx = start_idx + PROJECTS_PER_PAGE
                df_paginated_proj = df_filtered_proj.iloc[start_idx:end_idx]

                st.markdown(
                    df_paginated_proj.drop(columns=['id']).to_html(index=False, escape=False),
                    unsafe_allow_html=True
                )

                col_a, col_b, col_c = st.columns([15, 1, 1])
                with col_a:
                    st.write("")
                with col_b:
                    st.button("⬅️", on_click=go_prev_proj, disabled=(st.session_state.proj_user_page == 1), key="prev_proj_user")
                with col_c:
                    st.button("➡️", on_click=go_next_proj, disabled=(st.session_state.proj_user_page == total_pages), key="next_proj_user")

                st.markdown(
                    f"<p style='text-align:right; font-style: italic;'>Page {st.session_state.proj_user_page} sur {total_pages}</p>",
                    unsafe_allow_html=True
                )

    # Saisie heures projets ==================================================================================================
    with tab2:
        st.markdown("""
            <h4 style='
                background-color: #d6dcf5;
                padding: 10px 15px;
                border-radius: 8px;
                color: #000060;
                font-weight: 600;
                border-left: 6px solid #9aa7e5;
                margin-bottom: 20px;
            '>
                📝 Saisie heures par projet et semaine
            </h4>
        """, unsafe_allow_html=True)

        # Sélection année et mois
        col_year, col_month = st.columns(2)
        with col_year:
            selected_year = st.selectbox(
                "📆 Année",
                list(range(2020, 2031)),
                index=list(range(2020, 2031)).index(datetime.today().year),
                key="select_year"
            )
        with col_month:
            selected_month_name = st.selectbox("🗓️ Mois", list(calendar.month_name)[1:], index=datetime.now().month - 1, key="month_select")
            month_num = list(calendar.month_name).index(selected_month_name)

        date_start = date(selected_year, month_num, 1)
        last_day = calendar.monthrange(selected_year, month_num)[1]
        date_end = date(selected_year, month_num, last_day)

        # Vérification feuille validée
        try:
            conn = get_connection()
            statut_df = pd.read_sql_query(
                """
                SELECT statut
                FROM feuille_temps_statut
                WHERE user_id = %s AND annee = %s AND mois = %s
                """,
                conn,
                params=(user_id, selected_year, month_num)
            )

            if statut_df.empty or statut_df.iloc[0]['statut'] != 'validée':
                st.info("La feuille de temps de ce mois n'est pas validée.")
                df_feuille = pd.DataFrame()
            else:
                df_feuille = pd.read_sql_query(
                    """
                    SELECT date AS date_jour, valeur, statut_jour
                    FROM feuille_temps
                    WHERE user_id = %s AND date BETWEEN %s AND %s
                    """,
                    conn,
                    params=(user_id, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'))
                )
        except Exception as e:
            st.error(f"Erreur lors du chargement de la feuille validée : {e}")
            df_feuille = pd.DataFrame()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if df_feuille.empty:
            st.info("Aucune donnée de feuille de temps pour cette période.")
            st.stop()

        # Semaine
        max_weeks = 5
        week_num = st.slider("Semaine du mois", 1, max_weeks, 1)
        first_weekday = date_start.weekday()
        start_week_date = date_start + timedelta(days=(week_num - 1) * 7 - first_weekday)
        if start_week_date < date_start:
            start_week_date = date_start
        end_week_date = start_week_date + timedelta(days=6)
        if end_week_date > date_end:
            end_week_date = date_end

        jours_sem = pd.date_range(start_week_date, end_week_date).strftime('%Y-%m-%d').tolist()

        # Heures déjà saisies
        try:
            conn = get_connection()
            df_heures = pd.read_sql_query(
                """
                SELECT projet_id, date_jour, heures
                FROM heures_saisie
                WHERE user_id = %s AND date_jour BETWEEN %s AND %s
                """,
                conn,
                params=(user_id, start_week_date.strftime('%Y-%m-%d'), end_week_date.strftime('%Y-%m-%d'))
            )
        except Exception as e:
            st.error(f"Erreur lors du chargement des heures saisies : {e}")
            df_heures = pd.DataFrame()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        df_heures['date_jour'] = pd.to_datetime(df_heures['date_jour']).dt.strftime('%Y-%m-%d')
        df_feuille['date_jour'] = pd.to_datetime(df_feuille['date_jour']).dt.strftime('%Y-%m-%d')
        pd.set_option('future.no_silent_downcasting', True)
        df_heures['projet_id'] = df_heures['projet_id'].replace('', np.nan).infer_objects(copy=False)
        df_heures['projet_id'] = pd.to_numeric(df_heures['projet_id'], errors='coerce')
        df_heures = df_heures.dropna(subset=['projet_id'])
        df_heures['projet_id'] = df_heures['projet_id'].astype(int)

        # Projets utilisateur
        try:
            conn = get_connection()
            df_projets_user = pd.read_sql_query(
                """
                SELECT p.id, p.nom AS Projet, ap.date_fin
                FROM projets p
                INNER JOIN attribution_projet ap ON ap.projet_id = p.id
                WHERE ap.user_id = %s
                ORDER BY p.nom
                """,
                conn,
                params=(user_id,)
            )
        except Exception as e:
            st.error(f"Erreur lors du chargement des projets : {e}")
            st.stop()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        df_projets_user['date_fin'] = pd.to_datetime(df_projets_user['date_fin'], errors='coerce')
        today = pd.Timestamp.today().normalize()
        df_projets_user = df_projets_user[df_projets_user['date_fin'].isna() | (df_projets_user['date_fin'] >= today)]
        df_projets_user = df_projets_user.drop(columns=['date_fin'])

        # Absences approuvées
        try:
            conn = get_connection()
            df_abs_user = pd.read_sql_query(
                """
                SELECT date_debut, date_fin, type_absence
                FROM absences
                WHERE user_id = %s
                AND statut = 'Approuvée'
                AND date_fin >= %s
                AND date_debut <= %s
                """,
                conn,
                params=(user_id, start_week_date.strftime('%Y-%m-%d'), end_week_date.strftime('%Y-%m-%d'))
            )
        except Exception as e:
            st.error(f"Erreur lors du chargement des absences : {e}")
            df_abs_user = pd.DataFrame(columns=["date_absence", "type_absence_raw", "type_absence_norm"])
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if not df_abs_user.empty:
            expanded_rows = []
            for _, row in df_abs_user.iterrows():
                periode = pd.date_range(start=row['date_debut'], end=row['date_fin'])
                t_raw = str(row['type_absence']) if pd.notna(row['type_absence']) else ''
                t_norm = t_raw.strip().lower()
                if t_norm == 'télétravail':
                    continue
                for d in periode:
                    expanded_rows.append({
                        "date_absence": d.strftime('%Y-%m-%d'),
                        "type_absence_raw": t_raw.strip(),
                        "type_absence_norm": t_norm
                    })
            df_abs_user = pd.DataFrame(expanded_rows)
        else:
            df_abs_user = pd.DataFrame(columns=["date_absence", "type_absence_raw", "type_absence_norm"])

        absences_set = set(zip(
            df_abs_user.get('date_absence', pd.Series([], dtype=str)),
            df_abs_user.get('type_absence_norm', pd.Series([], dtype=str))
        ))

        # Jours fériés
        fr_holidays = holidays.France(years=selected_year)
        jours_feries_set = {
            d.strftime('%Y-%m-%d')
            for d in pd.to_datetime(list(fr_holidays.keys()))
            if start_week_date <= d.date() <= end_week_date
        }

        # Construction des lignes projets
        data = []
        for _, proj in df_projets_user.iterrows():
            row = {"projet_id": int(proj["id"]), "Projet": proj["Projet"]}  # <- fix nom colonne
            for jour in jours_sem:
                mask = (df_heures['projet_id'] == int(proj['id'])) & (df_heures['date_jour'] == jour)
                row[jour] = float(df_heures[mask]['heures'].values[0]) if not df_heures[mask].empty else 0.0
            data.append(row)

        # Types d'absences distincts
        try:
            conn = get_connection()
            df_types_raw = pd.read_sql_query("SELECT DISTINCT type_absence FROM absences", conn)
        except Exception:
            df_types_raw = pd.DataFrame(columns=['type_absence'])
        finally:
            try:
                conn.close()
            except Exception:
                pass

        types_seen = set()
        types_list = []
        for t in df_types_raw['type_absence'].dropna().astype(str):
            t_raw = t.strip()
            t_norm = t_raw.lower()
            if t_norm == 'télétravail' or t_norm in types_seen:
                continue
            types_seen.add(t_norm)
            types_list.append((t_norm, t_raw))

        for t_norm, t_raw in types_list:
            row = {"projet_id": None, "Projet": f"Absence - {t_raw}"}
            for jour in jours_sem:
                row[jour] = 8.0 if (jour, t_norm) in absences_set else 0.0
            data.append(row)

        # Ligne jours fériés
        if jours_feries_set:
            row = {"projet_id": None, "Projet": "Jour férié"}
            for jour in jours_sem:
                row[jour] = 8.0 if jour in jours_feries_set else 0.0
            data.append(row)

        df_ag = pd.DataFrame(data)

        # Garde : si pas de données, on évite AgGrid vide
        if df_ag.empty:
            st.info("Aucun projet actif ou aucune ligne à saisir pour la semaine sélectionnée.")
            return

        # En-têtes FR
        jours_semaine_fr = {'Mon': 'Lun','Tue': 'Mar','Wed': 'Mer','Thu': 'Jeu','Fri': 'Ven','Sat': 'Sam','Sun': 'Dim'}
        col_headers = {}
        for jour in jours_sem:
            dt = pd.to_datetime(jour)
            abbr_en = dt.strftime('%a')
            jour_fr = jours_semaine_fr.get(abbr_en, abbr_en)
            col_headers[jour] = f"{jour_fr} - {dt.day}"

        # Weekends + absences + jours fériés
        weekend_days = {d.strftime('%Y-%m-%d') for d in pd.date_range(start_week_date, end_week_date) if pd.to_datetime(d).weekday() >= 5}
        abs_dates = set(df_abs_user['date_absence']) if not df_abs_user.empty else set()

        # Grid
        gb = GridOptionsBuilder.from_dataframe(df_ag)
        gb.configure_column("projet_id", hide=True)

        editable_js = JsCode("""
        function(params) {
            return !params.data.Projet.startsWith('Absence') && !params.data.Projet.startsWith('Jour férié');
        }
        """)

        rowStyleJs = JsCode("""
        function(params) {
            if (params.data.Projet.startsWith('Absence') || params.data.Projet.startsWith('Jour férié')) {
                return {
                    'font-style': 'italic',
                    'background-color': '#f9f2ec',
                    'color': '#000000'
                };
            }
            return {};
        }
        """)

        for jour in jours_sem:
            val_jour = df_feuille[df_feuille['date_jour'] == jour]['valeur']
            stat_jour = df_feuille[df_feuille['date_jour'] == jour]['statut_jour']
            if (
                val_jour.empty or val_jour.values[0] == 0
                or (not stat_jour.empty and stat_jour.values[0] in ['congé', 'maladie', 'RTT', 'congé sans solde'])
                or (jour in weekend_days) or (jour in abs_dates) or (jour in jours_feries_set)
            ):
                gb.configure_column(
                    jour,
                    editable=False,
                    cellStyle={"background-color": "#f9f2ec", "color": "#000000", "fontStyle": "italic"},
                    headerName=col_headers[jour]
                )
            else:
                gb.configure_column(
                    jour,
                    editable=editable_js,
                    type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                    headerName=col_headers[jour],
                )

        gridOptions = gb.build()
        gridOptions['getRowStyle'] = rowStyleJs

        custom_css = {
            ".ag-header-cell": {"background-color": "#000060", "color": "white", "font-weight": "bold"},
            ".ag-row-even": {"background-color": "#f0f8ff"},
            ".ag-row-odd": {"background-color": "#ffffff"},
        }

        grid_response = AgGrid(
            df_ag,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True,
            theme='material',
            custom_css=custom_css,
            height=400,
            fit_columns_on_grid_load=True,
        )

        col_save, col_export,_ = st.columns([1.5,2,13])
        with col_save:
            if st.button("Enregistrer"):
                df_modif = pd.DataFrame(grid_response['data'])
                df_modif_sans_abs = df_modif[~df_modif['Projet'].str.startswith('Absence') & ~df_modif['Projet'].str.startswith('Jour férié')]

                erreurs = []
                for jour in jours_sem:
                    val_jour = df_feuille[df_feuille['date_jour'] == jour]['valeur']
                    if val_jour.empty or val_jour.values[0] == 0 or (jour in weekend_days) or (jour in abs_dates) or (jour in jours_feries_set):
                        continue
                    val_j = val_jour.values[0]
                    somme_heures = df_modif_sans_abs[jour].sum()
                    limite = 8 if val_j == 1 else 3
                    if somme_heures > limite:
                        erreurs.append(f"Total heures {somme_heures} > limite {limite} le {jour}")

                if erreurs:
                    st.error(" / ".join(erreurs))
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        for _, row in df_modif.iterrows():
                            if str(row['Projet']).startswith("Absence") or str(row['Projet']).startswith("Jour férié"):
                                continue
                            projet_id = row['projet_id']
                            for jour in jours_sem:
                                heures = row[jour]
                                if heures is None or heures == "":
                                    heures = 0
                                else:
                                    heures = float(heures)

                                if (jour in weekend_days) or (jour in abs_dates) or (jour in jours_feries_set):
                                    heures = 0.0
                                cur.execute("""
                                    INSERT INTO heures_saisie (user_id, projet_id, date_jour, heures)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (user_id, projet_id, date_jour) 
                                    DO UPDATE SET heures = EXCLUDED.heures
                                """, (user_id, projet_id, jour, heures))

                        conn.commit()
                        st.success("Heures enregistrées avec succès.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement : {e}")
                    finally:
                        try:
                            conn.close()
                        except Exception:
                            pass

        # Export excel
        with col_export:
            df_export = pd.DataFrame(grid_response['data'])
            df_export = df_export[~df_export['Projet'].str.startswith("Absence")]

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Semaine')
            buffer.seek(0)

            st.download_button(
                label="Exporter en Excel",
                data=buffer,
                file_name=f"Heures_{selected_year}_{month_num}_semaine{week_num}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Graphique repartition des heures travaillées par projet
        st.markdown(f"""
            <h4 style='
                background-color: #d6dcf5;
                padding: 10px 15px;
                border-radius: 8px;
                color: #000060;
                font-weight: 600;
                border-left: 6px solid #9aa7e5;
                margin-bottom: 20px;
            '>
                Répartition des heures travaillées par projet - {selected_month_name} {selected_year}
            </h4>
        """, unsafe_allow_html=True)

        try:
            conn = get_connection()
            df_heures_mois = pd.read_sql_query(
                """
                SELECT p.nom AS Projet, SUM(hs.heures) AS Total_heures
                FROM heures_saisie hs
                INNER JOIN projets p ON p.id = hs.projet_id
                WHERE hs.user_id = %s AND hs.date_jour BETWEEN %s AND %s
                GROUP BY p.nom
                ORDER BY Total_heures DESC
                """,
                conn,
                params=(user_id, date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'))
            )
        except Exception as e:
            st.error(f"Erreur lors du chargement du graphique : {e}")
            df_heures_mois = pd.DataFrame()
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if not df_heures_mois.empty:
            # Harmoniser les noms avant Plotly
            df_heures_mois = df_heures_mois.rename(columns={'Projet': 'projet', 'Total_heures': 'total_heures'})
            fig = px.bar(
                df_heures_mois,
                x='projet',
                y='total_heures',
                color='projet',
                labels={'total_heures': 'Heures totales', 'projet': 'Projet'},
                text='total_heures'
            )
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(
                yaxis=dict(
                    range=[0, df_heures_mois['total_heures'].max() * 1.1],
                    title='Total heures',
                    showgrid=True,
                    gridcolor='LightGray',
                    zeroline=True,
                    zerolinecolor='Gray'
                ),
                xaxis=dict(
                    tickangle=-45,
                    title='Projets',
                    tickmode='array',
                    tickfont=dict(size=10, color='black'),
                ),
                margin=dict(l=50, r=30, t=50, b=50),
                plot_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée d'heures saisies ce mois.")
