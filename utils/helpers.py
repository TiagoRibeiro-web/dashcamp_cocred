# =========================================================
# utils/helpers.py
# =========================================================
import pandas as pd
from datetime import datetime

def calcular_altura_tabela(num_linhas, num_colunas):
    """Calcula altura dinâmica para tabelas"""
    altura_base = 150
    altura_por_linha = 35
    altura_por_coluna = 2
    altura_conteudo = altura_base + (num_linhas * altura_por_linha) + (num_colunas * altura_por_coluna)
    altura_maxima = 2000
    return min(altura_conteudo, altura_maxima)

def converter_para_data(df, coluna):
    """Converte coluna para datetime"""
    try:
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce', dayfirst=True)
    except:
        pass
    return df

def extrair_tipo_demanda(df, texto):
    """Extrai contagem de demandas por tipo (fallback)"""
    count = 0
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                count += len(df[df[col].astype(str).str.contains(texto, na=False, case=False)])
            except:
                pass
    return count