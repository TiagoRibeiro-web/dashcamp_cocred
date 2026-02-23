# =========================================================
# pages/2_🎯_KPIs_COCRED.py
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
from utils.helpers import extrair_tipo_demanda

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="KPIs COCRED - COCRED",
    page_icon="🎯",
    layout="wide"
)

# =========================================================
# CARREGAR DADOS DO SESSION STATE
# =========================================================
if 'df' not in st.session_state:
    st.error("❌ Dados não carregados. Por favor, execute o app.py primeiro.")
    st.stop()

df = st.session_state.df

# =========================================================
# CALCULAR MÉTRICAS GLOBAIS
# =========================================================
total_linhas = len(df)
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
    .metric-card-cocred {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 5px;
        background: linear-gradient(135deg, #003366 0%, #00A3E0 100%);
        color: white;
    }
    
    .info-container-cocred {
        background-color: rgba(0, 51, 102, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #003366;
        color: inherit;
    }
    
    .resumo-card {
        background-color: var(--background-color);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
st.markdown("## 🎯 KPIs - Campanhas COCRED")

# Configurações de template para Plotly
is_dark = st.get_option('theme.base') == 'dark'
plotly_template = 'plotly_dark' if is_dark else 'plotly_white'
text_color = 'white' if is_dark else 'black'

# ========== FILTROS ==========
col_filtro_kpi1, col_filtro_kpi2, col_filtro_kpi3 = st.columns(3)

df_kpi = df.copy()

with col_filtro_kpi1:
    if 'Status' in df.columns:
        status_opcoes = ['Todos'] + sorted(df['Status'].dropna().unique().tolist())
        status_filtro = st.selectbox("📌 Filtrar por Status:", status_opcoes, key="kpi_status")
        if status_filtro != 'Todos':
            df_kpi = df_kpi[df_kpi['Status'] == status_filtro]

with col_filtro_kpi2:
    if 'Prioridade' in df.columns:
        prioridade_opcoes = ['Todos'] + sorted(df['Prioridade'].dropna().unique().tolist())
        prioridade_filtro = st.selectbox("⚡ Filtrar por Prioridade:", prioridade_opcoes, key="kpi_prioridade")
        if prioridade_filtro != 'Todos':
            df_kpi = df_kpi[df_kpi['Prioridade'] == prioridade_filtro]

with col_filtro_kpi3:
    periodo_kpi = st.selectbox(
        "📅 Período:", 
        ["Todo período", "Últimos 30 dias", "Últimos 90 dias", "Este ano", "Quinzena"], 
        key="kpi_periodo"
    )
    
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
            
        elif periodo_kpi == "Quinzena":
            quinzena_opcao = st.radio(
                "Escolha a quinzena:",
                ["Primeira quinzena (dias 1-15)", "Segunda quinzena (dias 16-31)"],
                horizontal=True,
                key="kpi_quinzena_opcao"
            )
            
            ano_atual = hoje.year
            mes_atual = hoje.month
            
            if quinzena_opcao == "Primeira quinzena (dias 1-15)":
                data_inicio_quinzena = date(ano_atual, mes_atual, 1)
                data_fim_quinzena = date(ano_atual, mes_atual, 15)
            else:
                ultimo_dia = (date(ano_atual, mes_atual, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                data_inicio_quinzena = date(ano_atual, mes_atual, 16)
                data_fim_quinzena = ultimo_dia
            
            data_inicio_ts = pd.Timestamp(data_inicio_quinzena)
            data_fim_ts = pd.Timestamp(data_fim_quinzena) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            df_kpi = df_kpi[
                (df_kpi['Data de Solicitação'] >= data_inicio_ts) & 
                (df_kpi['Data de Solicitação'] <= data_fim_ts)
            ]
            
            st.caption(f"📅 Período selecionado: {data_inicio_quinzena.strftime('%d/%m')} a {data_fim_quinzena.strftime('%d/%m')}")

total_kpi = len(df_kpi)
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
    
    coluna_campanha = None
    possiveis_nomes = ['Campanha', 'campanha', 'CAMPANHA', 'Nome da Campanha', 'Campanhas', 'campanhas']
    
    for col in df_kpi.columns:
        if any(nome in col for nome in possiveis_nomes):
            coluna_campanha = col
            break
    
    if coluna_campanha:
        campanhas_top = df_kpi[coluna_campanha].value_counts().head(10).reset_index()
        campanhas_top.columns = ['Campanha', 'Quantidade']
        
        campanhas_top = campanhas_top[campanhas_top['Campanha'].notna()]
        campanhas_top = campanhas_top[campanhas_top['Campanha'] != '']
        
        if not campanhas_top.empty:
            campanhas_top = campanhas_top.sort_values('Quantidade', ascending=True)
            
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
            
            if st.session_state.campanha_selecionada and st.session_state.campanha_selecionada in campanhas_top['Campanha'].values:
                cores = ['#003366'] * len(campanhas_top)
                idx = campanhas_top[campanhas_top['Campanha'] == st.session_state.campanha_selecionada].index[0]
                cores[campanhas_top.index.get_loc(idx)] = '#FF6600'
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
            
            st.markdown("##### 🔘 Selecione uma campanha:")
            
            for i in range(0, len(campanhas_top), 5):
                cols_botoes = st.columns(5)
                for j in range(5):
                    if i + j < len(campanhas_top):
                        idx = i + j
                        campanha = campanhas_top.iloc[idx]['Campanha']
                        qtd = campanhas_top.iloc[idx]['Quantidade']
                        nome_curto = campanha[:15] + '...' if len(campanha) > 15 else campanha
                        
                        with cols_botoes[j]:
                            if st.button(
                                f"{nome_curto} ({qtd})", 
                                key=f"btn_camp_{idx}",
                                use_container_width=True,
                                type="primary" if campanha == st.session_state.campanha_selecionada else "secondary"
                            ):
                                st.session_state.campanha_selecionada = campanha
                                st.rerun()
            
            if st.session_state.campanha_selecionada:
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    if st.button("🧹 Limpar Seleção", use_container_width=True, key="limpar_selecao"):
                        st.session_state.campanha_selecionada = None
                        st.rerun()
            
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

coluna_origem = None
possiveis_nomes_origem = ['Origem', 'origem', 'ORIGEM', 'Fonte', 'fonte', 'FONTE', 'Canal', 'canal']

for col in df_kpi.columns:
    if any(nome in col for nome in possiveis_nomes_origem):
        coluna_origem = col
        break

if coluna_origem:
    origem_counts = df_kpi[coluna_origem].value_counts().head(8).reset_index()
    origem_counts.columns = ['Origem', 'Quantidade']
    
    origem_counts = origem_counts[origem_counts['Origem'].notna()]
    origem_counts = origem_counts[origem_counts['Origem'] != '']
    
    if not origem_counts.empty:
        origem_counts['% do Total'] = (origem_counts['Quantidade'] / total_kpi * 100).round(1).astype(str) + '%'
        
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
        
        col_orig1, col_orig2, col_orig3 = st.columns(3)
        with col_orig1:
            st.metric("Total Origens", len(origem_counts))
        with col_orig2:
            st.metric("Total Demandas", origem_counts['Quantidade'].sum())
        with col_orig3:
            media_origem = origem_counts['Quantidade'].mean()
            st.metric("Média por Origem", f"{media_origem:.0f}")
    else:
        st.info("ℹ️ Dados de origem não disponíveis")
        
        if st.session_state.get('debug_mode', False):
            st.caption(f"📋 Coluna encontrada: {coluna_origem}, mas sem dados válidos")
else:
    st.info("ℹ️ Coluna 'Origem' não encontrada. Usando dados de exemplo...")
    
    if st.session_state.get('debug_mode', False):
        st.caption("📋 Colunas disponíveis no DataFrame:")
        st.write(df_kpi.columns.tolist())
    
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

# AUTO-REFRESH
if auto_refresh:
    refresh_placeholder = st.empty()
    for i in range(60, 0, -1):
        refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
        time.sleep(1)
    refresh_placeholder.empty()
    st.rerun()