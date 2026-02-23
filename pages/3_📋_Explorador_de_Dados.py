# =========================================================
# pages/3_📋_Explorador_de_Dados.py
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.auth import get_access_token
from utils.helpers import calcular_altura_tabela, converter_para_data

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Explorador de Dados - COCRED",
    page_icon="📋",
    layout="wide"
)

# =========================================================
# CARREGAR DADOS DO SESSION STATE
# =========================================================
if 'df' not in st.session_state:
    st.error("❌ Dados não carregados. Por favor, execute o app.py primeiro.")
    st.stop()

df = st.session_state.df
total_linhas = len(df)

# =========================================================
# CALCULAR MÉTRICAS GLOBAIS
# =========================================================
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
# SIDEBAR (COPIADO DO APP.PY)
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
        <p style="margin: 5px 0 0 0;">v4.3.0</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# CSS CUSTOMIZADO
# =========================================================
st.markdown("""
<style>
    .info-container-cocred {
        background-color: rgba(0, 51, 102, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #003366;
        color: inherit;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: inherit !important;
    }
    
    a {
        color: #00A3E0 !important;
    }
    
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
# CABEÇALHO
# =========================================================
st.markdown("## 📋 Explorador de Dados")

# =========================================================
# HEADER COM ESTATÍSTICAS RÁPIDAS
# =========================================================
col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

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
            label="📅 Período", 
            value=f"{data_min} a {data_max}",
            help="Período coberto pelos dados"
        )
    else:
        st.metric(label="📅 Período", value="N/A")

with col_stats3:
    if 'Status' in df.columns:
        status_unicos = df['Status'].nunique()
        st.metric(
            label="🏷️ Status", 
            value=status_unicos,
            help="Quantidade de status diferentes"
        )
    else:
        st.metric(label="🏷️ Status", value="N/A")

with col_stats4:
    st.metric(
        label="🔄 Atualização", 
        value=datetime.now().strftime('%d/%m/%Y'),
        help="Data da última atualização"
    )

st.divider()

# =========================================================
# FILTROS AVANÇADOS
# =========================================================
with st.container():
    st.markdown("##### 🔍 Filtros Avançados")
    
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
                    key="quinzena_opcao",
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
                ["Todos", "Hoje", "Esta semana", "Este mês", "Próximos 7 dias", "Próximos 30 dias", "Atrasados", "Personalizado"],
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
        coluna_entrega = None
        for col in df.columns:
            if 'entrega' in col.lower() or 'data entrega' in col.lower():
                coluna_entrega = col
                break
        
        if coluna_entrega is None and 'Data de Entrega' in df.columns:
            coluna_entrega = 'Data de Entrega'
        
        if coluna_entrega:
            periodo_entrega = st.selectbox(
                "📦 Data de Entrega", 
                ["Todos", "Hoje", "Esta semana", "Este mês", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"],
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
        aplicar_filtros = st.button("🔍 Aplicar Filtros", type="primary", use_container_width=True, key="tab3_aplicar_filtros")

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
    df_export = df.copy()
    
    for col, valor in filtros_ativos.items():
        if col not in ['data_inicio', 'data_fim', 'tem_filtro_data', 
                       'deadline_inicio', 'deadline_fim', 'tem_filtro_deadline', 'coluna_deadline',
                       'entrega_inicio', 'entrega_fim', 'tem_filtro_entrega', 'coluna_entrega']:
            df_export = df_export[df_export[col] == valor]
    
    if 'tem_filtro_data' in filtros_ativos and 'Data de Solicitação' in df.columns:
        data_inicio = pd.Timestamp(filtros_ativos['data_inicio'])
        data_fim = pd.Timestamp(filtros_ativos['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_export = df_export[
            (df_export['Data de Solicitação'] >= data_inicio) & 
            (df_export['Data de Solicitação'] <= data_fim)
        ]
    
    if 'tem_filtro_deadline' in filtros_ativos and 'coluna_deadline' in filtros_ativos:
        col_deadline = filtros_ativos['coluna_deadline']
        if col_deadline in df_export.columns:
            deadline_inicio = pd.Timestamp(filtros_ativos['deadline_inicio'])
            deadline_fim = pd.Timestamp(filtros_ativos['deadline_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_export = df_export[
                (df_export[col_deadline] >= deadline_inicio) & 
                (df_export[col_deadline] <= deadline_fim)
            ]
    
    if 'tem_filtro_entrega' in filtros_ativos and 'coluna_entrega' in filtros_ativos:
        col_entrega = filtros_ativos['coluna_entrega']
        if col_entrega in df_export.columns:
            entrega_inicio = pd.Timestamp(filtros_ativos['entrega_inicio'])
            entrega_fim = pd.Timestamp(filtros_ativos['entrega_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df_export = df_export[
                (df_export[col_entrega] >= entrega_inicio) & 
                (df_export[col_entrega] <= entrega_fim)
            ]
    
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
        if st.button("🧹 Limpar Tudo", use_container_width=True, key="tab3_limpar"):
            for key in list(st.session_state.keys()):
                if key.startswith('tab3_'):
                    del st.session_state[key]
            st.rerun()

# =========================================================
# APLICAR FILTROS E PESQUISA
# =========================================================
df_final = df.copy()

for col, valor in filtros_ativos.items():
    if col not in ['data_inicio', 'data_fim', 'tem_filtro_data', 
                   'deadline_inicio', 'deadline_fim', 'tem_filtro_deadline', 'coluna_deadline',
                   'entrega_inicio', 'entrega_fim', 'tem_filtro_entrega', 'coluna_entrega']:
        df_final = df_final[df_final[col] == valor]

if 'tem_filtro_data' in filtros_ativos and 'Data de Solicitação' in df.columns:
    data_inicio = pd.Timestamp(filtros_ativos['data_inicio'])
    data_fim = pd.Timestamp(filtros_ativos['data_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df_final = df_final[
        (df_final['Data de Solicitação'] >= data_inicio) & 
        (df_final['Data de Solicitação'] <= data_fim)
    ]

if 'tem_filtro_deadline' in filtros_ativos and 'coluna_deadline' in filtros_ativos:
    col_deadline = filtros_ativos['coluna_deadline']
    if col_deadline in df_final.columns:
        deadline_inicio = pd.Timestamp(filtros_ativos['deadline_inicio'])
        deadline_fim = pd.Timestamp(filtros_ativos['deadline_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_final = df_final[
            (df_final[col_deadline] >= deadline_inicio) & 
            (df_final[col_deadline] <= deadline_fim)
        ]

if 'tem_filtro_entrega' in filtros_ativos and 'coluna_entrega' in filtros_ativos:
    col_entrega = filtros_ativos['coluna_entrega']
    if col_entrega in df_final.columns:
        entrega_inicio = pd.Timestamp(filtros_ativos['entrega_inicio'])
        entrega_fim = pd.Timestamp(filtros_ativos['entrega_fim']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_final = df_final[
            (df_final[col_entrega] >= entrega_inicio) & 
            (df_final[col_entrega] <= entrega_fim)
        ]

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

if len(df_final) > 0:
    linhas_por_pagina_atual = linhas_por_pagina
    
    if linhas_por_pagina_atual == "Todas":
        altura_tabela = calcular_altura_tabela(len(df_final), len(df_final.columns))
        st.dataframe(df_final, height=min(altura_tabela, 700), use_container_width=True, hide_index=True)
    else:
        linhas_por_pagina_int = int(linhas_por_pagina_atual)
        total_paginas = (len(df_final) - 1) // linhas_por_pagina_int + 1 if len(df_final) > 0 else 1
        
        if 'tab3_pagina_atual' not in st.session_state:
            st.session_state.tab3_pagina_atual = 1
        
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

# AUTO-REFRESH
if auto_refresh:
    refresh_placeholder = st.empty()
    for i in range(60, 0, -1):
        refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
        time.sleep(1)
    refresh_placeholder.empty()
    st.rerun()