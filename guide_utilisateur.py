import streamlit as st

st.set_page_config(page_title="Guide utilisateur", layout="wide")

def show_guide_utilisateur():
    st.markdown(
        """
        <style>
        .bloc {
            background-color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
        }
        .step {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .number-circle {
            background-color: #006633;
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            margin-right: 10px;
        }

        .stApp {
            margin-top: 0;
            padding: 0;
            background-color: #f9f9f9;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }   

        .block-container {
            padding-top: 1.5rem !important;
            margin-top: 0 !important;
        }
                
        .main .block-container {
            margin-top: 0rem !important;
        }

        .guide-title {
            color: #006633;
            font-size: 30px;
            font-weight: bold;
            margin-bottom: 15px;
            text-align: center;
        }

        h4 {
            font-family: "New Icon", sans-serif;
            text-align: center;
            margin-bottom: 10px;
            font-style: italic;
            font-size: 22px;
            color: #2e8b57;
            position: relative;
        }
        h4::after {
            content: "";
            display: block;
            width: 40%;
            margin: 5px auto 0 auto;
            border-bottom: 2px solid #006633;
        }

        .bloc h5.subtitle {
            margin: 8px 0 12px 0;
            font-size: 21px;
            font-weight: 600;
            color: #333;
            font-family : "Times New Roman";
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="guide-title">Guide d’utilisation de l’application</div>', unsafe_allow_html=True)

    col1,_,col2 = st.columns([2,0.02,2])

    with col1:
        st.markdown(
            """
            <div class="bloc">
                <h4>👤 Utilisateur</h4>
                <h5 class="subtitle">I. Demande d’absence</h5>
                <div class="step"><div class="number-circle">1</div><div>Aller dans le menu latéral → sélectionner la page "Demande d'absence".</div></div>
                <div class="step"><div class="number-circle">2</div><div>Dans la page, aller à l’onglet "Demande d'absence".</div></div>
                <div class="step"><div class="number-circle">3</div><div>Remplir le formulaire de demande pour le mois où vous prévoyez une absence.</div></div>
                <div class="step"><div class="number-circle">4</div><div>Si la demande concerne un arrêt maladie, ajouter un justificatif.</div></div>
                <div class="step"><div class="number-circle">5</div><div>Cliquer sur "Soumettre la demande".</div></div>
                <div class="step"><div class="number-circle">6</div><div>Attendre la validation de la demande par l’administrateur/RH.</div></div>
                <h5 class="subtitle">II. Feuille de temps : Onglet Saisie feuille de temps</h5>
                <div class="step"><div class="number-circle">1</div><div>Aller dans la page "Feuille de temps" → onglet "Saisie feuille de temps".</div></div>
                <div class="step"><div class="number-circle">2</div><div>Choisir le mois et l’année (le mois en cours est sélectionné par défaut).</div></div>
                <div class="step"><div class="number-circle">3</div><div>Remplir les jours travaillés : 1 pour une journée complète et 0,5 pour une demi-journée.</div></div>
                <div class="step"><div class="number-circle">4</div><div>Cliquer sur "Enregistrer la feuille".</div></div>
                <div class="step"><div class="number-circle">5</div><div>Cliquer sur "Soumettre la feuille" pour valider définitivement la saisie.</div></div>
                <div class="step"><div class="number-circle">6</div><div>Cliquer sur "Modifier la feuille" pour corriger les éventuelles erreurs.</div></div>
                <div class="step"><div class="number-circle">7</div><div>Après soumission, attendre la validation par l’administrateur/RH.</div></div>
                <h5 class="subtitle">III. Feuille de temps : Onglet Gestion de projets</h5>
                <div class="step"><div class="number-circle">1</div><div>Complétez cet onglet quand votre feuille sera validée.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Dans la page, allez dans l'onglet "Gestion de projets".</div></div>
                <div class="step"><div class="number-circle">3</div><div>Choisir le mois, remplir le tableau semaine par semaine.</div></div>
                <div class="step"><div class="number-circle">4</div><div>Vérifier le total de l'heure par jour selon si vous avez indiquer 1 ou 0.5 dans le premier onglet.</div></div>
                <div class="step"><div class="number-circle">5</div><div>Cliquer sur "Enregistrer".</div></div>
                <div class="step"><div class="number-circle">6</div><div>Exporter le tableau en Excel via le bouton "Exporter".</div></div>
                <div class="step"><div class="number-circle">7</div><div>Voir la répartition des heures sur chaque projet dans le graphique.</div></div>
                <div class="step"><div class="number-circle">8</div><div>Onglet "Mes projets" : consulter la liste des projets affectés.</div></div>
                <h5 class="subtitle">IV. Feuille de temps : Onglet Historique</h5>
                <div class="step"><div class="number-circle">1</div><div>Voir toutes les demandes et feuilles soumises</div></div>
                <div class="step"><div class="number-circle">2</div><div>Filtrer par année et statut</div></div>
                <div class="step"><div class="number-circle">3</div><div>Exporter en Excel</div></div>
                <div class="step"><div class="number-circle">4</div><div>Consulter les motifs de refus des feuilles ou demandes</div></div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="bloc">
                <h4>👨‍💼 Administrateur</h4>
                <h5 class="subtitle">I. Administration : Onglet Utilisateurs</h5>
                <div class="step"><div class="number-circle">1</div><div>Aller dans la page "Administration" → onglet "Utilisateurs".</div></div>
                <div class="step"><div class="number-circle">2</div><div>Ajouter ou modifier un utilisateur via le formulaire à droite.</div></div>
                <div class="step"><div class="number-circle">3</div><div>Sélectionner un utilisateur dans le selectbox pour modification.</div></div>
                <div class="step"><div class="number-circle">4</div><div>Ou importer un fichier Excel avec plusieurs utilisateurs.</div></div>
                <div class="step"><div class="number-circle">5</div><div>Les utilisateurs sont affichés dans le tableau à gauche.</div></div>
                <div class="step"><div class="number-circle">6</div><div>Pour activer/désactiver un compte : sélectionner l’utilisateur dans le selectbox sous le tableau.</div></div>
                <div class="step"><div class="number-circle">7</div><div>Cliquer sur "Activer" ou "Désactiver".</div></div>
                <h5 class="subtitle">II. Administration : Onglet Projets</h5>
                <div class="step"><div class="number-circle">1</div><div>Ajouter ou modifier un projet via le formulaire et le selectbox.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Les projets ajoutés sont affichés dans le tableau à droite.</div></div>
                <h5 class="subtitle">III. Administration : Onglet Attribution des projets</h5>
                <div class="step"><div class="number-circle">1</div><div>Ajouter ou modifier des attributions via le formulaire.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Les attributions sont affichées dans le tableau à droite.</div></div>
                <h5 class="subtitle">IV. Administration : Onglet Définition CP & RTT</h5>
                <div class="step"><div class="number-circle">1</div><div>Entrer le nombre annuel de CP et RTT.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Modifier si nécessaire et visualiser les paramètres enregistrés.</div></div>
                <h5 class="subtitle">V. Validation absence : Onglet Demandes en attente</h5>
                <div class="step"><div class="number-circle">1</div><div>Voir toutes les demandes par catégorie.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Pour chaque demande, cliquer sur "Valider" ou "Rejeter".</div></div>
                <div class="step"><div class="number-circle">3</div><div>Si rejet, un champ texte apparaît pour entrer le motif du refus.</div></div>
                <h5 class="subtitle">VI. Validation absence : Onglet Historique</h5>
                <div class="step"><div class="number-circle">1</div><div>Consulter toutes les demandes soumises et leur statut.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Filtrer par critères disponibles.</div></div>
                <div class="step"><div class="number-circle">3</div><div>Exporter en Excel.</div></div>
                <h5 class="subtitle">VII. Validation feuille : Onglet Feuilles en attente</h5>
                <div class="step"><div class="number-circle">1</div><div>Même fonctionnement que pour les demandes d’absence.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Valider ou rejeter chaque feuille.</div></div>
                <h5 class="subtitle">VIII. Validation feuille : Onglet Validation heures</h5>
                <div class="step"><div class="number-circle">1</div><div>Voir toutes les heures saisies par les utilisateurs et modifier si nécessaire.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Filtrer par utilisateur, mois et année.</div></div>
                <h5 class="subtitle">IX. Validation feuille : Onglet Historique</h5>
                <div class="step"><div class="number-circle">1</div><div>Voir toutes les feuilles soumises et leur statut.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Utiliser les filtres pour affiner.</div></div>
                <div class="step"><div class="number-circle">3</div><div>Exporter en Excel.</div></div>
                <h5 class="subtitle">X. Dashboard : Onglet Temps de travail</h5>
                <div class="step"><div class="number-circle">1</div><div>Consulter les KPI et analyses sur les heures travaillées.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Filtrer selon les besoins pour approfondir l’analyse.</div></div>
                <h5 class="subtitle">XI. Dashboard : Onglet Absence</h5>
                <div class="step"><div class="number-circle">1</div><div>Absence de la semaine : tableau avec jours travaillés et absences.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Analyse avancée : analyses approfondies avec filtres.</div></div>
                <h5 class="subtitle">XII. Dashboard : Onglet Projets</h5>
                <div class="step"><div class="number-circle">1</div><div>KPI et tableau de suivi de l’avancement des projets.</div></div>
                <div class="step"><div class="number-circle">2</div><div>Analyses détaillées sur les projets.</div></div>

            </div>
            """,
            unsafe_allow_html=True
        )
