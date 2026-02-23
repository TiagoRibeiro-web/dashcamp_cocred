# =========================================================
# utils/auth.py
# =========================================================
import streamlit as st
import msal

@st.cache_resource
def get_msal_app():
    """Cria e retorna a aplicação MSAL"""
    MS_CLIENT_ID = st.secrets.get("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = st.secrets.get("MS_CLIENT_SECRET", "")
    MS_TENANT_ID = st.secrets.get("MS_TENANT_ID", "")
    
    if not all([MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT_ID]):
        st.error("❌ Credenciais da API não configuradas!")
        return None
    
    try:
        authority = f"https://login.microsoftonline.com/{MS_TENANT_ID}"
        app = msal.ConfidentialClientApplication(
            MS_CLIENT_ID,
            authority=authority,
            client_credential=MS_CLIENT_SECRET
        )
        return app
    except Exception as e:
        st.error(f"❌ Erro MSAL: {str(e)}")
        return None

@st.cache_data(ttl=1800)
def get_access_token():
    """Obtém token de acesso para a API do Graph"""
    app = get_msal_app()
    if not app:
        return None
    
    try:
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        return result.get("access_token")
    except Exception as e:
        st.error(f"❌ Erro token: {str(e)}")
        return None