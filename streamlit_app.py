import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =========================================================
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

# =========================================================
# 2. CARGA E TRATAMENTO DOS DADOS
# =========================================================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding="utf-8-sig")

    # --- NORMALIZA metrica_id (CRÍTICO)
    df['metrica_id'] = (
        df['metrica_id']
        .astype(str)
        .str.replace('.0', '', regex=False)
        .str.strip()
    )
    df['metrica_id'] = pd.to_numeric(df['metrica_id'], errors='coerce')

    # --- TRATAMENTO DO REALIZADO
    df['realizado'] = (
        df['realizado']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)

    # --- DATA
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)

    # --- LIMPEZA DE TEXTO
    df['titulo'] = df['titulo'].astype(str).str.upper().str.strip()

    return df


df = carregar_dados()

# =========================================================
# 3. SIDEBAR – FILTROS
# =========================================================
st.sidebar.image(
    "https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png",
    width=150
)
st.sidebar.title("Filtros")

meses = sorted(df['periodo'].dt.strftime('%m/%Y').unique())
mes_default = (
    df['periodo']
    .max()
    .strftime('%m/%Y')
)

mes_sel = st.sidebar.select_slider(
    "Período de análise",
    options=meses,
    value=mes_default
)

# =========================================================
# 4. FILTRO PRINCIPAL
# =========================================================
df['periodo_mes'] = df['periodo'].dt.to_period('M')
periodos = sorted(df['periodo_mes'].unique())
periodo_default = max(periodos)

periodo_sel = st.sidebar.select_slider(
    "Período de análise",
    options=periodos,
    value=periodo_default,
    format_func=lambda p: p.strftime('%m/%Y')
)


# =========================================================
# 5. FUNÇÃO DE NEGÓCIO (KPI)
# =========================================================
def get_val(metrica_id: int) -> float:
    return df_view.loc[
        df_view['metrica_id'] == metrica_id,
        'realizado'
    ].sum()

# =========================================================
# 6. MAPA DE MÉTRICAS (PADRÃO BI)
# =========================================================
METRICAS = {
    "PASSAGENS_CPUS": 143,
    "PASSAGENS_INTERNAS": 144,
    "PASSAGENS_FUNILARIA": 154
}

# =========================================================
# 7. CÁLCULO DOS KPIs
# =========================================================
passagens_cpus = get_val(METRICAS["PASSAGENS_CPUS"])
passagens_internas = get_val(METRICAS["PASSAGENS_INTERNAS"])
passagens_funilaria = get_val(METRICAS["PASSAGENS_FUNILARIA"])

passagens_totais = (
    passagens_cpus +
    passagens_internas +
    passagens_funilaria
)

# =========================================================
# 8. DASHBOARD – KPIs
# =========================================================
st.title(f"📌 Sumário Executivo – {mes_sel}")
st.subheader("📊 Volume de Passagens")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Passagens Totais", f"{passagens_totais:,.0f}")
c2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}")
c3.metric("Passagens Internas", f"{passagens_internas:,.0f}")
c4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}")

# =========================================================
# 9. ALERTA DE DADOS AUSENTES (INTELIGENTE)
# =========================================================
metricas_zeradas = [
    nome for nome, mid in METRICAS.items()
    if get_val(mid) == 0
]

if metricas_zeradas:
    st.warning(
        "⚠️ Atenção: métricas sem dados no período selecionado:\n\n"
        + ", ".join(metricas_zeradas)
    )

# =========================================================
# 10. DADOS DETALHADOS
# =========================================================
with st.expander("🔍 Ver dados brutos do período"):
    st.dataframe(
        df_view[
            [
                'periodo',
                'REGIAO',
                'STATE',
                'GRUPO',
                'DESCR_DEALER',
                'metrica_id',
                'titulo',
                'realizado'
            ]
        ].sort_values(by='realizado', ascending=False)
    )
