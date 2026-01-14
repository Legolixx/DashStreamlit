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

# 3. SIDEBAR (FILTROS MACRO)
st.sidebar.title("Filtros Estratégicos")
regioes = st.sidebar.multiselect("REGIAO", sorted(df['REGIAO'].unique()), default=df['REGIAO'].unique())

# Filtro de data simplificado para o Presidente
meses = df['periodo'].dt.strftime('%m/%Y').unique()
mes_sel = st.sidebar.select_slider("Período de Análise", options=sorted(meses))

# Aplicação dos filtros
df_view = df[df['REGIAO'].isin(regioes)]
df_view = df_view[df_view['periodo'].dt.strftime('%m/%Y') == mes_sel]

# 4. FUNÇÃO AUXILIAR PARA KPIS (Evita o erro de DataFrame vazio)
def calc_kpi(termos_busca):
    mask = df_view['titulo'].str.contains('|'.join(termos_busca), na=False)
    return df_view[mask]['realizado'].sum()

# Cálculos para a Visão Macro
p_cpus = calc_kpi(['CPUS'])
p_internas = calc_kpi(['INTERNAS'])
p_funilaria = calc_kpi(['FUNILARIA AND PINTURA', 'FUNILARIA E PINTURA'])
p_totais = p_cpus + p_internas + p_funilaria if (p_cpus+p_internas+p_funilaria) > 0 else calc_kpi(['PASSAGENS TOTAIS'])

fat_total = calc_kpi(['FATURAMENTO TOTAL'])
fat_funilaria = calc_kpi(['FATURAMENTO FUNILARIA'])
est_obsoleto_rs = calc_kpi(['ESTOQUE OBSOLETO'])
est_total_rs = calc_kpi(['ESTOQUE TOTAL'])

# Cálculos de Ticket Médio
tkt_geral = fat_total / p_totais if p_totais > 0 else 0
tkt_funilaria = fat_funilaria / p_funilaria if p_funilaria > 0 else 0
perc_obsoleto = (est_obsoleto_rs / est_total_rs * 100) if est_total_rs > 0 else 0

# 5. LAYOUT DO DASHBOARD
st.title(f"📊 Sumário Executivo - {mes_sel}")

# LINHA 1: PASSAGENS (O fluxo da oficina)
st.subheader("📍 Fluxo de Passagens")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Passagens Totais", f"{p_totais:,.0f}")
c2.metric("CPUS", f"{p_cpus:,.0f}", help="Passagens de Clientes")
c3.metric("Internas", f"{p_internas:,.0f}", help="Passagens de Veículos Internos/Frota")
c4.metric("Funilaria e Pintura", f"{p_funilaria:,.0f}")

st.markdown("---")

# LINHA 2: FINANCEIRO E TICKET MÉDIO
st.subheader("💸 Eficiência Financeira")
m1, m2, m3, m4 = st.columns(4)

# Lógica de cor para Ticket Médio (Meta: 500-800)
status_tkt = "normal" if 500 <= tkt_geral <= 800 else "inverse"
m1.metric("Ticket Médio Geral", f"R$ {tkt_geral:,.2f}", 
          delta=f"{tkt_geral - 650:.2f} vs Ideal", delta_color=status_tkt)

m2.metric("Tkt Médio Funilaria", f"R$ {tkt_funilaria:,.2f}")
m3.metric("Estoque Obsoleto", f"R$ {est_obsoleto_rs:,.0f}")
m4.metric("% Obsoleto/Total", f"{perc_obsoleto:.1f}%")

st.markdown("---")

# LINHA 3: RANKINGS E ANÁLISES
col_rank, col_dist = st.columns([1.5, 1])

with col_rank:
    st.subheader("🏆 Ranking Top 10 Grupos (Faturamento)")
    # Filtro específico para o ranking não dar erro
    df_rank = df_view[df_view['titulo'].str.contains('FATURAMENTO TOTAL')]
    df_rank = df_rank.groupby('GRUPO')['realizado'].sum().reset_index().sort_values('realizado', ascending=True).tail(10)
    
    if not df_rank.empty:
        fig_rank = px.bar(df_rank, x='realizado', y='GRUPO', orientation='h',
                          color='realizado', color_continuous_scale='Blues',
                          text_auto='.2s')
        fig_rank.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_rank, use_container_width=True)
    else:
        st.warning("Dados de Faturamento por Grupo não encontrados para este filtro.")

with col_dist:
    st.subheader("🌎 Distribuição por REGIAO")
    df_pie = df_view[df_view['titulo'].str.contains('FATURAMENTO TOTAL')].groupby('REGIAO')['realizado'].sum().reset_index()
    fig_pie = px.pie(df_pie, values='realizado', names='REGIAO', hole=.4, color_discrete_sequence=px.colors.qualitative.Prism)
    fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)
