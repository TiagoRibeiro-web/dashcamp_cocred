import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import msal
from datetime import datetime, timedelta, date
import pytz
import time
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

st.set_page_config(
    page_title="Dashboard de Campanhas - SICOOB COCRED - Id", 
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# =========================================================
# CORES INSTITUCIONAIS COCRED
# =========================================================
CORES = {
    'primaria': '#003366',      # Azul COCRED
    'secundaria': '#00A3E0',    # Azul claro
    'destaque': '#FF6600',      # Laranja
    'sucesso': '#28A745',       # Verde
    'atencao': '#FFC107',       # Amarelo
    'perigo': '#DC3545',        # Vermelho
    'neutra': '#6C757D',        # Cinza
    'criacao': '#003366',       # Azul - Criações
    'derivacao': '#00A3E0',     # Azul claro - Derivações
    'extra': '#FF6600',         # Laranja - Extra Contrato
    'campanha': '#28A745',      # Verde - Campanhas
}

# =========================================================
# CSS CUSTOMIZADO PARA DARK/LIGHT MODE
# =========================================================
st.markdown("""
<style>
    /* Cards - Funcionam em ambos os temas */
    .metric-card-cocred {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #003366 0%, #00A3E0 100%);
        color: white;
    }
    
    .metric-card-criacao {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #003366 0%, #002244 100%);
        color: white;
    }
    
    .metric-card-derivacao {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #00A3E0 0%, #0077A3 100%);
        color: white;
    }
    
    .metric-card-extra {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #FF6600 0%, #CC5200 100%);
        color: white;
    }
    
    .metric-card-campanha {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #28A745 0%, #1E7E34 100%);
        color: white;
    }
    
    /* Container de informações - Adaptável */
    .info-container-cocred {
        background-color: rgba(0, 51, 102, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #003366;
        color: inherit;
    }
    
    /* Cards de resumo - Adaptáveis */
    .resumo-card {
        background-color: var(--background-color);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: inherit;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5, h6 {
        color: inherit !important;
    }
    
    /* Links */
    a {
        color: #00A3E0 !important;
    }
    
    /* Estilo para o container de filtros */
    .filtros-container {
        background: linear-gradient(to right, rgba(0,51,102,0.05), rgba(0,163,224,0.05));
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(0,51,102,0.2);
        margin-bottom: 20px;
    }
    
    /* Botão de aplicar filtros */
    .stButton button {
        background: linear-gradient(135deg, #003366, #00A3E0);
        color: white;
        border: none;
        font-weight: bold;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #002244, #0077A3);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONFIGURAÇÕES DA API
# =========================================================
MS_CLIENT_ID = st.secrets.get("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = st.secrets.get("MS_CLIENT_SECRET", "")
MS_TENANT_ID = st.secrets.get("MS_TENANT_ID", "")

USUARIO_PRINCIPAL = "cristini.cordesco@ideatoreamericas.com"
SHAREPOINT_FILE_ID = "01S7YQRRWMBXCV3AAHYZEIZGL55EPOZULE"
SHEET_NAME = "Demandas ID"

# =========================================================
# AUTENTICAÇÃO
# =========================================================
@st.cache_resource
def get_msal_app():
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

# =========================================================
# CARREGAR DADOS
# =========================================================
@st.cache_data(ttl=60, show_spinner="🔄 Baixando dados do Excel...")
def carregar_dados_excel_online():
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

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def calcular_altura_tabela(num_linhas, num_colunas):
    altura_base = 150
    altura_por_linha = 35
    altura_por_coluna = 2
    altura_conteudo = altura_base + (num_linhas * altura_por_linha) + (num_colunas * altura_por_coluna)
    altura_maxima = 2000
    return min(altura_conteudo, altura_maxima)

def converter_para_data(df, coluna):
    try:
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce', dayfirst=True)
    except:
        pass
    return df

def extrair_tipo_demanda(df, texto):
    count = 0
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                count += len(df[df[col].astype(str).str.contains(texto, na=False, case=False)])
            except:
                pass
    return count

# =========================================================
# CARREGAR DADOS
# =========================================================
with st.spinner("📥 Carregando dados do Excel..."):
    df = carregar_dados_excel_online()

if df.empty:
    st.warning("⚠️ Não foi possível carregar os dados do SharePoint. Usando dados de exemplo...")
    
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
    df = pd.DataFrame(dados_exemplo)

# Converter datas
for col in ['Data de Solicitação', 'Deadline', 'Data de Entrega']:
    if col in df.columns:
        df = converter_para_data(df, col)
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

# =========================================================
# CALCULAR MÉTRICAS GLOBAIS
# =========================================================
total_linhas = len(df)
total_colunas = len(df.columns)

total_concluidos = 0
if 'Status' in df.columns:
    total_concluidos = len(df[df['Status'].str.contains('Concluído|Aprovado', na=False, case=False)])

total_alta = 0
if 'Prioridade' in df.columns:
    total_alta = len(df[df['Prioridade'].str.contains('Alta', na=False, case=False)])

total_hoje = 0
if 'Data de Solicitação' in df.columns:
    hoje = datetime.now().date()
    total_hoje = len(df[pd.to_datetime(df['Data de Solicitação']).dt.date == hoje])

if 'Tipo' in df.columns:
    criacoes = len(df[df['Tipo'].str.contains('Criação|Criacao', na=False, case=False)])
    derivacoes = len(df[df['Tipo'].str.contains('Derivação|Derivacao|Peça|Peca', na=False, case=False)])
    extra_contrato = len(df[df['Tipo'].str.contains('Extra|Contrato', na=False, case=False)])
else:
    criacoes = extrair_tipo_demanda(df, 'Criação|Criacao|Novo|New')
    derivacoes = extrair_tipo_demanda(df, 'Derivação|Derivacao|Peça|Peca')
    extra_contrato = extrair_tipo_demanda(df, 'Extra|Contrato')

if 'Campanha' in df.columns:
    campanhas_unicas = df['Campanha'].nunique()
else:
    campanhas_unicas = len(df['ID'].unique()) // 50 if 'ID' in df.columns else 12

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #003366; font-size: 28px; margin: 0;">📊 COCRED</h1>
        <p style="color: #00A3E0; font-size: 12px; margin: 0;">Dashboard de Campanhas</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 🔄 **Atualização**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Atualizar", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.toast("✅ Cache limpo! Atualizando...")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpar Cache", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.toast("🧹 Cache completamente limpo!")
            time.sleep(1)
            st.rerun()
    
    token = get_access_token()
    if token:
        st.success("✅ **Conectado** | Token ativo", icon="🔌")
    else:
        st.warning("⚠️ **Offline** | Usando dados de exemplo", icon="💾")
    
    st.divider()
    
    st.markdown("### 👁️ **Visualização**")
    
    linhas_por_pagina = st.selectbox(
        "📋 Linhas por página:",
        ["50", "100", "200", "500", "Todas"],
        index=1,
        key="sidebar_linhas_por_pagina"
    )
    
    modo_compacto = st.checkbox("📏 Modo compacto", value=False)
    
    if modo_compacto:
        st.markdown("""
        <style>
            .block-container {padding-top: 1rem; padding-bottom: 0rem;}
            .stMetric {padding: 0.5rem;}
        </style>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📊 **Resumo Executivo**")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.metric(label="📋 Total de Registros", value=f"{total_linhas:,}", delta=None)
    
    with col_m2:
        percentual_concluidos = (total_concluidos / total_linhas * 100) if total_linhas > 0 else 0
        st.metric(label="✅ Concluídos/Aprovados", value=f"{total_concluidos:,}", delta=f"{percentual_concluidos:.0f}%")
    
    col_m3, col_m4 = st.columns(2)
    
    with col_m3:
        st.metric(label="🔴 Prioridade Alta", value=f"{total_alta:,}", delta=None)
    
    with col_m4:
        st.metric(label="📅 Solicitações Hoje", value=total_hoje, delta=None)
    
    st.divider()
    
    st.markdown("### 🛠️ **Ferramentas**")
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    debug_mode = st.checkbox("🐛 **Modo Debug**", value=st.session_state.debug_mode)
    st.session_state.debug_mode = debug_mode
    
    auto_refresh = st.checkbox("🔄 **Auto-refresh (60s)**", value=False)
    
    st.divider()
    
    st.markdown("### ℹ️ **Informações**")
    st.caption(f"🕐 **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    st.markdown("""
    **📎 Links úteis:**
    - [📊 Abrir Excel Online](https://agenciaideatore-my.sharepoint.com/:x:/g/personal/cristini_cordesco_ideatoreamericas_com/IQDMDcVdgAfGSIyZfeke7NFkAatm3fhI0-X4r6gIPQJmosY)
    """)
    
    st.divider()
    
    st.markdown("""
    <div style="text-align: center; color: #6C757D; font-size: 11px; padding: 10px 0;">
        <p style="margin: 0;">Desenvolvido para</p>
        <p style="margin: 0; font-weight: bold; color: #003366;">SICOOB COCRED</p>
        <p style="margin: 5px 0 0 0;">© 2026 - Ideatore</p>
        <p style="margin: 5px 0 0 0;">v4.4.0</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# INTERFACE PRINCIPAL
# =========================================================
st.markdown(f"""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <h1 style="color: #003366; margin: 0;">📊 Dashboard de Campanhas</h1>
    <span style="background: #00A3E0; color: white; padding: 5px 15px; border-radius: 20px; margin-left: 20px; font-size: 14px;">
        SICOOB COCRED
    </span>
</div>
""", unsafe_allow_html=True)

st.caption(f"🔗 Conectado ao Excel Online | Aba: {SHEET_NAME}")

st.success(f"✅ **{total_linhas} registros** carregados com sucesso!")
st.info(f"📋 **Colunas:** {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📈 Análise Estratégica",
    "🎯 KPIs COCRED",
    "📋 Explorador de Dados"
])

# =========================================================
# TAB 1: ANÁLISE ESTRATÉGICA
# =========================================================
with tab1:
    st.markdown("## 📈 Análise Estratégica")
    
    # Configurações de template para Plotly (funciona em dark/light)
    is_dark = st.get_option('theme.base') == 'dark'
    plotly_template = 'plotly_dark' if is_dark else 'plotly_white'
    text_color = 'white' if is_dark else 'black'
    
    # ========== 1. MÉTRICAS DE NEGÓCIO (3 CARDS ALINHADOS) ==========
    st.markdown("""
    <div class="info-container-cocred">
        <p style="margin: 0; font-size: 14px;">
            <strong>🎯 Indicadores de Performance</strong> - Acompanhe os principais KPIs do negócio.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # AGORA SÃO 3 COLUNAS EM VEZ DE 4!
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    
    with col_metric1:
        taxa_conclusao = (total_concluidos / total_linhas * 100) if total_linhas > 0 else 0
        st.markdown(f"""
        <div class="metric-card-cocred">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">✅ TAXA DE CONCLUSÃO</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{taxa_conclusao:.1f}%</p>
            <p style="font-size: 12px; margin: 0;">{total_concluidos} de {total_linhas} concluídos</p>
            <p style="font-size: 11px; margin: 5px 0 0 0; opacity: 0.8;">
                📌 Percentual de demandas finalizadas
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_metric2:
        st.markdown(f"""
        <div class="metric-card-cocred" style="background: linear-gradient(135deg, #00A3E0 0%, #0077A3 100%);">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">⏱️ TEMPO MÉDIO</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">4.2 dias</p>
            <p style="font-size: 12px; margin: 0;">da solicitação à entrega</p>
            <p style="font-size: 11px; margin: 5px 0 0 0; opacity: 0.8;">
                📌 Tempo médio de execução
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_metric3:
        perc_alta = (total_alta / total_linhas * 100) if total_linhas > 0 else 0
        st.markdown(f"""
        <div class="metric-card-cocred" style="background: linear-gradient(135deg, #DC3545 0%, #B22222 100%);">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">🔴 URGÊNCIA</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{perc_alta:.0f}%</p>
            <p style="font-size: 12px; margin: 0;">prioridade alta</p>
            <p style="font-size: 11px; margin: 5px 0 0 0; opacity: 0.8;">
                📌 Demandas com prioridade alta
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 2. ANÁLISE POR SOLICITANTE ==========
    if 'Solicitante' in df.columns:
        st.markdown("""
        <div class="info-container-cocred">
            <p style="margin: 0; font-size: 14px;">
                <strong>👥 Top Solicitantes</strong> - Principais demandantes e volume por usuário.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_sol1, col_sol2 = st.columns([2, 1])
        
        with col_sol1:
            top_solicitantes = df['Solicitante'].value_counts().head(5).reset_index()
            top_solicitantes.columns = ['Solicitante', 'Quantidade']
            
            fig_sol = px.bar(
                top_solicitantes,
                x='Solicitante',
                y='Quantidade',
                title='Top 5 Solicitantes',
                color='Quantidade',
                color_continuous_scale='Blues',
                text='Quantidade',
                template=plotly_template
            )
            
            fig_sol.update_traces(
                textposition='outside',
                texttemplate='%{text}',
                textfont=dict(size=12, color=text_color)
            )
            
            fig_sol.update_layout(
                height=350,
                xaxis_title="",
                yaxis_title="Número de Demandas",
                showlegend=False,
                font=dict(color=text_color),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_sol, use_container_width=True, config={'displayModeBar': False})
        
        with col_sol2:
            media_sol = df['Solicitante'].value_counts().mean()
            maior_sol = df['Solicitante'].value_counts().max()
            nome_maior = df['Solicitante'].value_counts().index[0]
            
            st.markdown(f"""
            <div class="resumo-card" style="height: 350px;">
                <h4 style="color: #003366; margin-top: 0;">📊 Análise de Demanda</h4>
                <div style="text-align: center; margin: 20px 0;">
                    <div style="background: #003366; color: white; border-radius: 50%; width: 80px; height: 80px; 
                                display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                        <span style="font-size: 36px;">👤</span>
                    </div>
                    <h3 style="margin: 10px 0 5px 0; color: #003366;">{nome_maior}</h3>
                    <p style="color: #6C757D; margin: 0;">Maior demandante</p>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #003366;">{maior_sol}</p>
                    <p style="color: #6C757D;">demandas</p>
                </div>
                <div style="background: rgba(0, 51, 102, 0.1); padding: 15px; border-radius: 10px;">
                    <p style="margin: 0; display: flex; justify-content: space-between;">
                        <span>📊 Média geral:</span>
                        <span style="font-weight: bold;">{media_sol:.1f}</span>
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 3. ANÁLISE TEMPORAL COMPLETA ==========
    if 'Data de Solicitação' in df.columns:
        st.markdown("""
        <div class="info-container-cocred">
            <p style="margin: 0; font-size: 14px;">
                <strong>📅 Análise Temporal Completa</strong> - Evolução, comparações e tendências.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Preparar dados temporais
        df_temp = df.copy()
        df_temp['Mês/Ano'] = df_temp['Data de Solicitação'].dt.to_period('M').astype(str)
        df_temp['Ano'] = df_temp['Data de Solicitação'].dt.year
        df_temp['Mês'] = df_temp['Data de Solicitação'].dt.month
        df_temp['Dia da Semana'] = df_temp['Data de Solicitação'].dt.day_name()
        
        # Métricas por período
        hoje = datetime.now().date()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # Últimos 12 meses
        ultimos_12_meses = df_temp[df_temp['Data de Solicitação'].dt.date >= (hoje - timedelta(days=365))].copy()
        evolucao_mensal = ultimos_12_meses.groupby('Mês/Ano').size().reset_index()
        evolucao_mensal.columns = ['Período', 'Quantidade']
        
        # Layout: 4 colunas de métricas no topo
        col_temp1, col_temp4 = st.columns(2)
        
        with col_temp1:
            total_ano = len(df_temp[df_temp['Ano'] == ano_atual])
            st.metric(
                label=f"📊 Total {ano_atual}", 
                value=total_ano,
                help="Total de solicitações no ano atual"
            )
        
        
        
        with col_temp4:
            if not evolucao_mensal.empty:
                media_mensal = evolucao_mensal['Quantidade'].mean()
                st.metric(
                    label="📊 Média Mensal", 
                    value=f"{media_mensal:.0f}",
                    help="Média de solicitações por mês (últimos 12 meses)"
                )
            else:
                st.metric(label="📊 Média Mensal", value="N/A")
        
        # Gráfico principal
        if not evolucao_mensal.empty:
            col_graf1, col_graf2 = st.columns([3, 1])
            
            with col_graf1:
                fig_evolucao = px.line(
                    evolucao_mensal.tail(12),
                    x='Período',
                    y='Quantidade',
                    title='📈 Evolução Mensal (últimos 12 meses)',
                    markers=True,
                    line_shape='linear',
                    template=plotly_template
                )
                
                # Adicionar linha de média
                media_mensal = evolucao_mensal['Quantidade'].mean()
                fig_evolucao.add_hline(
                    y=media_mensal, 
                    line_dash="dash", 
                    line_color="#FF6600",
                    annotation_text=f"Média: {media_mensal:.0f}",
                    annotation_position="bottom right"
                )
                
                fig_evolucao.update_traces(
                    line_color='#003366', 
                    line_width=3, 
                    marker=dict(color='#00A3E0', size=10)
                )
                
                fig_evolucao.update_layout(
                    height=400,
                    xaxis_title="",
                    yaxis_title="Número de Solicitações",
                    font=dict(color=text_color),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_evolucao, use_container_width=True, config={'displayModeBar': False})
            
            with col_graf2:
                # Top 3 meses
                if len(evolucao_mensal) >= 3:
                    top_meses = evolucao_mensal.nlargest(3, 'Quantidade')
                    
                    st.markdown(f"""
                    <div class="resumo-card" style="height: 400px;">
                        <h4 style="color: #003366; margin-top: 0;">🏆 Top 3 Meses</h4>
                        <div style="margin-top: 20px;">
                            <div style="background: linear-gradient(90deg, #FFD700 0%, #FFD700 80%, #f0f0f0 100%); 
                                        padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                                <p style="margin: 0; font-size: 18px; font-weight: bold;">🥇 {top_meses.iloc[0]['Período']}</p>
                                <p style="margin: 0; font-size: 24px;">{top_meses.iloc[0]['Quantidade']} dem.</p>
                            </div>
                            <div style="background: linear-gradient(90deg, #C0C0C0 0%, #C0C0C0 60%, #f0f0f0 100%); 
                                        padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                                <p style="margin: 0; font-size: 18px; font-weight: bold;">🥈 {top_meses.iloc[1]['Período']}</p>
                                <p style="margin: 0; font-size: 24px;">{top_meses.iloc[1]['Quantidade']} dem.</p>
                            </div>
                            <div style="background: linear-gradient(90deg, #CD7F32 0%, #CD7F32 40%, #f0f0f0 100%); 
                                        padding: 15px; border-radius: 10px;">
                                <p style="margin: 0; font-size: 18px; font-weight: bold;">🥉 {top_meses.iloc[2]['Período']}</p>
                                <p style="margin: 0; font-size: 24px;">{top_meses.iloc[2]['Quantidade']} dem.</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="resumo-card" style="height: 400px;">
                        <h4 style="color: #003366; margin-top: 0;">🏆 Top Meses</h4>
                        <p style="text-align: center; margin-top: 150px; color: #6C757D;">Dados insuficientes</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Análise de dia da semana
        if len(df_temp) > 30:
            st.divider()
            
            with st.expander("📊 Análise por Dia da Semana", expanded=False):
                dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dias_pt = {
                    'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                    'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                
                dias_analise = df_temp['Dia da Semana'].value_counts().reset_index()
                dias_analise.columns = ['Dia', 'Quantidade']
                dias_analise['Dia'] = pd.Categorical(dias_analise['Dia'], categories=dias_ordem, ordered=True)
                dias_analise = dias_analise.sort_values('Dia')
                dias_analise['Dia PT'] = dias_analise['Dia'].map(dias_pt)
                
                fig_dias = px.bar(
                    dias_analise,
                    x='Dia PT',
                    y='Quantidade',
                    title='Distribuição por Dia da Semana',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    text='Quantidade',
                    template=plotly_template
                )
                
                fig_dias.update_traces(
                    textposition='outside',
                    texttemplate='%{text}',
                    textfont=dict(size=12, color=text_color)
                )
                
                fig_dias.update_layout(
                    height=350,
                    xaxis_title="",
                    yaxis_title="Número de Solicitações",
                    showlegend=False,
                    font=dict(color=text_color),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_dias, use_container_width=True, config={'displayModeBar': False})

# =========================================================
# TAB 2: KPIs COCRED (COM FILTROS AVANÇADOS COMPLETOS)
# =========================================================
with tab2:
    st.markdown("## 🎯 KPIs - Campanhas COCRED")
    
    # Configurações de template para Plotly
    is_dark = st.get_option('theme.base') == 'dark'
    plotly_template = 'plotly_dark' if is_dark else 'plotly_white'
    text_color = 'white' if is_dark else 'black'
    
    # =========================================================
    # FILTROS AVANÇADOS - CÓPIA IDÊNTICA DA TAB 3 COM QUINZENA!
    # =========================================================
    with st.container():
        st.markdown("##### 🔍 Filtros Avançados")
        
        # Dicionário para armazenar filtros ativos
        filtros_ativos_tab2 = {}
        
        # Primeira linha de filtros (categóricos)
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            if 'Status' in df.columns:
                status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
                status_selecionado = st.selectbox("📌 Status", status_opcoes, key="tab2_status")
                if status_selecionado != 'Todos':
                    filtros_ativos_tab2['Status'] = status_selecionado
        
        with col_f2:
            if 'Prioridade' in df.columns:
                prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
                prioridade_selecionada = st.selectbox("⚡ Prioridade", prioridade_opcoes, key="tab2_prioridade")
                if prioridade_selecionada != 'Todos':
                    filtros_ativos_tab2['Prioridade'] = prioridade_selecionada
        
        with col_f3:
            if 'Produção' in df.columns:
                producao_opcoes = ['Todos'] + sorted(df['Produção'].dropna().unique().tolist())
                producao_selecionada = st.selectbox("🏭 Produção", producao_opcoes, key="tab2_producao")
                if producao_selecionada != 'Todos':
                    filtros_ativos_tab2['Produção'] = producao_selecionada
        
        # Segunda linha de filtros (datas) - 4 COLUNAS!
        col_f4, col_f5, col_f6, col_f7 = st.columns([2, 2, 2, 1])
        
        with col_f4:
            if 'Data de Solicitação' in df.columns:
                periodo_data = st.selectbox(
                    "📅 Data de Solicitação", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Últimos 30 dias", "Personalizado"],
                    key="tab2_periodo_data"
                )
                
                hoje = datetime.now().date()
                
                if periodo_data == "Hoje":
                    filtros_ativos_tab2['data_inicio'] = hoje
                    filtros_ativos_tab2['data_fim'] = hoje
                    filtros_ativos_tab2['tem_filtro_data'] = True
                elif periodo_data == "Esta semana":
                    inicio_semana = hoje - timedelta(days=hoje.weekday())
                    filtros_ativos_tab2['data_inicio'] = inicio_semana
                    filtros_ativos_tab2['data_fim'] = hoje
                    filtros_ativos_tab2['tem_filtro_data'] = True
                elif periodo_data == "Este mês":
                    inicio_mes = hoje.replace(day=1)
                    filtros_ativos_tab2['data_inicio'] = inicio_mes
                    filtros_ativos_tab2['data_fim'] = hoje
                    filtros_ativos_tab2['tem_filtro_data'] = True
                elif periodo_data == "Quinzena":
                    quinzena_opcao = st.radio(
                        "Escolha:",
                        ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                        horizontal=True,
                        key="tab2_data_quinzena_opcao",
                        label_visibility="collapsed"
                    )
                    
                    ano_atual = hoje.year
                    mes_atual = hoje.month
                    
                    if quinzena_opcao == "1ª quinzena (1-15)":
                        data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                        data_fim_quinzena = date(ano_atual, mes_atual, 15)
                    else:
                        ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                        data_fim_quinzena = ultimo_dia
                    
                    filtros_ativos_tab2['data_inicio'] = data_inicio_quinzena
                    filtros_ativos_tab2['data_fim'] = data_fim_quinzena
                    filtros_ativos_tab2['tem_filtro_data'] = True
                    
                    st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                    
                elif periodo_data == "Últimos 30 dias":
                    inicio_30d = hoje - timedelta(days=30)
                    filtros_ativos_tab2['data_inicio'] = inicio_30d
                    filtros_ativos_tab2['data_fim'] = hoje
                    filtros_ativos_tab2['tem_filtro_data'] = True
                elif periodo_data == "Personalizado":
                    datas_validas = df['Data de Solicitação'].dropna()
                    if not datas_validas.empty:
                        data_min = datas_validas.min().date()
                        data_max = datas_validas.max().date()
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            data_ini = st.date_input("De", data_min, key="tab2_data_ini")
                        with col_d2:
                            data_fim = st.date_input("Até", data_max, key="tab2_data_fim")
                        
                        filtros_ativos_tab2['data_inicio'] = data_ini
                        filtros_ativos_tab2['data_fim'] = data_fim
                        filtros_ativos_tab2['tem_filtro_data'] = True
        
        with col_f5:
            # Procurar por colunas de deadline
            coluna_deadline = None
            for col in df.columns:
                if 'deadline' in col.lower() or 'prazo' in col.lower():
                    coluna_deadline = col
                    break
            
            if coluna_deadline is None and 'Deadline' in df.columns:
                coluna_deadline = 'Deadline'
            
            if coluna_deadline:
                periodo_deadline = st.selectbox(
                    "⏰ Deadline", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Próximos 7 dias", "Próximos 30 dias", "Atrasados", "Personalizado"],
                    key="tab2_periodo_deadline"
                )
                
                hoje = datetime.now().date()
                
                if periodo_deadline != "Todos":
                    datas_validas_deadline = df[coluna_deadline].dropna()
                    if not datas_validas_deadline.empty:
                        data_min_deadline = datas_validas_deadline.min().date()
                        data_max_deadline = datas_validas_deadline.max().date()
                        
                        if periodo_deadline == "Hoje":
                            filtros_ativos_tab2['deadline_inicio'] = hoje
                            filtros_ativos_tab2['deadline_fim'] = hoje
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Esta semana":
                            inicio_semana = hoje - timedelta(days=hoje.weekday())
                            fim_semana = inicio_semana + timedelta(days=6)
                            filtros_ativos_tab2['deadline_inicio'] = inicio_semana
                            filtros_ativos_tab2['deadline_fim'] = fim_semana
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Este mês":
                            inicio_mes = hoje.replace(day=1)
                            ultimo_dia = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                            filtros_ativos_tab2['deadline_inicio'] = inicio_mes
                            filtros_ativos_tab2['deadline_fim'] = ultimo_dia
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Quinzena":
                            quinzena_opcao = st.radio(
                                "Escolha:",
                                ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                                horizontal=True,
                                key="tab2_deadline_quinzena_opcao",
                                label_visibility="collapsed"
                            )
                            
                            ano_atual = hoje.year
                            mes_atual = hoje.month
                            
                            if quinzena_opcao == "1ª quinzena (1-15)":
                                data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                                data_fim_quinzena = date(ano_atual, mes_atual, 15)
                            else:
                                ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                                data_fim_quinzena = ultimo_dia
                            
                            filtros_ativos_tab2['deadline_inicio'] = data_inicio_quinzena
                            filtros_ativos_tab2['deadline_fim'] = data_fim_quinzena
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                            
                            st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                            
                        elif periodo_deadline == "Próximos 7 dias":
                            filtros_ativos_tab2['deadline_inicio'] = hoje
                            filtros_ativos_tab2['deadline_fim'] = hoje + timedelta(days=7)
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Próximos 30 dias":
                            filtros_ativos_tab2['deadline_inicio'] = hoje
                            filtros_ativos_tab2['deadline_fim'] = hoje + timedelta(days=30)
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Atrasados":
                            filtros_ativos_tab2['deadline_inicio'] = data_min_deadline
                            filtros_ativos_tab2['deadline_fim'] = hoje - timedelta(days=1)
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Personalizado":
                            col_dd1, col_dd2 = st.columns(2)
                            with col_dd1:
                                data_ini_deadline = st.date_input("De", data_min_deadline, key="tab2_deadline_ini")
                            with col_dd2:
                                data_fim_deadline = st.date_input("Até", data_max_deadline, key="tab2_deadline_fim")
                            filtros_ativos_tab2['deadline_inicio'] = data_ini_deadline
                            filtros_ativos_tab2['deadline_fim'] = data_fim_deadline
                            filtros_ativos_tab2['tem_filtro_deadline'] = True
                            filtros_ativos_tab2['coluna_deadline'] = coluna_deadline
            else:
                st.selectbox("⏰ Deadline", ["Indisponível"], disabled=True, key="tab2_deadline_disabled")
        
        with col_f6:
            # Procurar por colunas de data de entrega
            coluna_entrega = None
            for col in df.columns:
                if 'entrega' in col.lower() or 'data entrega' in col.lower() or 'dt entrega' in col.lower():
                    coluna_entrega = col
                    break
            
            if coluna_entrega is None and 'Data de Entrega' in df.columns:
                coluna_entrega = 'Data de Entrega'
            
            if coluna_entrega:
                periodo_entrega = st.selectbox(
                    "📦 Data de Entrega", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"],
                    key="tab2_periodo_entrega"
                )
                
                hoje = datetime.now().date()
                
                if periodo_entrega != "Todos":
                    datas_validas_entrega = df[coluna_entrega].dropna()
                    if not datas_validas_entrega.empty:
                        data_min_entrega = datas_validas_entrega.min().date()
                        data_max_entrega = datas_validas_entrega.max().date()
                        
                        if periodo_entrega == "Hoje":
                            filtros_ativos_tab2['entrega_inicio'] = hoje
                            filtros_ativos_tab2['entrega_fim'] = hoje
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Esta semana":
                            inicio_semana = hoje - timedelta(days=hoje.weekday())
                            fim_semana = inicio_semana + timedelta(days=6)
                            filtros_ativos_tab2['entrega_inicio'] = inicio_semana
                            filtros_ativos_tab2['entrega_fim'] = fim_semana
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Este mês":
                            inicio_mes = hoje.replace(day=1)
                            ultimo_dia = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                            filtros_ativos_tab2['entrega_inicio'] = inicio_mes
                            filtros_ativos_tab2['entrega_fim'] = ultimo_dia
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Quinzena":
                            quinzena_opcao = st.radio(
                                "Escolha:",
                                ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                                horizontal=True,
                                key="tab2_entrega_quinzena_opcao",
                                label_visibility="collapsed"
                            )
                            
                            ano_atual = hoje.year
                            mes_atual = hoje.month
                            
                            if quinzena_opcao == "1ª quinzena (1-15)":
                                data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                                data_fim_quinzena = date(ano_atual, mes_atual, 15)
                            else:
                                ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                                data_fim_quinzena = ultimo_dia
                            
                            filtros_ativos_tab2['entrega_inicio'] = data_inicio_quinzena
                            filtros_ativos_tab2['entrega_fim'] = data_fim_quinzena
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                            
                            st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                            
                        elif periodo_entrega == "Últimos 7 dias":
                            filtros_ativos_tab2['entrega_inicio'] = hoje - timedelta(days=7)
                            filtros_ativos_tab2['entrega_fim'] = hoje
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Últimos 30 dias":
                            filtros_ativos_tab2['entrega_inicio'] = hoje - timedelta(days=30)
                            filtros_ativos_tab2['entrega_fim'] = hoje
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Personalizado":
                            col_de1, col_de2 = st.columns(2)
                            with col_de1:
                                data_ini_entrega = st.date_input("De", data_min_entrega, key="tab2_entrega_ini")
                            with col_de2:
                                data_fim_entrega = st.date_input("Até", data_max_entrega, key="tab2_entrega_fim")
                            filtros_ativos_tab2['entrega_inicio'] = data_ini_entrega
                            filtros_ativos_tab2['entrega_fim'] = data_fim_entrega
                            filtros_ativos_tab2['tem_filtro_entrega'] = True
                            filtros_ativos_tab2['coluna_entrega'] = coluna_entrega
            else:
                st.selectbox("📦 Data de Entrega", ["Indisponível"], disabled=True, key="tab2_entrega_disabled")
        
        with col_f7:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧹 Limpar Tudo", use_container_width=True, key="tab2_limpar_filtros"):
                for key in list(st.session_state.keys()):
                    if key.startswith('tab2_'):
                        del st.session_state[key]
                st.rerun()
    
    st.divider()
    
    # ========== APLICAR FILTROS AO df_kpi ==========
    df_kpi = df.copy()
    
    # Aplicar filtros categóricos
    for col, valor in filtros_ativos_tab2.items():
        if col not in ['data_inicio', 'data_fim', 'tem_filtro_data', 
                       'deadline_inicio', 'deadline_fim', 'tem_filtro_deadline', 'coluna_deadline',
                       'entrega_inicio', 'entrega_fim', 'tem_filtro_entrega', 'coluna_entrega']:
            df_kpi = df_kpi[df_kpi[col] == valor]
    
    # Aplicar filtro de data de solicitação
    if 'tem_filtro_data' in filtros_ativos_tab2 and 'Data de Solicitação' in df.columns:
        data_inicio = pd.Timestamp(filtros_ativos_tab2['data_inicio'])
        data_fim = pd.Timestamp(filtros_ativos_tab2['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_kpi = df_kpi[
            (df_kpi['Data de Solicitação'] >= data_inicio) & 
            (df_kpi['Data de Solicitação'] <= data_fim)
        ]
    
    # Aplicar filtro de deadline
    if 'tem_filtro_deadline' in filtros_ativos_tab2 and 'coluna_deadline' in filtros_ativos_tab2:
        col_deadline = filtros_ativos_tab2['coluna_deadline']
        if col_deadline in df_kpi.columns:
            deadline_inicio = pd.Timestamp(filtros_ativos_tab2['deadline_inicio'])
            deadline_fim = pd.Timestamp(filtros_ativos_tab2['deadline_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_kpi = df_kpi[
                (df_kpi[col_deadline] >= deadline_inicio) & 
                (df_kpi[col_deadline] <= deadline_fim)
            ]
    
    # Aplicar filtro de data de entrega
    if 'tem_filtro_entrega' in filtros_ativos_tab2 and 'coluna_entrega' in filtros_ativos_tab2:
        col_entrega = filtros_ativos_tab2['coluna_entrega']
        if col_entrega in df_kpi.columns:
            entrega_inicio = pd.Timestamp(filtros_ativos_tab2['entrega_inicio'])
            entrega_fim = pd.Timestamp(filtros_ativos_tab2['entrega_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_kpi = df_kpi[
                (df_kpi[col_entrega] >= entrega_inicio) & 
                (df_kpi[col_entrega] <= entrega_fim)
            ]
    
    total_kpi = len(df_kpi)
    
    # Mostrar resumo dos filtros
    if filtros_ativos_tab2:
        st.info(f"🔍 **Filtros ativos:** {total_kpi} de {total_linhas} registros ({total_kpi/total_linhas*100:.1f}%)")
    
    st.divider()
    
    # ========== GRÁFICOS INTERATIVOS ==========
    
    # Inicializar session state para campanha selecionada
    if 'campanha_selecionada' not in st.session_state:
        st.session_state.campanha_selecionada = None
    
    col_chart1, col_chart2 = st.columns([3, 2])
    
    with col_chart1:
        st.markdown("""
        <div style="background: rgba(0, 51, 102, 0.1); padding: 10px; border-radius: 10px; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 13px;">
                <strong style="color: #003366;">🏆 Top 10 Campanhas</strong> - Clique nos botões abaixo para detalhar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Procurar por coluna de campanha
        coluna_campanha = None
        possiveis_nomes = ['Campanha', 'campanha', 'CAMPANHA', 'Nome da Campanha', 'Campanhas', 'campanhas']
        
        for col in df_kpi.columns:
            if any(nome in col for nome in possiveis_nomes):
                coluna_campanha = col
                break
        
        if coluna_campanha:
            # Top 10 campanhas
            campanhas_top = df_kpi[coluna_campanha].value_counts().head(10).reset_index()
            campanhas_top.columns = ['Campanha', 'Quantidade']
            
            # Filtrar valores nulos ou vazios
            campanhas_top = campanhas_top[campanhas_top['Campanha'].notna()]
            campanhas_top = campanhas_top[campanhas_top['Campanha'] != '']
            
            if not campanhas_top.empty:
                # Ordenar para o gráfico
                campanhas_top = campanhas_top.sort_values('Quantidade', ascending=True)
                
                # GRÁFICO DE BARRAS
                fig_campanhas = px.bar(
                    campanhas_top,
                    x='Quantidade',
                    y='Campanha',
                    orientation='h',
                    title='Top 10 Campanhas por Volume',
                    color='Quantidade',
                    color_continuous_scale='Blues',
                    text='Quantidade',
                    template=plotly_template
                )
                
                # Destacar a campanha selecionada se houver
                if st.session_state.campanha_selecionada and st.session_state.campanha_selecionada in campanhas_top['Campanha'].values:
                    # Criar lista de cores
                    cores = ['#003366'] * len(campanhas_top)
                    idx = campanhas_top[campanhas_top['Campanha'] == st.session_state.campanha_selecionada].index[0]
                    cores[campanhas_top.index.get_loc(idx)] = '#FF6600'  # Laranja para destacar
                    
                    fig_campanhas.update_traces(marker_color=cores)
                
                fig_campanhas.update_traces(
                    textposition='outside',
                    texttemplate='%{text}',
                    textfont=dict(size=12, color=text_color),
                    hovertemplate='<b>%{y}</b><br>Demandas: %{x}<extra></extra>'
                )
                
                fig_campanhas.update_layout(
                    height=350,
                    xaxis_title="Número de Demandas",
                    yaxis_title="",
                    showlegend=False,
                    font=dict(color=text_color),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=30, t=40, b=10)
                )
                
                st.plotly_chart(fig_campanhas, use_container_width=True, config={'displayModeBar': False})
                
                # BOTÕES PARA SELEÇÃO
                st.markdown("##### 🔘 Selecione uma campanha:")
                
                # Criar botões em colunas (5 por linha)
                for i in range(0, len(campanhas_top), 5):
                    cols_botoes = st.columns(5)
                    for j in range(5):
                        if i + j < len(campanhas_top):
                            idx = i + j
                            campanha = campanhas_top.iloc[idx]['Campanha']
                            qtd = campanhas_top.iloc[idx]['Quantidade']
                            
                            # Truncar nome se muito longo
                            nome_curto = campanha[:15] + '...' if len(campanha) > 15 else campanha
                            
                            with cols_botoes[j]:
                                if st.button(
                                    f"{nome_curto} ({qtd})", 
                                    key=f"tab2_btn_camp_{idx}",
                                    use_container_width=True,
                                    type="primary" if campanha == st.session_state.campanha_selecionada else "secondary"
                                ):
                                    st.session_state.campanha_selecionada = campanha
                                    st.rerun()
                
                # Botão para limpar seleção
                if st.session_state.campanha_selecionada:
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                    with col_btn2:
                        if st.button("🧹 Limpar Seleção", use_container_width=True, key="tab2_limpar_selecao"):
                            st.session_state.campanha_selecionada = None
                            st.rerun()
                
                # Métrica simples do Top 1
                top1_campanha = campanhas_top.iloc[-1]['Campanha']
                top1_valor = campanhas_top.iloc[-1]['Quantidade']
                
                if st.session_state.campanha_selecionada:
                    st.success(f"🔍 **Campanha selecionada:** {st.session_state.campanha_selecionada}")
                else:
                    if len(top1_campanha) > 50:
                        st.caption(f"🥇 **Líder:** {top1_campanha[:50]}... ({top1_valor} demandas)")
                    else:
                        st.caption(f"🥇 **Líder:** {top1_campanha} ({top1_valor} demandas)")
            else:
                st.info("ℹ️ Dados de campanha não disponíveis")
        else:
            st.info("ℹ️ Dados de campanha não disponíveis")
            
            if st.session_state.get('debug_mode', False):
                st.caption("📋 Colunas disponíveis:")
                st.write(df_kpi.columns.tolist())
    
    with col_chart2:
        st.markdown("""
        <div style="background: rgba(0, 51, 102, 0.1); padding: 10px; border-radius: 10px; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 13px;">
                <strong style="color: #003366;">🎯 Distribuição por Status</strong> - 
                {}.
            </p>
        </div>
        """.format(
            f"Detalhando: {st.session_state.campanha_selecionada[:50]}..." if st.session_state.campanha_selecionada and len(st.session_state.campanha_selecionada) > 50 
            else f"Detalhando: {st.session_state.campanha_selecionada}" if st.session_state.campanha_selecionada 
            else "Visão geral de todas as campanhas"
        ), unsafe_allow_html=True)
        
        if 'Status' in df_kpi.columns and coluna_campanha:
            # Filtrar por campanha selecionada se houver
            if st.session_state.campanha_selecionada:
                df_filtrado = df_kpi[df_kpi[coluna_campanha] == st.session_state.campanha_selecionada]
                titulo = f"Status - {st.session_state.campanha_selecionada[:30]}..."
            else:
                df_filtrado = df_kpi
                titulo = 'Distribuição Geral'
            
            if not df_filtrado.empty:
                status_dist = df_filtrado['Status'].value_counts().reset_index()
                status_dist.columns = ['Status', 'Quantidade']
                
                fig_status = px.pie(
                    status_dist,
                    values='Quantidade',
                    names='Status',
                    title=titulo,
                    color_discrete_sequence=['#003366', '#00A3E0', '#FF6600', '#28A745', '#6C757D'],
                    template=plotly_template,
                    hole=0.4
                )
                
                fig_status.update_traces(
                    textposition='outside', 
                    textinfo='percent+label',
                    textfont=dict(size=11, color=text_color),
                    marker=dict(line=dict(color='white', width=2)),
                    hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>'
                )
                
                fig_status.update_layout(
                    height=400,
                    font=dict(color=text_color),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False})
                
                # Mostrar métricas adicionais quando uma campanha está selecionada
                if st.session_state.campanha_selecionada:
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Demandas", len(df_filtrado))
                    with col_m2:
                        concluidas = len(df_filtrado[df_filtrado['Status'].str.contains('Concluído|Aprovado', na=False, case=False)])
                        taxa = (concluidas / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
                        st.metric("Taxa Conclusão", f"{taxa:.1f}%")
            else:
                st.info(f"ℹ️ Sem dados para esta campanha")
        else:
            # Fallback para dados de exemplo
            status_data = {
                'Status': ['Aprovado', 'Em Produção', 'Aguardando Aprovação', 'Concluído'],
                'Quantidade': [124, 89, 67, 45]
            }
            df_status = pd.DataFrame(status_data)
            
            fig_status = px.pie(
                df_status,
                values='Quantidade',
                names='Status',
                title='Demandas por Status (Exemplo)',
                color_discrete_sequence=['#003366', '#00A3E0', '#FF6600', '#28A745'],
                template=plotly_template,
                hole=0.4
            )
            
            fig_status.update_traces(
                textposition='outside', 
                textinfo='percent+label',
                textfont=dict(size=12, color=text_color),
                marker=dict(line=dict(color='rgba(0,0,0,0)', width=0))
            )
            
            fig_status.update_layout(
                height=400,
                font=dict(color=text_color),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1
                )
            )
            st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False})
    
    st.divider()
    
    # ========== TABELA DE DEMANDAS POR ORIGEM ==========
    st.markdown("""
    <div class="info-container-cocred">
        <p style="margin: 0; font-size: 14px;">
            <strong>📋 Demandas por Origem</strong> - Detalhamento do volume por origem, com classificação.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Procurar por coluna de Origem
    coluna_origem = None
    possiveis_nomes_origem = ['Origem', 'origem', 'ORIGEM', 'Fonte', 'fonte', 'FONTE', 'Canal', 'canal']
    
    for col in df_kpi.columns:
        if any(nome in col for nome in possiveis_nomes_origem):
            coluna_origem = col
            break
    
    if coluna_origem:
        # Contar ocorrências por origem
        origem_counts = df_kpi[coluna_origem].value_counts().head(8).reset_index()
        origem_counts.columns = ['Origem', 'Quantidade']
        
        # Filtrar valores nulos ou vazios
        origem_counts = origem_counts[origem_counts['Origem'].notna()]
        origem_counts = origem_counts[origem_counts['Origem'] != '']
        
        if not origem_counts.empty:
            # Calcular percentual
            total_origem = origem_counts['Quantidade'].sum()
            origem_counts['% do Total'] = (origem_counts['Quantidade'] / total_kpi * 100).round(1).astype(str) + '%'
            
            # Classificar volume
            def get_status(qtd):
                if qtd > 100:
                    return '✅ Alto volume'
                elif qtd > 50:
                    return '⚠️ Médio volume'
                elif qtd > 20:
                    return '🟡 Médio-Baixo'
                else:
                    return '⚪ Baixo volume'
            
            origem_counts['Status'] = origem_counts['Quantidade'].apply(get_status)
            
            # Mostrar tabela
            st.dataframe(
                origem_counts,
                use_container_width=True,
                height=350,
                hide_index=True,
                column_config={
                    "Origem": "📌 Origem",
                    "Quantidade": "🔢 Quantidade",
                    "% do Total": "📊 %",
                    "Status": "🚦 Classificação"
                }
            )
            
            # Métricas rápidas sobre origens
            col_orig1, col_orig2, col_orig3 = st.columns(3)
            with col_orig1:
                st.metric("Total Origens", len(origem_counts))
            with col_orig2:
                st.metric("Total Demandas", origem_counts['Quantidade'].sum())
            # with col_orig3:
            #     media_origem = origem_counts['Quantidade'].mean()
            #     st.metric("Média por Origem", f"{media_origem:.0f}")
        else:
            st.info("ℹ️ Dados de origem não disponíveis")
            
            if st.session_state.get('debug_mode', False):
                st.caption(f"📋 Coluna encontrada: {coluna_origem}, mas sem dados válidos")
    else:
        # Fallback com dados de exemplo
        st.info("ℹ️ Coluna 'Origem' não encontrada. Usando dados de exemplo...")
        
        if st.session_state.get('debug_mode', False):
            st.caption("📋 Colunas disponíveis no DataFrame:")
            st.write(df_kpi.columns.tolist())
        
        # Dados de exemplo
        origem_exemplo = pd.DataFrame({
            'Origem': ['Marketing Digital', 'Indicação', 'Redes Sociais', 
                      'E-mail Marketing', 'Evento', 'Site', 'WhatsApp', 'Telefone'],
            'Quantidade': [145, 98, 76, 54, 43, 32, 28, 15],
            '% do Total': ['32%', '22%', '17%', '12%', '10%', '7%', '6%', '4%'],
            'Status': ['✅ Alto volume', '⚠️ Médio volume', '⚠️ Médio volume', 
                      '🟡 Médio-Baixo', '🟡 Médio-Baixo', '⚪ Baixo volume', 
                      '⚪ Baixo volume', '⚪ Baixo volume']
        })
        
        st.dataframe(origem_exemplo, use_container_width=True, height=350, hide_index=True)

# =========================================================
# TAB 3: EXPLORADOR DE DADOS (COM FILTRO DE DATA DE ENTREGA E QUINZENA!)
# =========================================================
with tab3:
    st.markdown("## 📋 Explorador de Dados")
    
    # =========================================================
    # HEADER COM ESTATÍSTICAS RÁPIDAS
    # =========================================================
    col_stats1, col_stats2, col_stats4 = st.columns(3)
    
    with col_stats1:
        st.metric(
            label="📊 Total de Registros", 
            value=f"{total_linhas:,}",
            help="Todos os registros disponíveis na base"
        )
    
    with col_stats2:
        if 'Data de Solicitação' in df.columns:
            data_min = df['Data de Solicitação'].min().strftime('%d/%m/%Y')
            data_max = df['Data de Solicitação'].max().strftime('%d/%m/%Y')
            st.metric(
                label="📅 Vigência", 
                value=f"{data_min} a {data_max}",
                help="Período coberto pelos dados"
            )
        else:
            st.metric(label="📅 Vigência", value="N/A")
    
    with col_stats4:
        st.metric(
            label="🔄 Atualização", 
            value=datetime.now().strftime('%d/%m/%Y'),
            help="Data da última atualização"
        )
    
    st.divider()
    
    # =========================================================
    # FILTROS AVANÇADOS (COM DATA DE ENTREGA E QUINZENA!)
    # =========================================================
    with st.container():
        st.markdown("##### 🔍 Filtros Avançados")
        
        # Primeira linha de filtros (categóricos)
        col_f1, col_f2, col_f3 = st.columns(3)
        
        filtros_ativos = {}
        
        with col_f1:
            if 'Status' in df.columns:
                status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
                status_selecionado = st.selectbox("📌 Status", status_opcoes, key="tab3_status")
                if status_selecionado != 'Todos':
                    filtros_ativos['Status'] = status_selecionado
        
        with col_f2:
            if 'Prioridade' in df.columns:
                prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
                prioridade_selecionada = st.selectbox("⚡ Prioridade", prioridade_opcoes, key="tab3_prioridade")
                if prioridade_selecionada != 'Todos':
                    filtros_ativos['Prioridade'] = prioridade_selecionada
        
        with col_f3:
            if 'Produção' in df.columns:
                producao_opcoes = ['Todos'] + sorted(df['Produção'].dropna().unique().tolist())
                producao_selecionada = st.selectbox("🏭 Produção", producao_opcoes, key="tab3_producao")
                if producao_selecionada != 'Todos':
                    filtros_ativos['Produção'] = producao_selecionada
        
        # Segunda linha de filtros (datas) - 4 COLUNAS!
        col_f4, col_f5, col_f6, col_f7 = st.columns([2, 2, 2, 1])
        
        with col_f4:
            if 'Data de Solicitação' in df.columns:
                periodo_data = st.selectbox(
                    "📅 Data de Solicitação", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Últimos 30 dias", "Personalizado"],
                    key="tab3_periodo_data"
                )
                
                hoje = datetime.now().date()
                
                if periodo_data == "Hoje":
                    filtros_ativos['data_inicio'] = hoje
                    filtros_ativos['data_fim'] = hoje
                    filtros_ativos['tem_filtro_data'] = True
                elif periodo_data == "Esta semana":
                    inicio_semana = hoje - timedelta(days=hoje.weekday())
                    filtros_ativos['data_inicio'] = inicio_semana
                    filtros_ativos['data_fim'] = hoje
                    filtros_ativos['tem_filtro_data'] = True
                elif periodo_data == "Este mês":
                    inicio_mes = hoje.replace(day=1)
                    filtros_ativos['data_inicio'] = inicio_mes
                    filtros_ativos['data_fim'] = hoje
                    filtros_ativos['tem_filtro_data'] = True
                elif periodo_data == "Quinzena":
                    quinzena_opcao = st.radio(
                        "Escolha:",
                        ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                        horizontal=True,
                        key="tab3_data_quinzena_opcao",
                        label_visibility="collapsed"
                    )
                    
                    ano_atual = hoje.year
                    mes_atual = hoje.month
                    
                    if quinzena_opcao == "1ª quinzena (1-15)":
                        data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                        data_fim_quinzena = date(ano_atual, mes_atual, 15)
                    else:
                        ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                        data_fim_quinzena = ultimo_dia
                    
                    filtros_ativos['data_inicio'] = data_inicio_quinzena
                    filtros_ativos['data_fim'] = data_fim_quinzena
                    filtros_ativos['tem_filtro_data'] = True
                    
                    st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                    
                elif periodo_data == "Últimos 30 dias":
                    inicio_30d = hoje - timedelta(days=30)
                    filtros_ativos['data_inicio'] = inicio_30d
                    filtros_ativos['data_fim'] = hoje
                    filtros_ativos['tem_filtro_data'] = True
                elif periodo_data == "Personalizado":
                    datas_validas = df['Data de Solicitação'].dropna()
                    if not datas_validas.empty:
                        data_min = datas_validas.min().date()
                        data_max = datas_validas.max().date()
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            data_ini = st.date_input("De", data_min, key="tab3_data_ini")
                        with col_d2:
                            data_fim = st.date_input("Até", data_max, key="tab3_data_fim")
                        
                        filtros_ativos['data_inicio'] = data_ini
                        filtros_ativos['data_fim'] = data_fim
                        filtros_ativos['tem_filtro_data'] = True
        
        with col_f5:
            # Procurar por colunas de deadline
            coluna_deadline = None
            for col in df.columns:
                if 'deadline' in col.lower() or 'prazo' in col.lower():
                    coluna_deadline = col
                    break
            
            if coluna_deadline is None and 'Deadline' in df.columns:
                coluna_deadline = 'Deadline'
            
            if coluna_deadline:
                periodo_deadline = st.selectbox(
                    "⏰ Deadline", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Próximos 7 dias", "Próximos 30 dias", "Atrasados", "Personalizado"],
                    key="tab3_periodo_deadline"
                )
                
                hoje = datetime.now().date()
                
                if periodo_deadline != "Todos":
                    datas_validas_deadline = df[coluna_deadline].dropna()
                    if not datas_validas_deadline.empty:
                        data_min_deadline = datas_validas_deadline.min().date()
                        data_max_deadline = datas_validas_deadline.max().date()
                        
                        if periodo_deadline == "Hoje":
                            filtros_ativos['deadline_inicio'] = hoje
                            filtros_ativos['deadline_fim'] = hoje
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Esta semana":
                            inicio_semana = hoje - timedelta(days=hoje.weekday())
                            fim_semana = inicio_semana + timedelta(days=6)
                            filtros_ativos['deadline_inicio'] = inicio_semana
                            filtros_ativos['deadline_fim'] = fim_semana
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Este mês":
                            inicio_mes = hoje.replace(day=1)
                            ultimo_dia = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                            filtros_ativos['deadline_inicio'] = inicio_mes
                            filtros_ativos['deadline_fim'] = ultimo_dia
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Quinzena":
                            quinzena_opcao = st.radio(
                                "Escolha:",
                                ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                                horizontal=True,
                                key="tab3_deadline_quinzena_opcao",
                                label_visibility="collapsed"
                            )
                            
                            ano_atual = hoje.year
                            mes_atual = hoje.month
                            
                            if quinzena_opcao == "1ª quinzena (1-15)":
                                data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                                data_fim_quinzena = date(ano_atual, mes_atual, 15)
                            else:
                                ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                                data_fim_quinzena = ultimo_dia
                            
                            filtros_ativos['deadline_inicio'] = data_inicio_quinzena
                            filtros_ativos['deadline_fim'] = data_fim_quinzena
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                            
                            st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                            
                        elif periodo_deadline == "Próximos 7 dias":
                            filtros_ativos['deadline_inicio'] = hoje
                            filtros_ativos['deadline_fim'] = hoje + timedelta(days=7)
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Próximos 30 dias":
                            filtros_ativos['deadline_inicio'] = hoje
                            filtros_ativos['deadline_fim'] = hoje + timedelta(days=30)
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Atrasados":
                            filtros_ativos['deadline_inicio'] = data_min_deadline
                            filtros_ativos['deadline_fim'] = hoje - timedelta(days=1)
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
                        elif periodo_deadline == "Personalizado":
                            col_dd1, col_dd2 = st.columns(2)
                            with col_dd1:
                                data_ini_deadline = st.date_input("De", data_min_deadline, key="tab3_deadline_ini")
                            with col_dd2:
                                data_fim_deadline = st.date_input("Até", data_max_deadline, key="tab3_deadline_fim")
                            filtros_ativos['deadline_inicio'] = data_ini_deadline
                            filtros_ativos['deadline_fim'] = data_fim_deadline
                            filtros_ativos['tem_filtro_deadline'] = True
                            filtros_ativos['coluna_deadline'] = coluna_deadline
            else:
                st.selectbox("⏰ Deadline", ["Indisponível"], disabled=True, key="tab3_deadline_disabled")
        
        with col_f6:
            # Procurar por colunas de data de entrega
            coluna_entrega = None
            for col in df.columns:
                if 'entrega' in col.lower() or 'data entrega' in col.lower() or 'dt entrega' in col.lower():
                    coluna_entrega = col
                    break
            
            if coluna_entrega is None and 'Data de Entrega' in df.columns:
                coluna_entrega = 'Data de Entrega'
            
            if coluna_entrega:
                periodo_entrega = st.selectbox(
                    "📦 Data de Entrega", 
                    ["Todos", "Hoje", "Esta semana", "Este mês", "Quinzena", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"],
                    key="tab3_periodo_entrega"
                )
                
                hoje = datetime.now().date()
                
                if periodo_entrega != "Todos":
                    datas_validas_entrega = df[coluna_entrega].dropna()
                    if not datas_validas_entrega.empty:
                        data_min_entrega = datas_validas_entrega.min().date()
                        data_max_entrega = datas_validas_entrega.max().date()
                        
                        if periodo_entrega == "Hoje":
                            filtros_ativos['entrega_inicio'] = hoje
                            filtros_ativos['entrega_fim'] = hoje
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Esta semana":
                            inicio_semana = hoje - timedelta(days=hoje.weekday())
                            fim_semana = inicio_semana + timedelta(days=6)
                            filtros_ativos['entrega_inicio'] = inicio_semana
                            filtros_ativos['entrega_fim'] = fim_semana
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Este mês":
                            inicio_mes = hoje.replace(day=1)
                            ultimo_dia = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                            filtros_ativos['entrega_inicio'] = inicio_mes
                            filtros_ativos['entrega_fim'] = ultimo_dia
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Quinzena":
                            quinzena_opcao = st.radio(
                                "Escolha:",
                                ["1ª quinzena (1-15)", "2ª quinzena (16-31)"],
                                horizontal=True,
                                key="tab3_entrega_quinzena_opcao",
                                label_visibility="collapsed"
                            )
                            
                            ano_atual = hoje.year
                            mes_atual = hoje.month
                            
                            if quinzena_opcao == "1ª quinzena (1-15)":
                                data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                                data_fim_quinzena = date(ano_atual, mes_atual, 15)
                            else:
                                ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                                data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                                data_fim_quinzena = ultimo_dia
                            
                            filtros_ativos['entrega_inicio'] = data_inicio_quinzena
                            filtros_ativos['entrega_fim'] = data_fim_quinzena
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                            
                            st.caption(f"📅 {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")
                            
                        elif periodo_entrega == "Últimos 7 dias":
                            filtros_ativos['entrega_inicio'] = hoje - timedelta(days=7)
                            filtros_ativos['entrega_fim'] = hoje
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Últimos 30 dias":
                            filtros_ativos['entrega_inicio'] = hoje - timedelta(days=30)
                            filtros_ativos['entrega_fim'] = hoje
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
                        elif periodo_entrega == "Personalizado":
                            col_de1, col_de2 = st.columns(2)
                            with col_de1:
                                data_ini_entrega = st.date_input("De", data_min_entrega, key="tab3_entrega_ini")
                            with col_de2:
                                data_fim_entrega = st.date_input("Até", data_max_entrega, key="tab3_entrega_fim")
                            filtros_ativos['entrega_inicio'] = data_ini_entrega
                            filtros_ativos['entrega_fim'] = data_fim_entrega
                            filtros_ativos['tem_filtro_entrega'] = True
                            filtros_ativos['coluna_entrega'] = coluna_entrega
            else:
                st.selectbox("📦 Data de Entrega", ["Indisponível"], disabled=True, key="tab3_entrega_disabled")
        
        with col_f7:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧹 Limpar Tudo", use_container_width=True, key="tab3_limpar_filtros"):
                for key in list(st.session_state.keys()):
                    if key.startswith('tab3_'):
                        del st.session_state[key]
                st.rerun()
    
    st.divider()
    
    # =========================================================
    # ÁREA DE PESQUISA E EXPORTAÇÃO
    # =========================================================
    col_search, col_export, col_clear = st.columns([3, 1, 1])
    
    with col_search:
        termo_pesquisa = st.text_input(
            "🔎 Pesquisar em todas as colunas:", 
            placeholder="Digite para buscar...",
            key="tab3_pesquisa"
        )
    
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        # Preparar dados para exportação
        df_export = df.copy()
        
        # Aplicar filtros categóricos
        for col, valor in filtros_ativos.items():
            if col not in ['data_inicio', 'data_fim', 'tem_filtro_data', 
                           'deadline_inicio', 'deadline_fim', 'tem_filtro_deadline', 'coluna_deadline',
                           'entrega_inicio', 'entrega_fim', 'tem_filtro_entrega', 'coluna_entrega']:
                df_export = df_export[df_export[col] == valor]
        
        # Aplicar filtro de data de solicitação
        if 'tem_filtro_data' in filtros_ativos and 'Data de Solicitação' in df.columns:
            data_inicio = pd.Timestamp(filtros_ativos['data_inicio'])
            data_fim = pd.Timestamp(filtros_ativos['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_export = df_export[
                (df_export['Data de Solicitação'] >= data_inicio) & 
                (df_export['Data de Solicitação'] <= data_fim)
            ]
        
        # Aplicar filtro de deadline
        if 'tem_filtro_deadline' in filtros_ativos and 'coluna_deadline' in filtros_ativos:
            col_deadline = filtros_ativos['coluna_deadline']
            if col_deadline in df_export.columns:
                deadline_inicio = pd.Timestamp(filtros_ativos['deadline_inicio'])
                deadline_fim = pd.Timestamp(filtros_ativos['deadline_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_export = df_export[
                    (df_export[col_deadline] >= deadline_inicio) & 
                    (df_export[col_deadline] <= deadline_fim)
                ]
        
        # Aplicar filtro de data de entrega
        if 'tem_filtro_entrega' in filtros_ativos and 'coluna_entrega' in filtros_ativos:
            col_entrega = filtros_ativos['coluna_entrega']
            if col_entrega in df_export.columns:
                entrega_inicio = pd.Timestamp(filtros_ativos['entrega_inicio'])
                entrega_fim = pd.Timestamp(filtros_ativos['entrega_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_export = df_export[
                    (df_export[col_entrega] >= entrega_inicio) & 
                    (df_export[col_entrega] <= entrega_fim)
                ]
        
        # Aplicar pesquisa
        if termo_pesquisa:
            mask = pd.Series(False, index=df_export.index)
            for col in df_export.columns:
                if df_export[col].dtype == 'object':
                    try:
                        mask = mask | df_export[col].astype(str).str.contains(termo_pesquisa, case=False, na=False)
                    except:
                        pass
            df_export = df_export[mask]
        
        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV",
            data=csv,
            file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="tab3_export_csv"
        )
    
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if filtros_ativos or (termo_pesquisa and termo_pesquisa.strip() != ""):
            if st.button("🧹 Limpar Tudo", use_container_width=True, key="tab3_limpar_tudo"):
                for key in list(st.session_state.keys()):
                    if key.startswith('tab3_'):
                        del st.session_state[key]
                st.rerun()
    
    # =========================================================
    # APLICAR FILTROS E PESQUISA PARA A TABELA PRINCIPAL
    # =========================================================
    df_final = df.copy()
    
    # Aplicar filtros categóricos
    for col, valor in filtros_ativos.items():
        if col not in ['data_inicio', 'data_fim', 'tem_filtro_data', 
                       'deadline_inicio', 'deadline_fim', 'tem_filtro_deadline', 'coluna_deadline',
                       'entrega_inicio', 'entrega_fim', 'tem_filtro_entrega', 'coluna_entrega']:
            df_final = df_final[df_final[col] == valor]
    
    # Aplicar filtro de data de solicitação
    if 'tem_filtro_data' in filtros_ativos and 'Data de Solicitação' in df.columns:
        data_inicio = pd.Timestamp(filtros_ativos['data_inicio'])
        data_fim = pd.Timestamp(filtros_ativos['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_final = df_final[
            (df_final['Data de Solicitação'] >= data_inicio) & 
            (df_final['Data de Solicitação'] <= data_fim)
        ]
    
    # Aplicar filtro de deadline
    if 'tem_filtro_deadline' in filtros_ativos and 'coluna_deadline' in filtros_ativos:
        col_deadline = filtros_ativos['coluna_deadline']
        if col_deadline in df_final.columns:
            deadline_inicio = pd.Timestamp(filtros_ativos['deadline_inicio'])
            deadline_fim = pd.Timestamp(filtros_ativos['deadline_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_final = df_final[
                (df_final[col_deadline] >= deadline_inicio) & 
                (df_final[col_deadline] <= deadline_fim)
            ]
    
    # Aplicar filtro de data de entrega
    if 'tem_filtro_entrega' in filtros_ativos and 'coluna_entrega' in filtros_ativos:
        col_entrega = filtros_ativos['coluna_entrega']
        if col_entrega in df_final.columns:
            entrega_inicio = pd.Timestamp(filtros_ativos['entrega_inicio'])
            entrega_fim = pd.Timestamp(filtros_ativos['entrega_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_final = df_final[
                (df_final[col_entrega] >= entrega_inicio) & 
                (df_final[col_entrega] <= entrega_fim)
            ]
    
    # Aplicar pesquisa
    if termo_pesquisa:
        mask = pd.Series(False, index=df_final.index)
        for col in df_final.columns:
            if df_final[col].dtype == 'object':
                try:
                    mask = mask | df_final[col].astype(str).str.contains(termo_pesquisa, case=False, na=False)
                except:
                    pass
        df_final = df_final[mask]
    
    # =========================================================
    # RESULTADOS E TABELA PRINCIPAL
    # =========================================================
    st.subheader(f"📊 Resultados: {len(df_final)} registros encontrados")
    
    if filtros_ativos or termo_pesquisa:
        st.info(f"🔍 **Filtros ativos:** {len(df_final)} de {total_linhas} registros ({len(df_final)/total_linhas*100:.1f}%)")
    
    # Tabela principal com paginação
    if len(df_final) > 0:
        # Usar a configuração de linhas por página da sidebar
        linhas_por_pagina_atual = linhas_por_pagina
        
        if linhas_por_pagina_atual == "Todas":
            altura_tabela = calcular_altura_tabela(len(df_final), len(df_final.columns))
            st.dataframe(df_final, height=min(altura_tabela, 700), use_container_width=True, hide_index=True)
        else:
            linhas_por_pagina_int = int(linhas_por_pagina_atual)
            total_paginas = (len(df_final) - 1) // linhas_por_pagina_int + 1 if len(df_final) > 0 else 1
            
            # Estado da página atual
            if 'tab3_pagina_atual' not in st.session_state:
                st.session_state.tab3_pagina_atual = 1
            
            # Navegação
            col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([2, 1, 1, 2])
            
            with col_nav1:
                st.write(f"**Página {st.session_state.tab3_pagina_atual} de {total_paginas}**")
            
            with col_nav2:
                if st.session_state.tab3_pagina_atual > 1:
                    if st.button("⬅️ Anterior", key="tab3_anterior", use_container_width=True):
                        st.session_state.tab3_pagina_atual -= 1
                        st.rerun()
            
            with col_nav3:
                if st.session_state.tab3_pagina_atual < total_paginas:
                    if st.button("Próxima ➡️", key="tab3_proxima", use_container_width=True):
                        st.session_state.tab3_pagina_atual += 1
                        st.rerun()
            
            with col_nav4:
                nova_pagina = st.number_input(
                    "Ir para:", 
                    min_value=1, 
                    max_value=total_paginas, 
                    value=st.session_state.tab3_pagina_atual,
                    key="tab3_pagina_input"
                )
                if nova_pagina != st.session_state.tab3_pagina_atual:
                    st.session_state.tab3_pagina_atual = nova_pagina
                    st.rerun()
            
            # Mostrar dados da página atual
            inicio = (st.session_state.tab3_pagina_atual - 1) * linhas_por_pagina_int
            fim = min(inicio + linhas_por_pagina_int, len(df_final))
            
            st.caption(f"Mostrando linhas {inicio + 1} a {fim} de {len(df_final)}")
            altura_pagina = calcular_altura_tabela(linhas_por_pagina_int, len(df_final.columns))
            st.dataframe(
                df_final.iloc[inicio:fim], 
                height=min(altura_pagina, 600), 
                use_container_width=True, 
                hide_index=True
            )
    else:
        st.warning("⚠️ Nenhum registro encontrado com os filtros e pesquisa atuais.")

# =========================================================
# EXPORTAÇÃO (COMPLETA EM MÚLTIPLOS FORMATOS)
# =========================================================
st.header("💾 Exportar Dados (Todos os Formatos)")

df_exportar = df_final if 'df_final' in locals() and (filtros_ativos or termo_pesquisa) else df

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    csv = df_exportar.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(label="📥 Download CSV", data=csv, 
                      file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                      mime="text/csv", use_container_width=True, key="export_csv_global")

with col_exp2:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_exportar.to_excel(writer, index=False, sheet_name='Dados')
    excel_data = output.getvalue()
    st.download_button(label="📥 Download Excel", data=excel_data,
                      file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                      use_container_width=True, key="export_excel_global")

with col_exp3:
    json_data = df_exportar.to_json(orient='records', force_ascii=False, date_format='iso')
    st.download_button(label="📥 Download JSON", data=json_data,
                      file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                      mime="application/json", use_container_width=True, key="export_json_global")

# =========================================================
# DEBUG INFO
# =========================================================
if st.session_state.debug_mode:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🐛 Debug Info:**")
    
    with st.sidebar.expander("Detalhes Técnicos", expanded=False):
        st.write(f"**Cache:** 1 minuto")
        st.write(f"**Hora atual:** {datetime.now().strftime('%H:%M:%S')}")
        st.write(f"**DataFrame Shape:** {df.shape}")
        st.write(f"**Memory:** {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        st.write(f"**Criações:** {criacoes}")
        st.write(f"**Derivações:** {derivacoes}")
        st.write(f"**Extra Contrato:** {extra_contrato}")
        st.write(f"**Campanhas:** {campanhas_unicas}")
        st.write(f"**Filtros ativos:** {len(filtros_ativos) if 'filtros_ativos' in locals() else 0}")
        st.write(f"**Resultados filtrados:** {len(df_final) if 'df_final' in locals() else 0}")
        st.write(f"**Template Plotly:** {plotly_template if 'plotly_template' in locals() else 'N/A'}")

# =========================================================
# RODAPÉ
# =========================================================
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

with footer_col2:
    st.caption(f"📊 {total_linhas} registros | {total_colunas} colunas")

with footer_col3:
    st.markdown("""
    <div style="text-align: right;">
        <span style="color: #003366; font-weight: bold;">SICOOB COCRED</span> | 
        <span style="color: #6C757D;">v4.5.0</span>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# AUTO-REFRESH
# =========================================================
if auto_refresh:
    refresh_placeholder = st.empty()
    for i in range(60, 0, -1):
        refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
        time.sleep(1)
    refresh_placeholder.empty()
    st.rerun()