
# app.py
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard Hyundai", layout="wide")
st.title("📊 DashBoard Hyundai")

# === Carregar dados ===
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path, parse_dates=['periodo_dt'])
    return df

df = load_data('ger_servicos_clean.csv')

# === Classificação dos indicadores ===
# snapshot = "estoque/capacidade no mês" -> usar média / último mês / máximo
# flow     = "fluxo do mês" -> usar soma no período
INDICATOR_TYPE = {
    "R$ Estoque Obsoleto": "snapshot",
    "Estoque Total R$": "snapshot",
    "Dias Espera": "snapshot",
    "Qtd. Atual": "snapshot",
    "Box (S/Elevador)": "snapshot",
    "Box (C/Elevador)": "snapshot",
    "Box Quick Service": "snapshot",
    "Qtd. Pneus": "snapshot",
    # Fluxos:
    "Faturamento": "flow",
    "Faturamento Car Care": "flow",
    "Faturamento de Peças": "flow",
    "Faturamento de MDO": "flow",
    "Qtd. Revisões": "flow",
    "Qtd. Passagens": "flow",
    "Qtd. Passagens CPUS": "flow",
    "Qtd. Passagens Internas": "flow",
    "Qtd. de Sanitização / Hig. Ar-Cond.": "flow",
    "Qtd de Alinh. e/ou": "flow",
    "Qtd. Car Care": "flow",
}

# títulos disponíveis efetivamente no arquivo
titulos_disponiveis = sorted(df['titulo'].dropna().unique().tolist())

# === Sidebar ===
st.sidebar.header("Filtros")

# Indicador
ind_default = "R$ Estoque Obsoleto" if "R$ Estoque Obsoleto" in titulos_disponiveis else titulos_disponiveis[0]
indicador = st.sidebar.selectbox("Indicador", options=titulos_disponiveis, index=titulos_disponiveis.index(ind_default))

# Período
min_date = pd.to_datetime(df['periodo_dt']).min()
max_date = pd.to_datetime(df['periodo_dt']).max()
start_date, end_date = st.sidebar.date_input(
    "Período",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date()
)

# Dealers
dealers = sorted(df['chave'].dropna().unique().tolist())
dealers_sel = st.sidebar.multiselect("Dealers (chave)", dealers, default=dealers)

# Outliers
hide_outliers = st.sidebar.checkbox("Excluir outliers", value=True)

# Agregação temporal condicional
tipo = INDICATOR_TYPE.get(indicador, "snapshot")
if tipo == "snapshot":
    agg_choice = st.sidebar.radio("Agregação temporal (snapshot)", ["Média Mensal", "Último Mês Visível", "Máximo Mensal"], index=0)
else:
    agg_choice = st.sidebar.radio("Agregação temporal (fluxo)", ["Soma", "Média Mensal"], index=0)

# === Filtrar base ===
mask = (
    (df['titulo'] == indicador) &
    (df['periodo_dt'] >= pd.to_datetime(start_date)) &
    (df['periodo_dt'] <= pd.to_datetime(end_date)) &
    (df['chave'].isin(dealers_sel))
)
base = df.loc[mask].copy()
if hide_outliers and 'outlier_realizado' in base.columns:
    base = base[~base['outlier_realizado']]

# Mês referência (primeiro dia do mês)
base['mes_ref'] = base['periodo_dt'].values.astype('datetime64[M]')

# === Série mensal (soma por mês entre dealers) ===
monthly = base.groupby('mes_ref', as_index=False)['realizado_num'].sum().sort_values('mes_ref')

# KPI
kpi_label = indicador
if tipo == 'snapshot':
    if agg_choice == 'Média Mensal':
        kpi_value = monthly['realizado_num'].mean()
        kpi_suffix = ' (média)'
    elif agg_choice == 'Último Mês Visível':
        kpi_value = monthly.set_index('mes_ref')['realizado_num'].iloc[-1] if len(monthly)>0 else np.nan
        kpi_suffix = ' (último mês)'
    else:
        kpi_value = monthly['realizado_num'].max()
        kpi_suffix = ' (máximo)'
else:
    if agg_choice == 'Soma':
        kpi_value = monthly['realizado_num'].sum()
        kpi_suffix = ' (soma período)'
    else:
        kpi_value = monthly['realizado_num'].mean()
        kpi_suffix = ' (média mensal)'

# Variação mês a mês (com base na série mensal)
mm_change = None
if len(monthly) >= 2:
    cur = monthly['realizado_num'].iloc[-1]
    prev = monthly['realizado_num'].iloc[-2]
    mm_change = (cur - prev) / prev if prev not in [0, np.nan] and prev != 0 else np.nan

# === KPIs ===
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=f"{kpi_label}{kpi_suffix}", value=f"{kpi_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
with col2:
    if mm_change is not None and np.isfinite(mm_change):
        st.metric(label="Variação M/M", value=f"{(mm_change*100):.1f}%")
    else:
        st.metric(label="Variação M/M", value="—")
with col3:
    st.metric(label="Meses no período", value=len(monthly))

st.divider()

# === Tendência ===
st.subheader("Tendência mensal")
st.line_chart(monthly, x='mes_ref', y='realizado_num', height=300)

# === Ranking por dealer ===
st.subheader("Ranking por Dealer")
if tipo == 'snapshot':
    dealer_month = base.groupby(['chave','mes_ref'], as_index=False)['realizado_num'].sum()
    dealer_rank = dealer_month.groupby('chave', as_index=False)['realizado_num'].mean().rename(columns={'realizado_num':'valor'})
else:
    dealer_rank = base.groupby('chave', as_index=False)['realizado_num'].sum().rename(columns={'realizado_num':'valor'})

dealer_rank = dealer_rank.sort_values('valor', ascending=False)
st.bar_chart(dealer_rank.set_index('chave').head(15))

# === Detalhamento e download ===
st.subheader("Detalhamento (linhas)")
st.dataframe(base[['periodo_dt','chave','titulo','sub_titulo','realizado_num','outlier_realizado']].sort_values(['periodo_dt','chave']))

csv = base.to_csv(index=False).encode('utf-8')
st.download_button("Baixar dados filtrados (CSV)", data=csv, file_name="dados_filtrados.csv", mime="text/csv")
