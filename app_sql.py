import streamlit as st
import pandas as pd
import sqlite3
import os
import random
import string
import time


tabelas = {
    "candidatos": "candidatos.csv",
    "colocados": "colocados.csv",
    "candidatos_que_foram_colocados": "candidatos_que_foram_colocados.csv"
}

SENHA_CORRETA = '@@4$j'

def carregar_tabelas_no_sqlite(tabelas):
    conn = sqlite3.connect(":memory:")  
    for nome, caminho in tabelas.items():
        df = pd.read_csv(caminho)  
        df.to_sql(nome, conn, if_exists="replace", index=False) 
    return conn


def verificar_senha(senha):
    return senha == SENHA_CORRETA


def verificar_inatividade(timeout_sec=900):  # 15 minutos
    current_time = time.time()
    if "ultimo_acesso" in st.session_state:
        if current_time - st.session_state["ultimo_acesso"] > timeout_sec:
            return True
    st.session_state["ultimo_acesso"] = current_time
    return False

# Limitação de tentativas
MAX_TENTATIVAS = 3
if "tentativas_falhas" not in st.session_state:
    st.session_state["tentativas_falhas"] = 0

# Interface Streamlit
st.title("Interface de Visualização de Dados com SQL")
st.write("Realize consultas SQL nos dados carregados. Modificações não são permitidas.")

# Campo de senha
senha_input = st.text_input("Digite a senha para acessar o download:", type="password")

# Verifica se a senha está correta e tentativas falhas
if st.session_state["tentativas_falhas"] >= MAX_TENTATIVAS:
    st.error("Número máximo de tentativas atingido. Tente novamente mais tarde.")
else:
    if senha_input and verificar_senha(senha_input):
        st.session_state["tentativas_falhas"] = 0  # Reseta tentativas em caso de sucesso
        st.success("Senha correta! Você pode fazer a consulta e baixar os dados.")
        
        # Verifica o tempo de inatividade
        if verificar_inatividade():
            st.warning("Sua sessão expirou por inatividade. Por favor, insira novamente a senha.")
            senha_input = ""  # Reseta o campo de senha

        try:
            conn = carregar_tabelas_no_sqlite(tabelas)
            st.success("Tabelas carregadas com sucesso! Você pode executar consultas SQL.")
            st.write("### Tabelas Disponíveis:")
            st.write(", ".join(tabelas.keys()))

            # Texto área para o usuário digitar a consulta SQL
            consulta = st.text_area("Digite sua consulta SQL:", "SELECT * FROM candidatos LIMIT 10")

            if st.button("Executar Consulta"):
                try:
                    # Executando a consulta
                    resultado = pd.read_sql_query(consulta, conn)
                    st.write("### Resultado da Consulta:")
                    st.dataframe(resultado)  # Exibe os resultados na interface

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
                except Exception as e:
                    st.error(f"Erro ao executar consulta: {e}")

        except Exception as e:
            st.error(f"Erro ao carregar as tabelas: {e}")
    else:
        st.session_state["tentativas_falhas"] += 1
        st.error("Senha incorreta. Tente novamente.")
