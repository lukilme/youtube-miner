import streamlit as st


def render(st: st):
    st.title("Painel de Indicadores")

    aba_graficos, aba_tabelas = st.tabs(["Visão Visual", "Dados Analíticos"])

    with aba_graficos:
        st.subheader("Desempenho Mensal")
        st.line_chart([10, 20, 15, 30, 45])

    with aba_tabelas:
        st.subheader("Tabela de Registros")
        st.write("Aqui entraria o seu st.dataframe().")
