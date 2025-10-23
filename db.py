# db.py (extrait)
import socket
import psycopg2
import streamlit as st

PROJECT_REF = "bzospgaanewvvcmzjpgj"   # <- confirmé par ton URL https://bzospgaanewvvcmzjpgj.supabase.co

def _ipv4(hostname: str) -> str | None:
    try:
        infos = socket.getaddrinfo(hostname, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        return infos[0][4][0] if infos else None
    except Exception:
        return None

def _try_connect(host: str, port: int, db: str, user: str, pwd: str, force_ipv4: bool):
    kwargs = dict(host=host, port=port, dbname=db, user=user, password=pwd, sslmode="require")
    if force_ipv4:
        ip4 = _ipv4(host)
        if ip4:
            kwargs["hostaddr"] = ip4    # force IPv4 (évite les erreurs IPv6)
    return psycopg2.connect(**kwargs)

def get_connection():
    if "postgres" not in st.secrets:
        st.error("❌ [secrets.toml] section [postgres] manquante.")
        st.stop()

    cfg = st.secrets["postgres"]
    pwd = cfg.get("password", "")
    if not pwd:
        st.error("❌ Mot de passe PostgreSQL absent dans secrets.toml (ne pas utiliser la clé anon/service).")
        st.stop()

    # 1) Candidats POOLER (6543). On teste aws-1 puis aws-0 (selon les projets)
    pool_hosts = []
    if "host" in cfg and ".pooler.supabase.com" in cfg["host"]:
        pool_hosts.append(cfg["host"])  # celui du dashboard si déjà mis
    # Ajoute les deux variantes si pas déjà dans la liste
    for h in [f"aws-1-eu-central-1.pooler.supabase.com", f"aws-0-eu-central-1.pooler.supabase.com"]:
        if h not in pool_hosts:
            pool_hosts.append(h)

    pool_users = [
        f"postgres.{PROJECT_REF}",  # format multi-tenant le plus courant
        "postgres",                 # parfois accepté selon la config du projet
    ]

    # Essaie pooler : (host x user) et (IPv6/defaut puis IPv4 forcée)
    for host in pool_hosts:
        for user in pool_users:
            for force_ipv4 in (False, True):
                try:
                    conn = _try_connect(host, 6543, "postgres", user, pwd, force_ipv4)
                    st.info(f"✅ Connecté via pooler: host={host} user={user} IPv4={force_ipv4}")
                    return conn
                except Exception as e:
                    st.warning(f"⚠️ Pooler fail host={host} user={user} IPv4={force_ipv4}: {e}")

    # 2) Candidat DIRECT (5432) — debug uniquement
    direct_host = f"db.{PROJECT_REF}.supabase.co"
    for force_ipv4 in (False, True):  # tente défaut puis IPv4
        try:
            conn = _try_connect(direct_host, 5432, "postgres", "postgres", pwd, force_ipv4)
            st.info(f"✅ Connecté en direct: host={direct_host} IPv4={force_ipv4}")
            return conn
        except Exception as e:
            st.warning(f"⚠️ Direct fail IPv4={force_ipv4}: {e}")

    st.error("❌ Aucune connexion possible (pooler & direct). Vérifie host/port/user/password dans Supabase → Connect.")
    st.stop()
