import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="HMB - Executive Report", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 32px !important; color: #002C5F !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='latin1')
    
    # Tratamento numérico robusto
    df['realizado'] = df['realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)
    
    # Tratamento de data
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    
    # Limpeza de strings para evitar erros de busca
    df['titulo'] = df['titulo'].str.upper().str.strip()
    return df

df = carregar_dados()

# ---SIDEBAR ---
st.sidebar.image("https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png", width=150)
st.sidebar.title("Filtros")





# --- TABELA DE DADOS DETALHADA ---

with st.expander("VER DADOS BRUTOS FILTRADOS"):
    st.dataframe(
        df_final[['periodo', 'REGIAO', 'STATE']].sort_values(by='periodo', ascending=False)
    )









