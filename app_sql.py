import streamlit as st
import pandas as pd
import sqlite3
import os



tabelas = {
    "candidatos": "candidatos.csv",
    "colocados": "colocados.csv",
    "candidatos_que_foram_colocados": "candidatos_que_foram_colocados.csv"
}

def carregar_tabelas_no_sqlite(tabelas):
    conn = sqlite3.connect(":memory:")  
    for nome, caminho in tabelas.items():
        df = pd.read_csv(caminho) 
        df.to_sql(nome, conn, if_exists="replace", index=False)  
    return conn

st.title("Interface de Visualização de Dados com SQL")
st.write("Realize consultas SQL nos dados carregados. Modificações não são permitidas.")

try:
    conn = carregar_tabelas_no_sqlite(tabelas)
    st.success("Tabelas carregadas com sucesso! Você pode executar consultas SQL.")

    st.write("### Tabelas Disponíveis:")
    st.write(", ".join(tabelas.keys()))

   
    consulta = st.text_area("Digite sua consulta SQL:", "SELECT * FROM candidatos LIMIT 10")

    if st.button("Executar Consulta"):
        try:
          
            resultado = pd.read_sql_query(consulta, conn)
            st.write("### Resultado da Consulta:")
            st.dataframe(resultado)

          
            if not resultado.empty:
             
                csv = resultado.to_csv(index=False)

               
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
