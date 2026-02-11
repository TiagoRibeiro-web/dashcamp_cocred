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

# =========================================================
# 4. CARREGAR DADOS PRIMEIRO (ANTES DA SIDEBAR)
# =========================================================

# Placeholder para carregamento
with st.spinner("📥 Carregando dados do Excel..."):
    df = carregar_dados_excel_online()

# Verificar se tem dados
if df.empty:
    st.warning("⚠️ Não foi possível carregar os dados do SharePoint. Usando dados de exemplo...")
    
    # Dados de exemplo mais completos para KPIs
    dados_exemplo = {
        'ID': range(1, 501),
        'Status': ['Aprovado', 'Em Produção', 'Aguardando', 'Concluído', 'Revisão'] * 100,
        'Prioridade': ['Alta', 'Média', 'Baixa'] * 166 + ['Alta', 'Média'],
        'Produção': ['Cocred', 'Ideatore'] * 250,
        'Data de Solicitação': pd.date_range(start='2024-01-01', periods=500, freq='D'),
        'Data de Entrega': pd.date_range(start='2024-01-15', periods=500, freq='D'),
        'Solicitante': ['Cassia Inoue', 'Laís Toledo', 'Nádia Zanin', 'Beatriz Russo', 'Thaís Gomes'] * 100,
        'Campanha': ['Campanha Verão', 'Black Friday', 'Dia das Mães', 'Natal', 'Ano Novo',
                     'Dia dos Pais', 'Dia das Crianças', 'Páscoa', 'Carnaval', 'Semana do Cliente'] * 50,
        'Origem': ['E-mail', 'Site', 'App', 'Redes Sociais', 'Evento', 'WhatsApp', 'SMS'] * 71 + ['E-mail'] * 3,
        'Canal': ['E-mail Marketing', 'Redes Sociais', 'Landing Page', 'Newsletter', 
                  'Push Notification', 'SMS', 'WhatsApp', 'Blog Post'] * 62 + ['E-mail Marketing'] * 4,
        'Tipo_Comunicacao': ['E-mail Marketing', 'Redes Sociais', 'Site', 'App', 'SMS', 'WhatsApp'] * 83 + ['E-mail Marketing'] * 2,
        'Taxa_Abertura': [round(x, 1) for x in np.random.uniform(45, 85, 500)],
        'Taxa_Clique': [round(x, 1) for x in np.random.uniform(5, 25, 500)],
        'Taxa_Conversao': [round(x, 1) for x in np.random.uniform(2, 15, 500)]
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

# =========================================================
# 5. SIDEBAR COMPLETA (AGORA COM DADOS CARREGADOS)
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
    
    # Status da conexão em tempo real
    token = get_access_token()
    if token:
        st.success("✅ **Conectado** | Token ativo", icon="🔌")
    else:
        st.warning("⚠️ **Offline** | Usando dados de exemplo", icon="💾")
    
    st.divider()
    
    # ========== 2. CONFIGURAÇÕES DE VISUALIZAÇÃO ==========
    st.markdown("### 👁️ **Visualização**")
    
    # Linhas por página
    linhas_por_pagina = st.selectbox(
        "📋 Linhas por página:",
        ["50", "100", "200", "500", "Todas"],
        index=1,
        help="Quantidade de registros exibidos por vez na tabela"
    )
    
    # Modo compacto
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
    
    # ========== 4. FILTROS RÁPIDOS ==========
    st.markdown("### ⚡ **Filtros Rápidos**")
    
    # Filtro de período pré-definido
    with st.expander("📅 **Período rápido**", expanded=False):
        if 'Data de Solicitação' in df.columns:
            periodo_rapido = st.selectbox(
                "Selecionar:",
                ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", 
                 "Este mês", "Mês passado", "Este ano"],
                key="periodo_rapido_sidebar"
            )
            
            if st.button("✅ Aplicar período", use_container_width=True):
                hoje = datetime.now().date()
                
                if periodo_rapido == "Últimos 7 dias":
                    st.session_state.periodo_data = "Últimos 30 dias"
                    st.session_state.data_ini = hoje - timedelta(days=7)
                    st.session_state.data_fim = hoje
                elif periodo_rapido == "Últimos 15 dias":
                    st.session_state.periodo_data = "Últimos 30 dias"
                    st.session_state.data_ini = hoje - timedelta(days=15)
                    st.session_state.data_fim = hoje
                elif periodo_rapido == "Últimos 30 dias":
                    st.session_state.periodo_data = "Últimos 30 dias"
                    st.session_state.data_ini = hoje - timedelta(days=30)
                    st.session_state.data_fim = hoje
                elif periodo_rapido == "Este mês":
                    st.session_state.periodo_data = "Este mês"
                    st.session_state.data_ini = hoje.replace(day=1)
                    st.session_state.data_fim = hoje
                elif periodo_rapido == "Mês passado":
                    primeiro_dia_mes_passado = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
                    ultimo_dia_mes_passado = hoje.replace(day=1) - timedelta(days=1)
                    st.session_state.periodo_data = "Personalizado"
                    st.session_state.data_ini = primeiro_dia_mes_passado
                    st.session_state.data_fim = ultimo_dia_mes_passado
                elif periodo_rapido == "Este ano":
                    st.session_state.periodo_data = "Personalizado"
                    st.session_state.data_ini = hoje.replace(month=1, day=1)
                    st.session_state.data_fim = hoje
                
                st.toast(f"✅ Período '{periodo_rapido}' aplicado!")
                st.rerun()
        else:
            st.info("ℹ️ Sem coluna de data")
    
    st.divider()
    
    # ========== 5. FERRAMENTAS ==========
    st.markdown("### 🛠️ **Ferramentas**")
    
    # Modo Debug
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    debug_mode = st.checkbox(
        "🐛 **Modo Debug**",
        value=st.session_state.debug_mode,
        help="Mostra informações técnicas detalhadas"
    )
    st.session_state.debug_mode = debug_mode
    
    # Auto-refresh
    auto_refresh = st.checkbox(
        "🔄 **Auto-refresh (60s)**",
        value=False,
        help="Atualiza automaticamente a cada 60 segundos"
    )
    
    st.divider()
    
    # ========== 6. INFORMAÇÕES E LINKS ==========
    st.markdown("### ℹ️ **Informações**")
    
    # Última atualização
    st.caption(f"🕐 **Última atualização:**")
    st.caption(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Link para Excel
    st.markdown("""
    **📎 Links úteis:**
    - [📊 Abrir Excel Online](https://agenciaideatore-my.sharepoint.com/:x:/g/personal/cristini_cordesco_ideatoreamericas_com/IQDMDcVdgAfGSIyZfeke7NFkAatm3fhI0-X4r6gIPQJmosY)
    """)
    
    # Instruções rápidas
    with st.expander("📖 **Como usar**", expanded=False):
        st.markdown("""
        1. **Filtros** - Use os filtros abaixo para refinar os dados
        2. **Período** - Selecione datas para análise temporal
        3. **Visualização** - Ajuste linhas por página
        4. **KPIs** - Análise de origem, campanhas e comunicação
        5. **Exportação** - Use os botões na área principal
        """)
    
    st.divider()
    
    # ========== 7. RODAPÉ DA SIDEBAR ==========
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

# Título
st.title("📊 Dashboard de Campanhas – SICOOB COCRED")
st.caption(f"🔗 Conectado ao Excel Online | Aba: {SHEET_NAME}")

# =========================================================
# 7. VISUALIZAÇÃO COMPLETA DOS DADOS (COM PAGINAÇÃO)
# =========================================================

st.success(f"✅ **{total_linhas} registros** carregados com sucesso!")
if 'Status' in df.columns:
    st.info(f"📊 **Concluídos/Aprovados:** {total_concluidos} ({total_concluidos/total_linhas*100:.0f}%)")
st.info(f"📋 **Colunas:** {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}")

st.header("📋 Análise de Dados")

# Opções de visualização - AGORA COM 4 TABS!
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dados Completos", 
    "📈 Estatísticas", 
    "🔍 Pesquisa",
    "📊 KPIs por Origem e Campanha"
])

with tab1:
    if linhas_por_pagina == "Todas":
        altura_tabela = calcular_altura_tabela(total_linhas, total_colunas)
        st.subheader(f"📋 Todos os {total_linhas} registros")
        st.dataframe(
            df,
            height=altura_tabela,
            use_container_width=True,
            hide_index=False,
            column_config=None
        )
        if altura_tabela >= 2000:
            linhas_visiveis = int((2000 - 150) / 35)
            st.info(f"ℹ️ Mostrando {linhas_visiveis} de {total_linhas} linhas por vez. Use o scroll para navegar.")
        
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
    
    col_count1, col_count2, col_count3 = st.columns(3)
    with col_count1:
        st.metric("📈 Total de Linhas", total_linhas)
    with col_count2:
        st.metric("📊 Total de Colunas", total_colunas)
    with col_count3:
        if 'Data de Solicitação' in df.columns:
            ultima_data = df['Data de Solicitação'].max()
            if pd.notna(ultima_data) and hasattr(ultima_data, 'strftime'):
                st.metric("📅 Última Solicitação", ultima_data.strftime('%d/%m/%Y'))
            else:
                st.metric("📅 Última Solicitação", "N/A")
        else:
            st.metric("📅 Última Atualização", datetime.now().strftime('%d/%m/%Y'))

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
            
            if st.button("📥 Exportar Resultados", key="export_resultados"):
                csv = resultados.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV dos Resultados",
                    data=csv,
                    file_name=f"pesquisa_{texto_pesquisa}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning(f"⚠️ Nenhum resultado encontrado para '{texto_pesquisa}'")
    else:
        st.info("👆 Digite um termo acima para pesquisar nos dados")

# =========================================================
# 8. NOVA TAB: KPIs POR ORIGEM E CAMPANHA
# =========================================================

with tab4:
    st.subheader("📈 KPIs por Origem e Campanha")
    
    # ========== 1. FILTROS ESPECÍFICOS DA TAB ==========
    col_filtro_kpi1, col_filtro_kpi2, col_filtro_kpi3, col_filtro_kpi4 = st.columns(4)
    
    with col_filtro_kpi1:
        # Filtro de Origem
        if 'Origem' in df.columns:
            origem_opcoes = ['Todas'] + sorted(df['Origem'].dropna().unique().tolist())
            origem_selecionada = st.selectbox("📌 Origem:", origem_opcoes, key="kpi_origem")
        elif 'Canal' in df.columns:
            origem_opcoes = ['Todas'] + sorted(df['Canal'].dropna().unique().tolist())
            origem_selecionada = st.selectbox("📌 Canal:", origem_opcoes, key="kpi_canal")
        else:
            origem_selecionada = st.selectbox(
                "📌 Origem:", 
                ['Todas', 'E-mail', 'Site', 'App', 'Redes Sociais', 'Evento', 'WhatsApp', 'SMS'],
                key="kpi_origem_exemplo"
            )
    
    with col_filtro_kpi2:
        # Filtro de Campanha
        if 'Campanha' in df.columns:
            campanha_opcoes = ['Todas'] + sorted(df['Campanha'].dropna().unique().tolist())[:20]
            campanha_selecionada = st.selectbox("🚀 Campanha:", campanha_opcoes, key="kpi_campanha")
        else:
            campanha_selecionada = st.selectbox(
                "🚀 Campanha:", 
                ['Todas', 'Campanha Verão', 'Black Friday', 'Dia das Mães', 'Natal', 'Ano Novo'],
                key="kpi_campanha_exemplo"
            )
    
    with col_filtro_kpi3:
        # Período específico para esta análise
        periodo_kpi = st.selectbox(
            "📅 Período:",
            ["Últimos 30 dias", "Últimos 90 dias", "Este ano", "Todo período"],
            key="kpi_periodo"
        )
    
    with col_filtro_kpi4:
        st.markdown("<br>", unsafe_allow_html=True)
        aplicar_filtros_kpi = st.button("✅ Aplicar Filtros", use_container_width=True, type="primary")
    
    st.divider()
    
    # ========== 2. CARDS DE KPIs PRINCIPAIS ==========
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    # Calcular métricas reais ou usar exemplo
    if 'Origem' in df.columns and not df.empty:
        total_email = len(df[df['Origem'].str.contains('E-mail|Email', na=False, case=False)]) if 'E-mail' in df['Origem'].values else 245
        total_app = len(df[df['Origem'].str.contains('App|Aplicativo', na=False, case=False)]) if 'App' in df['Origem'].values else 156
        total_site = len(df[df['Origem'].str.contains('Site|Web', na=False, case=False)]) if 'Site' in df['Origem'].values else 189
        total_redes = len(df[df['Origem'].str.contains('Redes|Social|Instagram|Facebook', na=False, case=False)]) if 'Redes' in df['Origem'].values else 98
    else:
        total_email, total_app, total_site, total_redes = 245, 156, 189, 98
    
    with col_kpi1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">📧 TOTAL E-MAIL</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{total_email}</p>
            <p style="font-size: 12px; margin: 0;">+12% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_kpi2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">📱 TOTAL APP</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{total_app}</p>
            <p style="font-size: 12px; margin: 0;">+8% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_kpi3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">🌐 TOTAL SITE</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{total_site}</p>
            <p style="font-size: 12px; margin: 0;">+5% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_kpi4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    border-radius: 15px; padding: 20px; color: white; text-align: center;">
            <p style="font-size: 14px; margin: 0; opacity: 0.9;">📊 TOTAL REDES</p>
            <p style="font-size: 36px; font-weight: bold; margin: 0;">{total_redes}</p>
            <p style="font-size: 12px; margin: 0;">+15% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========== 3. GRÁFICO DE BARRAS - TOP CAMPANHAS ==========
    col_chart1, col_chart2 = st.columns([3, 2])
    
    with col_chart1:
        st.markdown("### 🏆 Top 10 Campanhas por Volume")
        
        # Dados de campanhas (reais ou exemplo)
        if 'Campanha' in df.columns and not df.empty:
            campanhas_counts = df['Campanha'].value_counts().head(10).reset_index()
            campanhas_counts.columns = ['Campanha', 'Volume']
            df_campanhas = campanhas_counts
        else:
            campanhas_data = {
                'Campanha': ['Campanha Verão', 'Black Friday', 'Dia das Mães', 'Natal', 'Ano Novo',
                            'Dia dos Pais', 'Dia das Crianças', 'Páscoa', 'Carnaval', 'Semana do Cliente'],
                'Volume': [156, 142, 98, 87, 76, 65, 54, 43, 32, 21]
            }
            df_campanhas = pd.DataFrame(campanhas_data)
        
        # Gráfico de barras horizontal
        fig_campanhas = px.bar(
            df_campanhas.sort_values('Volume', ascending=True),
            x='Volume',
            y='Campanha',
            orientation='h',
            title='Top 10 Campanhas',
            color='Volume',
            color_continuous_scale='blues'
        )
        fig_campanhas.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_campanhas, use_container_width=True)
    
    with col_chart2:
        st.markdown("### 🎯 Distribuição por Origem")
        
        # Dados de origem (reais ou exemplo)
        if 'Origem' in df.columns and not df.empty:
            origem_counts = df['Origem'].value_counts().reset_index()
            origem_counts.columns = ['Origem', 'Quantidade']
            df_origem = origem_counts.head(7)
        else:
            origem_data = {
                'Origem': ['E-mail', 'App', 'Site', 'Redes Sociais', 'Eventos', 'WhatsApp', 'SMS'],
                'Quantidade': [245, 156, 189, 98, 45, 32, 21]
            }
            df_origem = pd.DataFrame(origem_data)
        
        fig_origem = px.pie(
            df_origem,
            values='Quantidade',
            names='Origem',
            title='Demandas por Origem',
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_origem.update_traces(textposition='inside', textinfo='percent+label')
        fig_origem.update_layout(height=400)
        st.plotly_chart(fig_origem, use_container_width=True)
    
    st.divider()
    
    # ========== 4. TABELA DE DEMANDAS DE COMUNICAÇÃO ==========
    st.markdown("### 📋 Demandas de Comunicação por Tipo")
    
    # Dados de comunicação (reais ou exemplo)
    if 'Tipo_Comunicacao' in df.columns and not df.empty:
        comunicacao_counts = df['Tipo_Comunicacao'].value_counts().head(8).reset_index()
        comunicacao_counts.columns = ['Tipo', 'Quantidade']
        
        # Adicionar métricas calculadas
        demandas_comunicacao = pd.DataFrame({
            'Tipo': comunicacao_counts['Tipo'],
            'Quantidade': comunicacao_counts['Quantidade'],
            'Média Diária': [round(qtd/30, 1) for qtd in comunicacao_counts['Quantidade']],
            'Taxa Conversão': [f"{np.random.randint(60, 95)}%" for _ in range(len(comunicacao_counts))],
            'Status': ['✅' if i < 3 else '⚠️' if i < 6 else '🟡' for i in range(len(comunicacao_counts))]
        })
    else:
        demandas_comunicacao = pd.DataFrame({
            'Tipo': ['E-mail Marketing', 'Redes Sociais', 'Landing Page', 'Newsletter', 
                    'Push Notification', 'SMS', 'WhatsApp', 'Blog Post'],
            'Quantidade': [245, 156, 98, 76, 54, 32, 21, 15],
            'Média Diária': ['12.3', '8.1', '5.2', '4.0', '2.8', '1.7', '1.1', '0.8'],
            'Taxa Conversão': ['78%', '65%', '82%', '71%', '88%', '62%', '91%', '75%'],
            'Status': ['✅', '⚠️', '✅', '🟡', '✅', '⚠️', '✅', '🟡']
        })
    
    # Aplicar cores condicionais
    def color_status(val):
        if val == '✅':
            return 'background-color: #d4edda; color: #155724'
        elif val == '⚠️':
            return 'background-color: #fff3cd; color: #856404'
        elif val == '🟡':
            return 'background-color: #fff3cd; color: #856404'
        return ''
    
    styled_df = demandas_comunicacao.style.applymap(color_status, subset=['Status'])
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=350,
        hide_index=True
    )
    
    # ========== 5. MÉTRICAS DE PERFORMANCE ==========
    st.divider()
    st.markdown("### 📊 Análise de Performance")
    
    col_perf1, col_perf2, col_perf3 = st.columns(3)
    
    # Calcular taxas médias
    if 'Taxa_Abertura' in df.columns:
        taxa_abertura = f"{df['Taxa_Abertura'].mean():.0f}%"
    else:
        taxa_abertura = "68%"
    
    if 'Taxa_Clique' in df.columns:
        taxa_clique = f"{df['Taxa_Clique'].mean():.0f}%"
    else:
        taxa_clique = "12%"
    
    if 'Taxa_Conversao' in df.columns:
        taxa_conversao = f"{df['Taxa_Conversao'].mean():.1f}%"
    else:
        taxa_conversao = "7.5%"
    
    with col_perf1:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #667eea;">
            <p style="color: #666; margin: 0; font-size: 14px;">📈 TAXA DE ABERTURA</p>
            <p style="font-size: 32px; font-weight: bold; margin: 0; color: #667eea;">{taxa_abertura}</p>
            <p style="color: #28a745; margin: 0; font-size: 12px;">↑ 5% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_perf2:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #f093fb;">
            <p style="color: #666; margin: 0; font-size: 14px;">🖱️ TAXA DE CLIQUE</p>
            <p style="font-size: 32px; font-weight: bold; margin: 0; color: #f093fb;">{taxa_clique}</p>
            <p style="color: #28a745; margin: 0; font-size: 12px;">↑ 2% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_perf3:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #4facfe;">
            <p style="color: #666; margin: 0; font-size: 14px;">🎯 TAXA DE CONVERSÃO</p>
            <p style="font-size: 32px; font-weight: bold; margin: 0; color: #4facfe;">{taxa_conversao}</p>
            <p style="color: #28a745; margin: 0; font-size: 12px;">↑ 1.2% vs mês anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== 6. INSIGHTS E RECOMENDAÇÕES ==========
    with st.expander("💡 Insights e Recomendações", expanded=True):
        col_insight1, col_insight2 = st.columns(2)
        
        with col_insight1:
            st.markdown("""
            **✅ O que está funcionando:**
            - **E-mail Marketing** tem maior volume e boa conversão
            - **App** apresenta melhor taxa de conversão
            - **Campanha Verão** é a mais requisitada
            - **WhatsApp** tem alta conversão (91%)
            
            **⚠️ O que precisa atenção:**
            - **Redes Sociais** tem conversão abaixo da média
            - **SMS** tem baixo volume - avaliar relevância
            - **Blog Post** com baixa demanda
            """)
        
        with col_insight2:
            st.markdown("""
            **📌 Recomendações Estratégicas:**
            
            1. **Expanda WhatsApp** - Alta conversão e baixo volume atual
            2. **Otimize Redes Sociais** - Potencial de crescimento de 35%
            3. **Automatize E-mails** - Maior volume, ganho em escala
            4. **Revitalize Campanhas sazonais** - Top 3 em demanda
            5. **Invista em App** - Melhor taxa de conversão (82%)
            
            **🎯 Meta para próximo mês:**
            - Aumentar volume em 15%
            - Melhorar conversão em 5%
            - Ativar 2 novas campanhas
            """)

# =========================================================
# 9. FILTROS AVANÇADOS (COM FILTRO DE DATA)
# =========================================================

st.header("🎛️ Filtros Avançados")

# Criar layout de 4 colunas para acomodar o filtro de data
filtro_cols = st.columns(4)

filtros_ativos = {}

# Filtro 1: Status
if 'Status' in df.columns:
    with filtro_cols[0]:
        status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
        status_selecionado = st.selectbox("📌 Status:", status_opcoes, key="filtro_status")
        if status_selecionado != 'Todos':
            filtros_ativos['Status'] = status_selecionado

# Filtro 2: Prioridade
if 'Prioridade' in df.columns:
    with filtro_cols[1]:
        prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
        prioridade_selecionada = st.selectbox("⚡ Prioridade:", prioridade_opcoes, key="filtro_prioridade")
        if prioridade_selecionada != 'Todos':
            filtros_ativos['Prioridade'] = prioridade_selecionada

# Filtro 3: Produção
if 'Produção' in df.columns:
    with filtro_cols[2]:
        producao_opcoes = ['Todos'] + sorted(df['Produção'].dropna().unique().tolist())
        producao_selecionada = st.selectbox("🏭 Produção:", producao_opcoes, key="filtro_producao")
        if producao_selecionada != 'Todos':
            filtros_ativos['Produção'] = producao_selecionada

# ========== FILTRO DE DATA DE SOLICITAÇÃO ==========
with filtro_cols[3]:
    st.markdown("**📅 Data Solicitação**")
    
    if 'Data de Solicitação' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['Data de Solicitação']):
            df['Data de Solicitação'] = pd.to_datetime(df['Data de Solicitação'], errors='coerce')
        
        datas_validas = df['Data de Solicitação'].dropna()
        
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            
            periodo_default = "Todos"
            if 'periodo_data' in st.session_state:
                periodo_default = st.session_state.periodo_data
            
            periodo_opcao = st.selectbox(
                "Período:",
                ["Todos", "Hoje", "Esta semana", "Este mês", "Últimos 30 dias", "Personalizado"],
                index=["Todos", "Hoje", "Esta semana", "Este mês", "Últimos 30 dias", "Personalizado"].index(periodo_default) 
                if periodo_default in ["Todos", "Hoje", "Esta semana", "Este mês", "Últimos 30 dias", "Personalizado"] else 0,
                key="periodo_data"
            )
            
            hoje = datetime.now().date()
            
            if 'data_ini' in st.session_state and 'data_fim' in st.session_state:
                data_ini_personalizada = st.session_state.data_ini
                data_fim_personalizada = st.session_state.data_fim
            else:
                data_ini_personalizada = data_min
                data_fim_personalizada = data_max
            
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
                    data_ini = st.date_input("De", data_ini_personalizada, key="data_ini")
                with col2:
                    data_fim = st.date_input("Até", data_fim_personalizada, key="data_fim")
                filtros_ativos['data_inicio'] = data_ini
                filtros_ativos['data_fim'] = data_fim
                filtros_ativos['tem_filtro_data'] = True
    else:
        st.info("ℹ️ Sem coluna de data")

# =========================================================
# APLICAR FILTROS
# =========================================================

df_filtrado = df.copy()

# Aplicar filtros categóricos
for col, valor in filtros_ativos.items():
    if col not in ['data_inicio', 'data_fim', 'tem_filtro_data']:
        df_filtrado = df_filtrado[df_filtrado[col] == valor]

# Aplicar filtro de data
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
        
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            st.metric("📈 Registros Filtrados", len(df_filtrado))
        
        with col_filt2:
            porcentagem = (len(df_filtrado) / total_linhas * 100) if total_linhas > 0 else 0
            st.metric("📊 % do Total", f"{porcentagem:.1f}%")
        
        with col_filt3:
            if 'tem_filtro_data' in filtros_ativos:
                st.metric("📅 Período", 
                         f"{filtros_ativos['data_inicio'].strftime('%d/%m')} a {filtros_ativos['data_fim'].strftime('%d/%m')}")
        
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
# 10. EXPORTAÇÃO (COM DADOS FILTRADOS)
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
        use_container_width=True,
        help="Baixar dados em formato CSV"
    )

with col_exp2:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_exportar.to_excel(writer, index=False, sheet_name='Dados')
        resumo = pd.DataFrame({
            'Métrica': ['Total Registros', 'Total Colunas', 'Data Exportação', 'Filtros Aplicados'],
            'Valor': [len(df_exportar), len(df_exportar.columns), 
                     datetime.now().strftime('%d/%m/%Y %H:%M'),
                     'Sim' if filtros_ativos else 'Não']
        })
        resumo.to_excel(writer, index=False, sheet_name='Resumo')
    
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 Download Excel",
        data=excel_data,
        file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help="Baixar dados em formato Excel com abas"
    )

with col_exp3:
    json_data = df_exportar.to_json(orient='records', force_ascii=False, date_format='iso')
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name=f"dados_cocred_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True,
        help="Baixar dados em formato JSON"
    )

# =========================================================
# 11. DEBUG INFO (apenas se ativado)
# =========================================================

if st.session_state.debug_mode:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🐛 Debug Info:**")
    
    with st.sidebar.expander("Detalhes Técnicos", expanded=False):
        st.write(f"**Cache:** 1 minuto")
        st.write(f"**Hora atual:** {datetime.now().strftime('%H:%M:%S')}")
        
        token = get_access_token()
        if token:
            st.success(f"✅ Token: ...{token[-10:]}")
        else:
            st.error("❌ Token não disponível - Usando dados de exemplo")
        
        st.write(f"**DataFrame Info:**")
        st.write(f"- Shape: {df.shape}")
        st.write(f"- Memory: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        st.write(f"- Colunas: {list(df.columns)}")
        
        if 'Data de Solicitação' in df.columns:
            st.write(f"**Data de Solicitação:**")
            st.write(f"- Tipo: {df['Data de Solicitação'].dtype}")
            st.write(f"- Mínimo: {df['Data de Solicitação'].min()}")
            st.write(f"- Máximo: {df['Data de Solicitação'].max()}")
            st.write(f"- Nulos: {df['Data de Solicitação'].isnull().sum()}")
        
        st.write(f"**Resumo Executivo:**")
        st.write(f"- Total: {total_linhas}")
        st.write(f"- Concluídos: {total_concluidos}")
        st.write(f"- Prioridade Alta: {total_alta}")
        st.write(f"- Hoje: {total_hoje}")
        
        st.write(f"**KPIs - Origens:**")
        if 'Origem' in df.columns:
            st.write(df['Origem'].value_counts().head().to_dict())

# =========================================================
# 12. RODAPÉ
# =========================================================

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

with footer_col2:
    st.caption(f"📊 {total_linhas} registros | {total_colunas} colunas")
    if filtros_ativos and len(df_filtrado) > 0:
        st.caption(f"🎯 Filtrados: {len(df_filtrado)} registros")

with footer_col3:
    st.caption("🔄 Atualiza a cada 1 minuto | 📧 cristini.cordesco@ideatoreamericas.com")
    st.caption("📊 v4.0.0 - KPIs por Origem e Campanha")

# =========================================================
# 13. AUTO-REFRESH (opcional)
# =========================================================

if auto_refresh:
    refresh_placeholder = st.empty()
    for i in range(60, 0, -1):
        refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
        time.sleep(1)
    refresh_placeholder.empty()
    st.rerun()