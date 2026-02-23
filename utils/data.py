# =========================================================
# utils/data.py
# =========================================================
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime, timedelta
from utils.auth import get_access_token

USUARIO_PRINCIPAL = "cristini.cordesco@ideatoreamericas.com"
SHAREPOINT_FILE_ID = "01S7YQRRWMBXCV3AAHYZEIZGL55EPOZULE"
SHEET_NAME = "Demandas ID"

@st.cache_data(ttl=60, show_spinner="🔄 Baixando dados do Excel...")
def carregar_dados_excel_online():
    """Carrega dados do Excel Online via SharePoint"""
    access_token = get_access_token()
    if not access_token:
        return pd.DataFrame()
    
    file_url = f"https://graph.microsoft.com/v1.0/users/{USUARIO_PRINCIPAL}/drive/items/{SHAREPOINT_FILE_ID}/content"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/octet-stream"
    }
    
    try:
        response = requests.get(file_url, headers=headers, timeout=45)
        
        if response.status_code == 200:
            excel_file = BytesIO(response.content)
            
            try:
                df = pd.read_excel(excel_file, sheet_name=SHEET_NAME, engine='openpyxl')
                return df
            except Exception as e:
                st.warning(f"⚠️ Erro na aba '{SHEET_NAME}': {str(e)[:100]}")
                excel_file.seek(0)
                df = pd.read_excel(excel_file, engine='openpyxl')
                return df
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def carregar_dados_exemplo():
    """Retorna dados de exemplo para teste local"""
    dados_exemplo = {
        'ID': range(1, 501),
        'Status': ['Aprovado', 'Em Produção', 'Aguardando Aprovação', 'Concluído', 'Solicitação de Ajustes'] * 100,
        'Prioridade': ['Alta', 'Média', 'Baixa'] * 166 + ['Alta', 'Média'],
        'Produção': ['Cocred', 'Ideatore'] * 250,
        'Data de Solicitação': pd.date_range(start='2024-01-01', periods=500, freq='D'),
        'Deadline': pd.date_range(start='2024-01-15', periods=500, freq='D'),
        'Data de Entrega': pd.date_range(start='2024-01-20', periods=500, freq='D'),
        'Solicitante': ['Cassia Inoue', 'Laís Toledo', 'Nádia Zanin', 'Beatriz Russo', 'Thaís Gomes'] * 100,
        'Campanha': ['Campanha de Crédito Automático', 'Campanha de Consórcios', 'Campanha de Crédito PJ', 
                    'Campanha de Investimentos', 'Campanha de Conta Digital', 'Atualização de TVs internas'] * 83 + ['Campanha de Crédito Automático'] * 2,
        'Tipo': ['Criação', 'Derivação', 'Criação', 'Derivação', 'Extra Contrato', 'Criação'] * 83 + ['Derivação'] * 2,
        'Tipo Atividade': ['Evento', 'Comunicado', 'Campanha Orgânica', 'Divulgação de Produto', 
                          'Campanha de Incentivo/Vendas', 'E-mail Marketing'] * 83 + ['Evento'] * 2,
        'Peça': ['PEÇA AVULSA - DERIVAÇÃO', 'CAMPANHA - ESTRATÉGIA', 'CAMPANHA - ANÚNCIO',
                'CAMPANHA - LP/TKY', 'CAMPANHA - RELATÓRIO', 'CAMPANHA - KV'] * 83 + ['PEÇA AVULSA - DERIVAÇÃO'] * 2
    }
    return pd.DataFrame(dados_exemplo)

def carregar_dados_compartilhados():
    """Carrega dados e armazena no session state"""
    if 'df' not in st.session_state:
        with st.spinner("📥 Carregando dados..."):
            # Tenta carregar do SharePoint
            df = carregar_dados_excel_online()
            
            # Se falhar, usa dados de exemplo
            if df.empty:
                st.warning("⚠️ Usando dados de exemplo para teste...")
                df = carregar_dados_exemplo()
            
            # Converter datas
            for col in ['Data de Solicitação', 'Deadline', 'Data de Entrega']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.tz_localize(None)
            
            st.session_state.df = df
    
    return st.session_state.df