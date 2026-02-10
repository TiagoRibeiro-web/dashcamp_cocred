import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard de Campanhas - SICOOB COCRED", layout="wide")

# =========================================================
# VERIFICAÇÃO DO ARQUIVO
# =========================================================
@st.cache_data
def verificar_arquivo():
    if not os.path.exists("jobs.xlsx"):
        st.error("❌ Arquivo 'jobs.xlsx' não encontrado no diretório do projeto!")
        st.info("Certifique-se de que o arquivo jobs.xlsx está na mesma pasta do app.py")
        return False
    return True

# =========================================================
# CARREGAMENTO E TRATAMENTO DOS DADOS
# =========================================================
@st.cache_data
def carregar_dados():
    # Verifica se arquivo existe
    if not os.path.exists("jobs.xlsx"):
        st.error("Arquivo jobs.xlsx não encontrado!")
        return pd.DataFrame()
    
    try:
        # Usa engine explícita para evitar problemas de dependência
        df = pd.read_excel("jobs.xlsx", engine='openpyxl')
    except ImportError as e:
        st.error("""
        ⚠️ Erro de dependência: openpyxl não está instalado!
        
        **Solução:**
        1. Crie um arquivo `requirements.txt` na raiz do projeto com:
        ```
        streamlit==1.54.0
        pandas==2.3.3
        openpyxl>=3.0.0
        ```
        2. Commit e push para o GitHub
        3. O Streamlit Cloud reinstalará as dependências automaticamente
        """)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {str(e)}")
        return pd.DataFrame()

    # -------------------------
    # Tratamento do prazo
    # -------------------------
    if "Prazo em dias" in df.columns:
        df["Prazo em dias"] = (
            df["Prazo em dias"]
            .astype(str)
            .str.strip()
        )

        # Situação do prazo
        df["Situação do Prazo"] = df["Prazo em dias"].apply(
            lambda x: "Prazo encerrado"
            if "encerrado" in str(x).lower()
            else "Em prazo"
        )

        # Converter números
        df["Prazo em dias"] = pd.to_numeric(
            df["Prazo em dias"], errors="coerce"
        )

    # -------------------------
    # Faixa de prazo (checkbox)
    # -------------------------
    def classificar_faixa(row):
        if row["Situação do Prazo"] == "Prazo encerrado":
            return "Prazo encerrado"
        if pd.isna(row["Prazo em dias"]):
            return "Sem prazo"
        if row["Prazo em dias"] <= 0:
            return "Prazo encerrado"
        elif row["Prazo em dias"] <= 5:
            return "1 a 5 dias"
        elif row["Prazo em dias"] <= 10:
            return "6 a 10 dias"
        else:
            return "Acima de 10 dias"

    df["Faixa de Prazo"] = df.apply(classificar_faixa, axis=1)

    # -------------------------
    # Semáforo
    # -------------------------
    def classificar_semaforo(row):
        if row["Faixa de Prazo"] == "Prazo encerrado":
            return "Atrasado"
        elif row["Faixa de Prazo"] == "1 a 5 dias":
            return "Atenção"
        else:
            return "No prazo"

    df["Semáforo"] = df.apply(classificar_semaforo, axis=1)

    return df


# Verifica arquivo antes de continuar
if not verificar_arquivo():
    st.stop()

# Carrega dados
df = carregar_dados()

# Verifica se dados foram carregados
if df.empty:
    st.warning("Nenhum dado foi carregado. Verifique o arquivo jobs.xlsx.")
    st.stop()

# Remove linhas sem informações essenciais
df = df.dropna(subset=["Campanha ou Ação", "Status Operacional"])

# =========================================================
# TÍTULO
# =========================================================
st.title("📊 Dashboard de Campanhas – SICOOB COCRED")

# =========================================================
# LEGENDA
# =========================================================
with st.expander("📌 Legendas e critérios"):
    st.markdown("""
**Semáforo de Prazo**
- 🟢 **No prazo:** mais de 5 dias
- 🟡 **Atenção:** 1 a 5 dias
- 🔴 **Atrasado:** prazo encerrado ou vencido

**Faixas de Prazo**
- Prazo encerrado
- 1 a 5 dias
- 6 a 10 dias
- Acima de 10 dias
""")

# =========================================================
# FILTROS (SIDEBAR)
# =========================================================
st.sidebar.header("Filtros")
st.sidebar.caption("Os dados são atualizados automaticamente conforme o Excel.")

df_filtrado = df.copy()

# -------------------------
# Filtro por faixa de prazo
# -------------------------
st.sidebar.subheader("Prazo")
st.sidebar.caption("Filtra jobs por faixa de prazo.")

faixas_ordem = [
    "Prazo encerrado",
    "1 a 5 dias",
    "6 a 10 dias",
    "Acima de 10 dias"
]

faixas_disponiveis = df["Faixa de Prazo"].unique()
faixas_sel = []

for faixa in faixas_ordem:
    if faixa in faixas_disponiveis:
        marcado = st.sidebar.checkbox(
            faixa, value=True, key=f"faixa_{faixa}"
        )
        if marcado:
            faixas_sel.append(faixa)

if faixas_sel:
    df_filtrado = df_filtrado[df_filtrado["Faixa de Prazo"].isin(faixas_sel)]
else:
    st.sidebar.warning("Selecione pelo menos uma faixa de prazo")

# -------------------------
# Função genérica checkbox
# -------------------------
def filtro_checkbox(coluna, titulo, legenda):
    valores = sorted(df[coluna].dropna().unique())
    selecionados = []

    st.sidebar.subheader(titulo)
    st.sidebar.caption(legenda)

    for valor in valores:
        marcado = st.sidebar.checkbox(
            str(valor), value=True, key=f"{coluna}_{valor}"
        )
        if marcado:
            selecionados.append(valor)

    return selecionados


# Prioridade
if "Prioridade" in df.columns:
    prioridade_sel = filtro_checkbox(
        "Prioridade", "Prioridade", "Nível de urgência do job."
    )
    if prioridade_sel:
        df_filtrado = df_filtrado[df_filtrado["Prioridade"].isin(prioridade_sel)]

# Produção
if "Produção" in df.columns:
    producao_sel = filtro_checkbox(
        "Produção", "Produção", "Tipo ou canal de produção."
    )
    if producao_sel:
        df_filtrado = df_filtrado[df_filtrado["Produção"].isin(producao_sel)]

# Status
if "Status Operacional" in df.columns:
    status_sel = filtro_checkbox(
        "Status Operacional", "Status", "Status atual do job."
    )
    if status_sel:
        df_filtrado = df_filtrado[df_filtrado["Status Operacional"].isin(status_sel)]

# =========================================================
# ALERTA DE ATRASO
# =========================================================
if not df_filtrado.empty and "Semáforo" in df_filtrado.columns:
    atrasados = df_filtrado[df_filtrado["Semáforo"] == "Atrasado"]
    if len(atrasados) > 0:
        st.error(f"⚠️ {len(atrasados)} job(s) com prazo encerrado.")

# =========================================================
# RESUMO GERAL (CARDS)
# =========================================================
if not df_filtrado.empty and "Status Operacional" in df_filtrado.columns:
    st.subheader("Resumo Geral")
    st.caption("Total de jobs por status operacional.")

    cores_status = {
        "Aprovado": "#00A859",        # Verde SICOOB
        "Em Produção": "#007A3D",     # Verde escuro
        "Aguardando": "#7ED957",      # Verde claro
    }

    def cor_status(nome):
        nome = str(nome).lower()
        if "aprovado" in nome:
            return cores_status["Aprovado"]
        if "produção" in nome:
            return cores_status["Em Produção"]
        if "aguardando" in nome:
            return cores_status["Aguardando"]
        return "#6B7280"

    resumo_geral = (
        df_filtrado["Status Operacional"]
        .value_counts()
        .reset_index()
    )
    resumo_geral.columns = ["Status", "Quantidade"]

    cols = st.columns(len(resumo_geral))
    for i, row in resumo_geral.iterrows():
        cor = cor_status(row["Status"])
        cols[i].markdown(
            f"""
            <div style="
                background:{cor};
                padding:20px;
                border-radius:12px;
                text-align:center;
                color:white;
                font-weight:bold;
            ">
                <div style="font-size:16px;">{row['Status']}</div>
                <div style="font-size:34px;">{int(row['Quantidade'])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

# =========================================================
# RESUMO POR CAMPANHA (ESTILO EXCEL)
# =========================================================
if not df_filtrado.empty and "Campanha ou Ação" in df_filtrado.columns:
    st.subheader("Resumo por Campanha")
    st.caption("Campanhas com atraso aparecem no topo.")

    try:
        tabela_resumo = pd.pivot_table(
            df_filtrado,
            index="Campanha ou Ação",
            columns="Status Operacional",
            aggfunc="size",
            fill_value=0
        )

        tabela_resumo["Total"] = tabela_resumo.sum(axis=1)

        if "Semáforo" in df_filtrado.columns:
            campanhas_atrasadas = (
                df_filtrado[df_filtrado["Semáforo"] == "Atrasado"]
                ["Campanha ou Ação"]
                .unique()
            )
            tabela_resumo["Atrasada"] = tabela_resumo.index.isin(campanhas_atrasadas)
            tabela_resumo = tabela_resumo.sort_values(
                by=["Atrasada", "Total"],
                ascending=[False, False]
            ).reset_index()
        else:
            tabela_resumo = tabela_resumo.sort_values(
                by="Total",
                ascending=False
            ).reset_index()
            tabela_resumo["Atrasada"] = False

        def destacar_campanha(row):
            if row["Atrasada"]:
                return ["background-color:#FECACA"] * len(row)
            return [""] * len(row)

        st.dataframe(
            tabela_resumo.style.apply(destacar_campanha, axis=1),
            use_container_width=True
        )
    except Exception as e:
        st.warning("Não foi possível gerar o resumo por campanha.")

    st.divider()

# =========================================================
# TABELA DETALHADA
# =========================================================
if not df_filtrado.empty:
    st.subheader("Detalhamento dos Jobs")
    st.caption("Dados completos conforme filtros aplicados.")

    def destacar_semaforo(row):
        if "Semáforo" not in row.index:
            return [""] * len(row)
        if row["Semáforo"] == "Atrasado":
            return ["background-color:#FECACA"] * len(row)
        elif row["Semáforo"] == "Atenção":
            return ["background-color:#DCFCE7"] * len(row)
        return [""] * len(row)

    try:
        st.dataframe(
            df_filtrado.style.apply(destacar_semaforo, axis=1),
            use_container_width=True,
            height=400
        )
    except Exception as e:
        st.dataframe(df_filtrado, use_container_width=True, height=400)
else:
    st.warning("Nenhum dado encontrado com os filtros aplicados.")

# =========================================================
# RODAPÉ COM INFORMAÇÕES
# =========================================================
st.sidebar.divider()
st.sidebar.caption(f"📊 Total de registros: {len(df_filtrado)}")
st.sidebar.caption(f"📁 Fonte: jobs.xlsx")
st.sidebar.caption("Atualizado automaticamente")

# =========================================================
# MENSAGEM DE AJUDA PARA DEPLOY
# =========================================================
if "openpyxl" not in globals():
    with st.expander("⚠️ Problemas no deploy?"):
        st.markdown("""
        **Se estiver com erro de "ModuleNotFoundError: No module named 'openpyxl'":**

        1. **Crie um arquivo `requirements.txt`** na raiz do projeto com:
        ```
        streamlit==1.54.0
        pandas==2.3.3
        openpyxl>=3.0.0
        ```

        2. **Commit e push para o GitHub:**
        ```bash
        git add requirements.txt
        git commit -m "Add dependencies"
        git push origin main
        ```

        3. **O Streamlit Cloud** reinstalará as dependências automaticamente.

        4. **Verifique os logs** em "Manage app" → "Logs"
        """)