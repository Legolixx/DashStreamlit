import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="HMB - Executive Report", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 32px !important; color: #002C5F !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
@st.cache_data
def carregar_dados():
    # Carrega o CSV
    df = pd.read_csv("ger_servicos01.csv", sep=";", encoding='latin1')
    
    # Tratamento numérico: Remove pontos de milhar e troca vírgula por ponto decimal
    df['realizado'] = df['realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['realizado'] = pd.to_numeric(df['realizado'], errors='coerce').fillna(0)
    
    # Tratamento de data
    df['periodo'] = pd.to_datetime(df['periodo'], dayfirst=True)
    
    # Padronização da coluna de títulos (TUDO MAIÚSCULO E SEM ESPAÇOS SOBRANDO)
    df['titulo'] = df['titulo'].astype(str).str.upper().str.strip()
    
    return df

try:
    df = carregar_dados()

    # --- 3. SIDEBAR E FILTROS ---
    st.sidebar.image("https://logosmarcas.net/wp-content/uploads/2021/04/Hyundai-Logo.png", width=150)
    st.sidebar.title("Filtros")

    # Criar coluna auxiliar para o filtro de mês/ano
    df['mes_ano'] = df['periodo'].dt.strftime('%m/%Y')
    opcoes_meses = sorted(df['mes_ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))

    mes_sel = st.sidebar.select_slider("Selecione o Período", options=opcoes_meses)

    # --- 4. FILTRAGEM DOS DADOS (O df_view precisa ser criado ANTES de tudo) ---
    df_view = df[df['mes_ano'] == mes_sel].copy()

    # --- 5. FUNÇÃO DE CÁLCULO ---
    def get_val(nome_item):
        """Busca o valor somado para um título específico (case-insensitive)"""
        return df_view[df_view['titulo'] == nome_item.upper().strip()]['realizado'].sum()

    # --- 6. ATRIBUIÇÃO DOS KPIs (Ajuste os nomes entre aspas se o seu CSV for diferente) ---
    faturamento   = get_val("R$ FATURAMENTO TOTAL")
    pass_totais   = get_val("QTD. PASSAGENS TOTAIS")
    pass_cpus     = get_val("QTD. PASSAGENS CPUS")
    pass_internas = get_val("QTD. PASSAGENS INTERNAS")
    pass_funil    = get_val("QTD. PASSAGENS FUNILARIA")

    # --- 7. EXIBIÇÃO NO DASHBOARD ---
    st.title(f"Sumário Executivo - {mes_sel}")

    st.subheader("📊 Volume de Passagens")
    m1, m2, m3, m4 = st.columns(4)
    
    # Formatação para padrão brasileiro (1.234)
    m1.metric("Passagens Totais", f"{pass_totais:,.0f}".replace(",", "."))
    m2.metric("Passagens CPUS", f"{pass_cpus:,.0f}".replace(",", "."))
    m3.metric("Passagens Internas", f"{pass_internas:,.0f}".replace(",", "."))
    m4.metric("Funilaria e Pintura", f"{pass_funil:,.0f}".replace(",", "."))

    st.divider()
    
    col_fat, col_vazia = st.columns([1, 3])
    col_fat.metric("Faturamento Total", f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # --- 8. TABELA PARA CONFERÊNCIA ---
    with st.expander("🔍 Ver Tabela de Dados (Use para conferir os nomes exatos na coluna 'titulo')"):
        st.dataframe(df_view[['periodo', 'titulo', 'realizado']])

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.info("Verifique se o arquivo 'ger_servicos01.csv' está na mesma pasta do script.")
