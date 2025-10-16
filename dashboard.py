import streamlit as st
from db import get_connection
from datetime import datetime
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import calendar
import holidays
import pandas as pd
from streamlit_lottie import st_lottie
import requests

st.set_page_config(page_title="Dashboard admin/RH", layout="wide")

def show_dashboard():

    # Droits d'accès
    # Vérification des droits d'accès
    if "user_id" not in st.session_state or "role" not in st.session_state:
        st.error("Vous devez être connecté pour accéder au tableau de bord.")
        st.stop()

    if st.session_state["role"] != "admin":
        st.error("Accès réservé à l'administrateur.")
        st.stop()

    user_id = st.session_state["user_id"]

    st.markdown("""
        <div id="title">
            <h4> Dashboard RH / Administrateur </h4>  
        </div>
    """, unsafe_allow_html=True)

    # Connexion à la base
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            st.error("Utilisateur introuvable dans la base.")
            st.stop()
        user_name = row[0]
    except Exception as e:
        st.error(f"Erreur lors de la récupération de l'utilisateur : {e}")
        st.stop()


    st.markdown("""
        <style>
                
            .stApp {
                background-color: #f2f2f2;     
            }

            .block-container {
                padding-top: 1rem !important; 
                margin-top: 0 !important;
            }
                    
            .main .block-container {
                margin-top: 0rem !important;
            }

            header {
                visibility: hidden;
                height: 0px;
            }

            .stButton {
                background-color: #080686;
                font-size: 16px;
                border-radius: 5px;
                color: white;
            }

            .stButton>button:hover {
                background-color: white;
                color: #080686;
                border: 1px solid #080686;
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
            
            .welcome-message {
                font-size: 24px;
                font-weight: 500;
                margin: 30px 0px 20px 10px;
                color: #333333;
                font-family: 'Segoe UI', sans-serif;
            }

            .user-name-highlight {
                color: #1a40af;
                font-weight: 700;
            }

            .stTabs [data-baseweb="tab"] {
                font-size: 20px !important;
                font-weight: 600 !important;
                padding: 10px 20px !important;
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
                font-size: 1.6rem;
                font-weight: bold;
                color: #2b8a3e;
            }
                
            .kpi-subvalue {
                font-size: 18px;
                font-weight: bold;
                color: #0d2059;
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
                
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div class='welcome-message'>👋 Bienvenue, <span class='user-name-highlight'>{user_name}</span> !</div>",
        unsafe_allow_html=True
    )

    #-------------------- Filtres --------------------

    current_year = datetime.now().year
    current_month = datetime.now().month

    years_list = [str(y) for y in range(2023, current_year + 1)]
    years_list.reverse()

    mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    cursor.execute("SELECT id, name FROM users ORDER BY name")
    employees = cursor.fetchall()
    employee_options = ["Tous"] + [name for _, name in employees]

    role_options = ["Tous", "consultant", "rh", "admin"]


    default_month_index = current_month - 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_year = st.selectbox(
            "📆 Année",
            list(range(2020, 2031)),
            index=list(range(2020, 2031)).index(datetime.today().year)
        )
    with col2:
        selected_month_name = st.selectbox("🗓️ Mois", options=mois_fr, index=default_month_index)
    with col3:
        selected_employee = st.selectbox("🧑‍💼 Employé", options=employee_options, index=0)
    with col4:
        selected_role = st.selectbox("🎭 Rôle", options=role_options, index=0)

    def business_days_in_month(y, m, country="FR"):
        jours_feries = holidays.country_holidays(country, years=y)
        last_day = calendar.monthrange(y, m)[1]
        d0 = date(y, m, 1)
        d1 = date(y, m, last_day)
        days = 0
        cur = d0
        one = timedelta(days=1)

        while cur <= d1:
            if cur.weekday() < 5 and cur not in jours_feries:  
                days += 1
            cur += one

        return days

    tab1, tab2, tab3, tab4 = st.tabs(["Temps de travail", "Absence", "Projets", "Prévisions"])

    #--------------------------- Dashboard temps de travail ------------------------
    with tab1:

        mois_to_num = {m: i+1 for i, m in enumerate(mois_fr)}
        month_number = mois_to_num[selected_month_name]

        query = """
            SELECT u.name, ft.valeur
            FROM feuille_temps ft
            JOIN users u ON u.id = ft.user_id
            WHERE EXTRACT(YEAR FROM ft.date) = %s
            AND EXTRACT(MONTH FROM ft.date) = %s
        """
        params = [selected_year, month_number] 

        if selected_employee != "Tous":
            query += " AND u.name = %s"
            params.append(selected_employee)

        if selected_role != "Tous":
            query += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
            params.append(selected_role)


        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=["Utilisateur", "Valeur"])
            df["Heures"] = df["Valeur"].apply(lambda x: 8 if x == 1 else (3 if x == 0.5 else 0))
            df_grouped = df.groupby("Utilisateur", as_index=False)["Heures"].sum()
        else:
            df_grouped = pd.DataFrame(columns=["Utilisateur", "Heures"])
        
        #------------------------------- Calcul KPI ---------------------------
        query_ft = """
            SELECT u.id as user_id, u.name as Utilisateur,
                'Travail' as Statut,
                COUNT(*) as Jours
            FROM feuille_temps ft
            JOIN users u ON u.id = ft.user_id
            WHERE EXTRACT(YEAR FROM ft.date) = %s
            AND EXTRACT(MONTH FROM ft.date) = %s
            AND ft.statut_jour = 'travail'
        """
        params_ft = [selected_year, month_number]

        if selected_employee != "Tous":
            query_ft += " AND u.name = %s"
            params_ft.append(selected_employee)

        if selected_role != "Tous":
            query_ft += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
            params_ft.append(selected_role)

        query_ft += " GROUP BY u.id, u.name"

        cursor.execute(query_ft, tuple(params_ft))
        ft_rows = cursor.fetchall()
        df_ft = pd.DataFrame(ft_rows, columns=["user_id", "Utilisateur", "Statut", "Jours"])

        query_abs = """
            SELECT u.id as user_id, u.name as Utilisateur,
                a.type_absence as Statut,
                a.date_debut,
                a.date_fin
            FROM absences a
            JOIN users u ON u.id = a.user_id
            WHERE EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """
        params_abs = [selected_year, month_number] 

        if selected_employee != "Tous":
            query_abs += " AND u.name = %s"
            params_abs.append(selected_employee)

        if selected_role != "Tous":
            query_abs += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
            params_abs.append(selected_role)

        cursor.execute(query_abs, tuple(params_abs))
        abs_rows = cursor.fetchall()

        abs_rows_expanded = []
        for user_id, user_name, statut, date_debut, date_fin in abs_rows:
            current = date_debut
            while current <= date_fin:
                if current.year == int(selected_year) and current.month == month_number:
                    abs_rows_expanded.append((user_id, user_name, statut, 1))
                current += timedelta(days=1)

        df_abs = pd.DataFrame(abs_rows_expanded, columns=["user_id", "Utilisateur", "Statut", "Jours"])

        selected_year = int(selected_year)
        previous_year = selected_year - 1

        query_ft_prev = """
            SELECT u.id as user_id, u.name as Utilisateur,
                'Travail' as Statut,
                COUNT(*) as Jours
            FROM feuille_temps ft
            JOIN users u ON u.id = ft.user_id
            WHERE EXTRACT(YEAR FROM ft.date) = %s
            AND EXTRACT(MONTH FROM ft.date) = %s
        """
        params_ft_prev = [previous_year, month_number] 

        if selected_employee != "Tous":
            query_ft_prev += " AND u.name = %s"
            params_ft_prev.append(selected_employee)

        if selected_role != "Tous":
            query_ft_prev += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
            params_ft_prev.append(selected_role)

        query_ft_prev += " GROUP BY u.id, u.name"
        cursor.execute(query_ft_prev, tuple(params_ft_prev))
        ft_rows_prev = cursor.fetchall()
        df_ft_prev = pd.DataFrame(ft_rows_prev, columns=["user_id", "Utilisateur", "Statut", "Jours"])

        query_abs_prev = """
            SELECT u.id as user_id, u.name as Utilisateur,
                a.type_absence as Statut,
                a.date_debut,
                a.date_fin
            FROM absences a
            JOIN users u ON u.id = a.user_id
            WHERE EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """
        params_abs_prev = [previous_year, month_number] 

        if selected_employee != "Tous":
            query_abs_prev += " AND u.name = %s"
            params_abs_prev.append(selected_employee)

        if selected_role != "Tous":
            query_abs_prev += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
            params_abs_prev.append(selected_role)

        cursor.execute(query_abs_prev, tuple(params_abs_prev))
        abs_rows_prev = cursor.fetchall()

        abs_rows_expanded_prev = []
        for user_id, user_name, statut, date_debut, date_fin in abs_rows_prev:
            current = date_debut
            while current <= date_fin:
                if current.year == int(previous_year) and current.month == month_number:
                    abs_rows_expanded_prev.append((user_id, user_name, statut, 1))
                current += timedelta(days=1)

        df_abs_prev = pd.DataFrame(abs_rows_expanded_prev, columns=["user_id", "Utilisateur", "Statut", "Jours"])

        jours_travailles_prev = df_ft_prev["Jours"].sum() if not df_ft_prev.empty else 0
        teletravail_days_prev = df_abs_prev.loc[df_abs_prev["Statut"] == "Télétravail", "Jours"].sum() if not df_abs_prev.empty else 0
        absenteisme_days_prev = df_abs_prev.loc[df_abs_prev["Statut"].isin(["RTT", "Congé payé", "Maladie"]), "Jours"].sum() if not df_abs_prev.empty else 0
        total_theorique_prev = jours_travailles_prev + teletravail_days_prev + absenteisme_days_prev

        pct_teletravail_prev = round((teletravail_days_prev / total_theorique_prev) * 100, 1) if total_theorique_prev > 0 else 0

        if not df_grouped.empty:

            df_prev = pd.concat([df_ft_prev, df_abs_prev], ignore_index=True)
            if not df_prev.empty:
                df_grouped_prev = df_prev.groupby("Utilisateur", as_index=False)["Jours"].sum()
                top_employee_prev = df_grouped_prev.loc[df_grouped_prev['Jours'].idxmax(), 'Utilisateur']
            else:
                top_employee_prev = "Aucun"
        else:
            top_employee_prev = "Aucun"

        df_combined = pd.concat([df_ft, df_abs], ignore_index=True)

        jours_travailles = df_ft["Jours"].sum() if not df_ft.empty else 0
        teletravail_days = df_abs.loc[df_abs["Statut"] == "Télétravail", "Jours"].sum() if not df_abs.empty else 0
        absenteisme_days = df_abs.loc[df_abs["Statut"].isin(["RTT", "Congé payé", "Maladie"]), "Jours"].sum() if not df_abs.empty else 0
        total_theorique = jours_travailles + teletravail_days + absenteisme_days
        pct_teletravail = round((teletravail_days / total_theorique) * 100, 1) if total_theorique > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{jours_travailles} jours</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {jours_travailles_prev} jours</div>
                    <div class="kpi-label">📅 Jours travaillées</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{pct_teletravail} %</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {pct_teletravail_prev} %</div>
                    <div class="kpi-label">💻 % Télétravail</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            if not df_grouped.empty:
                top_employee = df_grouped.loc[df_grouped['Heures'].idxmax(), 'Utilisateur']
            else:
                top_employee = "Aucun"
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{top_employee}</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {top_employee_prev}</div>
                    <div class="kpi-label">🥇 Employé du mois</div>
                </div>
            """, unsafe_allow_html=True)

        col_graphe1, col_graphe2 = st.columns(2)

        with col_graphe1:
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
                Heures travaillées - {selected_month_name} {selected_year}</h4>
            """, unsafe_allow_html=True)

            if not df_grouped.empty:
                df_grouped = df_grouped.sort_values(by="Heures", ascending=False)
                fig = px.bar(
                    df_grouped,
                    x="Utilisateur",
                    y="Heures",
                    text="Heures",
                    color="Heures",
                    color_continuous_scale="Blues",
                )
                fig.update_traces(texttemplate='%{text:.0f}h', textposition='outside')
                fig.update_layout(
                    yaxis_title="Heures totales",
                    xaxis_title="Utilisateur",
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour ces filtres.")
        
        with col_graphe2:
            mois_map = {
            "Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4,
            "Mai": 5, "Juin": 6, "Juillet": 7, "Août": 8,
            "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12
            }

            selected_month = mois_map[selected_month_name]
            query = """
            SELECT type_absence, SUM((date_fin - date_debut + 1)) AS nb_jours
            FROM absences
            WHERE statut = 'Approuvée'
            AND (
                    (EXTRACT(MONTH FROM date_debut) = %s AND EXTRACT(YEAR FROM date_debut) = %s)
                    OR (EXTRACT(MONTH FROM date_fin) = %s AND EXTRACT(YEAR FROM date_fin) = %s)
                )
            GROUP BY type_absence;
            """

            cursor.execute(query, (selected_month, selected_year, selected_month, selected_year))
            rows = cursor.fetchall()

            df_grouped = pd.DataFrame(rows, columns=["Type d'absence", "Jours"])
            
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
                Répartition des statuts - {selected_month_name} {selected_year}</h4>
            """, unsafe_allow_html=True)
            if not df_grouped.empty and df_grouped["Jours"].sum() > 0:
                fig2 = px.pie(
                    df_grouped,
                    names="Type d'absence",
                    values="Jours",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig2.update_layout(
                    legend_title="",
                    legend=dict(
                        orientation="h",
                        y=-0.1,
                        x=0.5,
                        xanchor="center",
                        yanchor="top"
                    ),
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Aucune absence approuvée pour ces filtres.")

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
            Evolution de la tendance mensuelle par statut - {selected_year}</h4>
        """, unsafe_allow_html=True)

        statut_set = set()
        for i, mois_name in enumerate(mois_fr, start=1):
            query_ft = """
                SELECT DISTINCT ft.statut_jour as Statut
                FROM feuille_temps ft
                JOIN users u ON u.id = ft.user_id
                WHERE EXTRACT(YEAR FROM ft.date) = %s
                AND EXTRACT(MONTH FROM ft.date) = %s
            """
            params = [selected_year, i]

            if selected_employee != "Tous":
                query_ft += " AND u.name = %s"
                params.append(selected_employee)

            if selected_role != "Tous":
                query_ft += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
                params.append(selected_role)

            cursor.execute(query_ft, tuple(params))
            rows = cursor.fetchall()
            for r in rows:
                statut_set.add(r[0].capitalize())

            query_abs = """
                SELECT DISTINCT a.type_absence as Statut
                FROM absences a
                JOIN users u ON u.id = a.user_id
                WHERE EXTRACT(YEAR FROM a.date_debut) = %s
                AND EXTRACT(MONTH FROM a.date_debut) = %s
            """
            params_abs = [selected_year, i] 

            if selected_employee != "Tous":
                query_abs += " AND u.name = %s"
                params_abs.append(selected_employee)

            if selected_role != "Tous":
                query_abs += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
                params_abs.append(selected_role)

            cursor.execute(query_abs, tuple(params_abs))
            rows_abs = cursor.fetchall()
            for r in rows_abs:
                statut_set.add(r[0].capitalize())

        statut_options = ["Tous"] + sorted(list(statut_set))
        selected_statut = st.selectbox("Statut", options=statut_options, index=0)

        evolution_data = []

        for i, mois_name in enumerate(mois_fr, start=1):
            query_month = """
                SELECT u.id as user_id, u.name as Utilisateur,
                    ft.statut_jour as Statut,
                    COUNT(*) as Jours
                FROM feuille_temps ft
                JOIN users u ON u.id = ft.user_id
                WHERE EXTRACT(YEAR FROM ft.date) = %s
                AND EXTRACT(MONTH FROM ft.date) = %s
            """
            params_month = [selected_year, i] 

            if selected_employee != "Tous":
                query_month += " AND u.name = %s"
                params_month.append(selected_employee)

            if selected_role != "Tous":
                query_month += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
                params_month.append(selected_role)

            query_month += " GROUP BY u.id, u.name, ft.statut_jour"
            cursor.execute(query_month, tuple(params_month))
            rows_month = cursor.fetchall()
            df_month_ft = pd.DataFrame(rows_month, columns=["user_id", "Utilisateur", "Statut", "Jours"])

            query_abs_month = """
                SELECT u.id as user_id, u.name as Utilisateur,
                    a.type_absence as Statut,
                    a.date_debut,
                    a.date_fin
                FROM absences a
                JOIN users u ON u.id = a.user_id
                WHERE EXTRACT(YEAR FROM a.date_debut) = %s
                AND EXTRACT(MONTH FROM a.date_debut) = %s
            """
            params_abs_month = [selected_year, i]

            if selected_employee != "Tous":
                query_abs_month += " AND u.name = %s"
                params_abs_month.append(selected_employee)

            if selected_role != "Tous":
                query_abs_month += " AND u.id IN (SELECT user_id FROM roles WHERE role = %s)"
                params_abs_month.append(selected_role)

            cursor.execute(query_abs_month, tuple(params_abs_month))
            abs_rows_month = cursor.fetchall()

            abs_rows_expanded_month = []
            for user_id, user_name, statut, date_debut, date_fin in abs_rows_month:
                current = date_debut
                while current <= date_fin:
                    if current.year == int(selected_year) and current.month == i:
                        abs_rows_expanded_month.append((user_id, user_name, statut, 1))
                    current += timedelta(days=1)

            df_month_abs = pd.DataFrame(abs_rows_expanded_month, columns=["user_id", "Utilisateur", "Statut", "Jours"])

            df_month_combined = pd.concat([df_month_ft, df_month_abs], ignore_index=True)
            df_month_combined["Statut"] = df_month_combined["Statut"].str.capitalize()

            if selected_statut != "Tous":
                df_month_combined = df_month_combined[df_month_combined["Statut"] == selected_statut]

            df_month_grouped = df_month_combined.groupby("Statut", as_index=False)["Jours"].sum()

            if df_month_grouped.empty:
                if selected_statut == "Tous":
                    for s in statut_options[1:]:
                        evolution_data.append({"Mois": mois_name, "Statut": s, "Jours": 0})
                else:
                    evolution_data.append({"Mois": mois_name, "Statut": selected_statut, "Jours": 0})
            else:
                for statut_row in df_month_grouped.itertuples(index=False):
                    evolution_data.append({
                        "Mois": mois_name,
                        "Statut": statut_row.Statut,
                        "Jours": statut_row.Jours
                    })

        df_evolution = pd.DataFrame(evolution_data, columns=["Mois", "Statut", "Jours"])

        df_final = []
        for mois_name in mois_fr:
            mois_data = df_evolution[df_evolution['Mois'] == mois_name]
            for statut in mois_data['Statut'].unique():
                jours = mois_data[mois_data['Statut'] == statut]['Jours'].sum()
                df_final.append({"Mois": mois_name, "Statut": statut, "Jours": jours})

        df_final = pd.DataFrame(df_final)

        if df_final.empty or df_final["Jours"].sum() == 0:
            st.warning(f"Aucune donnée trouvée pour l'année {selected_year} avec les filtres choisis (Employé: {selected_employee}, Rôle: {selected_role}, Statut: {selected_statut}).")
        else:
            fig_line = px.line(
                df_final,
                x="Mois",
                y="Jours",
                color="Statut",
                markers=True,
            )
            fig_line.update_layout(
                xaxis=dict(categoryorder='array', categoryarray=mois_fr),
                yaxis_title="Nombre de jours",
                legend_title="Statut",
                margin=dict(l=50, r=50, t=50, b=50)
            )
            st.plotly_chart(fig_line, use_container_width=True)

    #----------------------------- Dashboard absences ---------------------------
    with tab2:

        month_number = mois_fr.index(selected_month_name) + 1
        previous_year = str(int(selected_year) - 1)

        query = """
            SELECT SUM((a.date_fin - a.date_debut) + 1) as total_jours
            FROM absences a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN roles r ON u.id = r.user_id
            WHERE a.statut = 'Approuvée'
            AND EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """
        params = [selected_year, month_number]

        if selected_employee != "Tous":
            query += " AND u.name = %s"
            params.append(selected_employee)

        if selected_role != "Tous":
            query += " AND r.role = %s"
            params.append(selected_role)

        cursor.execute(query, tuple(params))
        total_jours_absence = cursor.fetchone()[0] or 0

        params_prev = [previous_year, f"{month_number:02d}"]

        if selected_employee != "Tous":
            params_prev.append(selected_employee)

        if selected_role != "Tous":
            params_prev.append(selected_role)

        cursor.execute(query, params_prev)
        total_jours_prev = cursor.fetchone()[0] or 0

        if total_jours_prev == 0:
            variation = "N/A"
        else:
            variation = f"{((total_jours_absence - total_jours_prev) / total_jours_prev * 100):+.0f}%"
        
        query_total_absences = """
            SELECT COUNT(*) 
            FROM absences a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN roles r ON u.id = r.user_id
            WHERE a.statut = 'Approuvée'
            AND EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """

        query_teletravail = query_total_absences + " AND a.type_absence = 'Télétravail'"

        params = [selected_year, month_number] 

        if selected_employee != "Tous":
            query_total_absences += " AND u.name = %s"
            query_teletravail += " AND u.name = %s"
            params.append(selected_employee)

        if selected_role != "Tous":
            query_total_absences += " AND r.role = %s"
            query_teletravail += " AND r.role = %s"
            params.append(selected_role)


        cursor.execute(query_total_absences, tuple(params))
        total_absences = cursor.fetchone()[0] or 0

        cursor.execute(query_teletravail, params)
        total_teletravail = cursor.fetchone()[0] or 0

        pct_teletravail = 0 if total_absences == 0 else round((total_teletravail / total_absences) * 100)

        params_prev = [previous_year, f"{month_number:02d}"]
        if selected_employee != "Tous":
            params_prev.append(selected_employee)
        if selected_role != "Tous":
            params_prev.append(selected_role)

        cursor.execute(query_total_absences, params_prev)
        total_absences_prev = cursor.fetchone()[0] or 0

        cursor.execute(query_teletravail, params_prev)
        total_teletravail_prev = cursor.fetchone()[0] or 0

        pct_teletravail_prev = 0 if total_absences_prev == 0 else round((total_teletravail_prev / total_absences_prev) * 100)

        if pct_teletravail_prev == 0:
            if pct_teletravail == 0:
                variation_teletravail = "0%"
            else:
                variation_teletravail = "+100%"
        else:
            variation_teletravail = f"{((pct_teletravail - pct_teletravail_prev) / pct_teletravail_prev * 100):+.0f}%"

        month_number = mois_fr.index(selected_month_name) + 1
        year_int = int(selected_year)
        previous_year = str(year_int - 1)

        jours_ouvres_courant = business_days_in_month(year_int, month_number)
        jours_ouvres_prev = business_days_in_month(year_int - 1, month_number)

        query_abs_days = """
            SELECT COALESCE(SUM((a.date_fin - a.date_debut) + 1), 0)
            FROM absences a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN roles r ON u.id = r.user_id
            WHERE a.statut = 'Approuvée'
            AND a.type_absence <> 'Télétravail'
            AND EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """
        params_abs = [selected_year, month_number]  

        if selected_employee != "Tous":
            query_abs_days += " AND u.name = %s"
            params_abs.append(selected_employee)

        if selected_role != "Tous":
            query_abs_days += " AND r.role = %s"
            params_abs.append(selected_role)

        cursor.execute(query_abs_days, tuple(params_abs))
        jours_absence_courant = cursor.fetchone()[0] or 0

        params_abs_prev = [previous_year, f"{month_number:02d}"]
        if selected_employee != "Tous":
            params_abs_prev.append(selected_employee)
        if selected_role != "Tous":
            params_abs_prev.append(selected_role)

        cursor.execute(query_abs_days, params_abs_prev)
        jours_absence_prev = cursor.fetchone()[0] or 0

        query_headcount = """
            SELECT COUNT(*)
            FROM users u
            LEFT JOIN roles r ON u.id = r.user_id
            WHERE u.is_active = 1
        """
        params_hc = []

        if selected_employee != "Tous":
            query_headcount += " AND u.name = %s"
            params_hc.append(selected_employee)

        if selected_role != "Tous":
            query_headcount += " AND r.role = %s"
            params_hc.append(selected_role)

        cursor.execute(query_headcount, tuple(params_hc))
        effectif = cursor.fetchone()[0] or 0

        denom_courant = jours_ouvres_courant * effectif
        denom_prev = jours_ouvres_prev * effectif

        if denom_courant == 0:
            taux_absenteisme = None
        else:
            taux_absenteisme = round((jours_absence_courant / denom_courant) * 100)

        if denom_prev == 0:
            taux_absenteisme_prev = None
        else:
            taux_absenteisme_prev = round((jours_absence_prev / denom_prev) * 100)

        if (taux_absenteisme_prev is None) or (taux_absenteisme_prev == 0):
            if (taux_absenteisme is None) or (taux_absenteisme == 0):
                variation_abs = "0%"
            else:
                variation_abs = "+100%"
        else:
            variation_abs = f"{((taux_absenteisme - taux_absenteisme_prev) / taux_absenteisme_prev * 100):+.0f}%"

        query_top_abs = """
            SELECT u.name, COALESCE(SUM((a.date_fin - a.date_debut) + 1), 0) as jours_abs
            FROM absences a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN roles r ON u.id = r.user_id
            WHERE a.statut = 'Approuvée'
            AND a.type_absence <> 'Télétravail'
            AND EXTRACT(YEAR FROM a.date_debut) = %s
            AND EXTRACT(MONTH FROM a.date_debut) = %s
        """
        params_top = [selected_year, month_number]

        if selected_employee != "Tous":
            query_top_abs += " AND u.name = %s"
            params_top.append(selected_employee)

        if selected_role != "Tous":
            query_top_abs += " AND r.role = %s"
            params_top.append(selected_role)

        query_top_abs += " GROUP BY u.name ORDER BY jours_abs DESC LIMIT 1"

        cursor.execute(query_top_abs, tuple(params_top))
        row = cursor.fetchone()
        if row:
            top_name, top_days = row
        else:
            top_name, top_days = "N/A", 0

        params_top_prev = [previous_year, f"{month_number:02d}"]
        if selected_employee != "Tous":
            params_top_prev.append(selected_employee)
        if selected_role != "Tous":
            params_top_prev.append(selected_role)

        cursor.execute(query_top_abs, params_top_prev)
        row_prev = cursor.fetchone()
        if row_prev:
            top_name_prev, top_days_prev = row_prev
        else:
            top_name_prev, top_days_prev = "N/A", 0

        col1, col2, col3, col4 = st.columns([3,3,3,4])
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{int(total_jours_absence)} jours</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {int(total_jours_prev)} jours ({variation})</div>
                    <div class="kpi-label">🕒 Nombre de jours d'absence</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{pct_teletravail} %</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {pct_teletravail_prev} % ({variation_teletravail})</div>
                    <div class="kpi-label">💻 % Télétravail</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            valeur = f"{taux_absenteisme:.0f} %" if taux_absenteisme is not None else "N/A"
            prev_txt = f"{taux_absenteisme_prev:.0f} %" if taux_absenteisme_prev is not None else "N/A"
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{valeur} - <span class="kpi-subvalue">Seuil = 5%</span></div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {prev_txt} ({variation_abs})</div>
                    <div class="kpi-label">🚫 Taux d'absentéisme</div>
                </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{top_name} ({int(top_days)} jours)</div>
                    <div class="kpi-subvalue">{selected_month_name} {previous_year} : {top_name_prev} ({int(top_days_prev)} jours)</div>
                    <div class="kpi-label">🥇 Top absent</div>
                </div>
            """, unsafe_allow_html=True)

        tab_liste_absence, tab_graphique = st.tabs(["Absences de la semaine", "Analyse avancée"]) 
        
        with tab_liste_absence:

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
                Tableau des absences par semaine</h4>
            """, unsafe_allow_html=True)

            month_index = mois_fr.index(selected_month_name) + 1
            year = int(selected_year)

            first_day_of_month = date(year, month_index, 1)
            last_day_of_month = date(year, month_index, calendar.monthrange(year, month_index)[1])

            first_week_num = first_day_of_month.isocalendar()[1]
            last_week_num = last_day_of_month.isocalendar()[1]

            if last_week_num < first_week_num:
                last_week_num += date(year, 12, 28).isocalendar()[1]

            total_weeks = last_week_num - first_week_num + 1

            today = datetime.now().date()
            current_week_num = today.isocalendar()[1]
            default_week_index = 0 if today.month != month_index else max(0, min(total_weeks - 1, current_week_num - first_week_num))

            week_options = [f"Semaine {w}" for w in range(1, total_weeks + 1)]

            col1, col2 = st.columns([2, 3])
            with col1:
                selected_week = st.selectbox(
                    "📅 Semaine du mois",
                    options=week_options,
                    index=default_week_index
                )
            with col2:
                search_text = st.text_input("🔍 Rechercher un employé")

            cursor.execute("SELECT id, name FROM users ORDER BY name")
            employees = cursor.fetchall()
            employee_list = [name for _, name in employees]

            if search_text:
                employee_list = [name for name in employee_list if search_text.lower() in name.lower()]

            week_dates = []
            for i in range(7):
                week_number = int(selected_week.split()[1])
                day = first_day_of_month + timedelta(days=(week_number - 1) * 7 + i)
                if day.month == month_index:
                    week_dates.append(day)
            week_labels = [d.strftime("%d/%m") for d in week_dates]

            df_week = pd.DataFrame(index=employee_list, columns=week_labels)


            query_abs = """
                SELECT u.name, a.type_absence, a.date_debut, a.date_fin
                FROM absences a
                JOIN users u ON a.user_id = u.id
                WHERE a.statut = 'Approuvée'
                AND EXTRACT(YEAR FROM a.date_debut) = %s
                AND EXTRACT(MONTH FROM a.date_debut) = %s
                AND a.type_absence <> 'Télétravail'
            """
            params = [selected_year, month_index] 

            cursor.execute(query_abs, tuple(params))
            absences = cursor.fetchall()


            for name, type_abs, start, end in absences:
                start_date = pd.to_datetime(start).date()
                end_date = pd.to_datetime(end).date()
                for d in week_dates:
                    if start_date <= d <= end_date:
                        if type_abs == "Congé payé":
                            df_week.loc[name, d.strftime("%d/%m")] = "CP"
                        elif type_abs == "Congé sans solde":
                            df_week.loc[name, d.strftime("%d/%m")] = "CSS"
                        elif type_abs == "RTT":
                            df_week.loc[name, d.strftime("%d/%m")] = "RTT"
                        elif type_abs == "Maladie":
                            df_week.loc[name, d.strftime("%d/%m")] = "Maladie"

            for name in employee_list:
                for d in week_dates:
                    col = d.strftime("%d/%m")
                    if pd.isna(df_week.loc[name, col]):
                        if d.weekday() >= 5:
                            df_week.loc[name, col] = "Weekend"
                        else:
                            df_week.loc[name, col] = "T"

            def style_cell(val):
                if val == "CP":
                    color = "#28a745"  
                    icon = "🟢"
                elif val == "CSS":
                    color = "#ffc107"  
                    icon = "🟡"
                elif val == "RTT":
                    color = "#007bff"  
                    icon = "🔵"
                elif val == "Maladie":
                    color = "#dc3545" 
                    icon = "🔴"
                elif val == "Weekend":
                    color = "#f2f2f2" 
                    icon = "🌞"
                else:
                    color = "#f8f9fa" 
                    icon = ""
                return f'<td style="background-color:{color}; text-align:center; padding:8px;">{icon} {val}</td>'

            rows_per_page = 10
            total_rows = len(df_week)
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page 

            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

            start_idx = (page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            df_page = df_week.iloc[start_idx:end_idx]

            html_table = '''
            <table style="
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 14px;
            ">
            '''

            html_table += '<tr style="position: sticky; top: 0; background-color:#000060; color:white; text-align:center;">'
            html_table += '<th style="padding:8px; text-align:left;">Employé</th>'
            for col in df_page.columns:
                html_table += f'<th style="padding:8px; text-align:center;">{col}</th>'
            html_table += '</tr>'

            for row_num, (idx, row) in enumerate(df_page.iterrows()):
                bg_color = "#f9f9f9" if row_num % 2 == 0 else "#ffffff"
                html_table += f'<tr style="background-color:{bg_color};">'
                html_table += f'<td style="padding:8px; font-weight:bold;">{idx}</td>'
                for val in row:
                    html_table += style_cell(val)
                html_table += '</tr>'

            html_table += '</table>'

            st.markdown(html_table, unsafe_allow_html=True)
            st.caption(f"Page {page} / {total_pages}")

        with tab_graphique:
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
                Evolution de la tendance mensuelle des jours d'absence - Comparaison avec l'année précédente</h4>
            """, unsafe_allow_html=True)

            def get_monthly_absences(year, selected_employee, selected_role):
                query = """
                    SELECT EXTRACT(MONTH FROM a.date_debut) as mois,
                        COALESCE(SUM((a.date_fin - a.date_debut) + 1), 0) as jours_abs
                    FROM absences a
                    JOIN users u ON a.user_id = u.id
                    LEFT JOIN roles r ON u.id = r.user_id
                    WHERE a.statut = 'Approuvée'
                    AND EXTRACT(YEAR FROM a.date_debut) = %s
                    AND a.type_absence <> 'Télétravail'
                """
                params = [year]

                if selected_employee != "Tous":
                    query += " AND u.name = %s"
                    params.append(selected_employee)

                if selected_role != "Tous":
                    query += " AND r.role = %s"
                    params.append(selected_role)

                query += " GROUP BY mois ORDER BY mois"

                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()


                data = {m: 0 for m in range(1, 13)}
                for row in rows:
                    mois = int(row[0])
                    jours = row[1]
                    data[mois] = jours

                df = pd.DataFrame({
                    "Mois": list(data.keys()),
                    "Jours_absence": list(data.values())
                })
                return df

            df_current = get_monthly_absences(selected_year, selected_employee, selected_role)
            df_current["Année"] = selected_year

            df_prev = get_monthly_absences(previous_year, selected_employee, selected_role)
            df_prev["Année"] = previous_year

            df_all = pd.concat([df_current, df_prev])

            mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
            df_all["Mois"] = df_all["Mois"].apply(lambda x: mois_fr[x-1])

            fig = px.line(
                df_all,
                x="Mois", y="Jours_absence",
                color="Année",
                markers=True,
            )

            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns([4,2])

            with col1:
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
                    Taux d'absentéisme et de présence - {selected_year}</h4>
                """, unsafe_allow_html=True)

                mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

                df_taux = []

                for i, mois_name in enumerate(mois_fr, start=1):
                    jours_ouvres = business_days_in_month(int(selected_year), i)

                    query_abs = """
                        SELECT COALESCE(SUM((a.date_fin - a.date_debut) + 1), 0)
                        FROM absences a
                        JOIN users u ON a.user_id = u.id
                        LEFT JOIN roles r ON u.id = r.user_id
                        WHERE a.statut = 'Approuvée'
                        AND EXTRACT(YEAR FROM a.date_debut) = %s
                        AND EXTRACT(MONTH FROM a.date_debut) = %s
                        AND a.type_absence <> 'Télétravail'
                    """
                    params = [selected_year, i] 

                    if selected_employee != "Tous":
                        query_abs += " AND u.name = %s"
                        params.append(selected_employee)

                    if selected_role != "Tous":
                        query_abs += " AND r.role = %s"
                        params.append(selected_role)

                    cursor.execute(query_abs, tuple(params))
                    total_abs = cursor.fetchone()[0]


                    query_emp = "SELECT COUNT(*) FROM users u"
                    params_emp = []

                    if selected_employee != "Tous":
                        query_emp += " WHERE u.name = %s"
                        params_emp.append(selected_employee)

                    cursor.execute(query_emp, tuple(params_emp))
                    nb_employes = cursor.fetchone()[0]

                    total_jours_ouvres = jours_ouvres * nb_employes
                    taux_abs = (total_abs / total_jours_ouvres * 100) if total_jours_ouvres > 0 else 0
                    taux_pres = 100 - taux_abs

                    df_taux.append({
                        "Mois": mois_name,
                        "Absentéisme": taux_abs,
                        "Présence": taux_pres
                    })

                df_taux = pd.DataFrame(df_taux)

                fig_taux = px.bar(
                    df_taux,
                    x="Mois",
                    y=["Présence", "Absentéisme"],
                    text_auto='.1f', 
                    labels={"value": "Taux (%)"},
                    color_discrete_map={"Présence": "#009933", "Absentéisme": "#ef553b"}
                )
                fig_taux.update_traces(textposition="inside")
                fig_taux.update_layout(
                    barmode='stack',
                    yaxis=dict(range=[0, 100], title="Taux (%)"),
                    xaxis_title="Mois"
                )
                st.plotly_chart(fig_taux, use_container_width=True)

            with col2:
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
                    Employés avec 0 absences ({selected_month_name} {selected_year})</h4>
                """, unsafe_allow_html=True)
                
                query_zero_abs = """
                    SELECT u.name, COALESCE(r.role, 'N/A') as role
                    FROM users u
                    LEFT JOIN roles r ON u.id = r.user_id
                    LEFT JOIN (
                        SELECT a.user_id
                        FROM absences a
                        WHERE a.statut = 'Approuvée'
                        AND EXTRACT(YEAR FROM a.date_debut) = %s
                        AND EXTRACT(MONTH FROM a.date_debut) = %s
                        AND a.type_absence <> 'Télétravail'
                        GROUP BY a.user_id
                    ) abs ON u.id = abs.user_id
                    WHERE abs.user_id IS NULL
                """
                params_zero = [selected_year, month_number] 

                if selected_employee != "Tous":
                    query_zero_abs += " AND u.name = %s"
                    params_zero.append(selected_employee)

                if selected_role != "Tous":
                    query_zero_abs += " AND r.role = %s"
                    params_zero.append(selected_role)

                cursor.execute(query_zero_abs, tuple(params_zero))
                zero_rows = cursor.fetchall()

                df_zero = pd.DataFrame(zero_rows, columns=["Employé", "Rôle"])

                if df_zero.empty:
                    st.info("Aucun employé avec 0 absence ce mois-ci.")
                else:
                    rows_per_page = 6
                    total_rows = len(df_zero)
                    total_pages = (total_rows + rows_per_page - 1) // rows_per_page 

                    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="page_1")

                    start_idx = (page - 1) * rows_per_page
                    end_idx = start_idx + rows_per_page
                    df_page = df_zero.iloc[start_idx:end_idx]

                    html_table_zero = '<table style="border-collapse: collapse; width: 100%;">'
                    html_table_zero += '<tr style="background-color:#000060; color:white; text-align:center;">'
                    for col in df_page.columns:
                        html_table_zero += f'<th style="padding:8px;">{col}</th>'
                    html_table_zero += '</tr>'

                    for row_num, (idx, row) in enumerate(df_page.iterrows()):
                        bg_color = "#f9f9f9" if row_num % 2 == 0 else "#ffffff"
                        html_table_zero += f'<tr style="background-color:{bg_color}; text-align:center;">'
                        html_table_zero += f'<td style="padding:8px; font-weight:bold;">{row["Employé"]}</td>'
                        html_table_zero += f'<td style="padding:4px; border-radius:4px;">{row["Rôle"]}</td>'
                        html_table_zero += '</tr>'

                    html_table_zero += '</table>'

                    st.markdown(html_table_zero, unsafe_allow_html=True)
                    st.caption(f"Page {page} / {total_pages}")

    #--------------------- Dashboard : projets -----------------------
    with tab3:
        df_projets = pd.read_sql_query("SELECT id, nom, heures_prevues FROM projets ORDER BY nom", conn)

        projet_options = df_projets["nom"].tolist()
        projet_options.insert(0, "Tous") 
        selected_projet = st.selectbox("📁 Projet", projet_options)

        if selected_projet != "Tous":
            projet_id = df_projets[df_projets["nom"] == selected_projet]["id"].iloc[0]

        if selected_employee != "Tous":
            employee_id = [uid for uid, name in employees if name == selected_employee][0]

        selected_month_index = mois_fr.index(selected_month_name)
        selected_month_num = selected_month_index + 1

        params_cumule = [int(selected_year), int(selected_month_num)]

        query_hours_cumule = """
        SELECT COALESCE(SUM(h.heures),0) AS total_saisie
        FROM projets p
        JOIN attribution_projet a
            ON a.projet_id = p.id
            AND (a.date_fin IS NULL OR a.date_fin >= CURRENT_DATE)
        LEFT JOIN heures_saisie h
            ON h.projet_id = p.id
            AND h.user_id = a.user_id
            AND EXTRACT(YEAR FROM h.date_jour) = %s
            AND EXTRACT(MONTH FROM h.date_jour) <= %s
        WHERE 1=1
        """
        params_cumule = [int(selected_year), int(selected_month_num)]

        if selected_projet != "Tous":
            query_hours_cumule += " AND p.id = %s"
            params_cumule.append(int(projet_id))

        if selected_employee != "Tous":
            query_hours_cumule += " AND a.user_id = %s"
            params_cumule.append(int(employee_id))

        if selected_role != "Tous":
            query_hours_cumule += " AND EXISTS (SELECT 1 FROM roles r WHERE r.user_id = a.user_id AND r.role = %s)"
            params_cumule.append(selected_role)


        df_hours_cumule = pd.read_sql_query(query_hours_cumule, conn, params=params_cumule)
        total_saisie_cumule = df_hours_cumule["total_saisie"].iloc[0] if not df_hours_cumule.empty else 0

        # Heures prévues pour le KPI
        if selected_projet != "Tous":
            heures_prevues_total = df_projets[df_projets["id"] == projet_id]["heures_prevues"].iloc[0]
        else:
            heures_prevues_total = df_projets["heures_prevues"].sum()

        pct_avancement = round(total_saisie_cumule / heures_prevues_total * 100, 1) if heures_prevues_total else 0
        ecart_pct = round((total_saisie_cumule - heures_prevues_total) / heures_prevues_total * 100, 1) if heures_prevues_total else 0

        query_hours_month = """
            SELECT SUM(h.heures) AS total_saisie
            FROM heures_saisie h
            JOIN roles r ON h.user_id = r.user_id
            JOIN attribution_projet a ON a.projet_id = h.projet_id AND a.user_id = h.user_id
            WHERE EXTRACT(YEAR FROM h.date_jour) = %s
            AND EXTRACT(MONTH FROM h.date_jour) = %s
        """
        params_month = [selected_year, selected_month_num]

        if selected_employee != "Tous":
            query_hours_month += " AND h.user_id = %s"
            params_month.append(employee_id)
        if selected_role != "Tous":
            query_hours_month += " AND r.role = %s"
            params_month.append(selected_role)

        df_hours_month = pd.read_sql_query(query_hours_month, conn, params=params_month)
        total_saisie_month = df_hours_month["total_saisie"].iloc[0] if not df_hours_month.empty else 0
        total_saisie_month = 0 if total_saisie_month is None else total_saisie_month
        pct_occupation = round(total_saisie_month / 160 * 100, 1)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{pct_avancement}%</div>
                    <div class="kpi-subvalue">{total_saisie_cumule}h / {heures_prevues_total}h prévues</div>
                    <div class="kpi-label">📈 Avancement cumulé</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{ecart_pct}%</div>
                    <div class="kpi-subvalue">{total_saisie_cumule - heures_prevues_total} h</div>
                    <div class="kpi-label">📉 Écart cumulé</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{pct_occupation}%</div>
                    <div class="kpi-subvalue">{total_saisie_month} h / 160 h</div>
                    <div class="kpi-label">🔋 % Occupation mois</div>
                </div>
            """, unsafe_allow_html=True)

        params_projets = [selected_year, selected_month_num]

        employee_filter_sql = f"AND a.user_id = {employee_id}" if selected_employee != "Tous" else ""
        projet_filter_sql = f"AND p.id = {projet_id}" if selected_projet != "Tous" else ""
        role_filter_sql = f"AND EXISTS (SELECT 1 FROM roles r WHERE r.user_id = a.user_id AND r.role = '{selected_role}')" if selected_role != "Tous" else ""

        query_projets = f"""
            SELECT p.id, p.nom, p.heures_prevues,
                COALESCE(SUM(h.heures),0) AS heures_reelles
            FROM projets p
            JOIN attribution_projet a 
                ON a.projet_id = p.id
                AND (a.date_fin IS NULL OR a.date_fin >= CURRENT_DATE)
                {employee_filter_sql}
                {role_filter_sql}
            LEFT JOIN heures_saisie h
                ON h.projet_id = p.id
                AND h.user_id = a.user_id
                AND EXTRACT(YEAR FROM h.date_jour) = %s
                AND EXTRACT(MONTH FROM h.date_jour) <= %s
            WHERE 1=1
            {projet_filter_sql}
            GROUP BY p.id, p.nom, p.heures_prevues
            ORDER BY p.nom
        """

        df_analyse = pd.read_sql_query(query_projets, conn, params=params_projets)
        df_analyse["taux_conso"] = df_analyse.apply(
            lambda row: round(row["heures_reelles"] / row["heures_prevues"] * 100, 1) if row["heures_prevues"] else 0,
            axis=1
        )

        def definir_statut(taux):
            if taux == 0:
                return "⚪ À démarrer"
            elif taux < 50:
                return "🟡 en retard"
            elif taux <= 100:
                return "🟢 maîtrisé"
            else:
                return "🔴 dépassement"

        df_analyse["statut"] = df_analyse["taux_conso"].apply(definir_statut)

        def style_cell_projet(val, col_type, show_days=False):
            if val is None or val == "":
                return f'<td style="padding:8px; text-align:center;">-</td>'
            try:
                if show_days:
                    heures = float(val)
                    cell_text = f"{int(heures)} h ({heures/8:.2f} j)"
                    style = "padding:8px; text-align:center;"
                elif col_type == "taux_conso":
                    taux = float(val)
                    if taux <= 1:
                        taux *= 100
                    cell_text = f"{taux:.0f} %"
                    style = "padding:8px; text-align:center;"
                elif col_type == "statut":
                    statut = str(val)
                    cell_text = statut
                    if "⚪" in statut:
                        bg_color = "#d9d9d9"
                        txt_color = "black"
                    elif "🟡" in statut:
                        bg_color = "#ffc91a"
                        txt_color = "black"
                    elif "🟢" in statut:
                        bg_color = "#4bb464"
                        txt_color = "black"
                    elif "🔴" in statut:
                        bg_color = "#d92635"
                        txt_color = "white"
                    else:
                        bg_color = "white"
                        txt_color = "black"
                    style = f"padding:8px; text-align:center; font-weight:bold; background-color:{bg_color}; color:{txt_color};"
                else:
                    cell_text = str(val)
                    style = "padding:8px; text-align:center;"
            except (ValueError, TypeError):
                cell_text = str(val)
                style = "padding:8px; text-align:center;"
            return f'<td style="{style}">{cell_text}</td>'

        html_table = '''
        <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px;">
        '''
        html_table += '<tr style="position: sticky; top: 0; background-color:#000060; color:white; text-align:center;">'
        for col in ["Projet", "Heures prévues", "Heures saisies", "Taux consommation", "Statut"]:
            html_table += f'<th style="padding:8px; text-align:center;">{col}</th>'
        html_table += '</tr>'

        for row_num, row in df_analyse.iterrows():
            bg_color = "#f9f9f9" if row_num % 2 == 0 else "#ffffff"
            html_table += f'<tr style="background-color:{bg_color};">'
            html_table += f'<td style="padding:8px; font-weight:bold;">{row["nom"]}</td>'
            html_table += style_cell_projet(row["heures_prevues"], "heures_prevues", show_days=True)
            html_table += style_cell_projet(row["heures_reelles"], "heures_reelles", show_days=True)
            html_table += style_cell_projet(row["taux_conso"], "taux_conso")
            html_table += style_cell_projet(row["statut"], "statut")
            html_table += '</tr>'
        html_table += '</table>'

        st.markdown(f"<h4 style='background-color:#d6dcf5;padding:10px 15px;border-radius:8px;color:#000060;font-weight:600;border-left:6px solid #9aa7e5;margin-bottom:20px;'>Suivi des projets</h4>", unsafe_allow_html=True)
        st.markdown(html_table, unsafe_allow_html=True)
        st.markdown(f"<h4 style='background-color:#d6dcf5;padding:10px 15px;border-radius:8px;color:#000060;font-weight:600;border-left:6px solid #9aa7e5;margin-bottom:20px;'>Vision globale des contributions par projet</h4>", unsafe_allow_html=True)
        params = [int(selected_year)]
        project_filter_sql = f"AND h.projet_id = {projet_id}" if selected_projet != "Tous" else ""
        role_filter_sql = f"AND EXISTS (SELECT 1 FROM roles r WHERE r.user_id = h.user_id AND r.role = '{selected_role}')" if selected_role != "Tous" else ""

        query_evolution = f"""
            SELECT h.user_id, u.name AS employe,
                EXTRACT(MONTH FROM h.date_jour) AS mois,
                SUM(h.heures) AS total_heures
            FROM heures_saisie h
            JOIN users u ON h.user_id = u.id
            JOIN attribution_projet a 
                ON a.projet_id = h.projet_id
                AND a.user_id = h.user_id
                AND (a.date_fin IS NULL OR a.date_fin >= CURRENT_DATE)
            WHERE EXTRACT(YEAR FROM h.date_jour) = %s
            {project_filter_sql}
            {role_filter_sql}
        """

        if selected_employee != "Tous":
            query_evolution += f" AND h.user_id = {employee_id}"

        query_evolution += " GROUP BY h.user_id, mois, u.name ORDER BY h.user_id, mois"
        df_evolution = pd.read_sql_query(query_evolution, conn, params=params)

        if not df_evolution.empty:
            df_evolution["mois"] = df_evolution["mois"].astype(int)
            df_pivot = df_evolution.pivot(index="mois", columns="employe", values="total_heures").fillna(0)

            for m in range(1, 13):
                if m not in df_pivot.index:
                    df_pivot.loc[m] = [0] * df_pivot.shape[1]
            df_pivot = df_pivot.sort_index()

            if selected_projet != "Tous":
                df_pivot = df_pivot.loc[:, (df_pivot.sum(axis=0) > 0)]

            projet_affiche = selected_projet if selected_projet != "Tous" else "Tous les projets"

            fig_evolution = px.line(
                df_pivot,
                x=df_pivot.index,
                y=df_pivot.columns,
                labels={"value": "Heures", "mois": "Mois"},
                title=f"Projet : {projet_affiche}"
            )
            fig_evolution.update_xaxes(
                tickmode="array",
                tickvals=list(range(1, 13)),
                ticktext=["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
            )
            fig_evolution.update_yaxes(title="Heures saisies")
            fig_evolution.update_layout(
                title=dict(
                    text=f"Projet : {projet_affiche}",
                    x=0.05,
                    xanchor='left',
                    font=dict(size=16, color="#000060", family="Arial, sans-serif")
                ),
                legend_title="Employé"
            )

            st.plotly_chart(fig_evolution, use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour le filtre sélectionné.")

    with tab4:
        def load_lottieurl(url: str):
            r = requests.get(url)
            if r.status_code != 200:
                return None
            return r.json()

        st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Prévisions</h2>", unsafe_allow_html=True)

        lottie_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")
        st_lottie(lottie_animation, height=300, key="construction")

        st.success("🚧 Cette fonctionnalité sera bientôt disponible...!")