# db.py
import hashlib
import socket
import psycopg2
import streamlit as st

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _resolve_ipv4(host: str) -> str | None:
    try:
        infos = socket.getaddrinfo(host, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        return infos[0][4][0] if infos else None
    except Exception:
        return None

def get_connection():
    if "postgres" not in st.secrets:
        st.error("❌ [postgres] absent dans .streamlit/secrets.toml")
        st.stop()

    cfg = st.secrets["postgres"]
    required = ("host", "port", "dbname", "user", "password")
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        st.error(f"❌ secrets.toml incomplet → manquant: {', '.join(missing)}")
        st.stop()

    host     = str(cfg["host"]).strip()
    port     = int(cfg["port"])
    dbname   = str(cfg["dbname"]).strip()
    user     = str(cfg["user"]).strip()
    password = str(cfg["password"])
    hostaddr = str(cfg.get("hostaddr") or "").strip()

    # Vérifs de cohérence basiques
    if host.endswith(".supabase.co") and port == 6543:
        st.error("❌ Mauvais couple host/port: db.…supabase.co doit utiliser port 5432 (connexion directe).")
        st.stop()
    if host.endswith(".pooler.supabase.com") and port != 6543:
        st.error("❌ Mauvais couple host/port: *.pooler.supabase.com doit utiliser port 6543 (pooler).")
        st.stop()

    # Forcer IPv4 si provided ou si l’environnement ne renvoie qu’une AAAA
    inferred_ipv4 = _resolve_ipv4(host)
    use_addr = hostaddr or inferred_ipv4 or None

    st.caption(
        "🔌 Tentative connexion PostgreSQL → "
        f"host={host} port={port} db={dbname} user={user} "
        f"{'(IPv4 forcée=' + use_addr + ')' if use_addr else '(IPv4 non forcée)'}"
    )

    kwargs = dict(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="require",
        connect_timeout=6,         # évite d’attendre trop longtemps
        options="-c statement_timeout=15000"  # 15s pour les requêtes
    )
    if use_addr:
        kwargs["hostaddr"] = use_addr

    try:
        conn = psycopg2.connect(**kwargs)
        return conn
    except Exception as e:
        # Messages d’aide ciblés
        if "password authentication failed" in str(e):
            st.error("❌ Mot de passe PostgreSQL invalide. Réinitialise-le dans Supabase > Settings > Database.")
        elif "No address associated" in str(e) or "Name or service not known" in str(e):
            st.error("❌ DNS/host invalide. Vérifie 'host' dans secrets.toml.")
        elif "Cannot assign requested address" in str(e):
            st.error("❌ Ton runtime ne sort pas en IPv6. Ajoute 'hostaddr' (IPv4 publique du host) dans secrets.toml.")
        elif "FATAL: Tenant or user not found" in str(e):
            st.error("❌ Pooler: mauvais host/user/dbname. Utilise EXACTEMENT la Pooled connection string du Dashboard.")
        else:
            st.error("❌ Échec de connexion PostgreSQL.")
        st.exception(e)
        st.stop()
