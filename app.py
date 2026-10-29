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


def atualizar_projeto(dados):
    conn = sqlite3.connect("projetos_datacenter.db")
    c = conn.cursor()
    c.execute(
        """
        UPDATE projetos 
        SET nome = ?, arquitetos = ?, empresa = ?, capex = ?, opex = ?, fase = ?, escopo = ?, status_texto = ?, proximos_passos = ?, pontos_atencao = ?, data_atualizacao = DATE('now')
        WHERE id = ?
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


# Gerenciamento de Estado para navegação e modo de edição
if "projeto_selecionado_id" not in st.session_state:
    st.session_state.projeto_selecionado_id = None

if "editando_projeto" not in st.session_state:
    st.session_state.editando_projeto = False

# Interface Principal
st.title("🏢 Gestão de Projetos - Arquitetura Datacenter")

# Navegação por Abas
aba_lista, aba_detalhes, aba_novo = st.tabs(
    ["📋 Projetos Ativos", "🔍 Ver Detalhes", "➕ Novo Projeto"]
)

df_projetos = carregar_projetos()

# ABA 1: LISTA DE PROJETOS
with aba_lista:
    st.subheader("Visualização e Atualização de Projetos Ativos")

    if not df_projetos.empty:
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

        df_filtrado = df_projetos.copy()
        if busca:
            df_filtrado = df_filtrado[
                df_filtrado["nome"].str.contains(busca, case=False)
            ]
        if filtro_fase != "Todas":
            df_filtrado = df_filtrado[df_filtrado["fase"] == filtro_fase]

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
                    st.session_state.editando_projeto = (
                        False  # Reseta o modo de edição ao trocar de projeto
                    )
                    st.rerun()
            st.divider()
    else:
        st.info("Nenhum projeto cadastrado ainda.")

# ABA 2: DETALHES E EDIÇÃO DO PROJETO
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

        # Botão para alternar o modo de edição
        col_tit, col_btn_edit = st.columns([4, 1])
        with col_tit:
            st.markdown(
                f"## {p['nome']} <span style='color:green;'>● {p['fase']}</span>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"**Empresa:** {p['empresa']} | **Arquitetos:** {p['arquitetos']} | **Última Atualização:** {p['data_atualizacao']}"
            )
        with col_btn_edit:
            st.write("")
            if st.button(
                "✏️ Editar Projeto"
                if not st.session_state.editando_projeto
                else "❌ Cancelar Edição"
            ):
                st.session_state.editando_projeto = not st.session_state.editando_projeto
                st.rerun()

        st.divider()

        # SE ESTIVER NO MODO DE EDIÇÃO
        if st.session_state.editando_projeto:
            st.info(
                "Modo de Edição Ativo. Altere os campos abaixo e clique em 'Salvar Alterações'."
            )

            with st.form("form_edicao_projeto"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    novo_nome = st.text_input("Nome do Projeto *", value=p["nome"])
                with col2:
                    novos_arq = st.text_input(
                        "Arquitetos Responsáveis *", value=p["arquitetos"]
                    )
                with col3:
                    nova_empresa = st.text_input(
                        "Empresa / Unidade *", value=p["empresa"]
                    )

                col_cap, col_op, col_fase = st.columns(3)
                with col_cap:
                    novo_capex = st.number_input(
                        "CAPEX (R$)", min_value=0.0, step=1000.0, value=float(p["capex"])
                    )
                with col_op:
                    novo_opex = st.number_input(
                        "OPEX (R$)", min_value=0.0, step=1000.0, value=float(p["opex"])
                    )
                with col_fase:
                    fases_disponiveis = [
                        "Concepção",
                        "Design Detalhado",
                        "Em Andamento (GMUD Aberta)",
                        "Homologação",
                        "Concluído",
                        "Suspenso",
                    ]
                    idx_fase = (
                        fases_disponiveis.index(p["fase"])
                        if p["fase"] in fases_disponiveis
                        else 0
                    )
                    nova_fase = st.selectbox(
                        "Fase Atual", fases_disponiveis, index=idx_fase
                    )

                novo_escopo = st.text_area(
                    "Escopo do Projeto",
                    value=p["escopo"] if pd.notna(p["escopo"]) else "",
                )
                novo_status = st.text_area(
                    "Status Atual (com datas e marcos)",
                    value=p["status_texto"] if pd.notna(p["status_texto"]) else "",
                )
                novos_passos = st.text_area(
                    "Próximos Passos",
                    value=p["proximos_passos"]
                    if pd.notna(p["proximos_passos"])
                    else "",
                )
                novos_atencao = st.text_area(
                    "Pontos de Atenção / Riscos",
                    value=p["pontos_atencao"]
                    if pd.notna(p["pontos_atencao"])
                    else "",
                )

                btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações")

                if btn_salvar_edicao:
                    if novo_nome and novos_arq and nova_empresa:
                        atualizar_projeto((
                            novo_nome,
                            novos_arq,
                            nova_empresa,
                            novo_capex,
                            novo_opex,
                            nova_fase,
                            novo_escopo,
                            novo_status,
                            novos_passos,
novos_atencao,
                            projeto_sel_id,
                        ))
                        st.session_state.editando_projeto = False
                        st.success("Projeto atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha os campos obrigatórios marcados com *.")

        # SE NÃO ESTIVER NO MODO DE EDIÇÃO (EXIBIÇÃO NORMAL)
        else:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("CAPEX Previsto", f"R$ {p['capex']:,.2f}")
            col_m2.metric("OPEX Estimado", f"R$ {p['opex']:,.2f}")
            col_m3.metric("Fase do Projeto", p
