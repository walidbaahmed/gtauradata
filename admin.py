import streamlit as st
import pandas as pd
from db import get_connection, hash_password
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#Fonction générer mot de passe temporaire
def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(random.choices(characters, k=length))


#Fonction envoi du mdp temporaire par mail
def send_email_gmail(to_email, temp_password):

    sender_email = st.secrets["email"]["gmail_user"]
    sender_password = st.secrets["email"]["gmail_app_password"] 

    subject = "Activation de votre compte - Mot de passe temporaire"
    body = f"""
    Bonjour,

    Votre compte a été activé. Voici votre mot de passe temporaire :

    🔐 Mot de passe : {temp_password}

    Veuillez vous connecter en utilisant ce mot de passe.

    Merci,
    L'équipe Admin
    """
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"Email envoyé à {to_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi du mail à {to_email} : {e}")

#--------------------------------------------------------------------------------------------

def show_admin():

    # Droits d'accès
    if "role" not in st.session_state or st.session_state["role"] != "admin":
        st.error("Accès réservé à l'administrateur.")
        st.stop()
        
    st.markdown("""
        <style>
        .stApp {
            background-color: #f2f2f2;     
        }

        .block-container {
            padding-top: 2.5rem !important;
            margin-top: 0 !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 20px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
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
            border: 1px solid #000060;
        }

        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0, 0, 96, 0.2);
        }

        #title {
            position: fixed;
            top: 0;
            left: 200px;
            background-color: #ffffff;
            z-index: 999;
            width:100%;
            padding: 10px 20px;
            margin-bottom: 0px;
            border-bottom: 2px solid #000060;
        }

        #title h4 {
            font-size: 29px;
            font-weight: 600;
            color: #000060;
            margin-left: 730px;
            font-family: 'New Icon';
            padding-bottom: 6px;
        }

        table {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            color: #222;
            border-collapse: collapse;
        }
                
        th {
            background-color: #080686;
            color: white;
            font-weight: 700;
            padding: 10px 12px;
            text-align: left !important;
            user-select: none;
        }
                
        td {
            background-color: white;
            padding: 10px 12px;
            text-align: left;
            vertical-align: middle;
        }
        </style>
        """, unsafe_allow_html=True)

    # Vérification connexion
    if "username" not in st.session_state:
        st.error("Vous devez être connecté pour accéder à cette page.")
        st.stop()

    st.markdown("""
        <div id="title">
            <h4> Administration </h4>  
        </div>
    """, unsafe_allow_html=True)


    tab1, tab2, tab3, tab4 = st.tabs(["Utilisateurs", "Projets", "Attribution des projets", "Définition CP & RTT"])

    #------------------------------------- Gestion des utilisateurs -------------------------------
    with tab1:

        def load_users():
            conn = get_connection()
            df = pd.read_sql_query("""
                SELECT users.id, users.email, users.name, roles.role, users.is_active, users.activated_once
                FROM users
                LEFT JOIN roles ON users.id = roles.user_id
                ORDER BY users.id
            """, conn)
            conn.close()
            return df

        df_users = load_users()

        col_list_users, _, col_form = st.columns([4, 0.2, 3])
        
        with col_list_users:
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
                    📋 Utilisateurs existants
                </h4>
            """, unsafe_allow_html=True)


            filter_text = st.text_input("🔍 Rechercher un utilisateur")

            if filter_text:
                df_filtered = df_users[
                    df_users["name"].str.contains(filter_text, case=False, na=False) |
                    df_users["email"].str.contains(filter_text, case=False, na=False)
                ]
            else:
                df_filtered = df_users.copy()

            USERS_PER_PAGE = 6
            df_filtered["Première activation"] = df_filtered["activated_once"].apply(lambda x: "Oui" if x else "Non")
            df_filtered["Statut"] = df_filtered["is_active"].apply(lambda x: "🟢 Actif" if x else "🔴 Désactivé")

            total_users = len(df_filtered)
            total_pages = (total_users - 1) // USERS_PER_PAGE + 1

            if "page_number" not in st.session_state:
                st.session_state.page_number = 1

            def go_prev():
                if st.session_state.page_number > 1:
                    st.session_state.page_number -= 1

            def go_next():
                if st.session_state.page_number < total_pages:
                    st.session_state.page_number += 1

            start_idx = (st.session_state.page_number - 1) * USERS_PER_PAGE
            end_idx = start_idx + USERS_PER_PAGE
            paginated_df = df_filtered.iloc[start_idx:end_idx]

            users_list_container = st.empty()
            users_list_container.markdown(
                f"""
                <div style="overflow-x:auto; width:100%;">
                    {paginated_df.drop(columns=['id', 'is_active', 'activated_once']).to_html(index=False, escape=False)}
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2, col3 = st.columns([8, 1, 1])
            with col1:
                st.write("")
            with col2:
                st.button("⬅️", on_click=go_prev, disabled=(st.session_state.page_number == 1))
            with col3:
                st.button("➡️", on_click=go_next, disabled=(st.session_state.page_number == total_pages))

            st.markdown(f"<p style='text-align:right; font-style: italic;'>Page {st.session_state.page_number} sur {total_pages}</p>", unsafe_allow_html=True)

            # Sélection utilisateur pour activer/désactiver
            all_users = load_users()
            user_options_for_status = {f"{row['name']}": row for _, row in all_users.iterrows()}

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
                    🔄 Activer / Désactiver un utilisateur
                </h4>
            """, unsafe_allow_html=True)

            if "selected_user_label" not in st.session_state:
                st.session_state.selected_user_label = list(user_options_for_status.keys())[0]

            selected_user_label = st.selectbox(
                "Choisissez un utilisateur",
                options=list(user_options_for_status.keys()),
                key="selected_user_label"
            )

            selected_user = user_options_for_status[selected_user_label]
            is_active_current = selected_user["is_active"]

            button_label = "Désactiver" if is_active_current else "Activer"

            col_button, _ = st.columns([3, 1])
            with col_button:
                if st.button(f"{button_label}"):
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        new_status = 0 if is_active_current else 1
                        cursor.execute(
                            "UPDATE users SET is_active = %s WHERE id = %s",
                            (new_status, selected_user["id"])
                        )
                        conn.commit()

                        if new_status == 1 and is_active_current == 0:
                            if selected_user.get("activated_once", 0) == 0:
                                temp_pass = generate_temp_password()
                                hashed = hash_password(temp_pass)

                                cursor.execute(
                                    "UPDATE users SET password_hashed = %s, activated_once = 1 WHERE id = %s",
                                    (hashed, selected_user["id"])
                                )
                                conn.commit()

                                send_email_gmail(selected_user["email"], temp_pass)
                            else:
                                pass

                    except Exception as e:
                        st.error(f"Erreur lors de la mise à jour : {e}")
                    finally:
                        conn.close()

                    df_users = load_users()
                    df_users["Statut"] = df_users["is_active"].apply(lambda x: "🟢 Actif" if x else "🔴 Désactivé")
                    users_list_container.markdown(
                        df_users.drop(columns=["id", "is_active"]).to_html(index=False, escape=False),
                        unsafe_allow_html=True
                    )
                    st.rerun()

        with col_form:

            if "uploader_key" not in st.session_state:
                st.session_state.uploader_key = 0

            uploaded_file = st.file_uploader(
                "📥 Importer un fichier Excel",
                type=["xlsx"],
                key=f"uploader_{st.session_state.uploader_key}"
            )

            if uploaded_file is not None:
                try:
                    df_import = pd.read_excel(uploaded_file)

                    expected_cols = {"name", "email", "role"}
                    if not expected_cols.issubset(df_import.columns.str.lower()):
                        st.error("Le fichier doit contenir les colonnes : name, email, role")
                    else:
                        df_import.columns = [col.lower() for col in df_import.columns]

                        conn = get_connection()
                        cursor = conn.cursor()
                        existing_emails = set(row[0] for row in cursor.execute("SELECT email FROM users").fetchall())

                        for _, row in df_import.iterrows():
                            name = row["name"]
                            email = row["email"]
                            role = row["role"].lower()

                            if role not in ["admin", "consultant", "rh"]:
                                st.warning(f"❗ Rôle invalide pour {name} : {role}. Utilisateur ignoré.")
                                continue

                            if email in existing_emails:
                                st.warning(f"⚠️ L'email {email} existe déjà. Utilisateur ignoré.")
                                continue

                            fake_hashed = hash_password("temp")

                            cursor.execute("""
                                INSERT INTO users (name, email, password_hashed, is_active, activated_once)
                                VALUES (?, ?, ?, 0, 0)
                            """, (name, email, fake_hashed))
                            user_id = cursor.lastrowid

                            cursor.execute("""
                                INSERT INTO roles (user_id, role)
                                VALUES (?, ?)
                            """, (user_id, role))

                            existing_emails.add(email)

                        conn.commit()
                        conn.close()

                        st.toast("✅ Utilisateurs importés avec succès.")

                        st.session_state.uploader_key += 1
                        st.rerun()

                except Exception as e:
                    st.error(f"Erreur lors de l'importation : {e}")


            user_options = {f"{row['name']}": row['id'] for _, row in df_users.iterrows()}
            user_options = {"➕ Créer un nouvel utilisateur": None, **user_options}

            st.markdown("##### 👤 Sélectionnez un utilisateur à modifier ou ajoutez-en un nouveau")
            selected_user_label = st.selectbox(
                label="Sélection utilisateur",
                options=list(user_options.keys()),
                label_visibility="collapsed"
            )
            selected_user_id = user_options[selected_user_label]

            if selected_user_id is not None:
                user_data = df_users[df_users["id"] == selected_user_id].iloc[0]
                form_title = "✏️ Modifier l'utilisateur"
                default_name = user_data["name"]
                default_email = user_data["email"]
                default_role = user_data["role"]
                default_is_active = user_data["is_active"]
            else:
                form_title = "➕ Ajouter un nouvel utilisateur"
                default_name = ""
                default_email = ""
                default_role = "consultant"
                default_is_active = 0

            with st.form("user_form"):
                st.markdown(f"### {form_title}")
                name = st.text_input("👤 Nom", value=default_name)
                email = st.text_input("📧 Email", value=default_email)
                role = st.selectbox("🎓 Rôle", options=["consultant", "rh", "admin"], index=["consultant", "rh", "admin"].index(default_role))
                is_active = st.checkbox("Actif", value=bool(default_is_active))

                submit_btn = st.form_submit_button("Enregistrer")

                if submit_btn:
                    if not email or not name:
                        st.warning("❗ Les champs nom et email sont obligatoires.")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()

                            if selected_user_id is None:
                                # Création
                                cursor.execute("""
                                    INSERT INTO users (email, name, password_hashed, is_active)
                                    VALUES (%s, %s, %s, %s)
                                    RETURNING id
                                """, (email, name, hash_password(generate_temp_password()), 0))

                                user_id = cursor.fetchone()[0]

                                cursor.execute("""
                                    INSERT INTO roles (user_id, role)
                                    VALUES (%s, %s)
                                """, (user_id, role))

                                conn.commit()
                                st.toast("✅ Utilisateur ajouté avec succès !")
                            else:
                                # Modification
                                cursor.execute("""
                                    UPDATE users SET name = %s, email = %s, is_active = %s WHERE id = %s
                                """, (name, email, int(is_active), selected_user_id))

                                cursor.execute("""
                                    UPDATE roles SET role = %s WHERE user_id = %s
                                """, (role, selected_user_id))

                                conn.commit()

                                st.toast("✏️ Utilisateur modifié avec succès !")
                        except Exception as e:
                            st.error(f"Erreur : {e}")
                        finally:
                            conn.close()

                        df_users = load_users()
                        df_users["Statut"] = df_users["is_active"].apply(lambda x: "🟢 Actif" if x else "🔴 Désactivé")
                        users_list_container.markdown(
                            df_users.drop(columns=["id", "is_active"]).to_html(index=False, escape=False),
                            unsafe_allow_html=True
                        )

    #---------------------------------- Gestion de projets ---------------------------------------

    with tab2:
        col1, _, col2 = st.columns([3, 0.2, 3])

        # ------------------------ FORMULAIRE PROJETS ------------------------
        with col1:
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
                    🔗 Projets
                </h4>
            """, unsafe_allow_html=True)

            conn = get_connection()
            df_projets = pd.read_sql_query("SELECT * FROM projets ORDER BY id", conn)
            conn.close()

            projet_options = {f"{row['nom']}": row for _, row in df_projets.iterrows()}
            projet_options = {"➕ Nouveau projet": None, **projet_options}

            selected_projet_label = st.selectbox("Sélectionnez un projet", list(projet_options.keys()))
            selected_projet = projet_options[selected_projet_label]

            if selected_projet is not None:
                default_nom = selected_projet["nom"]
                default_outil = selected_projet["outil"]
                default_jours = int(selected_projet["heures_prevues"] / 8) if pd.notna(selected_projet["heures_prevues"]) else 0
            else:
                default_nom = ""
                default_outil = ""
                default_jours = 0

            if selected_projet is None:
                st.markdown("### ➕ Création d'un nouveau projet")
            else:
                st.markdown(f"### ✏️ Modification du projet : **{selected_projet['nom']}**")

            with st.form("form_projet"):
                nom_projet = st.text_input("Nom du projet", value=default_nom)
                outil_projet = st.text_input("Outil associé", value=default_outil)
                
                jours_prevus = st.number_input(
                    "Jours prévus",
                    min_value=0,
                    step=1,
                    value=default_jours
                )

                heures_prevues = jours_prevus * 8

                submit_label = "Ajouter le projet" if selected_projet is None else "Modifier"

                if selected_projet is not None:
                    col_btn1, col_btn2 = st.columns([1, 5])
                    with col_btn1:
                        delete_proj = st.form_submit_button("Supprimer")
                    with col_btn2:
                        submit_projet = st.form_submit_button(submit_label)
                else:
                    submit_projet = st.form_submit_button("Ajouter")
                    delete_proj = False

                if submit_projet:
                    if not nom_projet or not outil_projet:
                        st.warning("Tous les champs sont requis.")
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            if selected_projet is None:
                                # Ajout
                                cursor.execute("""
                                    INSERT INTO projets (nom, outil, heures_prevues)
                                    VALUES (%s, %s, %s)
                                """, (nom_projet, outil_projet, heures_prevues))
                                st.success("Projet ajouté avec succès.")
                            else:
                                # Modification
                                cursor.execute("""
                                    UPDATE projets
                                    SET nom = %s, outil = %s, heures_prevues = %s
                                    WHERE id = %s
                                """, (nom_projet, outil_projet, heures_prevues, selected_projet["id"]))
                                st.success("Projet modifié avec succès.")
                            conn.commit()
                        except Exception as e:
                            st.error(f"Erreur : {e}")
                        finally:
                            conn.close()
                    st.rerun() 

                if "confirm_delete" not in st.session_state:
                    st.session_state.confirm_delete = False

                if delete_proj:
                    if not st.session_state.confirm_delete:
                        st.warning("⚠️ Cette action supprimera le projet **et toutes ses attributions associées**. Cliquez à nouveau sur 'Supprimer' pour confirmer.")
                        st.session_state.confirm_delete = True
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM projets WHERE id = %s", (selected_projet["id"],))
                            cursor.execute("DELETE FROM attribution_projet WHERE projet_id = %s", (selected_projet["id"],))
                            conn.commit()
                            st.success("Projet supprimé avec succès.")
                        except Exception as e:
                            st.error(f"Erreur lors de la suppression : {e}")
                        finally:
                            conn.close()
                        st.session_state.confirm_delete = False
                        st.rerun()

        # ------------------------ LISTE DES PROJETS ------------------------
        with col2:
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
                    📁 Liste des projets existants
                </h4>
            """, unsafe_allow_html=True)

            conn = get_connection()
            df_projets = pd.read_sql_query("""
                SELECT nom AS projet, outil, 
                    COALESCE(heures_prevues, 0) AS heures_prevues
                FROM projets
                ORDER BY id
            """, conn)
            conn.close()

            search_proj = st.text_input("🔍 Rechercher un projet")
            if search_proj:
                df_projets = df_projets[
                    df_projets["projet"].str.contains(search_proj, case=False, na=False) |
                    df_projets["outil"].str.contains(search_proj, case=False, na=False)
                ]

            df_projets["Jours prévus"] = (df_projets["heures_prevues"] / 8).astype(int)
            df_projets["Heures prévues"] = df_projets["heures_prevues"].astype(int)

            df_projets_affichage = df_projets[["projet", "outil", "Jours prévus", "Heures prévues"]]

            PROJETS_PER_PAGE = 10
            total_projets = len(df_projets_affichage)
            total_pages_projets = (total_projets - 1) // PROJETS_PER_PAGE + 1

            if "page_projets" not in st.session_state:
                st.session_state.page_projets = 1

            def go_prev_projets():
                if st.session_state.page_projets > 1:
                    st.session_state.page_projets -= 1

            def go_next_projets():
                if st.session_state.page_projets < total_pages_projets:
                    st.session_state.page_projets += 1

            start_proj = (st.session_state.page_projets - 1) * PROJETS_PER_PAGE
            end_proj = start_proj + PROJETS_PER_PAGE
            df_paginated_projets = df_projets_affichage.iloc[start_proj:end_proj]

            st.markdown(
                df_paginated_projets.to_html(index=False, escape=False),
                unsafe_allow_html=True
            )

            colp1, colp2, colp3 = st.columns([8, 1, 1])
            with colp1:
                st.write("")
            with colp2:
                st.button("⬅️", on_click=go_prev_projets, disabled=(st.session_state.page_projets == 1), key="prev_proj_btn")
            with colp3:
                st.button("➡️", on_click=go_next_projets, disabled=(st.session_state.page_projets == total_pages_projets), key="next_proj_btn")

            st.markdown(f"<p style='text-align:right; font-style: italic;'>Page {st.session_state.page_projets} sur {total_pages_projets}</p>", unsafe_allow_html=True)

    #-------------------------------------------------- Attribution projet --------------------------------------------------

    with tab3:
        col3, _, col4 = st.columns([3, 0.2, 3])

        # -------------------------------------------------- Tableau des attributions --------------------------------------------------
        with col4:
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
                    👥 Projets attribués aux utilisateurs
                </h4>
            """, unsafe_allow_html=True)

            conn = get_connection()
            df_attributions = pd.read_sql_query("""
                SELECT users.name AS utilisateur,
                    projets.nom AS projet,
                    attribution_projet.date_debut,
                    attribution_projet.date_fin
                FROM attribution_projet
                JOIN users ON attribution_projet.user_id = users.id
                JOIN projets ON attribution_projet.projet_id = projets.id
                ORDER BY utilisateur
            """, conn)
            conn.close()

            df_attributions['date_debut'] = pd.to_datetime(df_attributions['date_debut']).dt.date
            df_attributions['date_fin'] = pd.to_datetime(df_attributions['date_fin']).dt.date

            df_attrib_display = df_attributions.copy()

            search_attrib = st.text_input("🔍 Rechercher une attribution")
            if search_attrib:
                df_attrib_display = df_attrib_display[
                    df_attrib_display["utilisateur"].str.contains(search_attrib, case=False, na=False) |
                    df_attrib_display["projet"].str.contains(search_attrib, case=False, na=False)
                ]

            # Pagination
            ATTRIBS_PER_PAGE = 10
            total_attribs = len(df_attrib_display)
            total_pages_attribs = (total_attribs - 1) // ATTRIBS_PER_PAGE + 1

            if "page_attribs" not in st.session_state:
                st.session_state.page_attribs = 1

            def go_prev_attribs():
                if st.session_state.page_attribs > 1:
                    st.session_state.page_attribs -= 1

            def go_next_attribs():
                if st.session_state.page_attribs < total_pages_attribs:
                    st.session_state.page_attribs += 1

            start_attrib = (st.session_state.page_attribs - 1) * ATTRIBS_PER_PAGE
            end_attrib = start_attrib + ATTRIBS_PER_PAGE
            df_paginated_attrib = df_attrib_display.iloc[start_attrib:end_attrib]

            st.markdown(
                df_paginated_attrib.to_html(index=False, escape=False),
                unsafe_allow_html=True
            )

            cola1, cola2, cola3 = st.columns([8, 1, 1])
            with cola1:
                st.write("")
            with cola2:
                st.button("⬅️", on_click=go_prev_attribs, disabled=(st.session_state.page_attribs == 1), key="prev_attrib_btn")
            with cola3:
                st.button("➡️", on_click=go_next_attribs, disabled=(st.session_state.page_attribs == total_pages_attribs), key="next_attrib_btn")

            st.markdown(f"<p style='text-align:right; font-style: italic;'>Page {st.session_state.page_attribs} sur {total_pages_attribs}</p>", unsafe_allow_html=True)

        # -------------------------------------------------- Formulaire attribution --------------------------------------------------
        with col3:
            import datetime
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
                    🔗 Attributions de projet
                </h4>
            """, unsafe_allow_html=True)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM users")
            utilisateurs = cursor.fetchall()

            cursor.execute("SELECT id, nom FROM projets")
            projets = cursor.fetchall()

            cursor.execute("""
                SELECT id, user_id, projet_id, date_debut, date_fin
                FROM attribution_projet
            """)
            attributions = cursor.fetchall()
            conn.close()

            user_dict = {id: name for id, name in utilisateurs}
            projet_dict = {id: nom for id, nom in projets}

            attrib_options = {
                f"{user_dict[user_id]} - {projet_dict[projet_id]}": attrib_id
                for attrib_id, user_id, projet_id, _, _ in attributions
            }
            attrib_options = {"➕ Nouvelle attribution": None, **attrib_options}

            selected_attrib_label = st.selectbox("Sélectionnez une attribution", list(attrib_options.keys()))
            selected_attrib_id = attrib_options[selected_attrib_label]

            if selected_attrib_id is not None:
                selected_row = next((row for row in attributions if row[0] == selected_attrib_id), None)
                default_user_id = selected_row[1]
                default_projet_id = selected_row[2]
                default_date_debut = selected_row[3].date() if isinstance(selected_row[3], datetime.datetime) else selected_row[3]
                default_date_debut = default_date_debut or datetime.date.today()
                default_date_fin = selected_row[4].date() if isinstance(selected_row[4], datetime.datetime) else selected_row[4]
            else:
                default_user_id = None
                default_projet_id = None
                default_date_debut = datetime.date.today()
                default_date_fin = None

            if selected_attrib_id is None:
                st.markdown("### ➕ Attribuer un projet")
            else:
                st.markdown("### ✏️ Modification ")

            with st.form("form_attribution"):
                user_keys = list(user_dict.keys())
                if default_user_id not in user_keys:
                    default_user_id = user_keys[0] if user_keys else None

                selected_user_id = st.selectbox(
                    "Utilisateur",
                    user_keys,
                    index=user_keys.index(default_user_id) if default_user_id in user_keys else 0,
                    format_func=lambda x: user_dict.get(x, "Utilisateur inconnu")
                )
                selected_user_name = user_dict.get(selected_user_id, "Utilisateur inconnu")

                projet_keys = list(projet_dict.keys())
                if default_projet_id not in projet_keys:
                    default_projet_id = projet_keys[0] if projet_keys else None

                selected_projet_id = st.selectbox(
                    "Projet",
                    projet_keys,
                    index=projet_keys.index(default_projet_id) if default_projet_id in projet_keys else 0,
                    format_func=lambda x: projet_dict.get(x, "Projet inconnu")
                )
                selected_projet_name = projet_dict.get(selected_projet_id, "Projet inconnu")

                date_debut = st.date_input("Date de début", value=default_date_debut)
                date_fin = st.date_input("Date de fin", value=default_date_fin)

                if selected_attrib_id is not None:
                    col_btn1, col_btn2 = st.columns([1, 5])
                    with col_btn1:
                        delete_attrib = st.form_submit_button("Supprimer")
                    with col_btn2:
                        submit_attrib = st.form_submit_button("Modifier")
                else:
                    submit_attrib = st.form_submit_button("Ajouter")
                    delete_attrib = False

                # ----- Ajout / Modification -----
                if submit_attrib:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()

                        if selected_attrib_id is None:
                            cursor.execute("""
                                INSERT INTO attribution_projet (user_id, projet_id, date_debut, date_fin)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (user_id, projet_id) DO NOTHING
                            """, (selected_user_id, selected_projet_id, date_debut, date_fin))
                            st.success("Attribution ajoutée avec succès.")
                        else:
                            cursor.execute("""
                                UPDATE attribution_projet
                                SET user_id = %s, projet_id = %s, date_debut = %s, date_fin = %s
                                WHERE id = %s
                            """, (selected_user_id, selected_projet_id, date_debut, date_fin, selected_attrib_id))
                            st.success("Attribution modifiée avec succès.")

                        conn.commit()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                    finally:
                        conn.close()
                    st.rerun()

                # ----- Suppression avec confirmation -----
                if "confirm_delete_attrib" not in st.session_state:
                    st.session_state.confirm_delete_attrib = False

                if delete_attrib:
                    if not st.session_state.confirm_delete_attrib:
                        st.warning(f"⚠️ Cette action supprimera l’attribution entre **{selected_user_name}** et **{selected_projet_name}**. Cliquez à nouveau sur 'Supprimer' pour confirmer.")
                        st.session_state.confirm_delete_attrib = True
                    else:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM attribution_projet WHERE id = %s", (selected_attrib_id,))
                            conn.commit()
                            st.success("Attribution supprimée avec succès.")
                        except Exception as e:
                            st.error(f"Erreur lors de la suppression : {e}")
                        finally:
                            conn.close()
                        st.session_state.confirm_delete_attrib = False
                        st.rerun()
    #--------------------------------- Définition CP & RTT ----------------------------------

    with tab4:

        col1, _, col2 = st.columns([3, 0.2, 3])

        conn = get_connection()
        cursor = conn.cursor()

        df_conges = pd.read_sql_query("SELECT annee, cp_total, rtt_total FROM parametres_conges ORDER BY annee DESC", conn)
        conn.close()

        with col1:
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
                    📅 Définition des congés annuels (CP & RTT)
                </h4>
            """, unsafe_allow_html=True)

            options = {f"{row['annee']}": row for _, row in df_conges.iterrows()}
            options = {"➕ Nouvelle année": None, **options}

            selected_label = st.selectbox("Sélectionnez une année", list(options.keys()))
            selected_row = options[selected_label]

            if selected_row is not None:
                default_annee = int(selected_row["annee"])
                default_cp = int(selected_row["cp_total"])
                default_rtt = int(selected_row["rtt_total"])
            else:
                from datetime import datetime
                default_annee = datetime.now().year
                default_cp = 25
                default_rtt = 10

            if selected_row is None:
                st.markdown("### ➕ Ajouter une nouvelle année")
                submit_label = "Ajouter"
            else:
                st.markdown(f"### ✏️ Modifier {default_annee}")
                submit_label = "Modifier"

            with st.form("form_conges"):
                annee = st.number_input("📆 Année", value=default_annee, step=1, format="%d")
                cp_total = st.number_input("🏖️ Nombre de jours de CP", min_value=0, max_value=60, value=default_cp, step=1)
                rtt_total = st.number_input("🕒 Nombre de jours de RTT", min_value=0, max_value=60, value=default_rtt, step=1)

                submit_btn = st.form_submit_button(submit_label)

                if submit_btn:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO parametres_conges (annee, cp_total, rtt_total)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (annee) DO UPDATE
                            SET cp_total = EXCLUDED.cp_total,
                                rtt_total = EXCLUDED.rtt_total
                        """, (annee, cp_total, rtt_total))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Paramètres enregistrés pour {annee} : {cp_total} CP / {rtt_total} RTT")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

        with col2:
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
                    Historique des paramètres enregistrés
                </h4>
            """, unsafe_allow_html=True)

            st.markdown(
                df_conges.to_html(index=False, escape=False),
                unsafe_allow_html=True
            )
