
import streamlit as st
import pandas as pd
import plotly.express as px

# 1) CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="HMB - Executive Report", layout="wide", page_icon="📈")

# Corrige o <style> (sem entidades HTML)
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
[data-testid="stMetricValue"] { font-size: 32px !important; color: #002C5F !important; }
.stTabs [data-baseweb="tab-list"] { gap: 24px; }
.stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# 2) CARREGAMENTO E LIMPEZA
@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding="latin1")

    # Numérico robusto
    df["realizado"] = (
        df["realizado"].astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["realizado"] = pd.to_numeric(df["realizado"], errors="coerce").fillna(0)

    # Datas (dayfirst) + coerção para evitar NaT silencioso
    df["periodo"] = pd.to_datetime(df["periodo"], dayfirst=True, errors="coerce")

    # Padronização de títulos
    df["titulo"] = df["titulo"].astype(str).str.upper().str.strip()

    return df

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.image("https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png", width=150)
st.sidebar.title("Filtros")

meses = df["periodo"].dt.strftime("%m/%Y")
opcoes_meses = sorted(meses.dropna().unique())
if not opcoes_meses:
    st.error("Não há períodos válidos no CSV (coluna 'periodo'). Verifique o arquivo.")
    st.stop()

mes_sel = st.sidebar.select_slider("Período de análise", options=opcoes_meses, value=opcoes_meses[-1])

# --- LAYOUT ---
st.title(f"Sumário Executivo - {mes_sel}")

# 3) AQUI CRIA O DF_VIEW **ANTES** DE QUALQUER KPI
df_view = df[df["periodo"].dt.strftime("%m/%Y") == mes_sel].copy()

if df_view.empty:
    st.warning("Nenhum dado encontrado para o período selecionado. Tente outro mês ou verifique o CSV.")
    st.stop()

# 4) FUNÇÃO DE BUSCA DE VALOR (usa df_view já criado)
