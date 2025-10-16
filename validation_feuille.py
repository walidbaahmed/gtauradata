import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import datetime, date, timedelta
from db import get_connection
import holidays
import io
import smtplib
from email.message import EmailMessage
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from io import BytesIO

st.set_page_config(page_title="Validation des feuilles", layout="wide")

def envoyer_email_rejet(destinataire_email, nom_utilisateur, mois_nom, annee, motif):
    expediteur_email = st.secrets["email"]["gmail_user"]
    mot_de_passe_app = st.secrets["email"]["gmail_app_password"]

    msg = EmailMessage()
    msg['Subject'] = f"Feuille de temps rejetée - {mois_nom} {annee}"
    msg['From'] = expediteur_email
    msg['To'] = destinataire_email

    msg.set_content(f"""
        Bonjour {nom_utilisateur},

        Votre feuille de temps pour le mois de {mois_nom} {annee} a été rejetée.

        Motif du refus :
        {motif}

        Merci de vous connecter à votre espace pour effectuer les modifications nécessaires.

        Cordialement,
        L’équipe RH
            """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(expediteur_email, mot_de_passe_app)
            smtp.send_message(msg)
        print("✅ Email envoyé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {e}")

def envoyer_email_validation(destinataire_email, nom_utilisateur, mois_nom, annee):
    expediteur_email = st.secrets["email"]["gmail_user"]
    mot_de_passe_app = st.secrets["email"]["gmail_app_password"]

    msg = EmailMessage()
    msg['Subject'] = f"Feuille de temps validée - {mois_nom} {annee}"
    msg['From'] = expediteur_email
    msg['To'] = destinataire_email

    msg.set_content(f"""
        Bonjour {nom_utilisateur},

        Votre feuille de temps pour le mois de {mois_nom} {annee} a été validée.

        Merci de revenir dans l'application et compléter vos heures dans le deuxième onglet "Saisie heures" dans la page Feuille de temps.

        Cordialement,
        L’équipe RH
    """)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(expediteur_email, mot_de_passe_app)
            smtp.send_message(msg)
        print("✅ Email de validation envoyé avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email de validation : {e}")


def show_validation_feuille():

    # Droits d'accès
    if "role" not in st.session_state or st.session_state["role"] != "admin":
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    st.markdown("""
        <div id="title">
            <h4> Validation des feuilles de temps </h4> 
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
                
            .stApp {
                margin-top: 0;
                padding: 0;
                background-color: #f2f2f2; 
            }
                
            .stButton>button {
                background-color: #080686 !important;
                color: white !important;
                border-radius: 5px;
                font-size: 16px;
            }
                
            .stDownloadButton > button {
                background-color: #080686 !important;
                color: white !important;
                border-radius: 5px;
                font-size: 16px;
            }

            .stButton>button:hover {
                background-color: white !important;
                color: #080686 !important;
                border: 1px solid #080686 !important;
            }
                
            .stDownloadButton>button:hover {
                background-color: white !important;
                color: #080686 !important;
                border: 1px solid #080686 !important;
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
                
            .stTabs {
                margin-top: -50px !important;
            }
                
            .stTabs [data-baseweb="tab"] {
                font-size: 20px !important;
                font-weight: 600 !important;
                padding: 10px 20px !important;
            }
                
            .kpi-card {
                background-color: #ffcccc;
                padding: 1rem;
                border-radius: 1rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 1rem;
                border: 1px solid #f5c2c7;
            }

            .kpi-value {
                font-size: 1.5rem;
                font-weight: bold;
                color: #c82333;
            }
                
            .kpi-label {
                font-size: 1.1rem;
                font-weight: 500;
                color: #721c24;
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
                
            tbody tr:nth-child(odd) td {
                background-color: #f9f9fb;
            }
                
            tbody tr:hover td {
                background-color: #e6f0ff;
                cursor: pointer;
            }
        </style>
    """, unsafe_allow_html=True)

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT fts.user_id, u.name, fts.annee, fts.mois, fts.statut
        FROM feuille_temps_statut fts
        JOIN users u ON u.id = fts.user_id
        WHERE fts.statut = 'en attente'
        ORDER BY fts.annee DESC, fts.mois DESC
    """
    cur.execute(query)
    feuilles = cur.fetchall()

    tab1, tab2, tab3 = st.tabs(["Feuilles en attente", "Validation heures", "Historique"])

    # Feuilles en attente
    with tab1:
        nb_feuilles_attente = len(feuilles) 

        col1, col2 = st.columns([1,5])
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{nb_feuilles_attente}</div>
                    <div class="kpi-label">🕒 Total feuilles en attente</div>
                </div>
            """, unsafe_allow_html=True)

            annee_actuelle = date.today().year
            mois_fr = {
                1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
            }

            utilisateurs_f = sorted(set([f[1] for f in feuilles]))
            annees_completes = list(range(2020, 2031))
            mois_tous_noms = [mois_fr[m] for m in range(1, 13)]

            st.markdown("### 🔍 Filtres")
            utilisateur_filtre = st.selectbox("🙍 Utilisateur", ["Tous"] + utilisateurs_f, key="feuille_utilisateur")
            annee_filtre = st.selectbox("📅 Année", ["Toutes"] + [str(a) for a in annees_completes], key="feuille_annee")
            mois_filtre_nom = st.selectbox("📆 Mois", ["Tous"] + mois_tous_noms, key="feuille_mois")

            mois_filtre_num = None
            if mois_filtre_nom != "Tous":
                mois_filtre_num = {v: k for k, v in mois_fr.items()}[mois_filtre_nom]

            feuilles_filtrees = feuilles
            if utilisateur_filtre != "Tous":
                feuilles_filtrees = [f for f in feuilles_filtrees if f[1] == utilisateur_filtre]
            if annee_filtre != "Toutes":
                feuilles_filtrees = [f for f in feuilles_filtrees if str(f[2]) == annee_filtre]
            if mois_filtre_num is not None:
                feuilles_filtrees = [f for f in feuilles_filtrees if f[3] == mois_filtre_num]

        with col2:
            if not feuilles:
                st.info("Aucune feuille de temps en attente de validation.")

            emoji_absences = {
                "Maladie": "🤒",
                "Congé payé": "🏖️",
                "RTT": "⏳",
                "Congé sans solde" : "🏖️",
            }

            def nom_jour(date_obj):
                jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                return jours[date_obj.weekday()]

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

            def afficher_recap_validation(jours_ligne, cols, abs_dict, feries_dict, df):
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

                    elif jour in df.index:
                        val = df.loc[jour]["valeur"]
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

            if not feuilles_filtrees:
                st.info("🔍 Aucun résultat pour les filtres sélectionnés.")
            else:
                for feuille in feuilles_filtrees:
                    user_id, nom, annee, mois, statut = feuille
                    key_rejet = f"show_rejet_{user_id}_{annee}_{mois}"
                    if key_rejet not in st.session_state:
                        st.session_state[key_rejet] = False
                    mois_nom = calendar.month_name[mois]

                    query_data = """
                        SELECT date, valeur 
                        FROM feuille_temps
                        WHERE user_id = %s 
                        AND EXTRACT(MONTH FROM date) = %s
                        AND EXTRACT(YEAR FROM date) = %s
                    """
                    df = pd.read_sql_query(
                        query_data,
                        conn,
                        params=(user_id, mois, annee),
                        parse_dates=["date"]
                    )

                    df.set_index("date", inplace=True)
                    df.index = df.index.date
                    
                    col3, col4, col5, col6 = st.columns(4)
                    if "mode_modification" not in st.session_state:
                        st.session_state["mode_modification"] = True

                    total_heures_preview = 0
                    for jour, row in df.iterrows():
                        if jour.weekday() < 5: 
                            val = row["valeur"]
                            total_heures_preview += 8 if val == 1 else 3

                    def card(valeur, couleur="#000", fond="#f8f9fa", emoji=""):
                        return f"""
                            <div style='
                                background:{fond};
                                padding:1rem;
                                border-radius:12px;
                                box-shadow:0 3px 6px rgba(0,0,0,0.1);
                                text-align:center;
                                height:100%;
                            '>
                                <div style='font-size:1rem; font-weight:bold; color:{couleur};'>
                                    {emoji} {valeur}
                                </div>

                            </div>
                        """

                    with col3:
                        st.markdown(card(nom, "#004085", "#e7f1ff", "👤"), unsafe_allow_html=True)
                    with col4:
                        st.markdown(card(f"{mois_nom} {annee}", "#004085", "#e7f1ff", "📅"), unsafe_allow_html=True)
                    with col5:
                        st.markdown(card(statut.capitalize(), "#9c5700", "#ffedd5", "📌 Statut :"), unsafe_allow_html=True)
                    with col6:
                        st.markdown(card(total_heures_preview, "#000066", "#f8f9fa", "⏱️ Total heures :"), unsafe_allow_html=True)

                    query_abs = """
                        SELECT date_debut, date_fin, type_absence
                        FROM absences
                        WHERE user_id = %s AND statut = 'Approuvée'
                        AND (
                            (date_debut BETWEEN %s AND %s)
                            OR (date_fin BETWEEN %s AND %s)
                            OR (date_debut <= %s AND date_fin >= %s)
                        )
                    """

                    debut_periode = date(annee, mois, 1)
                    fin_periode = date(annee, mois, calendar.monthrange(annee, mois)[1])

                    df_abs = pd.read_sql_query(
                        query_abs, conn,
                        params=(
                            user_id,
                            debut_periode, fin_periode,
                            debut_periode, fin_periode,
                            debut_periode, fin_periode,
                        )
                    )


                    abs_dict = {}
                    for _, row in df_abs.iterrows():
                        start = pd.to_datetime(row["date_debut"]).date()
                        end = pd.to_datetime(row["date_fin"]).date()
                        for i in range((end - start).days + 1):
                            abs_dict[start + timedelta(days=i)] = row["type_absence"]

                    feries = holidays.CountryHoliday("FR", years=[annee])
                    feries_dict = {jour: nom for jour, nom in feries.items() if jour.month == mois}

                    cal = calendar.Calendar(firstweekday=0)
                    jours_mois = list(cal.itermonthdates(annee, mois))
                    jours_visibles = [j for j in jours_mois if j.month == mois]

                    mi_point = len(jours_visibles) // 2 + len(jours_visibles) % 2
                    ligne1 = jours_visibles[:mi_point]
                    ligne2 = jours_visibles[mi_point:]

                    st.markdown("<div style='overflow-x:auto; white-space:nowrap;'>", unsafe_allow_html=True)
                    cols1 = st.columns(len(ligne1), gap="small")
                    afficher_recap_validation(ligne1, cols1, abs_dict, feries_dict, df)
                    st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
                    cols2 = st.columns(len(ligne2), gap="small")
                    afficher_recap_validation(ligne2, cols2, abs_dict, feries_dict, df)
                    st.markdown("</div>", unsafe_allow_html=True)

                    col_val, col_rej, _ = st.columns([2,2,12])
                    with col_val:
                        if st.button("Valider", key=f"valider_{user_id}_{annee}_{mois}"):
                            # Mettre à jour le statut dans la DB
                            cur.execute("""
                                UPDATE feuille_temps_statut
                                SET statut = 'validée'
                                WHERE user_id = %s AND annee = %s AND mois = %s
                            """, (user_id, annee, mois))
                            conn.commit()

                            # Récupérer l'email de l'utilisateur
                            cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                            result = cur.fetchone()
                            if result:
                                destinataire_email = result[0]
                                try:
                                    # Appel de la fonction d'envoi d'email de validation
                                    envoyer_email_validation(destinataire_email, nom, mois_nom, annee)
                                except Exception as e:
                                    st.error(f"Erreur lors de l'envoi de l'email : {e}")
                            else:
                                st.warning("Email de l'utilisateur introuvable.")

                            st.success(f"✅ Feuille de temps de {nom} validée.")
                            st.rerun()
                    
                    with col_rej:
                        key_rejet = f"show_rejet_{user_id}_{annee}_{mois}"
                        motif_refus_key = f"motif_refus_{user_id}_{annee}_{mois}"
                        confirmer_key = f"confirmer_rejet_{user_id}_{annee}_{mois}"

                        if key_rejet not in st.session_state:
                            st.session_state[key_rejet] = False

                        if not st.session_state[key_rejet]:
                            if st.button("Rejeter", key=f"rejeter_{user_id}_{annee}_{mois}"):
                                st.session_state[key_rejet] = True
                                st.rerun()
                        else:
                            motif_refus = st.text_area("✏️ Motif du refus :", key=motif_refus_key)
                            #
                            if st.button("Confirmer le rejet", key=confirmer_key):
                                if not motif_refus.strip():
                                    st.error("❗ Veuillez saisir un motif de refus.")
                                else:
                                    cur.execute("""
                                        UPDATE feuille_temps_statut
                                        SET statut = 'rejetée', motif_refus = %s
                                        WHERE user_id = %s AND annee = %s AND mois = %s
                                    """, (motif_refus.strip(), user_id, annee, mois))

                                    conn.commit()

                                    cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                                    result = cur.fetchone()
                                    if result:
                                        destinataire_email = result[0]
                                        try:
                                            envoyer_email_rejet(destinataire_email, nom, mois_nom, annee, motif_refus.strip())
                                        except Exception as e:
                                            st.error(f"Erreur lors de l'envoi de l'email : {e}")
                                    else:
                                        st.warning("Email de l'utilisateur introuvable.")

                                    st.success(f"🚫 Feuille de temps de {nom} rejetée avec le motif.")
                                    st.session_state[key_rejet] = False
                                    st.rerun()

                    st.markdown("---")

    # Historique 
    with tab3:
        historique_query = """
            SELECT u.id as user_id, u.name, fts.annee, fts.mois, fts.statut
            FROM feuille_temps_statut fts
            JOIN users u ON u.id = fts.user_id
            WHERE fts.statut IN ('validée', 'rejetée')
            ORDER BY fts.annee DESC, fts.mois DESC
        """
        historique_df = pd.read_sql_query(historique_query, conn)

        if historique_df.empty:
            st.info("Aucun historique disponible pour le moment.")
            st.stop()

        def calcul_total_heures(row):
            user_id = row["user_id"]
            annee = row["annee"]
            mois = row["mois"]

            query_data = """
                SELECT date, valeur FROM feuille_temps
                WHERE user_id = %s
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(YEAR FROM date) = %s
            """
            df = pd.read_sql_query(
                query_data, conn,
                params=(user_id, mois, annee),
                parse_dates=["date"]
            )

            if df.empty:
                return 0
            total_heures = 0
            for _, row in df.iterrows():
                jour = row["date"]
                if jour.weekday() < 5:
                    val = row["valeur"]
                    if val == 1:
                        total_heures += 8
                    else:
                        total_heures += 3

            return total_heures

        historique_df["Total heures"] = historique_df.apply(calcul_total_heures, axis=1)
        historique_df = historique_df.rename(columns={
            "name": "Utilisateur",
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

        utilisateurs = ["Tous"] + sorted(historique_df["Utilisateur"].dropna().unique().tolist())
        mois_options = ["Tous"] + list(mois_fr.values())
        statuts = ["Tous"] + sorted(historique_df["Statut"].dropna().unique().tolist())

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            utilisateur_filtre = st.selectbox("🙍 Utilisateur", utilisateurs)
        with col2:
            annee_filtre = st.selectbox(
            "📆 Année",
            list(range(2020, 2031)),
            index=list(range(2020, 2031)).index(datetime.today().year),
            key="year_select"
            )
        with col3:
            mois_filtre = st.selectbox("📆 Mois", mois_options)
        with col4:
            statut_filtre = st.selectbox("📌 Statut", statuts)

        df_filtre = historique_df.copy()

        if utilisateur_filtre != "Tous":
            df_filtre = df_filtre[df_filtre["Utilisateur"] == utilisateur_filtre]

        if annee_filtre != "Toutes":
            df_filtre = df_filtre[df_filtre["Année"] == int(annee_filtre)]

        if mois_filtre != "Tous":
            df_filtre = df_filtre[df_filtre["Mois"] == mois_filtre]

        if statut_filtre != "Tous":
            df_filtre = df_filtre[df_filtre["Statut"] == statut_filtre]

        if df_filtre.empty:
            st.info("Aucune donnée correspondant aux filtres.")
            st.stop()

        export_df = df_filtre.copy()
        export_df["Statut"] = export_df["Statut"].str.replace(r"<.*?>", "", regex=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Historique')
        buffer.seek(0)

        df_filtre["Statut"] = df_filtre["Statut"].apply(
            lambda s: f"<span class='status-badge {s}'>{s.capitalize()}</span>"
        )

        display_df = df_filtre[["Utilisateur", "Année", "Mois", "Total heures", "Statut"]]
        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        nom_fichier = "historique_feuilles"
        if annee_filtre != "Toutes":
            nom_fichier += f"_{annee_filtre}"
        if mois_filtre != "Tous":
            nom_fichier += f"_{mois_filtre}"
        nom_fichier += ".xlsx"

        cols = st.columns([6, 0.9])
        with cols[-1]:
            st.download_button(
                label="Exporter en Excel",
                data=buffer,
                file_name=nom_fichier,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


    # Validation heures par utilisateur
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
        Administration - Saisie et suivi des heures
        </h4>
        """, unsafe_allow_html=True)

        # Chargement utilisateurs
        try:
            conn = get_connection()
            df_users = pd.read_sql_query("SELECT id, name AS nom_user FROM users ORDER BY name", conn)
            conn.close()
        except Exception as e:
            st.error(f"Erreur lors du chargement des utilisateurs : {e}")
            st.stop()

        # Filtre utilisateur
        col_user, col_project, col_year, col_month = st.columns(4)
        with col_user:
            user_options = df_users.set_index('id')['nom_user'].to_dict()
            selected_user_id = st.selectbox("🧑‍💼 Utilisateur", options=list(user_options.keys()), format_func=lambda x: user_options[x])

        # Projets utilisateur
        try:
            conn = get_connection()
            query_projets_user = """
                SELECT p.id, p.nom AS Projet, ap.date_fin
                FROM projets p
                INNER JOIN attribution_projet ap ON ap.projet_id = p.id
                WHERE ap.user_id = %s
                ORDER BY p.nom
            """
            df_projets_user = pd.read_sql_query(query_projets_user, conn, params=(selected_user_id,))
            #st.write(df_projets_user.columns)
            conn.close()

            df_projets_user['date_fin'] = pd.to_datetime(df_projets_user['date_fin'], errors='coerce')
            today = pd.Timestamp.today().normalize()
            df_projets_user = df_projets_user[df_projets_user['date_fin'].isna() | (df_projets_user['date_fin'] >= today)]
            df_projets_user = df_projets_user.drop(columns=['date_fin'])
        except Exception as e:
            st.error(f"Erreur lors du chargement des projets : {e}")
            st.stop()

        # Filtre projet
        with col_project:
            project_options = df_projets_user.set_index('id')['projet'].to_dict()
            project_options_with_all = {'all': 'Tous les projets'}
            project_options_with_all.update(project_options)
            selected_projects = st.selectbox(
                "📂 Projet",
                options=list(project_options_with_all.keys()),
                format_func=lambda x: project_options_with_all[x]
            )

        # Filtre année et mois
        with col_year:
            selected_year = st.selectbox(
                "📆 Année",
                list(range(2020, 2031)),
                index=list(range(2020, 2031)).index(datetime.today().year)
            )

        with col_month:
            selected_month_name = st.selectbox("🗓️ Mois", list(calendar.month_name)[1:], index=datetime.now().month - 1)
            month_num = list(calendar.month_name).index(selected_month_name)

        date_start = date(selected_year, month_num, 1)
        last_day = calendar.monthrange(selected_year, month_num)[1]
        date_end = date(selected_year, month_num, last_day)

        # Vérification feuille validée
        try:
            conn = get_connection()
            query_statut = """
                SELECT statut
                FROM feuille_temps_statut
                WHERE user_id = %s AND annee = %s AND mois = %s
            """
            statut_df = pd.read_sql_query(query_statut, conn, params=(selected_user_id, selected_year, month_num))
            conn.close()

            if statut_df.empty or statut_df.iloc[0]['statut'] != 'validée':
                st.info("La feuille de temps de ce mois n'est pas validée.")
                st.stop()
            else:
                try:
                    conn = get_connection()
                    query_jours = """
                        SELECT date AS date_jour, valeur, statut_jour
                        FROM feuille_temps
                        WHERE user_id = %s AND date BETWEEN %s AND %s
                    """
                    df_feuille = pd.read_sql_query(query_jours, conn, params=(selected_user_id, date_start, date_end))
                    conn.close()
                except Exception as e:
                    st.error(f"Erreur lors du chargement de la feuille validée : {e}")
                    st.stop()
        except Exception as e:
            st.error(f"Erreur lors du chargement du statut : {e}")
            st.stop()

        # Semaine
        max_weeks = 5
        week_num = st.slider("Semaine", 1, max_weeks, 1)
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
            query_heures = """
                SELECT projet_id, date_jour, heures
                FROM heures_saisie
                WHERE user_id = %s AND date_jour BETWEEN %s AND %s
            """
            df_heures = pd.read_sql_query(query_heures, conn, params=(selected_user_id, start_week_date, end_week_date))
            conn.close()
        except Exception as e:
            st.error(f"Erreur lors du chargement des heures saisies : {e}")
            df_heures = pd.DataFrame()

        # Conversion dates et nettoyage
        if not df_heures.empty:
            df_heures['date_jour'] = pd.to_datetime(df_heures['date_jour']).dt.strftime('%Y-%m-%d')
        if not df_feuille.empty:
            df_feuille['date_jour'] = pd.to_datetime(df_feuille['date_jour']).dt.strftime('%Y-%m-%d')

        pd.set_option('future.no_silent_downcasting', True)
        df_heures['projet_id'] = df_heures['projet_id'].replace('', np.nan).infer_objects(copy=False)
        df_heures['projet_id'] = pd.to_numeric(df_heures['projet_id'], errors='coerce')
        df_heures = df_heures.dropna(subset=['projet_id'])
        df_heures['projet_id'] = df_heures['projet_id'].astype(int)

        # Filtrer projets selon sélection
        # Filtrer projets selon sélection
        if selected_projects == 'all':
            df_projets_user_filtered = df_projets_user.copy()
        else:
            df_projets_user_filtered = df_projets_user[df_projets_user['id'].isin([selected_projects])]


        # --- Absences approuvées ---
        try:
            conn = get_connection()
            query_abs_user = """
                SELECT date_debut, date_fin, type_absence
                FROM absences
                WHERE user_id = %s AND statut = 'Approuvée'
                AND date_fin >= %s AND date_debut <= %s
            """
            df_abs_user = pd.read_sql_query(query_abs_user, conn,
                                            params=(selected_user_id, start_week_date, end_week_date))
            conn.close()

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
        except Exception as e:
            st.error(f"Erreur lors du chargement des absences : {e}")
            df_abs_user = pd.DataFrame(columns=["date_absence", "type_absence_raw", "type_absence_norm"])

        absences_set = set(zip(df_abs_user.get('date_absence', pd.Series([], dtype=str)),
                            df_abs_user.get('type_absence_norm', pd.Series([], dtype=str))))

        # Jours fériés
        fr_holidays = holidays.France(years=selected_year)
        jours_feries_set = {d.strftime('%Y-%m-%d') for d in pd.to_datetime(list(fr_holidays.keys()))
                            if start_week_date <= d.date() <= end_week_date}

        # Construction des lignes projets
        data = []
        for _, proj in df_projets_user_filtered.iterrows():
            row = {"projet_id": proj["id"], "Projet": proj["projet"]}
            for jour in jours_sem:
                mask = (df_heures['projet_id'] == proj['id']) & (df_heures['date_jour'] == jour)
                row[jour] = float(df_heures[mask]['heures'].values[0]) if not df_heures[mask].empty else 0.0
            data.append(row)

        # Types d'absences distincts
        try:
            conn = get_connection()
            df_types_raw = pd.read_sql_query("SELECT DISTINCT type_absence FROM absences", conn)
            conn.close()
        except Exception as e:
            st.error(f"Erreur lors du chargement des types d'absences : {e}")
            df_types_raw = pd.DataFrame(columns=['type_absence'])

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
            if jour in weekend_days:
                gb.configure_column(
                    jour,
                    editable=False,
                    cellStyle={"background-color": "#e0e0e0", "color": "#888888", "fontStyle": "italic"},
                    headerName=col_headers[jour]
                )
            elif jour in abs_dates or jour in jours_feries_set:
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

        # Bouton Enregistrer
        col_save, col_export,_ = st.columns([1.5,2,16])
        with col_save:
            if st.button("Enregistrer"):
                df_modif = pd.DataFrame(grid_response['data'])
                df_modif_sans_abs = df_modif[~df_modif['Projet'].str.startswith('Absence') & ~df_modif['Projet'].str.startswith('Jour férié')]

                erreurs = []
                for jour in jours_sem:
                    if (jour in weekend_days) or (jour in abs_dates) or (jour in jours_feries_set):
                        continue
                    val_jour = df_feuille[df_feuille.get('date_jour', pd.Series([], dtype=str)) == jour]['valeur']
                    if val_jour.empty:
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
                                if (jour in weekend_days) or (jour in abs_dates) or (jour in jours_feries_set):
                                    heures = 0.0
                                else:
                                    heures = row[jour] if row[jour] else 0.0
                                cur.execute("""
                                    INSERT INTO heures_saisie (user_id, projet_id, date_jour, heures)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (user_id, projet_id, date_jour) DO UPDATE SET heures = EXCLUDED.heures
                                """, (selected_user_id, projet_id, jour, float(heures)))

                        conn.commit()
                        conn.close()
                        st.toast("Heures enregistrées avec succès.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement : {e}")

        with col_export:

            # Filtrer projets selon sélection
            if selected_projects == 'all':
                projets_a_exporter = df_projets_user.copy()
            else:
                projets_a_exporter = df_projets_user[df_projets_user['id'].isin([selected_projects])]

            # Récupérer toutes les heures du mois pour l'utilisateur
            try:
                conn = get_connection()
                query_heures_mois = """
                    SELECT projet_id, date_jour, heures
                    FROM heures_saisie
                    WHERE user_id = %s
                    AND date_jour BETWEEN %s AND %s
                """
                df_heures_mois = pd.read_sql_query(query_heures_mois, conn, params=(selected_user_id, date_start, date_end))
                conn.close()

                # Normaliser les dates en format YYYY-MM-DD
                if not df_heures_mois.empty:
                    df_heures_mois['date_jour'] = pd.to_datetime(df_heures_mois['date_jour']).dt.strftime('%Y-%m-%d')

            except Exception as e:
                st.error(f"Erreur lors du chargement des heures du mois : {e}")
                df_heures_mois = pd.DataFrame()

            # Récupérer toutes les absences approuvées sur le mois
            try:
                conn = get_connection()
                query_abs_user = """
                    SELECT date_debut, date_fin
                    FROM absences
                    WHERE user_id = %s AND statut = 'Approuvée'
                    AND date_fin >= %s AND date_debut <= %s
                """
                df_abs_user_full = pd.read_sql_query(query_abs_user, conn, params=(selected_user_id, date_start, date_end))
                conn.close()

                if not df_abs_user_full.empty:
                    expanded_rows = []
                    for _, row in df_abs_user_full.iterrows():
                        periode = pd.date_range(start=row['date_debut'], end=row['date_fin'])
                        for d in periode:
                            expanded_rows.append(d.strftime('%Y-%m-%d'))
                    jours_absence = set(expanded_rows)
                else:
                    jours_absence = set()
            except Exception as e:
                st.error(f"Erreur lors du chargement des absences du mois : {e}")
                jours_absence = set()

            # Création de la liste de tous les jours du mois
            jours_mois = pd.date_range(date_start, date_end).strftime('%Y-%m-%d').tolist()
            jours_semaine_fr = {'Mon': 'Lun','Tue': 'Mar','Wed': 'Mer','Thu': 'Jeu','Fri': 'Ven','Sat': 'Sam','Sun': 'Dim'}

            # Préparer le dataframe export
            data_export = []
            for _, proj in projets_a_exporter.iterrows():
                row = {"Projet": proj["projet"]}
                for jour in jours_mois:
                    dt = pd.to_datetime(jour)
                    abbr_en = dt.strftime('%a')
                    jour_fr = jours_semaine_fr.get(abbr_en, abbr_en)
                    col_name = f"{jour_fr}-{dt.day}"  # ex: Lun-17

                    # Weekend
                    if dt.weekday() >= 5:
                        row[col_name] = "Weekend"
                    # Férié
                    elif jour in jours_feries_set:
                        row[col_name] = "Férié"
                    # Absence
                    elif jour in jours_absence:
                        row[col_name] = "Absence"
                    # Heures saisies
                    else:
                        mask = (df_heures_mois['projet_id'] == proj['id']) & (df_heures_mois['date_jour'] == jour)
                        if not df_heures_mois[mask].empty:
                            row[col_name] = float(df_heures_mois[mask]['heures'].values[0])
                        else:
                            row[col_name] = 0.0
                data_export.append(row)

            df_export = pd.DataFrame(data_export)

            # Créer le fichier Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Heures Mois')
            processed_data = output.getvalue()

            user_name = user_options[selected_user_id].replace(" ", "_")
            st.download_button(
                label="Exporter en Excel",
                data=processed_data,
                file_name=f"Heures_{user_name}_{selected_month_name}_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )