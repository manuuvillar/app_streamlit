import streamlit as st
import pandas as pd
import sqlite3
import os

tabelas = {
    "candidatos": "candidatos.csv",
    "colocados": "colocados.csv",
    "candidatos_que_foram_colocados": "candidatos_que_foram_colocados.csv"
}

SENHA_CORRETA = "manu_elisa_joana"


def carregar_tabelas_no_sqlite(tabelas):
    conn = sqlite3.connect(":memory:")  
    for nome, caminho in tabelas.items():
        df = pd.read_csv(caminho)  
        df.to_sql(nome, conn, if_exists="replace", index=False)  # Salva no SQLite
    return conn


def verificar_senha(senha):
    return senha == SENHA_CORRETA


st.title("Interface de Visualização de Dados com SQL")
st.write("Realize consultas SQL nos dados carregados. Modificações não são permitidas.")


senha_input = st.text_input("Digite a senha para acessar o download:", type="password")

try:
    conn = carregar_tabelas_no_sqlite(tabelas)
    st.success("Tabelas carregadas com sucesso! Você pode executar consultas SQL.")
    
    st.write("### Tabelas Disponíveis:")
    st.write(", ".join(tabelas.keys()))

    consulta = st.text_area("Digite sua consulta SQL:", "SELECT * FROM candidatos LIMIT 10")

    if st.button("Executar Consulta"):
        try:
            # Executando a consulta
            resultado = pd.read_sql_query(consulta, conn)
            st.write("### Resultado da Consulta:")
            st.dataframe(resultado)  # Exibe os resultados na interface

            # Se o usuário inseriu a senha corretamente, liberar o download
            if senha_input:
                if verificar_senha(senha_input):
                    st.success("Senha correta! Você pode baixar o arquivo.")

                    # Gerar CSV para download
                    if not resultado.empty:
                        csv = resultado.to_csv(index=False)

                        # Botão para o usuário baixar o CSV
                        st.download_button(
                            label="Baixar Resultado em CSV",
                            data=csv,
                            file_name="resultado_consulta.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("A consulta não retornou resultados.")
                else:
                    st.error("Senha incorreta. Tente novamente.")
            else:
                st.warning("Por favor, insira a senha para baixar os dados.")
                
        except Exception as e:
            st.error(f"Erro ao executar consulta: {e}")

except Exception as e:
    st.error(f"Erro ao carregar as tabelas: {e}")
