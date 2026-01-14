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
    # Substitua pelo caminho correto do seu arquivo
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='latin1')
    
    # Tratamento numérico robusto
    df['realizado'] = df['realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)
    
    # Tratamento de data
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    
    # Limpeza de strings
    df['titulo'] = df['titulo'].str.upper().str.strip()
    return df

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.image("https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png", width=150)
st.sidebar.title("Filtros")

# Criamos uma lista de meses formatados para o slider
df['mes_ano'] = df['periodo'].dt.strftime('%m/%Y')
lista_meses = sorted(df['mes_ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))

mes_sel = st.sidebar.select_slider("Período de análise", options=lista_meses)

# --- FILTRAGEM DOS DADOS (Onde o erro acontecia) ---
# Primeiro definimos o df_view filtrado pelo mês selecionado
df_view = df[df['mes_ano'] == mes_sel].copy()

# --- LÓGICA DE NEGÓCIO ---
def get_val(titulo_nome):
    # Agora df_view já existe e pode ser acessado
    valor = df_view[df_view['titulo'] == titulo_nome.upper()]['realizado'].sum()
    return valor

# Cálculo dos KPIs
faturamento_total = get_val("R$ FATURAMENTO TOTAL")
passagens_totais  = get_val("QTD. PASSAGENS TOTAIS")
passagens_cpus    = get_val("QTD. PASSAGENS CPUS")
# Adicionei as variáveis que faltavam no seu código original para não dar erro no m3 e m4
passagens_internas = get_val("QTD. PASSAGENS INTERNAS") 
passagens_funilaria = get_val("QTD. PASSAGENS FUNILARIA")

# --- LAYOUT DO DASHBOARD ---
st.title(f"Sumário Executivo - {mes_sel}")

# LINHA 1: KPIs DE PASSAGENS (VOLUME)
st.subheader("📊 Volume de Passagens")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Passagens Totais", f"{passagens_totais:,.0f}".replace(",", "."))
m2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}".replace(",", "."))
m3.metric("Passagens Internas", f"{passagens_internas:,.0f}".replace(",", "."))
m4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}".replace(",", "."))

# --- TABELA DE DADOS DETALHADA ---
with st.expander("VER DADOS BRUTOS FILTRADOS"):
    st.dataframe(df_view)
