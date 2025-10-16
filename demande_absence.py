import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import holidays
from db import get_connection
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Demande d'absences", layout="wide")

#Fonction pour détecter le dépassement de la limite de télétravail
def get_nb_teletravail_semaine(user_id, date_debut, date_fin, conn):
    df_tt = pd.read_sql_query("""
        SELECT date_debut, date_fin
        FROM absences
        WHERE user_id = %s 
        AND type_absence = 'Télétravail' 
        AND statut IN ('En attente', 'Approuvée')
    """, conn, params=(user_id,))

    df_tt["date_debut"] = pd.to_datetime(df_tt["date_debut"])
    df_tt["date_fin"] = pd.to_datetime(df_tt["date_fin"])

    dates_tt = []
    for _, row in df_tt.iterrows():
        jours = pd.date_range(start=row["date_debut"], end=row["date_fin"], freq='D')
        jours = [d for d in jours if d.weekday() < 5]
        dates_tt.extend(jours)

    nouvelles_dates = pd.date_range(start=date_debut, end=date_fin, freq='D')
    nouvelles_dates = [d for d in nouvelles_dates if d.weekday() < 5]
    toutes_dates = dates_tt + nouvelles_dates

    semaine_counts = {}
    for d in toutes_dates:
        key = (d.isocalendar().year, d.isocalendar().week)
        semaine_counts[key] = semaine_counts.get(key, 0) + 1

    semaines_depassees = {sem: count for sem, count in semaine_counts.items() if count > 2}
    return semaines_depassees

#Fonction pour récupérer les soldes annuel définis
def get_soldes_annuels(conn, annee: int):
    row = pd.read_sql_query(
        "SELECT cp_total, rtt_total FROM parametres_conges WHERE annee = %s",
        conn,
        params=(annee,)
    )

    if row.empty:
        return 0, 0
    return int(row.iloc[0]["cp_total"]), int(row.iloc[0]["rtt_total"])


def calcul_cp_mensuel(cumul_mensuel, cp_total):
    """
    cumul_mensuel : DataFrame avec les colonnes 'mois' et 'Congé payé'
    cp_total : nombre total de CP annuel
    Retourne une série avec le solde CP restant mois par mois
    """
    cp_mensuel_max = cp_total / 12
    mois_range = range(1, 13)
    solde_cp_mois = []

    cp_deja_utilises = 0
    for mois in mois_range:
        cp_deja_utilises += cumul_mensuel.loc[cumul_mensuel['mois'] == mois, 'Congé payé'].sum()
        solde = (mois * cp_mensuel_max) - cp_deja_utilises
        solde_cp_mois.append(max(solde, 0))

    return pd.Series(solde_cp_mois, index=mois_range)

def show_demande_absence():

    conn = get_connection()

    if "user_id" not in st.session_state:
        st.error("Vous devez être connecté pour accéder à cette page.")
        st.stop()

    user_id = st.session_state["user_id"]

    st.markdown("""
        <div id="title">
            <h4> Demande d'absence </h4> 
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

        .stButton > button {
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

        .stButton > button:hover {
            background-color: #f0f0f0; 
            color: #000060;  
            box-shadow: 0 6px 12px rgba(0, 0, 96, 0.6);
            transform: translateY(-3px);
        }

        .stButton > button:active {
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
                
        .kpi-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 1rem;
        }
                
        .kpi-value {
            font-size: 2rem;
            font-weight: bold;
            color: #2b8a3e;
        }
                
        .kpi-label {
            font-size: 1rem;
            font-weight: 500;
            color: #6c757d;
        }
                
        .kpi-icon {
            font-size: 1.8rem;
            margin-bottom: 0.3rem;
        }

        .custom-table {
            width: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #222;
            border-collapse: collapse;
        }

        .custom-table th {
            background-color: #080686 !important;
            color: white !important;
            font-weight: 700;
            padding: 10px 12px;
            text-align: center !important;
            user-select: none;
        }

        .custom-table td {
            background-color: white;
            padding: 10px 12px;
            text-align: center;
            vertical-align: middle;
        }

        .custom-table tbody tr:nth-child(odd) td {
            background-color: #f9f9fb;
        }

        .custom-table tbody tr:hover td {
            background-color: #e6f0ff;
            cursor: pointer;
        }

        @media (max-width: 600px) {
            .custom-table, 
            .custom-table thead, 
            .custom-table tbody, 
            .custom-table th, 
            .custom-table td, 
            .custom-table tr {
                display: block;
            }
                
            .custom-table th {
                text-align: left;
                border-radius: 8px 8px 0 0;
            }
                    
            .custom-table td {
                border: none;
                border-bottom: 1px solid #eee;
                position: relative;
                padding-left: 50%;
                text-align: left;
            }
                    
            .custom-table td:before {
                position: absolute;
                top: 50%;
                left: 15px;
                transform: translateY(-50%);
                white-space: nowrap;
                font-weight: 700;
                color: #080686;
            }

            .custom-table td:nth-of-type(1):before { content: "Date demande"; }
            .custom-table td:nth-of-type(2):before { content: "Type"; }
            .custom-table td:nth-of-type(3):before { content: "Motif"; }
        }
                
        .stTabs [data-baseweb="tab"] {
            font-size: 20px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
        }
                
        </style>
    """, unsafe_allow_html=True)

    mois_options = list(range(1, 13))

    df_type_abs = pd.read_sql_query(
        "SELECT DISTINCT type_absence FROM absences WHERE user_id = %s",
        conn,
        params=(user_id,)
    )
    type_options = sorted(df_type_abs["type_absence"].dropna().unique())
    type_options = ["Tous"] + type_options

    col1, col2, col3 = st.columns(3)
    with col1:
        annee_filtre = st.selectbox(
            "📆 Année",
            list(range(2020, 2031)),
            index=list(range(2020, 2031)).index(datetime.today().year)
        )
    with col2:
        mois_filtre = st.selectbox(
        "📅 Mois",
        options=mois_options,
        format_func=lambda x: pd.to_datetime(x, format='%m').strftime('%B')
    )
    with col3:
        type_filtre = st.selectbox("🏷️ Type d'absence", options=type_options)

    st.session_state["annee_filtre"] = annee_filtre
    st.session_state["mois_filtre"] = mois_filtre
    st.session_state["type_filtre"] = type_filtre

    tab1, tab2 = st.tabs(["Tableau de bord", "Demande d'absence"])
    
    # Onglet dashboard
    with tab1:
        
        annee_courante = st.session_state.get("annee_filtre", date.today().year)
        solde_cp, solde_rtt = get_soldes_annuels(conn, annee_courante)

        def calcul_jours_ouvres(debut, fin):
            annees = list(range(debut.year, fin.year + 1))
            fr_holidays = holidays.France(years=annees)

            jours_ouvres = pd.date_range(start=debut, end=fin, freq='D')
            jours_ouvres = [d for d in jours_ouvres if d.weekday() < 5 and d not in fr_holidays]
            return len(jours_ouvres)

        df_conso = pd.read_sql_query("""
            SELECT type_absence, date_debut, date_fin
            FROM absences
            WHERE user_id = %s 
            AND statut = 'Approuvée'
            AND EXTRACT(YEAR FROM date_debut) = %s
        """, conn, params=(user_id, annee_courante))

        if not df_conso.empty:
            df_conso["date_debut"] = pd.to_datetime(df_conso["date_debut"])
            df_conso["date_fin"] = pd.to_datetime(df_conso["date_fin"])
            df_conso["jours_ouvres"] = df_conso.apply(lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1)

            jours_conges = df_conso.loc[df_conso["type_absence"] == "Congé payé", "jours_ouvres"].sum()
            jours_rtt = df_conso.loc[df_conso["type_absence"] == "RTT", "jours_ouvres"].sum()
        else:
            jours_conges = 0
            jours_rtt = 0

        mois_courant = date.today().month
        mois_courant_nom = date.today().strftime("%B")
        cp_acquis = (solde_cp / 12) * mois_courant

        jours_restants_conges = max(0, cp_acquis - jours_conges)
        jours_restants_rtt = solde_rtt - jours_rtt

        col_cg, col_rtt = st.columns(2)

        with col_cg:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{jours_restants_conges:.0f}jours</div>
                    <div class="kpi-label">🌴 Congés restants - {mois_courant_nom}</div>
                </div>
            """, unsafe_allow_html=True)

        with col_rtt:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{jours_restants_rtt:.0f} jours</div>
                    <div class="kpi-label">🕒 RTT restants</div>
                </div>
            """, unsafe_allow_html=True)

        # Suivi cumulatif des jours d'absence - CP & RTT
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
            Suivi cumulatif des jours d'absence - CP & RTT</h4>
        """, unsafe_allow_html=True)

        col_graphe, col_resume = st.columns([5,2])
        
        with col_graphe:

            df_cumul = pd.read_sql_query("""
                SELECT type_absence, date_debut, date_fin
                FROM absences
                WHERE user_id = %s
                AND statut = 'Approuvée'
                AND EXTRACT(YEAR FROM date_debut) = %s
            """, conn, params=(user_id, annee_courante))


            cur = conn.cursor()
            cur.execute(
                "SELECT cp_total, rtt_total FROM parametres_conges WHERE annee = %s",
                (annee_courante,)
            )
            row = cur.fetchone()

            parametres_annee = {"cp_total": row[0], "rtt_total": row[1]} if row else {"cp_total": 0, "rtt_total": 0}

            if df_cumul.empty:
                st.info("Aucune absence approuvée pour l'année sélectionnée.")
                cumul_mensuel = pd.DataFrame({
                    "mois": range(1, 13),
                    "Congé payé": [0]*12,
                    "RTT": [0]*12,
                })
            else:
                df_cumul["date_debut"] = pd.to_datetime(df_cumul["date_debut"])
                df_cumul["date_fin"] = pd.to_datetime(df_cumul["date_fin"])
                df_cumul["jours_ouvres"] = df_cumul.apply(
                    lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1
                )
                df_cumul["mois"] = df_cumul["date_debut"].dt.month
                df_cumul = df_cumul[df_cumul["type_absence"].isin(["Congé payé", "RTT"])]

                cumul_mensuel = (
                    df_cumul.groupby(["mois", "type_absence"])["jours_ouvres"]
                    .sum()
                    .unstack(fill_value=0)
                    .reindex(index=range(1,13), fill_value=0)
                    .cumsum()
                    .reset_index()
                )

                for col in ["Congé payé", "RTT"]:
                    if col not in cumul_mensuel.columns:
                        cumul_mensuel[col] = 0

            cumul_mensuel["mois_nom"] = cumul_mensuel["mois"].apply(lambda m: pd.to_datetime(str(m), format="%m").strftime("%B"))
            cumul_mensuel["mois_nom"] = pd.Categorical(
                cumul_mensuel["mois_nom"],
                categories=[pd.to_datetime(str(m), format="%m").strftime("%B") for m in range(1,13)],
                ordered=True
            )

            cp_total = parametres_annee["cp_total"]
            cumul_mensuel["CP_restant"] = [(cp_total / 12) * (i+1) - cumul_mensuel.loc[i, "Congé payé"] for i in range(12)]
            rtt_total = parametres_annee["rtt_total"]
            cumul_mensuel["RTT_restant"] = [(rtt_total / 12) * (i+1) - cumul_mensuel.loc[i, "RTT"] for i in range(12)]

            fig_line = px.line(
                cumul_mensuel,
                x="mois_nom",
                y=["Congé payé", "RTT"],
                labels={"value": "Jours cumulés", "mois_nom": "Mois", "variable": "Type"},
                markers=True,
                color_discrete_map={"Congé payé": "#46c4c4", "RTT": "#f6c85f"}
            )

            fig_line.add_scatter(
                x=cumul_mensuel["mois_nom"],
                y=cumul_mensuel["CP_restant"],
                mode="lines+markers",
                name="CP restant",
                line=dict(color="#00BFFF", dash="dot")
            )

            fig_line.add_hline(y=cp_total, line_dash="solid", line_color="#46c4c4", opacity=0.6,
                            annotation=dict(text=f"Max CP : {cp_total} jours", font=dict(size=12, color="#046666"), align="left"))
            fig_line.add_hline(y=rtt_total, line_dash="solid", line_color="#f6c85f", opacity=0.6,
                            annotation=dict(text=f"Max RTT : {rtt_total} jours", font=dict(size=12, color="#665000"), align="left"))
            fig_line.update_layout(
                height=350,
                xaxis_tickangle=-45,
                yaxis=dict(tickformat=".0f", title="Jours cumulés"),
                margin=dict(t=40, b=20, l=20, r=20),
                legend_title_text="Type d'absence"
            )

            st.plotly_chart(fig_line, use_container_width=True)
                
        with col_resume:
            if cumul_mensuel.empty:
                st.info("Aucune donnée de consommation annuelle à afficher.")
            else:
                dernier_mois = cumul_mensuel.iloc[-1]

                conso_cp = int(dernier_mois.get("Congé payé", 0))
                conso_rtt = int(dernier_mois.get("RTT", 0))

                reste_cp = max(0, int(dernier_mois.get("CP_restant", 0)))
                reste_rtt = max(0, int(rtt_total - conso_rtt))

                def badge(msg, color):
                    return f"""
                    <span style="
                        display: inline-block;
                        background-color: {color};
                        color: white;
                        width: 100%;
                        padding: 10px 20px;
                        border-radius: 20px;
                        font-size: 14px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    ">{msg}</span>
                    """
                
                if reste_cp > 0:
                    msg_cp = badge(f"✅ {conso_cp}/{cp_total} CP utilisés (reste {reste_cp})", "#4CAF50")
                else:
                    msg_cp = badge(f"⚠️ {conso_cp}/{cp_total} CP atteints", "#E53935")

                if reste_rtt > 0:
                    msg_rtt = badge(f"✅ {conso_rtt}/{rtt_total} RTT utilisés (reste {reste_rtt})", "#4CAF50")
                else:
                    msg_rtt = badge(f"⚠️ {conso_rtt}/{rtt_total} RTT atteints", "#E53935")

                reste_msg = f"""
                <div style="
                    padding: 8px 12px;
                    background-color: #E8F5E9;
                    border-radius: 8px;
                    margin-top: 25px;
                    color: #2E7D32;
                    font-weight: bold;
                    display: inline-block;
                ">
                    📌 Il vous reste {reste_cp} CP et {reste_rtt} RTT à poser d’ici la fin de l’année
                </div>
                """
                card_html = f"""
                <div style="
                    background-color: #ffffff;
                    border-radius: 12px;
                    padding: 20px;
                    height: 350px;
                    box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
                    font-family: 'Segoe UI';
                ">
                    <h4 style="color: #4B6A9B; margin-bottom: 17px;">Consommation annuelle CP & RTT</h4>
                    <div style="margin-bottom: 10px; text-align: center;">{msg_cp}</div>
                    <div style="margin-bottom: 10px; text-align: center;">{msg_rtt}</div>
                    {reste_msg}
                </div>
                """

                st.markdown(card_html, unsafe_allow_html=True)




        # Comparaison annuelle des absences
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
            Comparaison annuelle des absences</h4>
        """, unsafe_allow_html=True)

        annees_disponibles = pd.read_sql_query("""
            SELECT DISTINCT EXTRACT(YEAR FROM date_debut) AS annee
            FROM absences
            WHERE user_id = %s 
            AND statut = 'Approuvée'
            ORDER BY annee
        """, conn, params=(user_id,))

        annees = annees_disponibles["annee"].tolist()


        # Générer autant de %s qu'il y a d'années
        if annees:
            placeholders = ', '.join(['%s'] * len(annees))
            df_all_years = pd.read_sql_query(f"""
                SELECT type_absence, date_debut, date_fin
                FROM absences
                WHERE user_id = %s
                AND statut = 'Approuvée'
                AND EXTRACT(YEAR FROM date_debut) IN ({placeholders})
            """, conn, params=(user_id, *annees))
        else:
            df_all_years = pd.DataFrame(columns=["type_absence", "date_debut", "date_fin"])


        if df_all_years.empty:
            st.info("Aucune absence approuvée enregistrée pour ces années.")
        else:
            df_all_years["date_debut"] = pd.to_datetime(df_all_years["date_debut"])
            df_all_years["date_fin"] = pd.to_datetime(df_all_years["date_fin"])
            df_all_years["annee"] = df_all_years["date_debut"].dt.year
            df_all_years["jours_ouvres"] = df_all_years.apply(
                lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1
            )

            if type_filtre == "Tous":
                grouped = df_all_years.groupby(["annee", "type_absence"])["jours_ouvres"].sum().reset_index()

                fig_compare = px.line(
                    grouped,
                    x="annee",
                    y="jours_ouvres",
                    color="type_absence",
                    markers=True,
                    labels={
                        "annee": "Année",
                        "jours_ouvres": "Jours ouvrés",
                        "type_absence": "Type d'absence"
                    },
                    title="Évolution annuelle des absences par type"
                )
            else:
                df_filtre = df_all_years[df_all_years["type_absence"] == type_filtre]
                grouped = df_filtre.groupby("annee")["jours_ouvres"].sum().reset_index()

                fig_compare = px.line(
                    grouped,
                    x="annee",
                    y="jours_ouvres",
                    markers=True,
                    labels={"annee": "Année", "jours_ouvres": "Jours ouvrés"},
                    title=f"Évolution annuelle des absences - {type_filtre}"
                )

            fig_compare.update_layout(
                height=300,
                xaxis=dict(tickmode='linear'),
                yaxis=dict(tickformat=".0f"),
                margin=dict(t=40, b=20, l=20, r=20)
            )

            st.plotly_chart(fig_compare, use_container_width=True)

            col_left, col_right = st.columns([4,2])

            # Évolution mensuelle du nombre de jours d'absence
            with col_left:
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
                    Évolution mensuelle des absences par type - {annee_filtre}</h4>
                """, unsafe_allow_html=True)

                df_evolution = pd.read_sql_query("""
                    SELECT type_absence, date_debut, date_fin
                    FROM absences
                    WHERE user_id = %s
                    AND statut = 'Approuvée'
                    AND EXTRACT(YEAR FROM date_debut) = %s
                """, conn, params=(user_id, annee_courante))

                if df_evolution.empty:
                    st.info("Aucune absence approuvée pour l'année sélectionnée.")
                else:
                    df_evolution["date_debut"] = pd.to_datetime(df_evolution["date_debut"])
                    df_evolution["date_fin"] = pd.to_datetime(df_evolution["date_fin"])
                    df_evolution["mois"] = df_evolution["date_debut"].dt.month

                    df_evolution["jours_ouvres"] = df_evolution.apply(
                        lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1
                    )

                    grouped = df_evolution.groupby(["mois", "type_absence"])["jours_ouvres"].sum().reset_index()

                    grouped["mois_nom"] = grouped["mois"].apply(lambda m: pd.to_datetime(str(m), format="%m").strftime("%B"))
                    grouped["mois_nom"] = pd.Categorical(grouped["mois_nom"],
                        categories=[pd.to_datetime(str(m), format="%m").strftime("%B") for m in range(1,13)],
                        ordered=True
                    )

                    fig_stacked = px.bar(
                        grouped,
                        x="mois_nom",
                        y="jours_ouvres",
                        color="type_absence",
                        labels={"jours_ouvres": "Jours ouvrés", "mois_nom": "Mois"},
                        color_discrete_map={
                            "Congé payé": "#46c4c4",
                            "RTT": "#f6c85f",
                            "Maladie": "#e06666",
                            "Télétravail": "#6fa8dc",
                            "Autre": "#cccccc"
                        }
                    )

                    fig_stacked.update_layout(
                        barmode='group',
                        height=350,
                        xaxis_tickangle=-45,
                        legend_title_text="Type d'absence",
                        yaxis=dict(tickformat=".0f"),
                        margin=dict(t=50, b=20, l=20, r=20)
                    )

                    st.plotly_chart(fig_stacked, use_container_width=True)


            # Répartition des absences par type
            with col_right:
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
                    Répartition des absences par type</h4>
                """, unsafe_allow_html=True)

                df_repartition = pd.read_sql_query("""
                    SELECT type_absence, date_debut, date_fin
                    FROM absences
                    WHERE user_id = %s
                    AND statut = 'Approuvée'
                    AND EXTRACT(YEAR FROM date_debut) = %s
                """, conn, params=(user_id, annee_courante))

                if df_repartition.empty:
                    st.info("Aucune absence approuvée pour l'année sélectionnée.")
                else:
                    df_repartition["date_debut"] = pd.to_datetime(df_repartition["date_debut"])
                    df_repartition["date_fin"] = pd.to_datetime(df_repartition["date_fin"])
                    df_repartition["jours_ouvres"] = df_repartition.apply(
                        lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1
                    )

                    repartition = df_repartition.groupby("type_absence")["jours_ouvres"].sum().reset_index()
                    repartition = repartition[repartition["jours_ouvres"] > 0]

                    fig_pie = px.pie(
                        repartition,
                        names="type_absence",
                        values="jours_ouvres",
                        color="type_absence",
                        hole=0.4,
                        color_discrete_map={
                            "Congé payé": "#46c4c4",
                            "RTT": "#f6c85f",
                            "Maladie": "#e06666",
                            "Télétravail": "#6fa8dc",
                            "Autre": "#cccccc"
                        }
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(height=350, margin=dict(t=50, b=20, l=20, r=20))

                    st.plotly_chart(fig_pie, use_container_width=True)

            # Gantt
            mois_noms = {
                1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
            }

            nom_mois = date.today().strftime("%B")
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
                Vision globale - absences approuvées - {nom_mois} {annee_filtre}</h4>
            """, unsafe_allow_html=True)

            df_gantt = pd.read_sql_query("""
                SELECT type_absence, date_debut, date_fin
                FROM absences
                WHERE user_id = %s
                AND statut = 'Approuvée'
                ORDER BY date_debut
            """, conn, params=(user_id,))

            if df_gantt.empty:
                st.info("Aucune absence approuvée à afficher.")
            else:
                df_gantt["date_debut"] = pd.to_datetime(df_gantt["date_debut"])
                df_gantt["date_fin"] = pd.to_datetime(df_gantt["date_fin"]) + timedelta(days=1)

                df_gantt["annee"] = df_gantt["date_debut"].dt.year
                df_gantt["mois"] = df_gantt["date_debut"].dt.month

                annee_sel = st.session_state.get("annee_filtre", date.today().year)
                mois_sel = date.today().month 

                df_filtre = df_gantt[df_gantt["annee"] == annee_sel]
                if mois_sel:
                    df_filtre = df_filtre[df_filtre["mois"] == mois_sel]

                if df_filtre.empty:
                    st.info("Aucune absence pour cette période.")
                else:
                    df_filtre["duree_jours"] = df_filtre.apply(lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"] - timedelta(days=1)), axis=1)
                    df_filtre["label"] = df_filtre.apply(lambda r: f"{r['type_absence']} ({r['duree_jours']} j. ouvrés)", axis=1)
                    df_filtre["custom_text"] = df_filtre["duree_jours"].astype(str) + " j."

                    fig = px.timeline(
                        df_filtre,
                        x_start="date_debut",
                        x_end="date_fin",
                        y="type_absence",
                        color="type_absence",
                        text="custom_text",
                        hover_name="label",
                        color_discrete_map={
                            "Congé payé": "#46c4c4",  
                            "RTT": "#f6c85f",         
                            "Maladie": "#e06666",    
                            "Télétravail": "#6fa8dc",  
                            "Autre": "#cccccc"     
                        },
                        title=f"Absences approuvées - Diagramme de Gantt ({annee_sel} - {mois_sel:02d})",
                        height=350,
                    )
                    fig.update_yaxes(autorange="reversed", title="Type d'absence", showgrid=True, gridcolor='LightGray')
                    fig.update_xaxes(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='LightGray',
                        dtick="D1",
                        tickformat="%d %b",
                        tickangle=45,
                        title="Dates"
                    )
                    fig.update_layout(
                        margin=dict(l=20, r=20, t=50, b=50),
                        legend_title_text="Type d'absence",
                        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                    )

                    st.plotly_chart(fig, use_container_width=True)
        
    # Onglet demande et historique =====================================
    with tab2:

        annee_courante = st.session_state.get("annee_filtre", date.today().year)
        solde_cp, solde_rtt = get_soldes_annuels(conn, annee_courante)

        # Calcul des jours consommés
        df_conso = pd.read_sql_query("""
            SELECT type_absence, date_debut, date_fin
            FROM absences
            WHERE user_id = %s
            AND statut = 'Approuvée'
            AND EXTRACT(YEAR FROM date_debut) = %s
        """, conn, params=(user_id, annee_courante))

        if not df_conso.empty:
            df_conso["date_debut"] = pd.to_datetime(df_conso["date_debut"])
            df_conso["date_fin"] = pd.to_datetime(df_conso["date_fin"])
            df_conso["jours_ouvres"] = df_conso.apply(lambda row: calcul_jours_ouvres(row["date_debut"], row["date_fin"]), axis=1)

            jours_conges = df_conso.loc[df_conso["type_absence"] == "Congé payé", "jours_ouvres"].sum()
            jours_rtt = df_conso.loc[df_conso["type_absence"] == "RTT", "jours_ouvres"].sum()
        else:
            jours_conges = 0
            jours_rtt = 0

        jours_restants_conges = solde_cp - jours_conges
        jours_restants_rtt = solde_rtt - jours_rtt

        # Création du dossier upload si nécessaire
        UPLOAD_DIR = "./uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        col_left1, col_right1 = st.columns([4,5])

        # ------------------ Colonne gauche : Formulaire + refus ------------------
        with col_left1:
            # Formulaire nouvelle demande
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
                ➕ Nouvelle demande</h4>
            """, unsafe_allow_html=True)

            with st.form("form_demande_absence"):
                type_absence = st.selectbox(
                    "Type d'absence",
                    ["Congé payé", "RTT", "Maladie", "Télétravail", "Congé sans solde"]
                )
                col1, col2 = st.columns(2)
                with col1:
                    date_debut = st.date_input("Date de début", value=date.today())
                with col2:
                    date_fin = st.date_input("Date de fin", value=date.today())

                justificatif = None
                if type_absence == "Maladie":
                    justificatif = st.file_uploader("Ajouter un justificatif", type=["pdf", "png", "jpg", "jpeg"])

                disable_submit = False
                if type_absence == "Congé payé" and jours_restants_conges <= 0:
                    st.warning("⚠️ Vous n'avez plus de congés disponibles.")
                    disable_submit = True
                elif type_absence == "RTT" and jours_restants_rtt <= 0:
                    st.warning("⚠️ Vous n'avez plus de RTT disponibles.")
                    disable_submit = True
                
                # Vérification des weekends
                if date_debut.weekday() >= 5 or date_fin.weekday() >= 5:
                    disable_submit = True

                submitted = st.form_submit_button("Soumettre la demande", disabled=disable_submit)

                if submitted:
                    nb_jours_demande = calcul_jours_ouvres(date_debut, date_fin)

                    # Vérifications préliminaires
                    if date_fin < date_debut:
                        st.warning("La date de fin ne peut pas être antérieure à la date de début.")
                    elif type_absence == "Maladie" and justificatif is None:
                        st.warning("Un justificatif est obligatoire pour une absence maladie.")
                    elif type_absence == "Congé payé" and nb_jours_demande > jours_restants_conges:
                        st.warning(f"Vous ne disposez pas d'assez de jours de congés. Solde restant : {jours_restants_conges:.0f} jour(s).")
                    elif type_absence == "RTT" and nb_jours_demande > jours_restants_rtt:
                        st.warning(f"Vous ne disposez pas d'assez de jours de RTT. Solde restant : {jours_restants_rtt:.0f} jour(s).")
                    elif date_debut.weekday() >= 5 or date_fin.weekday() >= 5:
                        st.warning("⚠️ La date de début et de fin ne peut pas tomber un week-end.")
                    else:
                        # Gestion du justificatif
                        nom_justificatif = None
                        if justificatif is not None:
                            nom_justificatif = f"{user_id}_{date.today().isoformat()}_{justificatif.name}"
                            chemin_fichier = os.path.join(UPLOAD_DIR, nom_justificatif)
                            with open(chemin_fichier, "wb") as f:
                                f.write(justificatif.getbuffer())

                        # Vérification télétravail
                        teletravail_ok = True
                        if type_absence == "Télétravail":
                            semaines_depassees = get_nb_teletravail_semaine(user_id, date_debut, date_fin, conn)
                            if semaines_depassees:
                                semaines_txt = ", ".join([f"Semaine {sem[1]}" for sem in semaines_depassees.keys()])
                                st.warning(f"⚠️ Vous dépassez la limite de 2 jours de télétravail sur les semaines suivantes : {semaines_txt}.")
                                teletravail_ok = False

                        # Insertion si tout est ok
                        if teletravail_ok:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO absences (
                                        user_id, type_absence, date_debut, date_fin, statut, date_demande, justificatif
                                    )
                                    VALUES (%s, %s, %s, %s, 'En attente', CURRENT_DATE, %s)
                                """, (
                                    user_id,
                                    type_absence,
                                    date_debut.isoformat(),
                                    date_fin.isoformat(),
                                    nom_justificatif
                                ))
                                conn.commit()
                                st.success(f"Demande d'{type_absence.lower()} soumise avec succès.")
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Erreur lors de l'insertion : {e}")


                    
            # Bloc Motif de refus
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
                ❌ Motif de refus</h4>
            """, unsafe_allow_html=True)

            df_refus = pd.read_sql_query("""
                SELECT 
                    a.date_demande, 
                    a.type_absence, 
                    v.commentaire
                FROM validation_absence v
                JOIN absences a ON v.absence_id = a.id
                WHERE a.user_id = %s
                AND v.statut = 'Rejetée'
                ORDER BY a.date_demande DESC
            """, conn, params=(user_id,))

            if not df_refus.empty:
                df_refus["date_demande"] = pd.to_datetime(df_refus["date_demande"]).dt.strftime("%d/%m/%Y")
                df_refus.rename(columns={
                    "date_demande": "Date demande",
                    "type_absence": "Type",
                    "commentaire": "Motif"
                }, inplace=True)
                colonnes_affichees_refus = ["Date demande", "Type", "Motif"]
                table_html_refus = df_refus[colonnes_affichees_refus].to_html(
                    escape=False, 
                    index=False, 
                    classes='custom-table'
                )
                st.markdown(f"<div style='overflow-x:auto; width:100%;'>{table_html_refus}</div>", unsafe_allow_html=True)
            else:
                st.info("Aucun refus enregistré.")

        # ------------------ Colonne droite : Historique ------------------
        with col_right1:
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
                📖 Historique de vos demandes</h4>
            """ , unsafe_allow_html=True)

            df = pd.read_sql_query("""
                SELECT date_demande, type_absence, date_debut, date_fin, justificatif, statut
                FROM absences
                WHERE user_id = %s
                ORDER BY date_debut DESC
            """, conn, params=(user_id,))

            df["date_debut_dt"] = pd.to_datetime(df["date_debut"])
            #df = df[df["date_debut_dt"].dt.year == annee_courante]
            if type_filtre != "Tous":
                df = df[df["type_absence"] == type_filtre]

            if not df.empty:
                df["date_debut"] = pd.to_datetime(df["date_debut"]).dt.strftime("%d/%m/%Y")
                df["date_fin"] = pd.to_datetime(df["date_fin"]).dt.strftime("%d/%m/%Y")
                df["date_demande"] = pd.to_datetime(df["date_demande"]).dt.strftime("%d/%m/%Y")

                def style_statut(statut):
                    couleur = {
                        "En attente": "#facc15", 
                        "Approuvée": "#22c55e",
                        "Rejetée": "#ef4444",
                    }.get(statut, "#d1d5db")
                    return f'<span style="background-color:{couleur};color:white;padding:4px 10px;border-radius:10px;font-size:13px;">{statut}</span>'

                df["statut_badge"] = df["statut"].apply(style_statut)

                df_affiche = df.rename(columns={
                    "date_demande": "Date demande",
                    "type_absence": "Type",
                    "date_debut": "Début",
                    "date_fin": "Fin",
                    "statut_badge": "Statut"
                })

                colonnes_affichees = ["Date demande", "Type", "Début", "Fin", "Statut"]
                table_html = df_affiche[colonnes_affichees].to_html(
                    escape=False, 
                    index=False, 
                    classes='custom-table'
                )
                st.markdown(f"<div style='overflow-x:auto; width:100%;'>{table_html}</div>", unsafe_allow_html=True)
            else:
                st.info("Aucune demande d'absence enregistrée.")

        conn.close()
