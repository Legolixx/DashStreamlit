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
    df = pd.read_csv(
        "ger_servicos01.csv",
        sep=";",
        encoding="utf-8-sig"
    )

    # NORMALIZA COLUNAS
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
    )

    # metrica_id
    df['metrica_id'] = (
        df['metrica_id']
        .astype(str)
        .str.replace('.0', '', regex=False)
        .str.strip()
    )
    df['metrica_id'] = pd.to_numeric(df['metrica_id'], errors='coerce')

    # realizado
    df['realizado'] = (
        df['realizado']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)

    # datas
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    df['periodo_mes'] = df['periodo'].dt.to_period('M')

    return df


df = carregar_dados()

# =========================================================
# 3. SIDEBAR – FILTRO DE PERÍODO
# =========================================================
st.sidebar.image(
    "https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png",
    width=150
)
st.sidebar.title("Filtros")

periodos = sorted(df['periodo_mes'].unique())
periodo_default = max(periodos)

periodo_sel = st.sidebar.select_slider(
    "Período de análise",
    options=periodos,
    value=periodo_default,
    format_func=lambda p: p.strftime('%m/%Y')
)

# =========================================================
# 4. FILTRO PRINCIPAL
# =========================================================
df_view = df[df['periodo_mes'] == periodo_sel]

# =========================================================
# 5. MAPA DE MÉTRICAS
# =========================================================
METRICAS_PASSAGENS = [143, 144, 154]

# =========================================================
# 6. FUNÇÕES DE NEGÓCIO
# =========================================================
def total_passagens(df_base):
    return (
        df_base[df_base['metrica_id'].isin(METRICAS_PASSAGENS)]
        ['realizado']
        .sum()
    )

# =========================================================
# 7. KPIs + DELTA MÊS A MÊS
# =========================================================
valor_atual = total_passagens(df_view)

periodo_anterior = periodo_sel - 1
valor_anterior = total_passagens(
    df[df['periodo_mes'] == periodo_anterior]
)

delta = valor_atual - valor_anterior

# =========================================================
# 8. DASHBOARD – KPIs
# =========================================================
st.title(f"📌 Sumário Executivo – {periodo_sel.strftime('%m/%Y')}")
st.subheader("📊 Volume de Passagens")

c1, c2 = st.columns([1, 3])

with c1:
    st.metric(
        "Passagens Totais",
        f"{valor_atual:,.0f}",
        delta=f"{delta:,.0f}"
    )

    if st.button("📈 Ver evolução (6 meses)"):
        st.session_state["ver_evolucao"] = True

# =========================================================
# 9. EVOLUÇÃO – ÚLTIMOS 6 MESES
# =========================================================
with c2:
    if st.session_state.get("ver_evolucao", False):
        evolucao = (
            df[df['metrica_id'].isin(METRICAS_PASSAGENS)]
            .groupby('periodo_mes')['realizado']
            .sum()
            .reset_index()
            .sort_values('periodo_mes')
            .tail(6)
        )

        fig_evolucao = px.line(
            evolucao,
            x='periodo_mes',
            y='realizado',
            markers=True,
            title="Evolução – Passagens Totais (Últimos 6 meses)"
        )

        st.plotly_chart(fig_evolucao, use_container_width=True)

# =========================================================
# 10. RANKING DE DEALERS
# =========================================================
st.subheader("🏆 Ranking de Dealers – Passagens Totais")

ranking = (
    df_view[df_view['metrica_id'].isin(METRICAS_PASSAGENS)]
    .groupby('descr_dealer')['realizado']
    .sum()
    .reset_index()
    .sort_values('realizado', ascending=False)
)

top10 = ranking.head(10)

fig_rank = px.bar(
    top10,
    x='realizado',
    y='descr_dealer',
    orientation='h',
    title="Top 10 Dealers – Mês Selecionado"
)

st.plotly_chart(fig_rank, use_container_width=True)

# =========================================================
# 11. DADOS DETALHADOS
# =========================================================
with st.expander("🔍 Ver dados brutos do período"):
    st.dataframe(
        df_view[
            [
                'periodo',
                'regiao',
                'state',
                'grupo',
                'descr_dealer',
                'metrica_id',
                'realizado'
            ]
        ].sort_values(by='realizado', ascending=False)
    )
