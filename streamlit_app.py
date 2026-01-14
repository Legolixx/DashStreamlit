
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="HMB - Executive Report", layout="wide", page_icon="📈")

# CORREÇÃO: usar <style> real (sem entidades HTML) para aplicar CSS
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
    df['realizado'] = (
        df['realizado']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)
    
    # Tratamento de data
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True, errors='coerce')
    
    # Limpeza de strings para evitar erros de busca
    df['titulo'] = df['titulo'].astype(str).str.upper().str.strip()
    return df

df = carregar_dados()

# --- SIDEBAR ---
st.sidebar.image("https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png", width=150)
st.sidebar.title("Filtros")

# CORREÇÃO: opções únicas e ordenadas (formato mm/YYYY)
meses = df['periodo'].dt.strftime('%m/%Y')
opcoes_meses = sorted(meses.dropna().unique())
mes_sel = st.sidebar.select_slider("Período de análise", options=opcoes_meses)

# --- LAYOUT DO DASHBOARD ---
st.title(f"Sumário Executivo - {mes_sel}")

# CORREÇÃO: criar df_view antes de usar e filtrar corretamente
df_view = df[df['periodo'].dt.strftime('%m/%Y') == mes_sel].copy()

if df_view.empty:
    st.warning("Nenhum dado encontrado para o período selecionado. Verifique o CSV ou tente outro mês.")
else:
    # --- LÓGICA DE NEGÓCIO (Cálculo dos KPIs do Presidente) ---
    # CORREÇÃO: alinhar caixa alta no parametro e tratar ausência
    def get_val(titulo_nome: str) -> float:
        chave = str(titulo_nome).strip().upper()
        return df_view.loc[df_view['titulo'] == chave, 'realizado'].sum()

    # Exemplos de títulos (ajuste conforme seu CSV exato)
    faturamento_total = get_val("R$ Faturamento Total")  # função já converte para UPPER
    passagens_totais = get_val("Qtd. Passagens Totais")
    passagens_cpus = get_val("Qtd. Passagens CPUS")
    # CORREÇÃO: variáveis que faltavam
    passagens_internas = get_val("Qtd. Passagens Internas")
    passagens_funilaria = get_val("Funilaria e Pintura")  # ajuste o texto conforme o CSV

    # LINHA 1: KPIs DE PASSAGENS (VOLUME)
    st.subheader("📊 Volume de Passagens")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Passagens Totais", f"{passagens_totais:,.0f}")
    m2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}")
    m3.metric("Passagens Internas", f"{passagens_internas:,.0f}")
    m4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}")

    # LINHA 2: Faturamento (exemplo adicional)
    st.subheader("💰 Faturamento")
    st.metric("Faturamento Total (R$)", f"{faturamento_total:,.2f}")

    # --- TABELA DE DADOS DETALHADA ---
    with st.expander("VER DADOS BRUTOS FILTRADOS"):
        cols_existentes = [c for c in ['periodo', 'REGIAO', 'STATE', 'GRUPO', 'DESCR_DEALER', 'titulo', 'realizado'] if c in df_view.columns]
        st.dataframe(
            df_view[cols_existentes].sort_values(by='periodo', ascending=False)
        )
``
