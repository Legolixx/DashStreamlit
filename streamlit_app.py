import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página (deve ser a primeira linha)
st.set_page_config(page_title="Dashboard Hyundai - Gestão", layout="wide", page_icon="🚘")

# --- 1. FUNÇÕES DE CARREGAMENTO E LIMPEZA ---

@st.cache_data
def carregar_dados():
    # ATENÇÃO: Mudamos o separador para ';' conforme o novo arquivo
    # encoding='latin1' ou 'utf-8' ajuda a ler acentos corretos (ex: Região)
    try:
        df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='latin1')
    return df

def limpar_dados(df):
    df_clean = df.copy()

    # 1. Tratar a coluna 'realizado'
    # Remove aspas se houver, remove ponto de milhar, troca vírgula decimal por ponto
    col_realizado = df_clean['realizado'].astype(str)
    col_realizado = col_realizado.str.replace('"', '', regex=False)
    col_realizado = col_realizado.str.replace('.', '', regex=False) # Remove ponto de milhar
    col_realizado = col_realizado.str.replace(',', '.', regex=False) # Troca vírgula por ponto
    df_clean['realizado'] = pd.to_numeric(col_realizado, errors='coerce')

    # 2. Tratar datas
    df_clean['periodo'] = pd.to_datetime(df_clean['periodo'], dayfirst=True, errors='coerce')

    # 3. Preencher nulos nas colunas de texto para evitar erros nos filtros
    cols_texto = ['REGIÃO', 'STATE', 'GRUPO', 'DESCR_DEALER', 'GERENTE']
    for col in cols_texto:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna("Não Informado").astype(str)

    return df_clean

def tratar_outliers(df, coluna='realizado'):
    if df.empty: return df, 0
    
    Q1 = df[coluna].quantile(0.25)
    Q3 = df[coluna].quantile(0.75)
    IQR = Q3 - Q1
    
    limite_superior = Q3 + 1.5 * IQR
    limite_inferior = Q1 - 1.5 * IQR
    
    # Filtra mantendo apenas o que está dentro do intervalo aceitável
    df_sem_outliers = df[(df[coluna] >= limite_inferior) & (df[coluna] <= limite_superior)]
    return df_sem_outliers, limite_superior

# --- 2. CARREGAMENTO INICIAL ---

st.title("📊 Dashboard Hyundai - Visão Estratégica")
st.markdown("---")

try:
    df_raw = carregar_dados()
    df = limpar_dados(df_raw)
except FileNotFoundError:
    st.error("Arquivo 'ger_servicos01.csv' não encontrado.")
    st.stop()

# --- 3. SIDEBAR: FILTROS HIERÁRQUICOS ---

st.sidebar.header("Filtros de Análise")

# 1. Título (Obrigatório selecionar um para a escala do gráfico fazer sentido)
titulos = df['titulo'].unique()
titulo_sel = st.sidebar.selectbox("1. Selecione o KPI (Indicador):", titulos)
df_kpi = df[df['titulo'] == titulo_sel]

# 2. Região (Multiselect) - CORRIGIDO O ESPAÇO AQUI
# Se você alterou o nome no CSV para REGIAO, mude abaixo. Se o CSV estiver original, use REGIÃO
coluna_regiao = 'REGIAO' if 'REGIAO' in df_kpi.columns else 'REGIÃO'

regioes_disp = sorted(df_kpi[coluna_regiao].unique())
regiao_sel = st.sidebar.multiselect("2. Região:", regioes_disp, default=regioes_disp)

if regiao_sel:
    df_kpi = df_kpi[df_kpi[coluna_regiao].isin(regiao_sel)]

# 3. Estado (Filtrado pelas regiões selecionadas acima)
estados_disp = sorted(df_kpi['STATE'].unique())
estado_sel = st.sidebar.multiselect("3. Estado (UF):", estados_disp, default=estados_disp)

if estado_sel:
    df_kpi = df_kpi[df_kpi['STATE'].isin(estado_sel)]

# 4. Grupo (Filtrado pelos estados selecionados)
grupos_disp = sorted(df_kpi['GRUPO'].unique())
grupo_sel = st.sidebar.multiselect("4. Grupo de Concessionárias:", options=grupos_disp)

if grupo_sel:
    df_kpi = df_kpi[df_kpi['GRUPO'].isin(grupo_sel)]

# 5. Filtro de Data
min_date = df_kpi['periodo'].min()
max_date = df_kpi['periodo'].max()

if pd.notnull(min_date) and pd.notnull(max_date):
    dates = st.sidebar.date_input("Período:", [min_date, max_date])
    # Verifica se o usuário selecionou data de inicio e fim (lista com 2 itens)
    if len(dates) == 2:
        df_kpi = df_kpi[
            (df_kpi['periodo'] >= pd.to_datetime(dates[0])) & 
            (df_kpi['periodo'] <= pd.to_datetime(dates[1]))
        ]

# --- 4. TRATAMENTO DE OUTLIERS (Switch) ---
st.sidebar.markdown("---")
usar_filtro_outliers = st.sidebar.checkbox("Remover Outliers", value=True)

df_final = df_kpi.copy()
teto_corte = 0
msg_outliers = ""

if using_filtro_outliers := usar_filtro_outliers: # Walrus operator
    linhas_antes = len(df_final)
    df_final, teto_corte = tratar_outliers(df_final)
    removidos = linhas_antes - len(df_final)
    if removidos > 0:
        msg_outliers = f"Foram removidos {removidos} registros acima de {teto_corte:,.2f}"

# --- 5. VISUALIZAÇÃO PRINCIPAL ---

# Métricas de Topo
col1, col2, col3, col4 = st.columns(4)

total = df_final['realizado'].sum()
media = df_final['realizado'].mean()
contagem = df_final.shape[0]
num_dealers = df_final['chave'].nunique()

prefixo = "R$ " if "R$" in titulo_sel else ""

col1.metric("Total Realizado", f"{prefixo}{total:,.2f}")
col2.metric("Média", f"{prefixo}{media:,.2f}")
col3.metric("Registros", contagem)
col4.metric("Dealers Ativos", num_dealers)

if msg_outliers:
    st.caption(f"ℹ️ *Nota Estatística: {msg_outliers}*")

st.markdown("---")

# LINHA 1: Evolução + Comparativo Macro
row1_1, row1_2 = st.columns([2, 1])

with row1_1:
    st.subheader("📈 Evolução Mensal")
    df_time = df_final.groupby(df_final['periodo'].dt.to_period("M"))['realizado'].sum().reset_index()
    df_time['periodo'] = df_time['periodo'].astype(str) # Converter para string para o plotly plotar bonito
    
    fig_time = px.line(df_time, x='periodo', y='realizado', markers=True, title=f"Tendência de {titulo_sel}")
    st.plotly_chart(fig_time, use_container_width=True)

with row1_2:
    st.subheader("🌎 Por Região")
    df_regiao = df_final.groupby('REGIÃO')['realizado'].sum().reset_index()
    fig_pie = px.pie(df_regiao, values='realizado', names='REGIÃO', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# LINHA 2: Análise de Dealer e Grupos
st.subheader("🏢 Performance por Grupo e Dealer")

tab1, tab2 = st.tabs(["Ranking de Grupos", "Detalhe por Dealer"])

with tab1:
    # Agrupa por GRUPO e ordena
    df_grupo = df_final.groupby('GRUPO')['realizado'].sum().reset_index().sort_values('realizado', ascending=False).head(15)
    fig_bar_grp = px.bar(
        df_grupo, 
        x='realizado', 
        y='GRUPO', 
        orientation='h', 
        title="Top 15 Grupos",
        text_auto='.2s',
        color='realizado',
        color_continuous_scale='Blues'
    )
    fig_bar_grp.update_layout(yaxis={'categoryorder':'total ascending'}) # Ordena barras
    st.plotly_chart(fig_bar_grp, use_container_width=True)

with tab2:
    # Agrupa por Dealer (Nome descritivo)
    df_dealer = df_final.groupby(['DESCR_DEALER', 'STATE'])['realizado'].sum().reset_index().sort_values('realizado', ascending=False).head(20)
    fig_bar_dealer = px.bar(
        df_dealer, 
        x='DESCR_DEALER', 
        y='realizado', 
        color='STATE', # Colore pelo estado para dar mais contexto
        title="Top 20 Concessionárias (Dealers)",
        text_auto='.2s'
    )
    st.plotly_chart(fig_bar_dealer, use_container_width=True)

# --- 6. TABELA DE DADOS DETALHADA ---
with st.expander("📂 Ver Dados Brutos Filtrados"):
    st.dataframe(
        df_final[['periodo', 'REGIÃO', 'STATE', 'GRUPO', 'DESCR_DEALER', 'titulo', 'realizado']]
        .sort_values(by='periodo', ascending=False)
    )
