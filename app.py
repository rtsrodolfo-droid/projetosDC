import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Gestão de Projetos - Datacenter", page_icon="🏢", layout="wide"
)


# Inicialização do Banco de Dados SQLite
def init_db():
    conn = sqlite3.connect("projetos_datacenter.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            arquitetos TEXT,
            empresa TEXT,
            capex REAL,
            opex REAL,
            fase TEXT,
            escopo TEXT,
            status_texto TEXT,
            proximos_passos TEXT,
            pontos_atencao TEXT,
            data_atualizacao DATE
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Funções de Manipulação de Dados
def salvar_projeto(dados):
    conn = sqlite3.connect("projetos_datacenter.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO projetos (nome, arquitetos, empresa, capex, opex, fase, escopo, status_texto, proximos_passos, pontos_atencao, data_atualizacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'))
    """,
        dados,
    )
    conn.commit()
    conn.close()


def carregar_projetos():
    conn = sqlite3.connect("projetos_datacenter.db")
    df = pd.read_sql_query("SELECT * FROM projetos", conn)
    conn.close()
    return df


# Gerenciamento de Estado para navegação
if "projeto_selecionado_id" not in st.session_state:
    st.session_state.projeto_selecionado_id = None

# Interface Principal
st.title("🏢 Gestão de Projetos - Arquitetura Datacenter")

# Navegação por Abas
aba_lista, aba_detalhes, aba_novo = st.tabs(
    ["📋 Projetos Ativos", "🔍 Ver Detalhes", "➕ Novo / Editar Projeto"]
)

df_projetos = carregar_projetos()

# ABA 1: LISTA DE PROJETOS (Mantendo o formato de tabela original + botão individual)
with aba_lista:
    st.subheader("Visualização e Atualização de Projetos Ativos")

    if not df_projetos.empty:
        # Filtros Rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            busca = st.text_input(
                "🔎 Buscar por Nome do Projeto:", placeholder="Digite para filtrar..."
            )
        with col_f2:
            filtro_fase = st.selectbox(
                "Filtrar por Fase:",
                ["Todas"] + list(df_projetos["fase"].unique()),
            )

        # Aplicação dos Filtros
        df_filtrado = df_projetos.copy()
        if busca:
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.contains(busca, case=False)
            ]
        if filtro_fase != "Todas":
            df_filtrado = df_filtrado[df_filtrado["fase"] == filtro_fase]

        # Tabela limpa e original
        for index, row in df_filtrado.iterrows():
            cols = st.columns([2, 2, 2, 1.5, 1.5, 1.5, 1])
            with cols[0]:
                st.text(row["nome"])
            with cols[1]:
                st.text(row["arquitetos"])
            with cols[2]:
                st.text(row["empresa"])
            with cols[3]:
                st.text(f"R$ {row['capex']:,.2f}")
            with cols[4]:
                st.text(row["fase"])
            with cols[5]:
                st.text(str(row["data_atualizacao"]))
            with cols[6]:
                if st.button("Detalhes", key=f"tbl_btn_{row['id']}"):
                    st.session_state.projeto_selecionado_id = row["id"]
                    st.rerun()
            st.divider()
    else:
        st.info("Nenhum projeto cadastrado ainda.")

# ABA 2: DETALHES DO PROJETO
with aba_detalhes:
    if not df_projetos.empty:
        ids_disponiveis = df_projetos["id"].tolist()
        indice_padrao = 0

        if st.session_state.projeto_selecionado_id in ids_disponiveis:
            indice_padrao = ids_disponiveis.index(
                st.session_state.projeto_selecionado_id
            )

        projeto_sel_id = st.selectbox(
            "Selecione o Projeto para visualizar:",
            ids_disponiveis,
            index=indice_padrao,
            format_func=lambda x: f"{x} - {df_projetos[df_projetos['id'] == x]['nome'].values[0]}",
        )

        st.session_state.projeto_selecionado_id = projeto_sel_id
        p = df_projetos[df_projetos["id"] == projeto_sel_id].iloc[0]

        st.markdown(
            f"## {p['nome']} <span style='color:green;'>● {p['fase']}</span>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"**Empresa:** {p['empresa']} | **Arquitetos:** {p['arquitetos']} | **Última Atualização:** {p['data_atualizacao']}"
        )

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("CAPEX Previsto", f"R$ {p['capex']:,.2f}")
        col_m2.metric("OPEX Estimado", f"R$ {p['opex']:,.2f}")
        col_m3.metric("Fase do Projeto", p["fase"])

        st.divider()

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.subheader("📝 Escopo")
            st.info(p["escopo"] if p["escopo"] else "Não informado.")
            st.subheader("📊 Status Atual")
            st.write(
                p["status_texto"] if p["status_texto"] else "Sem atualizações."
            )
            st.subheader("🚀 Próximos Passos")
            st.write(
                p["proximos_passos"]
                if p["proximos_passos"]
                else "Nenhum próximo passo mapeado."
            )
            st.subheader("⚠️ Pontos de Atenção / Riscos")
            st.warning(
                p["pontos_atencao"]
                if p["pontos_atencao"]
                else "Nenhum risco informado."
            )

        with col_right:
            st.subheader("💰 Resumo Financeiro")
            df_orcam = pd.DataFrame(
                {
                    "Tipo": ["CAPEX", "OPEX"],
                    "Valor": [p["capex"], p["opex"]],
                }
            )
            fig_bar = px.bar(
                df_orcam,
                x="Tipo",
                y="Valor",
                color="Tipo",
                text_auto=".2s",
                title="Distribuição do Orçamento",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ABA 3: FORMULÁRIO DE CADASTRO
with aba_novo:
    st.subheader("Registrar Novo Projeto")

    with st.form("form_cadastro_projeto", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome do Projeto *", placeholder="Ex: OTRS - DR")
        with col2:
            arquitetos = st.text_input(
                "Arquitetos Responsáveis *", placeholder="Ex: Antonacci / Zanini"
            )
        with col3:
            empresa = st.text_input(
                "Empresa / Unidade *", placeholder="Ex: Claro empresas"
            )

        col_cap, col_op, col_fase = st.columns(3)
        with col_cap:
            capex = st.number_input("CAPEX (R$)", min_value=0.0, step=1000.0)
        with col_op:
            opex = st.number_input("OPEX (R$)", min_value=0.0, step=1000.0)
        with col_fase:
            fase = st.selectbox(
                "Fase Atual",
                [
                    "Concepção",
                    "Design Detalhado",
                    "Em Andamento (GMUD Aberta)",
                    "Homologação",
                    "Concluído",
                    "Suspenso",
                ],
            )

        escopo = st.text_area("Escopo do Projeto")
        status_texto = st.text_area("Status Atual (com datas e marcos)")
        proximos_passos = st.text_area("Próximos Passos")
        pontos_atencao = st.text_area("Pontos de Atenção / Riscos")

        btn_salvar = st.form_submit_button("💾 Salvar Projeto")

        if btn_salvar:
            if nome and arquitetos and empresa:
                salvar_projeto((
                    nome,
                    arquitetos,
                    empresa,
                    capex,
                    opex,
                    fase,
                    escopo,
                    status_texto,
                    proximos_passos,
                    pontos_atencao,
                ))
                st.success("Projeto registado com sucesso!")
            else:
                st.error("Preencha os campos obrigatórios marcados com *.")
