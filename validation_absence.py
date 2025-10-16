import streamlit as st
import pandas as pd
from db import get_connection
from datetime import datetime
import base64
import holidays
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io

st.set_page_config(page_title="Validation des absences", layout="wide")

def envoyer_mail_notification(email_destinataire, nom_utilisateur):
    expediteur = st.secrets["email"]["gmail_user"]
    mdp = st.secrets["email"]["gmail_app_password"]
    sujet = "Refus de votre demande d'absence"
    corps = f"""
    Bonjour {nom_utilisateur},

    Votre demande d'absence a été rejetée par l'administrateur.
    Veuillez vous connecter à votre espace pour plus de détails.

    Cordialement,
    L'équipe RH
    """
    message = MIMEMultipart()
    message["From"] = expediteur
    message["To"] = email_destinataire
    message["Subject"] = sujet
    message.attach(MIMEText(corps, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
            serveur.login(expediteur, mdp)
            serveur.sendmail(expediteur, email_destinataire, message.as_string())
    except Exception as e:
        st.error(f"Erreur lors de l'envoi du mail : {e}")
        raise

def show_validation_absence():

    # Droits d'accès
    if "role" not in st.session_state or st.session_state["role"] != "admin":
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT a.id, u.name AS utilisateur, a.type_absence, a.date_debut, a.date_fin,
            a.commentaire, a.statut, a.date_demande, a.justificatif
        FROM absences a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.date_demande DESC
    """
    df = pd.read_sql_query(query, conn, parse_dates=["date_debut", "date_fin", "date_demande"])

    st.markdown("""
        <div id="title">
            <h4> Validation des absences </h4> 
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

            .stButton>button:hover {
                background-color: white !important;
                color: #080686 !important;
                border: 1px solid #080686 !important;
            }
                
            div.stDownloadButton > button {
                background-color: #080686 !important;
                color: white !important;
                border-radius: 5px;
                font-size: 16px;
            }
                
            div.stDownloadButton > button:hover {
                background-color: white !important;
                color: #080686 !important;
                border: 1px solid #080686 !important;
            }

            .absence-card {
                border: 1px solid #cccccc;
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 10px;
                background-color: #fdfdfd;
                box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
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

            .Approuvée {
                background-color: #4CAF50 !important;
            }

            .Rejetée {
                background-color: #F44336 !important;
            }

            .En_attente {
                background-color: #FF9800 !important;
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

            .col-absence {
                padding: 10px 15px;
                border-right: 2px solid #000060;
                background-color: #e8ebf9;
                border-radius: 8px 8px 0 0;
                text-align: center;
                font-weight: 700;
                font-size: 18px;
                color: #000060;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                user-select: none;
                margin-bottom: 10px;
            }

            .col-absence:last-child {
                border-right: none;
            }

            .stTabs {
                margin-top: -50px !important;
            }

            .absence-card.conge-paye {
                background-color: #e6f0ff;
            }

            .absence-card.rtt {
                background-color: #ffffff;
            }

            .absence-card.teletravail {
                background-color: #e6f0ff;
            }

            .absence-card.maladie {
                background-color: #e6f0ff;
            }
                
            .absence-card.conge-sans-solde {
                background-color: #ffffff;
            }

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

            @media (max-width: 600px) {
                table, thead, tbody, th, td, tr {
                    display: block;
                }

                th {
                    text-align: left;
                    border-radius: 8px 8px 0 0;
                }

                td {
                    border: none;
                    border-bottom: 1px solid #eee;
                    position: relative;
                    padding-left: 50%;
                    text-align: left;
                }

                td:before {
                    position: absolute;
                    top: 50%;
                    left: 15px;
                    transform: translateY(-50%);
                    white-space: nowrap;
                    font-weight: 700;
                    color: #080686;
                }

                td:nth-of-type(1):before { content: "Utilisateur"; }
                td:nth-of-type(2):before { content: "Type d'absence"; }
                td:nth-of-type(3):before { content: "Période"; }
                td:nth-of-type(4):before { content: "Demandé le"; }
                td:nth-of-type(5):before { content: "Statut"; }
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
            
        </style>
    """, unsafe_allow_html=True)

    attente_df = df[df["statut"] == "En attente"]

    historique_df = df[df["statut"] != "En attente"].copy()

    tab1, tab2 = st.tabs(["Demandes en attente", "Historique"])

    annee_actuelle = datetime.today().year
    jours_feries = holidays.France(years=range(2023, annee_actuelle + 1))

    def calculer_jours_ouvres(debut, fin):
        jours_ouvres = 0
        for jour in pd.date_range(debut, fin):
            if jour.weekday() < 5 and jour not in jours_feries:
                jours_ouvres += 1
        return jours_ouvres

    # Demandes en attente 
    with tab1:
        utilisateurs_df = pd.read_sql_query("SELECT DISTINCT name FROM users ORDER BY name", conn)
        utilisateurs_disponibles = utilisateurs_df["name"].dropna().tolist()

        annees_disponibles = list(range(2020, 2031))
        annees_disponibles = list(map(str, sorted(annees_disponibles)))

        col1, col2, col3 = st.columns([2,3,3])

        with col2:
            annee_selectionnee = st.selectbox("📅 Année", options=["Toutes"] + annees_disponibles)
        with col3:
            utilisateur_selectionne = st.selectbox("🙍 Utilisateur", options=["Tous"] + utilisateurs_disponibles)
        with col1:
            df_filtre = attente_df.copy()
            nb_demandes_attente = len(df_filtre)
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{nb_demandes_attente}</div>
                    <div class="kpi-label">🕒 Total demande en attente</div>
                </div>
            """, unsafe_allow_html=True)

        df_filtre = attente_df.copy()
        
        if annee_selectionnee != "Toutes":
            df_filtre = df_filtre[df_filtre["date_demande"].dt.year == int(annee_selectionnee)]

        if utilisateur_selectionne != "Tous":
            df_filtre = df_filtre[df_filtre["utilisateur"] == utilisateur_selectionne]

        def gestion_absences_type(df_type, css_class, label):
            if df_type.empty:
                st.info(f"Aucune demande {label.lower()} en attente.")
            else:
                for _, row in df_type.iterrows():
                    statut_class = row["statut"].replace(" ", "_")
                    st.markdown(f"""
                        <div class="absence-card {css_class}">
                            <strong>👤 {row["utilisateur"]}</strong><br>
                            <b>Du :</b> {row["date_debut"].strftime("%d/%m/%Y")} au {row["date_fin"].strftime("%d/%m/%Y")}<br>
                            <b>Demandé le :</b> {row["date_demande"].strftime("%d/%m/%Y")}<br>
                            <b>Nombre de jours demandés :</b> {calculer_jours_ouvres(row["date_debut"], row["date_fin"])}<br>
                            <span class="status-badge {statut_class}">{row["statut"]}</span><br><br>
                    """, unsafe_allow_html=True)

                    cols_btn = st.columns(3)
                    with cols_btn[0]:
                        valider = st.button("✅", key=f"valider_{row['id']}")
                    with cols_btn[1]:
                        rejeter = st.button("❌", key=f"rejeter_{row['id']}")

                    rejeter_mode_key = f"rejeter_mode_{row['id']}"
                    if rejeter_mode_key not in st.session_state:
                        st.session_state[rejeter_mode_key] = False

                    if rejeter:
                        st.session_state[rejeter_mode_key] = True

                    if st.session_state[rejeter_mode_key]:
                        commentaire_key = f"commentaire_{row['id']}"
                        commentaire = st.text_area("Motif du refus", key=commentaire_key)
                        #
                        if st.button("Confirmer le rejet", key=f"confirmer_rejet_{row['id']}"):
                            if commentaire.strip() == "":
                                st.warning("Veuillez saisir un motif de refus.")
                            else:
                                # ⚠️ Vérifier que row contient bien "utilisateur"
                                cursor.execute("SELECT email FROM users WHERE name = %s", (row["utilisateur"],))
                                result = cursor.fetchone()
                                email_utilisateur = result[0] if result else None

                                cursor.execute("UPDATE absences SET statut = 'Rejetée' WHERE id = %s", (row["id"],))
                                cursor.execute("""
                                    INSERT INTO validation_absence (absence_id, validateur_id, date_validation, statut, commentaire)
                                    VALUES (%s, %s, %s, 'Rejetée', %s)
                                """, (row["id"], st.session_state.user_id, datetime.today().date(), commentaire))
                                conn.commit()

                                if email_utilisateur:
                                    envoyer_mail_notification(email_utilisateur, row["utilisateur"])

                                st.session_state[rejeter_mode_key] = False
                                st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

                    if valider:
                        cursor.execute("UPDATE absences SET statut = 'Approuvée' WHERE id = %s", (row["id"],))
                        cursor.execute("""
                            INSERT INTO validation_absence (absence_id, validateur_id, date_validation, statut)
                            VALUES (%s, %s, %s, 'Approuvée')
                        """, (row["id"], st.session_state.user_id, datetime.today().date()))
                        conn.commit()
                        st.rerun()

        col_cp, col_rtt, col_tt, col_css, col_mal = st.columns(5)

        with col_cp:
            st.markdown('<div class="col-absence">🌴 Congé payé</div>', unsafe_allow_html=True)
            cp_df = df_filtre[df_filtre["type_absence"] == "Congé payé"]
            gestion_absences_type(cp_df, "conge-paye", "Congé payé")

        with col_rtt:
            st.markdown('<div class="col-absence">⏳ RTT</div>', unsafe_allow_html=True)
            rtt_df = df_filtre[df_filtre["type_absence"] == "RTT"]
            gestion_absences_type(rtt_df, "rtt", "RTT")

        with col_tt:
            st.markdown('<div class="col-absence">💻 Télétravail</div>', unsafe_allow_html=True)
            tt_df = df_filtre[df_filtre["type_absence"] == "Télétravail"]
            gestion_absences_type(tt_df, "teletravail", "Télétravail")
        
        with col_css:
            st.markdown('<div class="col-absence">🏖️ Congé sans solde</div>', unsafe_allow_html=True)
            css_df = df_filtre[df_filtre["type_absence"] == "Congé sans solde"]
            gestion_absences_type(css_df, "conge-sans-solde", "Congé sans solde")

        with col_mal:
            st.markdown('<div class="col-absence">🤒 Maladie</div>', unsafe_allow_html=True)
            mal_df = df_filtre[df_filtre["type_absence"] == "Maladie"]
            if mal_df.empty:
                st.info("Aucune demande maladie en attente.")
            else:
                for _, row in mal_df.iterrows():
                    statut_class = row["statut"].replace(" ", "_")
                    st.markdown(f"""
                        <div class="absence-card maladie">
                            <strong>👤 {row["utilisateur"]}</strong><br>
                            <b>Du :</b> {row["date_debut"].strftime("%d/%m/%Y")} au {row["date_fin"].strftime("%d/%m/%Y")}<br>
                            <b>Demandé le :</b> {row["date_demande"].strftime("%d/%m/%Y")}<br>
                            <b>Nombre de jours demandés :</b> {calculer_jours_ouvres(row["date_debut"], row["date_fin"])}<br>
                            <span class="status-badge {statut_class}">{row["statut"]}</span><br><br>
                    """, unsafe_allow_html=True)

                    if row.get("justificatif"):
                        with st.expander("📎 Justificatif maladie"):
                            justificatif_path = f"./uploads/{row['justificatif']}"
                            ext = row["justificatif"].split('.')[-1].lower()
                            try:
                                if ext in ["png", "jpg", "jpeg"]:
                                    st.image(justificatif_path, width=700)
                                elif ext == "pdf":
                                    with open(justificatif_path, "rb") as f:
                                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="600" type="application/pdf"></iframe>'
                                    st.markdown(pdf_display, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"[Télécharger justificatif]({justificatif_path})")
                            except Exception as e:
                                st.error(f"Erreur lors du chargement du justificatif : {e}")

                    cols_btn = st.columns(3)
                    with cols_btn[0]:
                        valider = st.button("✅", key=f"valider_{row['id']}")
                    with cols_btn[1]:
                        rejeter = st.button("❌", key=f"rejeter_{row['id']}")

                    rejeter_mode_key = f"rejeter_mode_{row['id']}"
                    if rejeter_mode_key not in st.session_state:
                        st.session_state[rejeter_mode_key] = False

                    if rejeter:
                        st.session_state[rejeter_mode_key] = True

                    if st.session_state[rejeter_mode_key]:
                        commentaire_key = f"commentaire_{row['id']}"
                        commentaire = st.text_area("Motif du refus", key=commentaire_key)

                        if st.button("Confirmer le rejet", key=f"confirmer_rejet_{row['id']}"):
                            if commentaire.strip() == "":
                                st.warning("Veuillez saisir un motif de refus.")
                            else:
                                cursor.execute("UPDATE absences SET statut = 'Rejetée' WHERE id = %s", (row["id"],))
                                cursor.execute("""
                                    INSERT INTO validation_absence (absence_id, validateur_id, date_validation, statut, commentaire)
                                    VALUES (%s, %s, %s, 'Rejetée', %s)
                                """, (row["id"], st.session_state.user_id, datetime.today().date(), commentaire))

                                conn.commit()
                                st.session_state[rejeter_mode_key] = False
                                st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

                    if valider:
                        cursor.execute("UPDATE absences SET statut = 'Approuvée' WHERE id = %s", (row["id"],))
                        cursor.execute("""
                            INSERT INTO validation_absence (absence_id, validateur_id, date_validation, statut)
                            VALUES (%s, %s, %s, 'Approuvée')
                        """, (row["id"], st.session_state.user_id, datetime.today().date()))
                        conn.commit()
                        st.rerun()

    # Historique
    with tab2:
        utilisateurs_h = historique_df["utilisateur"].dropna().unique().tolist()
        type_absence_h = historique_df["type_absence"].dropna().unique().tolist()
        statut_h = historique_df["statut"].dropna().unique().tolist()

        mois_fr = {
            1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
            5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
            9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
        }

        annees_completes = list(range(2020, 2031))
        annee_options = ["Toutes"] + [str(a) for a in annees_completes]
        mois_nommes = [(num, nom) for num, nom in mois_fr.items()]
        mois_options = ["Tous"] + [nom for _, nom in mois_nommes]

        # Filtres
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            utilisateur_filtre = st.selectbox("🙍 Utilisateur", ["Tous"] + sorted(utilisateurs_h), key="hist_utilisateur")
        with col2:
            annee_filtre = st.selectbox("📅 Année", annee_options, key="hist_annee")
        with col3:
            mois_filtre = st.selectbox("📆 Mois", options=mois_options, key="hist_mois")
        with col4:
            type_filtre = st.selectbox("🗂️ Type d'absence", ["Tous"] + sorted(type_absence_h), key="hist_type")
        with col5:
            statut_filtre = st.selectbox("📌 Statut", ["Tous"] + sorted(statut_h), key="hist_statut")

        df_hist_filtre = historique_df.copy()
        if utilisateur_filtre != "Tous":
            df_hist_filtre = df_hist_filtre[df_hist_filtre["utilisateur"] == utilisateur_filtre]
        if annee_filtre != "Toutes":
            df_hist_filtre = df_hist_filtre[df_hist_filtre["date_demande"].dt.year == int(annee_filtre)]
        if mois_filtre != "Tous":
            mois_num = [num for num, nom in mois_nommes if nom == mois_filtre][0]
            df_hist_filtre = df_hist_filtre[df_hist_filtre["date_demande"].dt.month == mois_num]
        if type_filtre != "Tous":
            df_hist_filtre = df_hist_filtre[df_hist_filtre["type_absence"] == type_filtre]
        if statut_filtre != "Tous":
            df_hist_filtre = df_hist_filtre[df_hist_filtre["statut"] == statut_filtre]

        if df_hist_filtre.empty:
            st.info("Aucune demande correspondant aux filtres.")
        else:
            df_hist_filtre["Jours demandés"] = df_hist_filtre.apply(
                lambda x: calculer_jours_ouvres(x["date_debut"], x["date_fin"]), axis=1)
            df_hist_filtre["Période"] = df_hist_filtre.apply(
                lambda x: f"{x['date_debut'].strftime('%d/%m/%Y')} au {x['date_fin'].strftime('%d/%m/%Y')}", axis=1)
            df_hist_filtre["Demandé le"] = df_hist_filtre["date_demande"].dt.strftime("%d/%m/%Y")

            # --- Header du tableau ---
            header_cols = st.columns([3,2,3,2,2,2], gap="small")
            headers = ["Utilisateur", "Type d'absence", "Période", "Jours demandés", "Statut", "Actions"]
            for col, title in zip(header_cols, headers):
                col.markdown(
                    f"<div style='background-color:#080686; color:white; text-align:center; font-weight:bold; padding:8px; border:1px solid #000060; height:40px; display:flex; align-items:center; justify-content:center; margin-bottom:10px'>{title}</div>",
                    unsafe_allow_html=True
                )

            # --- Lignes du tableau ---
            for i, row in df_hist_filtre.iterrows():
                cols = st.columns([3,2,3,2,2,2], gap="small")
                for j, value in enumerate([
                    row['utilisateur'],
                    row['type_absence'],
                    row['Période'],
                    row['Jours demandés'],
                    f"<span class='status-badge {row['statut'].replace(' ', '_')}'>{row['statut']}</span>"  # plus de div blanc
                ]):
                    if j != 4:  # sauf pour le statut
                        cols[j].markdown(
                            f"<div style='background-color:white; padding:8px; text-align:center; border:1px solid #cccccc; height:50px; display:flex; align-items:center; justify-content:center'>{value}</div>",
                            unsafe_allow_html=True
                        )
                    else:  # statut sans fond blanc
                        cols[j].markdown(
                            f"<div style='text-align:center; display:flex; align-items:center; justify-content:center; height:40px'>{value}</div>",
                            unsafe_allow_html=True
                        )
                    
                # Bouton supprimer
                with cols[5]:
                    if st.button("Supprimer", key=f"suppr_{row['id']}"):
                        cursor.execute("DELETE FROM validation_absence WHERE absence_id = %s", (row['id'],))
                        cursor.execute("DELETE FROM absences WHERE id = %s", (row['id'],))
                        conn.commit()
                        st.toast("Absence supprimée !")
                        st.rerun()


            # --- Export Excel ---
            export_df = df_hist_filtre[[
                "utilisateur","type_absence","Période","Jours demandés","Demandé le","statut"
            ]].rename(columns={
                "utilisateur":"Utilisateur",
                "type_absence":"Type d'absence",
                "Période":"Période",
                "Jours demandés":"Jours demandés",
                "Demandé le":"Date de demande",
                "statut":"Statut"
            })

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name='Demandes')
            buffer.seek(0)

            st.download_button(
                label="Exporter en Excel",
                data=buffer,
                file_name="historique_absence.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
