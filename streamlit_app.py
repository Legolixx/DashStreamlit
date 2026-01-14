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

meses = df['periodo'].dt.strftime('%m/%Y')
mes_sel = st.sidebar.select_slider("Período de análise", options=sorted(meses))


# --- LAYOUT DO DASHBOARD ---
st.title(f"Sumário Executivo - {mes_sel}")

# Aplicação dos filtros
df_view = df[df['REGIÃO'].isin(regioes)]
df_view = df_view[df_view['periodo'].dt.strftime('%m/%Y') == mes_sel]

# --- LÓGICA DE NEGÓCIO (Cálculo dos KPIs do Presidente) ---
def get_val(titulo_nome):
    return df_view[df_view['titulo'] == titulo_nome]['realizado'].sum()


# Agrupando valores para cálculos transversais
faturamento_total = get_val("R$ Faturamento Total") # Ajuste o nome conforme seu CSV exato
passagens_totais = get_val("Qtd. Passagens Totais")
passagens_cpus = get_val("Qtd. Passagens CPUS")


# LINHA 1: KPIs DE PASSAGENS (VOLUME)
st.subheader("📊 Volume de Passagens")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Passagens Totais", f"{passagens_totais:,.0f}")
m2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}")
m3.metric("Passagens Internas", f"{passagens_internas:,.0f}")
m4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}")









# --- TABELA DE DADOS DETALHADA ---

with st.expander("VER DADOS BRUTOS FILTRADOS"):
    st.dataframe(
        df[['periodo', 'REGIAO', 'STATE', 'GRUPO', 'DESCR_DEALER', 'titulo', 'realizado']].sort_values(by='periodo', ascending=False)
    )









