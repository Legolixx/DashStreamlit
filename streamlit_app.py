import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração de visual de alto nível
st.set_page_config(page_title="Executive Dashboard | Hyundai", layout="wide", page_icon="📈")

# Estilo CSS para os cards de métricas ficarem mais "Premium"
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #002C5F; }
    [data-testid="stMetricLabel"] { font-size: 16px; font-weight: bold; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_clean():
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='latin1')
    
    # Limpeza financeira
    df['realizado'] = df['realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    
    # Padronização de nomes para facilitar cálculos
    df['titulo'] = df['titulo'].str.strip()
    return df

df = load_and_clean()

# --- SIDEBAR ESTRATÉGICA ---
st.sidebar.image("https://www.hyundai.com.br/etc.clientlibs/hyundai/clientlibs/clientlib-site/resources/images/hyundai-logo.png", width=150)
st.sidebar.title("Filtros Executivos")

# Filtro de Data (Presidente olha geralmente o mês fechado ou acumulado)
min_date, max_date = df['periodo'].min(), df['periodo'].max()
date_range = st.sidebar.date_input("Período de Análise", [min_date, max_date])

# Filtros Macro
regioes = st.sidebar.multiselect("Região", sorted(df['REGIÃO'].unique()), default=df['REGIÃO'].unique())
grupos = st.sidebar.multiselect("Grupos Econômicos", sorted(df['GRUPO'].unique()))

# Aplicação dos filtros
df_view = df[df['REGIÃO'].isin(regioes)]
if grupos:
    df_view = df_view[df_view['GRUPO'].isin(grupos)]
if len(date_range) == 2:
    df_view = df_view[(df_view['periodo'] >= pd.to_datetime(date_range[0])) & (df_view['periodo'] <= pd.to_datetime(date_range[1]))]

# --- LÓGICA DE NEGÓCIO (Cálculo dos KPIs do Presidente) ---
def get_val(titulo_nome):
    return df_view[df_view['titulo'] == titulo_nome]['realizado'].sum()

# Agrupando valores para cálculos transversais
faturamento_total = get_val("R$ Faturamento Total") # Ajuste o nome conforme seu CSV exato
passagens_totais = get_val("Qtd. Passagens Totais")
passagens_cpus = get_val("Qtd. Passagens CPUS")
passagens_internas = get_val("Qtd. Passagens Internas")
passagens_funilaria = get_val("Qtd. Passagens Funilaria e Pintura")
faturamento_funilaria = get_val("R$ Faturamento Funilaria e Pintura")
estoque_obsoleto_rs = get_val("R$ Estoque Obsoleto")
estoque_total = get_val("R$ Estoque Total") # Se tiver essa métrica no CSV

# Cálculos Derivados
ticket_medio_geral = faturamento_total / passagens_totais if passagens_totais > 0 else 0
ticket_medio_funilaria = faturamento_funilaria / passagens_funilaria if passagens_funilaria > 0 else 0
perc_obsoleto = (estoque_obsoleto_rs / estoque_total * 100) if estoque_total > 0 else 0

# --- DASHBOARD LAYOUT ---
st.title("🚗 Visão Macro de Operações - Presidência")
st.markdown(f"Exibindo dados de **{date_range[0].strftime('%d/%m/%Y')}** até **{date_range[1].strftime('%d/%m/%Y')}**")

# LINHA 1: KPIs DE PASSAGENS (VOLUME)
st.subheader("📊 Volume de Passagens")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Passagens Totais", f"{passagens_totais:,.0f}")
m2.metric("Passagens CPUS", f"{passagens_cpus:,.0f}")
m3.metric("Passagens Internas", f"{passagens_internas:,.0f}")
m4.metric("Funilaria e Pintura", f"{passagens_funilaria:,.0f}")

st.markdown("---")

# LINHA 2: TICKET MÉDIO E SAÚDE FINANCEIRA
st.subheader("💰 Ticket Médio e Eficiência")
c1, c2, c3, c4 = st.columns(4)

# Lógica de cor para o Ticket Médio (500 a 800)
cor_ticket = "normal" if 500 <= ticket_medio_geral <= 800 else "inverse"
c1.metric("Ticket Médio Geral", f"R$ {ticket_medio_geral:,.2f}", 
          delta=f"{ticket_medio_geral - 650:.2f} vs Alvo Central", delta_color=cor_ticket)

c2.metric("Tkt Médio Funilaria", f"R$ {ticket_medio_funilaria:,.2f}")

c3.metric("Estoque Obsoleto (R$)", f"R$ {estoque_obsoleto_rs:,.0f}")

c4.metric("% Obsoleto s/ Total", f"{perc_obsoleto:.1f}%")

st.markdown("---")

# LINHA 3: GRÁFICOS ESTRATÉGICOS
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Evolução Mensal: Passagens vs Ticket Médio")
    # Gráfico de duas linhas para o presidente ver se o volume sobe e o ticket cai (perda de margem)
    df_evol = df_view.groupby(df_view['periodo'].dt.to_period("M")).agg({
        'realizado': 'sum' # Aqui precisaria de um filtro específico por KPI para ser preciso
    }).reset_index()
    df_evol['periodo'] = df_evol['periodo'].astype(str)
    
    fig = px.bar(df_view[df_view['titulo'].str.contains("Passagens")], 
                 x='periodo', y='realizado', color='titulo', 
                 title="Mix de Passagens por Mês", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Performance por Região (Faturamento)")
    fig_reg = px.sunburst(df_view[df_view['titulo'].str.contains("Faturamento")], 
                          path=['REGIÃO', 'STATE'], values='realizado',
                          color='realizado', color_continuous_scale='RdBu')
    st.plotly_chart(fig_reg, use_container_width=True)

# LINHA 4: RANKINGS
st.subheader("🏆 Top 10 Grupos por Performance")
df_rank = df_view[df_view['titulo'] == "R$ Faturamento Total"].groupby('GRUPO')['realizado'].sum().reset_index()
df_rank = df_rank.sort_values('realizado', ascending=False).head(10)

fig_rank = px.bar(df_rank, x='realizado', y='GRUPO', orientation='h', 
                  text_auto='.2s', color='realizado', showlegend=False)
st.plotly_chart(fig_rank, use_container_width=True)
