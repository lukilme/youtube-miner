import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

DB_PATH_DEFAULT = "youtube.db"


@st.cache_resource(show_spinner=False)
def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}")


def list_tables(engine):
    inspector = inspect(engine)
    return inspector.get_table_names()


def render(st: st):
    st.title("SQL Explore")
    st.caption("Execute queries SQL no banco youtube.db e visualize o resultado em tabela.")

    if "query_input" not in st.session_state:
        st.session_state.query_input = "SELECT name FROM sqlite_master WHERE type='table';"
    if "sql_history" not in st.session_state:
        st.session_state.sql_history = []

    engine = None
    tables = []

    with st.sidebar:
        st.subheader("Banco de dados")
        db_path = st.text_input("Arquivo SQLite", value=DB_PATH_DEFAULT)

        try:
            engine = get_engine(db_path)
            tables = list_tables(engine)
        except Exception as e:
            st.error(f"Não foi possível abrir o banco: {e}")

        if tables:
            st.subheader("Tabelas")
            for t in tables:
                if st.button(t, use_container_width=True, key=f"tbl_{t}"):
                    st.session_state.query_input = f"SELECT * FROM {t} LIMIT 100;"
                    st.rerun()
        elif engine is not None:
            st.caption("Nenhuma tabela encontrada.")

    query = st.text_area("Digite sua query SQL", height=180, key="query_input")

    col1, _ = st.columns([1, 5])
    with col1:
        run = st.button("Executar", type="primary", use_container_width=True)

    if run:
        if not query.strip():
            st.warning("Digite uma query antes de executar.")
        elif engine is None:
            st.warning("Não foi possível conectar ao banco.")
        else:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(query))

                    if result.returns_rows:
                        df = pd.DataFrame(result.fetchall(), columns=result.keys())
                        st.success(f"{len(df)} linha(s) retornada(s).")
                        st.dataframe(df, use_container_width=True)

                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "Baixar CSV",
                            data=csv,
                            file_name="resultado.csv",
                            mime="text/csv",
                        )
                    else:
                        conn.commit()
                        st.success("Comando executado com sucesso (sem linhas de retorno).")

                st.session_state.sql_history.insert(0, query)
                st.session_state.sql_history = st.session_state.sql_history[:10]

            except SQLAlchemyError as e:
                st.error(f"Erro ao executar a query: {e}")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")

    if st.session_state.sql_history:
        with st.expander("Histórico de queries recentes"):
            for q in st.session_state.sql_history:
                st.code(q, language="sql")