import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Dashboard Hyundai", layout="wide", page_icon="🚗")

# --- 1. FUNÇÕES DE CARREGAMENTO E LIMPEZA ---

@st.cache_data
def carregar_dados():
    # Carrega o CSV. Assumindo que o separador é vírgula, mas ajustável
    df = pd.read_csv("ger_servicos.csv")
    return df

def limpar_dados(df):
    # Cópia para não alterar o cache original
    df_clean = df.copy()

    # 1. Tratar a coluna 'realizado' (Converter de "1.200,50" para float 1200.50)
    # Remove aspas, remove pontos de milhar, troca vírgula por ponto
    df_clean['realizado'] = df_clean['realizado'].astype(str).str.replace('"', '', regex=False)
    df_clean['realizado'] = df_clean['realizado'].str.replace('.', '', regex=False)
    df_clean['realizado'] = df_clean['realizado'].str.replace(',', '.', regex=False)
    df_clean['realizado'] = pd.to_numeric(df_clean['realizado'], errors='coerce')

    # 2. Tratar a coluna 'periodo' (Converter para Datetime)
    df_clean['periodo'] = pd.to_datetime(df_clean['periodo'], format='%d/%m/%Y', errors='coerce')

    return df_clean

def tratar_outliers(df, coluna='realizado'):
    """
    Remove outliers usando o método do Intervalo Interquartil (IQR).
    Tudo que estiver muito acima do 3º quartil ou muito abaixo do 1º é removido.
    """
    if df.empty:
        return df
        
    Q1 = df[coluna].quantile(0.25)
    Q3 = df[coluna].quantile(0.75)
    IQR = Q3 - Q1
    
    # Definindo limites (1.5 é o padrão estatístico para outliers moderados)
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR
    
    # Retorna apenas os dados dentro dos limites
    df_sem_outliers = df[(df[coluna] >= limite_inferior) & (df[coluna] <= limite_superior)]
    
    return df_sem_outliers, limite_superior

# --- 2. INTERFACE DO DASHBOARD ---

st.title("📊 Dashboard Hyundai - Análise de Serviços")
st.markdown("---")

# Carregar e Limpar
try:
    df_raw = carregar_dados()
    df = limpar_dados(df_raw)
except FileNotFoundError:
    st.error("Arquivo 'ger_servicos.csv' não encontrado. Por favor, faça o upload.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
    st.stop()

# --- SIDEBAR (Filtros) ---
st.sidebar.header("Filtros")

# Filtro de Título (Importante: não misturar R$ com Qtd na mesma análise)
titulos_unicos = df['titulo'].unique()
titulo_selecionado = st.sidebar.selectbox("Selecione o Indicador (Título):", titulos_unicos)

# Filtrar o DataFrame pelo título primeiro
df_filtrado = df[df['titulo'] == titulo_selecionado]

# Filtro de Data
min_date = df_filtrado['periodo'].min()
max_date = df_filtrado['periodo'].max()

if pd.notnull(min_date) and pd.notnull(max_date):
    data_inicio, data_fim = st.sidebar.date_input(
        "Selecione o Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    # Aplicar filtro de data
    df_filtrado = df_filtrado[
        (df_filtrado['periodo'] >= pd.to_datetime(data_inicio)) & 
        (df_filtrado['periodo'] <= pd.to_datetime(data_fim))
    ]

# Filtro de Chave (Lojas/Setores)
chaves = st.sidebar.multiselect(
    "Filtrar por Chave/Unidade:",
    options=df_filtrado['chave'].unique(),
    default=df_filtrado['chave'].unique()
)
df_filtrado = df_filtrado[df_filtrado['chave'].isin(chaves)]

# --- CONTROLE DE OUTLIERS ---
st.sidebar.markdown("---")
st.sidebar.subheader("Tratamento de Dados")
aplicar_outliers = st.sidebar.checkbox("Remover Outliers (Valores Extremos)", value=True)

df_final = df_filtrado.copy()
outliers_removidos = 0

if aplicar_outliers:
    registros_antes = len(df_final)
    df_final, teto = tratar_outliers(df_final)
    registros_depois = len(df_final)
    outliers_removidos = registros_antes - registros_depois
    
    st.sidebar.info(f"Corte aplicado acima de: {teto:,.2f}")
    if outliers_removidos > 0:
        st.sidebar.warning(f"{outliers_removidos} registros outliers removidos.")

# --- KPIS (Indicadores Chave) ---

col1, col2, col3 = st.columns(3)

total_realizado = df_final['realizado'].sum()
media_realizado = df_final['realizado'].mean()
total_registros = df_final.shape[0]

# Formatação condicional baseada no tipo de indicador (Dinheiro ou Qtd)
prefixo = "R$ " if "R$" in titulo_selecionado else ""

col1.metric("Total Realizado", f"{prefixo}{total_realizado:,.2f}")
col2.metric("Média por Registro", f"{prefixo}{media_realizado:,.2f}")
col3.metric("Registros Analisados", total_registros)

st.markdown("---")

# --- GRÁFICOS ---

row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("Evolução Temporal")
    # Agrupar por mês/data para limpar o gráfico
    df_timeline = df_final.groupby('periodo')['realizado'].sum().reset_index()
    
    fig_line = px.line(
        df_timeline, 
        x='periodo', 
        y='realizado', 
        markers=True,
        title=f"Evolução de {titulo_selecionado} ao longo do tempo"
    )
    fig_line.update_layout(xaxis_title="Período", yaxis_title="Valor Realizado")
    st.plotly_chart(fig_line, use_container_width=True)

with row1_col2:
    st.subheader("Distribuição (Boxplot)")
    # O Boxplot é ótimo para ver como ficaram os dados após limpar outliers
    fig_box = px.box(
        df_final, 
        y="realizado", 
        title="Distribuição dos Valores",
        points="all" # mostra os pontos individuais
    )
    st.plotly_chart(fig_box, use_container_width=True)

st.subheader("Performance por Chave (Unidade/Loja)")
# Top performances
df_barras = df_final.groupby('chave')['realizado'].sum().reset_index().sort_values(by='realizado', ascending=False)

fig_bar = px.bar(
    df_barras, 
    x='chave', 
    y='realizado', 
    color='realizado',
    color_continuous_scale='Blues',
    title="Comparativo por Chave"
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- VISUALIZAÇÃO DOS DADOS BRUTOS ---
with st.expander("Ver Tabela de Dados (Processados)"):
    st.dataframe(df_final.sort_values(by='periodo', ascending=False))
