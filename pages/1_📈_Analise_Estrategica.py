# =========================================================
# pages/1_📈_Analise_Estrategica.py
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
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
    page_title="Análise Estratégica - COCRED",
    page_icon="📈",
    layout="wide"
)
# =========================================================
# REMOVER MENU SUPERIOR E FOOTER (NOVO!)
# =========================================================
st.markdown("""
    <style>
        /* Remove apenas o primeiro item do menu (o "app") */
        .stAppDeployButton {display: none;}
        div[data-testid="stDecoration"] li:first-child {display: none;}
        
        /* Ajusta o espaçamento dos itens restantes */
        div[data-testid="stDecoration"] li {
            margin-left: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
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
</style>
""", unsafe_allow_html=True)

# =========================================================
# CABEÇALHO
# =========================================================
st.markdown("## 📈 Análise Estratégica")

# Configurações de template para Plotly
is_dark = st.get_option('theme.base') == 'dark'
plotly_template = 'plotly_dark' if is_dark else 'plotly_white'
text_color = 'white' if is_dark else 'black'

# ========== 1. MÉTRICAS DE NEGÓCIO ==========
st.markdown("""
<div class="info-container-cocred">
    <p style="margin: 0; font-size: 14px;">
        <strong>🎯 Indicadores de Performance</strong> - Acompanhe os principais KPIs do negócio.
    </p>
</div>
""", unsafe_allow_html=True)

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

# ========== 2. ANÁLISE TEMPORAL COMPLETA ==========
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
    
    # Métricas por período
    hoje = datetime.now().date()
    ano_atual = hoje.year
    
    # Últimos 12 meses
    ultimos_12_meses = df_temp[df_temp['Data de Solicitação'].dt.date >= (hoje - timedelta(days=365))].copy()
    evolucao_mensal = ultimos_12_meses.groupby('Mês/Ano').size().reset_index()
    evolucao_mensal.columns = ['Período', 'Quantidade']
    
    # Layout: 3 colunas de métricas
    col_temp1, col_temp2, col_temp3 = st.columns(3)
    
    with col_temp1:
        total_ano = len(df_temp[df_temp['Ano'] == ano_atual])
        st.metric(
            label=f"📊 Total {ano_atual}", 
            value=total_ano,
            help="Total de solicitações no ano atual"
        )
    
    with col_temp2:
        if len(evolucao_mensal) >= 2:
            ultimo_mes = evolucao_mensal.iloc[-1]['Quantidade']
            penultimo_mes = evolucao_mensal.iloc[-2]['Quantidade']
            variacao_mensal = ((ultimo_mes - penultimo_mes) / penultimo_mes * 100) if penultimo_mes > 0 else 0
            st.metric(
                label="📈 Vs Mês Anterior", 
                value=ultimo_mes,
                delta=f"{variacao_mensal:+.1f}%",
                delta_color="normal",
                help="Comparação com o mês anterior"
            )
        else:
            st.metric(label="📈 Vs Mês Anterior", value="N/A")
    
    with col_temp3:
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

    # AUTO-REFRESH
    if auto_refresh:
        refresh_placeholder = st.empty()
        for i in range(60, 0, -1):
            refresh_placeholder.caption(f"🔄 Atualizando em {i} segundos...")
            time.sleep(1)
        refresh_placeholder.empty()
        st.rerun()