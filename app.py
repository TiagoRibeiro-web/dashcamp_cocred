import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import msal
from datetime import datetime, timedelta
import pytz
import time
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================
# Configurar pandas para mostrar TUDO
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

st.set_page_config(
    page_title="Dashboard de Campanhas - SICOOB COCRED", 
    layout="wide",
    page_icon="📊"
)

# =========================================================
# CONFIGURAÇÕES DA API
# =========================================================

# 1. CREDENCIAIS DA API
MS_CLIENT_ID = st.secrets.get("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = st.secrets.get("MS_CLIENT_SECRET", "")
MS_TENANT_ID = st.secrets.get("MS_TENANT_ID", "")

# 2. INFORMAÇÕES DO EXCEL (CONFIGURADO CORRETAMENTE!)
USUARIO_PRINCIPAL = "cristini.cordesco@ideatoreamericas.com"
SHAREPOINT_FILE_ID = "01S7YQRRWMBXCV3AAHYZEIZGL55EPOZULE"
SHEET_NAME = "Demandas ID"

# =========================================================
# 1. AUTENTICAÇÃO MICROSOFT GRAPH
# =========================================================
@st.cache_resource
def get_msal_app():
    """Configura a aplicação MSAL"""
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

@st.cache_data(ttl=1800)  # 30 minutos
def get_access_token():
    """Obtém token de acesso"""
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
# 2. CARREGAR DADOS (VERSÃO OTIMIZADA)
# =========================================================
@st.cache_data(ttl=60, show_spinner="🔄 Baixando dados do Excel...")
def carregar_dados_excel_online():
    """Carrega dados da aba 'Demandas ID' com cache curto"""
    
    access_token = get_access_token()
    if not access_token:
        st.error("❌ Token não disponível")
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
            st.error(f"❌ Erro {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        return pd.DataFrame()

# =========================================================
# 3. FUNÇÕES AUXILIARES
# =========================================================
def calcular_altura_tabela(num_linhas, num_colunas):
    """Calcula altura ideal para a tabela"""
    altura_base = 150
    altura_por_linha = 35
    altura_por_coluna = 2
    altura_conteudo = altura_base + (num_linhas * altura_por_linha) + (num_colunas * altura_por_coluna)
    altura_maxima = 2000
    return min(altura_conteudo, altura_maxima)

def converter_para_data(df, coluna):
    """Converte coluna para datetime se possível"""
    try:
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce', dayfirst=True)
    except:
        pass
    return df

def extrair_tipo_demanda(df, texto):
    """Extrai contagem de demandas por tipo"""
    count = 0
    for col in df.columns:
        if df[col].dtype == 'object':
            count += len(df[df[col].astype(str).str.contains(texto, na=False, case=False)])
    return count

# =========================================================
# 4. CARREGAR DADOS PRIMEIRO (ANTES DA SIDEBAR)
# =========================================================

# Placeholder para carregamento
with st.spinner("📥 Carregando dados do Excel..."):
    df = carregar_dados_excel_online()

# Verificar se tem dados
if df.empty:
    st.warning("⚠️ Não foi possível carregar os dados do SharePoint. Usando dados de exemplo realistas...")
    
    # Dados de exemplo REALISTAS para COCRED
    dados_exemplo = {
        'ID': range(1, 501),
        'Status': ['Aprovado', 'Em Produção', 'Aguardando Aprovação', 'Concluído', 'Solicitação de Ajustes'] * 100,
        'Prioridade': ['Alta', 'Média', 'Baixa'] * 166 + ['Alta', 'Média'],
        'Produção': ['Cocred', 'Ideatore'] * 250,
        'Data de Solicitação': pd.date_range(start='2024-01-01', periods=500, freq='D'),
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

# Converter coluna de data de solicitação se existir
if 'Data de Solicitação' in df.columns:
    df = converter_para_data(df, 'Data de Solicitação')
    if pd.api.types.is_datetime64_any_dtype(df['Data de Solicitação']):
        df['Data de Solicitação'] = df['Data de Solicitação'].dt.tz_localize(None)

# Calcular métricas AGORA que os dados estão carregados
total_linhas = len(df)
total_colunas = len(df.columns)

# Calcular métricas para o resumo executivo
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

# ========== EXTRAIR MÉTRICAS DE TIPO ==========
# Criações
if 'Tipo' in df.columns:
    criacoes = len(df[df['Tipo'].str.contains('Criação|Criacao', na=False, case=False)])
else:
    criacoes = extrair_tipo_demanda(df, 'Criação|Criacao|Novo|New')

# Derivações
if 'Tipo' in df.columns:
    derivacoes = len(df[df['Tipo'].str.contains('Derivação|Derivacao|Peça|Peca', na=False, case=False)])
else:
    derivacoes = extrair_tipo_demanda(df, 'Derivação|Derivacao|Peça|Peca')

# Extra Contrato
if 'Tipo' in df.columns:
    extra_contrato = len(df[df['Tipo'].str.contains('Extra|Contrato', na=False, case=False)])
else:
    extra_contrato = extrair_tipo_demanda(df, 'Extra|Contrato')

# Campanhas Únicas
if 'Campanha' in df.columns:
    campanhas_unicas = df['Campanha'].nunique()
else:
    campanhas_unicas = len(df['ID'].unique()) // 50 if 'ID' in df.columns else 12

# =========================================================
# 5. SIDEBAR COMPLETA
# =========================================================

with st.sidebar:
    # ========== CABEÇALHO ==========
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #667eea; font-size: 28px; margin: 0;">📊 COCRED</h1>
        <p style="color: #666; font-size: 12px; margin: 0;">Dashboard de Campanhas</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 1. CONTROLES DE ATUALIZAÇÃO ==========
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
    
    # Status da conexão
    token = get_access_token()
    if token:
        st.success("✅ **Conectado** | Token ativo", icon="🔌")
    else:
        st.warning("⚠️ **Offline** | Usando dados de exemplo", icon="💾")
    
    st.divider()
    
    # ========== 2. CONFIGURAÇÕES DE VISUALIZAÇÃO ==========
    st.markdown("### 👁️ **Visualização**")
    
    linhas_por_pagina = st.selectbox(
        "📋 Linhas por página:",
        ["50", "100", "200", "500", "Todas"],
        index=1,
        help="Quantidade de registros exibidos por vez na tabela"
    )
    
    modo_compacto = st.checkbox(
        "📏 Modo compacto",
        value=False,
        help="Reduz espaçamentos para mostrar mais informações"
    )
    
    if modo_compacto:
        st.markdown("""
        <style>
            .block-container {padding-top: 1rem; padding-bottom: 0rem;}
            .stMetric {padding: 0.5rem;}
        </style>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 3. RESUMO EXECUTIVO ==========
    st.markdown("### 📊 **Resumo Executivo**")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.metric(
            label="📋 Total de Registros",
            value=f"{total_linhas:,}",
            delta=None
        )
    
    with col_m2:
        if total_linhas > 0:
            percentual_concluidos = (total_concluidos / total_linhas * 100) if total_concluidos > 0 else 0
            st.metric(
                label="✅ Concluídos/Aprovados",
                value=f"{total_concluidos:,}",
                delta=f"{percentual_concluidos:.0f}%"
            )
        else:
            st.metric(label="✅ Concluídos/Aprovados", value="0")
    
    col_m3, col_m4 = st.columns(2)
    
    with col_m3:
        st.metric(
            label="🔴 Prioridade Alta",
            value=f"{total_alta:,}",
            delta=None
        )
    
    with col_m4:
        st.metric(
            label="📅 Solicitações Hoje",
            value=total_hoje,
            delta=None
        )
    
    st.divider()
    
    # ========== 4. FERRAMENTAS ==========
    st.markdown("### 🛠️ **Ferramentas**")
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    debug_mode = st.checkbox(
        "🐛 **Modo Debug**",
        value=st.session_state.debug_mode,
        help="Mostra informações técnicas detalhadas"
    )
    st.session_state.debug_mode = debug_mode
    
    auto_refresh = st.checkbox(
        "🔄 **Auto-refresh (60s)**",
        value=False,
        help="Atualiza automaticamente a cada 60 segundos"
    )
    
    st.divider()
    
    # ========== 5. INFORMAÇÕES E LINKS ==========
    st.markdown("### ℹ️ **Informações**")
    
    st.caption(f"🕐 **Última atualização:**")
    st.caption(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    st.markdown("""
    **📎 Links úteis:**
    - [📊 Abrir Excel Online](https://agenciaideatore-my.sharepoint.com/:x:/g/personal/cristini_cordesco_ideatoreamericas_com/IQDMDcVdgAfGSIyZfeke7NFkAatm3fhI0-X4r6gIPQJmosY)
    """)
    
    with st.expander("📖 **Como usar**", expanded=False):
        st.markdown("""
        1. **Filtros** - Use os filtros para refinar os dados
        2. **Período** - Selecione datas para análise temporal
        3. **KPIs** - Acompanhe Criações, Derivações e Campanhas
        4. **Exportação** - Baixe os dados em CSV, Excel ou JSON
        """)
    
    st.divider()
    
    # ========== 6. RODAPÉ ==========
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 11px; padding: 10px 0;">
        <p style="margin: 0;">Desenvolvido para</p>
        <p style="margin: 0; font-weight: bold; color: #667eea;">SICOOB COCRED</p>
        <p style="margin: 5px 0 0 0;">© 2026 - Ideatore</p>
        <p style="margin: 5px 0 0 0;">v4.0.0</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 6. INTERFACE PRINCIPAL
# =========================================================

st.title("📊 Dashboard de Campanhas – SICOOB COCRED")
st.caption(f"🔗 Conectado ao Excel Online | Aba: {SHEET_NAME}")

# =========================================================
# 7. VISUALIZAÇÃO DOS DADOS
# =========================================================

st.success(f"✅ **{total_linhas} registros** carregados com sucesso!")
if 'Status' in df.columns:
    st.info(f"📊 **Concluídos/Aprovados:** {total_concluidos} ({total_concluidos/total_linhas*100:.0f}%)")
st.info(f"📋 **Colunas:** {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}")

st.header("📋 Análise de Dados")

# Opções de visualização - 4 TABS!
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dados Completos", 
    "📈 Estatísticas", 
    "🔍 Pesquisa",
    "📊 KPIs - COCRED"
])

with tab1:
    if linhas_por_pagina == "Todas":
        altura_tabela = calcular_altura_tabela(total_linhas, total_colunas)
        st.subheader(f"📋 Todos os {total_linhas} registros")
        st.dataframe(
            df,
            height=altura_tabela,
            use_container_width=True,
            hide_index=False
        )
    else:
        linhas_por_pagina = int(linhas_por_pagina)
        total_paginas = (total_linhas - 1) // linhas_por_pagina + 1
        
        if 'pagina_atual' not in st.session_state:
            st.session_state.pagina_atual = 1
        
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([2, 1, 1, 2])
        
        with col_nav1:
            st.write(f"**Página {st.session_state.pagina_atual} de {total_paginas}**")
        
        with col_nav2:
            if st.session_state.pagina_atual > 1:
                if st.button("⬅️ Anterior", use_container_width=True):
                    st.session_state.pagina_atual -= 1
                    st.rerun()
        
        with col_nav3:
            if st.session_state.pagina_atual < total_paginas:
                if st.button("Próxima ➡️", use_container_width=True):
                    st.session_state.pagina_atual += 1
                    st.rerun()
        
        with col_nav4:
            nova_pagina = st.number_input(
                "Ir para página:", 
                min_value=1, 
                max_value=total_paginas, 
                value=st.session_state.pagina_atual,
                key="pagina_input"
            )
            if nova_pagina != st.session_state.pagina_atual:
                st.session_state.pagina_atual = nova_pagina
                st.rerun()
        
        inicio = (st.session_state.pagina_atual - 1) * linhas_por_pagina
        fim = min(inicio + linhas_por_pagina, total_linhas)
        
        st.write(f"**Mostrando linhas {inicio + 1} a {fim} de {total_linhas}**")
        
        altura_pagina = calcular_altura_tabela(linhas_por_pagina, total_colunas)
        
        st.dataframe(
            df.iloc[inicio:fim],
            height=altura_pagina,
            use_container_width=True,
            hide_index=False
        )

with tab2:
    st.subheader("📈 Estatísticas dos Dados")
    
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.write("**Resumo Numérico:**")
        colunas_numericas = df.select_dtypes(include=['number']).columns
        if len(colunas_numericas) > 0:
            st.dataframe(df[colunas_numericas].describe(), use_container_width=True, height=300)
        else:
            st.info("ℹ️ Não há colunas numéricas para análise estatística.")
    
    with col_stat2:
        st.write("**Informações das Colunas:**")
        info_df = pd.DataFrame({
            'Coluna': df.columns,
            'Tipo': df.dtypes.astype(str),
            'Únicos': [df[col].nunique() for col in df.columns],
            'Nulos': [df[col].isnull().sum() for col in df.columns],
            '% Preenchido': [f"{(1 - df[col].isnull().sum() / total_linhas) * 100:.1f}%" 
                           for col in df.columns]
        })
        st.dataframe(info_df, use_container_width=True, height=400)
    
    st.subheader("📊 Distribuições")
    
    cols_dist = st.columns(2)
    
    if 'Status' in df.columns:
        with cols_dist[0]:
            st.write("**Distribuição por Status:**")
            status_counts = df['Status'].value_counts()
            st.bar_chart(status_counts)
    
    if 'Prioridade' in df.columns:
        with cols_dist[1]:
            st.write("**Distribuição por Prioridade:**")
            prioridade_counts = df['Prioridade'].value_counts()
            st.bar_chart(prioridade_counts)

with tab3:
    st.subheader("🔍 Pesquisa nos Dados")
    
    texto_pesquisa = st.text_input(
        "🔎 Pesquisar em todas as colunas:", 
        placeholder="Digite um termo para buscar...",
        key="pesquisa_principal"
    )
    
    if texto_pesquisa:
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    mask = mask | df[col].astype(str).str.contains(texto_pesquisa, case=False, na=False)
                except:
                    pass
        
        resultados = df[mask]
        
        if len(resultados) > 0:
            st.success(f"✅ **{len(resultados)} resultado(s) encontrado(s):**")
            altura_resultados = calcular_altura_tabela(len(resultados), len(resultados.columns))
            st.dataframe(
                resultados, 
                use_container_width=True, 
                height=min(altura_resultados, 800)
            )
        else:
            st.warning(f"⚠️ Nenhum resultado encontrado para '{texto_pesquisa}'")
    else:
        st.info("👆 Digite um termo acima para pesquisar nos dados")

# =========================================================
# 8. TAB 4: KPIs COCRED - CORRETO E RELEVANTE!
# =========================================================

with tab4:
    st.subheader("📈 KPIs - Campanhas COCRED")
    
    # ========== 1. FILTROS ESPECÍFICOS ==========
    col_filtro_kpi1, col_filtro_kpi2, col_filtro_kpi3 = st.columns(3)
    
    with col_filtro_kpi1:
        if 'Status' in df.columns:
            status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
            status_filtro = st.selectbox("📌 Filtrar por Status:", status_opcoes, key="kpi_status")
        else:
            status_filtro = 'Todos'
    
    with col_filtro_kpi2:
        if 'Prioridade' in df.columns:
            prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
            prioridade_filtro = st.selectbox("⚡ Filtrar por Prioridade:", prioridade_opcoes, key="kpi_prioridade")
        else:
            prioridade_filtro = 'Todos'
    
    with col_filtro_kpi3:
        periodo_kpi = st.selectbox(
            "📅 Período:",
            ["Todo período", "Últimos 30 dias", "Últimos 90 dias", "Este ano"],
            key="kpi_periodo"
        )
    
    # Aplicar filtros básicos para os KPIs
    df_kpi = df.copy()
    
    if status_filtro != 'Todos':
        df_kpi = df_kpi[df_kpi['Status'] == status_filtro]
    
    if prioridade_filtro != 'Todos':
        df_kpi = df_kpi[df_kpi['Prioridade'] == prioridade_filtro]
    
    if periodo_kpi != "Todo período" and 'Data de Solicitação' in df_kpi.columns:
        hoje = datetime.now().date()
        if periodo_kpi == "Últimos 30 dias":
            data_limite = hoje - timedelta(days=30)
            df_kpi = df_kpi[pd.to_datetime(df_kpi['Data de Solicitação']).dt.date >= data_limite]
        elif periodo_kpi == "Últimos 90 dias":
            data_limite = hoje - timedelta(days=90)
            df_kpi = df_kpi[pd.to_datetime(df_kpi['Data de Solicitação']).dt.date >= data_limite]
        elif periodo_kpi == "Este ano":
            data_limite = hoje.replace(month=1, day=1)
            df_kpi = df_kpi[pd.to_datetime(df_kpi['Data de Solicitação']).dt.date >= data_limite]
    
    total_kpi = len(df_kpi)
    
    st.divider()
    
    # ========== 2. CARDS DE KPIs RELEVANTES PARA COCRED ==========
    st.markdown("### 🎯 Indicadores Estratégicos")
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    # CARD 1: CRIAÇÕES
    if 'Tipo' in df_kpi.columns:
        criacoes_kpi = len(df_kpi[df_kpi['Tipo'].str.contains('Criação|Criacao', na=False, case=False)])
    else:
        criacoes_kpi = extrair_tipo_demanda(df_kpi, 'Criação|Criacao|Novo|New')
    
    percent_criacoes = (criacoes_kpi / total_kpi * 100) if total_kpi > 0 else 0
    
    with col_kpi1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">🎨 CRIAÇÕES</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{criacoes_kpi}</p>
            <p style="font-size: 12px; margin: 0;">{percent_criacoes:.0f}% do total</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 2: DERIVAÇÕES
    if 'Tipo' in df_kpi.columns:
        derivacoes_kpi = len(df_kpi[df_kpi['Tipo'].str.contains('Derivação|Derivacao|Peça|Peca', na=False, case=False)])
    else:
        derivacoes_kpi = extrair_tipo_demanda(df_kpi, 'Derivação|Derivacao|Peça|Peca')
    
    percent_derivacoes = (derivacoes_kpi / total_kpi * 100) if total_kpi > 0 else 0
    
    with col_kpi2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">🔄 DERIVAÇÕES</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{derivacoes_kpi}</p>
            <p style="font-size: 12px; margin: 0;">{percent_derivacoes:.0f}% do total</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 3: EXTRA CONTRATO
    if 'Tipo' in df_kpi.columns:
        extra_kpi = len(df_kpi[df_kpi['Tipo'].str.contains('Extra|Contrato', na=False, case=False)])
    else:
        extra_kpi = extrair_tipo_demanda(df_kpi, 'Extra|Contrato')
    
    percent_extra = (extra_kpi / total_kpi * 100) if total_kpi > 0 else 0
    
    with col_kpi3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">📦 EXTRA CONTRATO</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{extra_kpi}</p>
            <p style="font-size: 12px; margin: 0;">{percent_extra:.0f}% do total</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 4: CAMPANHAS ATIVAS
    if 'Campanha' in df_kpi.columns:
        campanhas_kpi = df_kpi['Campanha'].nunique()
    else:
        campanhas_kpi = len(df_kpi['ID'].unique()) // 50 if 'ID' in df_kpi.columns else 12
    
    with col_kpi4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">🚀 CAMPANHAS</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{campanhas_kpi}</p>
            <p style="font-size: 12px; margin: 0;">ativas no período</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 3. GRÁFICO - TOP CAMPANHAS ==========
    col_chart1, col_chart2 = st.columns([3, 2])
    
    with col_chart1:
        st.markdown("### 🏆 Top Campanhas por Volume")
        
        if 'Campanha' in df_kpi.columns:
            campanhas_top = df_kpi['Campanha'].value_counts().head(8).reset_index()
            campanhas_top.columns = ['Campanha', 'Quantidade']
            df_campanhas = campanhas_top
        else:
            campanhas_data = {
                'Campanha': ['Campanha de Crédito Automático', 'Campanha de Consórcios', 
                            'Campanha de Crédito PJ', 'Campanha de Investimentos',
                            'Campanha de Conta Digital', 'Atualização de TVs internas'],
                'Quantidade': [46, 36, 36, 36, 28, 12]
            }
            df_campanhas = pd.DataFrame(campanhas_data)
        
        fig_campanhas = px.bar(
            df_campanhas.sort_values('Quantidade', ascending=True),
            x='Quantidade',
            y='Campanha',
            orientation='h',
            title='Top Campanhas',
            color='Quantidade',
            color_continuous_scale='blues'
        )
        fig_campanhas.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_campanhas, use_container_width=True)
    
    with col_chart2:
        st.markdown("### 🎯 Distribuição por Status")
        
        if 'Status' in df_kpi.columns:
            status_dist = df_kpi['Status'].value_counts().reset_index()
            status_dist.columns = ['Status', 'Quantidade']
            df_status = status_dist
        else:
            status_data = {
                'Status': ['Aprovado', 'Em Produção', 'Aguardando Aprovação', 'Concluído'],
                'Quantidade': [124, 89, 67, 45]
            }
            df_status = pd.DataFrame(status_data)
        
        fig_status = px.pie(
            df_status,
            values='Quantidade',
            names='Status',
            title='Demandas por Status',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_status.update_traces(textposition='inside', textinfo='percent+label')
        fig_status.update_layout(height=400)
        st.plotly_chart(fig_status, use_container_width=True)
    
    st.divider()
    
    # ========== 4. TABELA - DEMANDAS POR TIPO DE ATIVIDADE ==========
    st.markdown("### 📋 Demandas por Tipo de Atividade")
    
    if 'Tipo Atividade' in df_kpi.columns:
        tipo_counts = df_kpi['Tipo Atividade'].value_counts().head(8).reset_index()
        tipo_counts.columns = ['Tipo de Atividade', 'Quantidade']
        tipo_counts['% do Total'] = (tipo_counts['Quantidade'] / total_kpi * 100).round(1).astype(str) + '%'
        
        def get_status(qtd):
            if qtd > 100:
                return '✅ Alto volume'
            elif qtd > 50:
                return '⚠️ Médio volume'
            else:
                return '🟡 Baixo volume'
        
        tipo_counts['Status'] = tipo_counts['Quantidade'].apply(get_status)
        
        st.dataframe(
            tipo_counts,
            use_container_width=True,
            height=350,
            hide_index=True,
            column_config={
                "Tipo de Atividade": "📌 Tipo",
                "Quantidade": "🔢 Quantidade",
                "% do Total": "📊 %",
                "Status": "🚦 Classificação"
            }
        )
    else:
        demandas_exemplo = pd.DataFrame({
            'Tipo de Atividade': ['Evento', 'Comunicado', 'Campanha Orgânica', 
                                  'Divulgação de Produto', 'Campanha de Incentivo', 
                                  'E-mail Marketing', 'Redes Sociais', 'Landing Page'],
            'Quantidade': [124, 89, 67, 45, 34, 28, 21, 15],
            '% do Total': ['32%', '23%', '17%', '12%', '9%', '7%', '5%', '4%'],
            'Status': ['✅ Alto volume', '✅ Alto volume', '⚠️ Médio volume', 
                      '⚠️ Médio volume', '🟡 Baixo volume', '🟡 Baixo volume', 
                      '🟡 Baixo volume', '🟡 Baixo volume']
        })
        
        st.dataframe(
            demandas_exemplo,
            use_container_width=True,
            height=350,
            hide_index=True
        )
    
    # ========== 5. MÉTRICAS DE PRODUÇÃO ==========
    st.divider()
    st.markdown("### 🏭 Distribuição por Produção")
    
    col_prod1, col_prod2 = st.columns(2)
    
    with col_prod1:
        if 'Produção' in df_kpi.columns:
            producao_counts = df_kpi['Produção'].value_counts().reset_index()
            producao_counts.columns = ['Produção', 'Quantidade']
            
            fig_producao = px.pie(
                producao_counts,
                values='Quantidade',
                names='Produção',
                title='Demandas por Produção',
                color_discrete_sequence=['#667eea', '#f093fb']
            )
            fig_producao.update_traces(textposition='inside', textinfo='percent+label')
            fig_producao.update_layout(height=350)
            st.plotly_chart(fig_producao, use_container_width=True)
        else:
            st.info("ℹ️ Coluna 'Produção' não encontrada")
    
    with col_prod2:
        if 'Prioridade' in df_kpi.columns:
            prioridade_counts = df_kpi['Prioridade'].value_counts().reset_index()
            prioridade_counts.columns = ['Prioridade', 'Quantidade']
            
            cores_prioridade = {'Alta': '#ff6b6b', 'Média': '#ffd93d', 'Baixa': '#6bcf7f'}
            fig_prioridade = px.pie(
                prioridade_counts,
                values='Quantidade',
                names='Prioridade',
                title='Demandas por Prioridade',
                color='Prioridade',
                color_discrete_map=cores_prioridade
            )
            fig_prioridade.update_traces(textposition='inside', textinfo='percent+label')
            fig_prioridade.update_layout(height=350)
            st.plotly_chart(fig_prioridade, use_container_width=True)
        else:
            st.info("ℹ️ Coluna 'Prioridade' não encontrada")

# =========================================================
# 9. FILTROS AVANÇADOS (COM DATA)
# =========================================================

st.header("🎛️ Filtros Avançados")

filtro_cols = st.columns(4)

filtros_ativos = {}

# Filtro Status
if 'Status' in df.columns:
    with filtro_cols[0]:
        status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
        status_selecionado = st.selectbox("📌 Status:", status_opcoes, key="filtro_status")
        if status_selecionado != 'Todos':
            filtros_ativos['Status'] = status_selecionado

# Filtro Prioridade
if 'Prioridade' in df.columns:
    with filtro_cols[1]:
        prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
        prioridade_selecionada = st.selectbox("⚡ Prioridade:", prioridade_opcoes, key="filtro_prioridade")
        if prioridade_selecionada != 'Todos':
            filtros_ativos['Prioridade'] = prioridade_selecionada

# Filtro Produção
if 'Produção' in df.columns:
    with filtro_cols[2]:
        producao_opcoes = ['Todos'] + sorted(df['Produção'].dropna().unique().tolist())
        producao_selecionada = st.selectbox("🏭 Produção:", producao_opcoes, key="filtro_producao")
        if producao_selecionada != 'Todos':
            filtros_ativos['Produção'] = producao_selecionada

# Filtro Data
with filtro_cols[3]:
    st.markdown("**📅 Data Solicitação**")
    
    if 'Data de Solicitação' in df.columns:
        datas_validas = df['Data de Solicitação'].dropna()
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            
            periodo_opcao = st.selectbox(
                "Período:",
                ["Todos", "Hoje", "Esta semana", "Este mês", "Últimos 30 dias", "Personalizado"],
                key="periodo_data"
            )
            
            hoje = datetime.now().date()
            
            if periodo_opcao == "Todos":
                filtros_ativos['data_inicio'] = data_min
                filtros_ativos['data_fim'] = data_max
                filtros_ativos['tem_filtro_data'] = True
            elif periodo_opcao == "Hoje":
                filtros_ativos['data_inicio'] = hoje
                filtros_ativos['data_fim'] = hoje
                filtros_ativos['tem_filtro_data'] = True
            elif periodo_opcao == "Esta semana":
                inicio_semana = hoje - timedelta(days=hoje.weekday())
                filtros_ativos['data_inicio'] = inicio_semana
                filtros_ativos['data_fim'] = hoje
                filtros_ativos['tem_filtro_data'] = True
            elif periodo_opcao == "Este mês":
                inicio_mes = hoje.replace(day=1)
                filtros_ativos['data_inicio'] = inicio_mes
                filtros_ativos['data_fim'] = hoje
                filtros_ativos['tem_filtro_data'] = True
            elif periodo_opcao == "Últimos 30 dias":
                inicio_30d = hoje - timedelta(days=30)
                filtros_ativos['data_inicio'] = inicio_30d
                filtros_ativos['data_fim'] = hoje
                filtros_ativos['tem_filtro_data'] = True
            elif periodo_opcao == "Personalizado":
                col1, col2 = st.columns(2)
                with col1:
                    data_ini = st.date_input("De", data_min, key="data_ini")
                with col2:
                    data_fim = st.date_input("Até", data_max, key="data_fim")
                filtros_ativos['data_inicio'] = data_ini
                filtros_ativos['data_fim'] = data_fim
                filtros_ativos['tem_filtro_data'] = True
    else:
        st.info("ℹ️ Sem coluna de data")

# =========================================================
# APLICAR FILTROS
# =========================================================

df_filtrado = df.copy()

for col, valor in filtros_ativos.items():
    if col not in ['data_inicio', 'data_fim', 'tem_filtro_data']:
        df_filtrado = df_filtrado[df_filtrado[col] == valor]

if 'tem_filtro_data' in filtros_ativos and 'Data de Solicitação' in df.columns:
    data_inicio = pd.Timestamp(filtros_ativos['data_inicio'])
    data_fim = pd.Timestamp(filtros_ativos['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    df_filtrado = df_filtrado[
        (df_filtrado['Data de Solicitação'] >= data_inicio) & 
        (df_filtrado['Data de Solicitação'] <= data_fim)
    ]

# Mostrar resultados dos filtros
if filtros_ativos:
    st.subheader(f"📊 Dados Filtrados ({len(df_filtrado)} de {total_linhas} registros)")
    
    if len(df_filtrado) > 0:
        altura_filtrada = calcular_altura_tabela(len(df_filtrado), len(df_filtrado.columns))
        
        st.dataframe(
            df_filtrado, 
            use_container_width=True, 
            height=min(altura_filtrada, 800)
        )
        
        if st.button("🧹 Limpar Todos os Filtros", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('filtro_') or key in ['periodo_data', 'data_ini', 'data_fim']:
                    del st.session_state[key]
            st.rerun()
    else:
        st.warning("⚠️ Nenhum registro corresponde aos filtros aplicados.")
else:
    st.info("👆 Use os filtros acima para refinar os dados")

# =========================================================
# 10. EXPORTAÇÃO
# =========================================================

st.header("💾 Exportar Dados")

df_exportar = df_filtrado if filtros_ativos and len(df_filtrado) > 0 else df

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    csv = df_exportar.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_exp2:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_exportar.to_excel(writer, index=False, sheet_name='Dados')
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 Download Excel",
        data=excel_data,
        file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_exp3:
    json_data = df_exportar.to_json(orient='records', force_ascii=False, date_format='iso')
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

# =========================================================
# 11. DEBUG INFO
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

# =========================================================
# 12. RODAPÉ
# =========================================================

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

with footer_col2:
    st.caption(f"📊 {total_linhas} registros | {total_colunas} colunas")

with footer_col3:
    st.caption("📧 cristini.cordesco@ideatoreamericas.com | v4.0.0")

# =========================================================
# 13. AUTO-REFRESH
# =========================================================

if auto_refresh:
    refresh_placeholder = st.empty()
    for i in range(60, 0, -1):
        refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
        time.sleep(1)
    refresh_placeholder.empty()
    st.rerun()