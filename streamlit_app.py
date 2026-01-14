import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(
    page_title="HMB - Executive Report",
    layout="wide",
    page_icon="📈"
)

st.markdown("""
<style>
.main { background-color: #f8f9fa; }
[data-testid="stMetricValue"] {
    font-size: 32px !important;
    color: #002C5F !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 24px; }
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding="latin1")

    # Tratamento numérico
    df['realizado'] = (
        df['realizado']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)

    # Tratamento de data
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)

    # Limpeza de strings
    df['titulo'] = df['titulo'].str.upper().str.strip()

    return df

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.image(
    "https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png",
    width=150
)
st.sidebar.title("Filtros")

meses = sorted(df['periodo'].dt.strftime('%m/%Y').unique())
mes_sel = st.sidebar.select_slider(
    "Período de análise",
    options=meses
)

# --- FILTRO DE DADOS ---
df_view = df[df['periodo'].dt.strftime('%m/%Y') == mes_sel]

# --- TÍTULO ---
st.title(f"Sumário Executivo - {mes_sel}")


# --- FUNÇÃO DE APOIO ---
def get_val(titulo_nome):
    return df_view.loc[
        df_view['metrica_id'] == titulo_nome,
        'realizado'
    ].sum()

# --- KPIs ---
passagens_cpus = get_val(143)
passagens_internas = get_val(144)
passagens_funilaria = get_val(154)
passagens_totais = passagens_cpus + passagens_internas + passagens_funilaria

# --- KPIs DE VOLUME ---
st.subheader("📊 Volume de Passagens")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Passagens Totais", f"{passagens_totais:,.0f}")
m2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}")
m3.metric("Passagens Internas", f"{passagens_internas:,.0f}")
m4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}")
