
import streamlit as st
import pandas as pd

st.set_page_config(page_title="HMB - Executive Report", layout="wide", page_icon="📈")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding="latin1")
    df["realizado"] = (
        df["realizado"].astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["realizado"] = pd.to_numeric(df["realizado"], errors="coerce").fillna(0)
    df["periodo"] = pd.to_datetime(df["periodo"], dayfirst=True, errors="coerce")
    df["titulo"] = df["titulo"].astype(str).str.upper().str.strip()
    return df

df = carregar_dados()

# Sidebar
meses = df["periodo"].dt.strftime("%m/%Y")
opcoes_meses = sorted(meses.dropna().unique())
mes_sel = st.sidebar.select_slider("Período de análise", options=opcoes_meses, value=opcoes_meses[-1])

st.title(f"Sumário Executivo - {mes_sel}")

# >>> CRIA df_view ANTES DE USAR <<<
df_view = df[df["periodo"].dt.strftime("%m/%Y") == mes_sel].copy()
if df_view.empty:
    st.warning("Nenhum dado para o período selecionado.")
    st.stop()

# >>> get_val recebe o DF explicitamente <<<
def get_val(df_local: pd.DataFrame, titulo_nome: str) -> float:
    chave = str(titulo_nome).strip().upper()
    return df_local.loc[df_local["titulo"] == chave, "realizado"].sum()

# KPIs (ajuste exatamente conforme seu CSV)
faturamento_total   = get_val(df_view, "R$ FATURAMENTO TOTAL")
passagens_totais    = get_val(df_view, "QTD. PASSAGENS TOTAIS")
passagens_cpus      = get_val(df_view, "QTD. PASSAGENS CPUS")
passagens_internas  = get_val(df_view, "QTD. PASSAGENS INTERNAS")
