import streamlit as st
import pandas as pd
import plotly.express as px

# =========================================================
# 1. CONFIGURAÇÃO
# =========================================================
st.set_page_config(
    page_title="HMB - Executive Report",
    layout="wide",
    page_icon="📈"
)

st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 32px !important;
    color: #002C5F !important;
}
.metric-container {
    position: relative;
}
.metric-container button {
    position: absolute;
    inset: 0;
    opacity: 0;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CARGA DOS DADOS
# =========================================================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding="latin1")

    df.columns = df.columns.str.replace("ï»¿", "", regex=False)

    df['realizado'] = (
        df['realizado']
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)

    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    df['periodo_mes'] = df['periodo'].dt.to_period("M")

    return df

df = carregar_dados()

# =========================================================
# 3. FILTRO DE PERÍODO (ORDENADO + DEFAULT MAX)
# =========================================================
meses = (
    df[['periodo_mes']]
    .drop_duplicates()
    .sort_values('periodo_mes')
)

meses_label = meses['periodo_mes'].dt.strftime('%m/%Y').tolist()
mes_default = meses_label[-1]

mes_sel = st.sidebar.select_slider(
    "Período de análise",
    options=meses_label,
    value=mes_default
)

periodo_sel = pd.Period(mes_sel, freq="M")
df_view = df[df['periodo_mes'] == periodo_sel]

st.title(f"Sumário Executivo – {mes_sel}")

# =========================================================
# 4. DEFINIÇÕES DE MÉTRICAS
# =========================================================
METRICAS = {
    "Total": [143, 144, 154],
    "CPUS": [143],
    "Internas": [144],
    "Funilaria": [154]
}

def valor_mes(metrica_ids, periodo):
    return df[
        (df['metrica_id'].isin(metrica_ids)) &
        (df['periodo_mes'] == periodo)
    ]['realizado'].sum()

def delta_mes(metrica_ids):
    atual = valor_mes(metrica_ids, periodo_sel)
    anterior = valor_mes(metrica_ids, periodo_sel - 1)
    return atual - anterior

# =========================================================
# 5. KPIs CLICÁVEIS (SEM BOTÃO VISÍVEL)
# =========================================================
cols = st.columns(4)

for col, (nome, ids) in zip(cols, METRICAS.items()):
    with col:
        key = f"toggle_{nome}"

        if key not in st.session_state:
            st.session_state[key] = False

        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric(
            f"Passagens {nome}",
            f"{valor_mes(ids, periodo_sel):,.0f}",
            f"{delta_mes(ids):,.0f}"
        )
        if st.button("", key=key):
            st.session_state[key] = not st.session_state[key]
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 6. GRÁFICOS DE EVOLUÇÃO (ABRE E FECHA)
# =========================================================
for nome, ids in METRICAS.items():
    if st.session_state.get(f"toggle_{nome}", False):

        evolucao = (
            df[df['metrica_id'].isin(ids)]
            .groupby('periodo_mes')['realizado']
            .sum()
            .reset_index()
            .sort_values('periodo_mes')
            .tail(6)
        )

        evolucao['periodo_label'] = evolucao['periodo_mes'].dt.to_timestamp()

        col1, col2 = st.columns(2)

        # 🔹 LINHA
        with col1:
            fig_linha = px.line(
                evolucao,
                x='periodo_label',
                y='realizado',
                markers=True,
                text='realizado',
                title=f"Evolução – Passagens {nome}"
            )
            fig_linha.update_traces(textposition="top center")
            fig_linha.update_xaxes(tickformat="%m/%Y")
            st.plotly_chart(fig_linha, use_container_width=True)

        # 🔹 BARRAS
        with col2:
            fig_barra = px.bar(
                evolucao,
                x='periodo_label',
                y='realizado',
                text='realizado',
                title=f"Comparativo – Passagens {nome}"
            )
            fig_barra.update_traces(textposition="outside")
            fig_barra.update_xaxes(tickformat="%m/%Y")
            st.plotly_chart(fig_barra, use_container_width=True)
