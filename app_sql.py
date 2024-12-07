import streamlit as st
import pandas as pd
import sqlite3
import time

# Caminho relativo dos arquivos CSV
tabelas = {
    "candidatos": "candidatos.csv",
    "colocados": "colocados.csv",
    "candidatos_que_foram_colocados": "candidatos_que_foram_colocados.csv"
}

# Obtendo a senha do arquivo de secrets
SENHA_CORRETA = st.secrets["password"]["senha"]

def carregar_tabelas_no_sqlite(tabelas):
    conn = sqlite3.connect(":memory:")  
    for nome, caminho in tabelas.items():
        df = pd.read_csv(caminho)  # Carregar o CSV em um DataFrame
        df.to_sql(nome, conn, if_exists="replace", index=False)  # Inserir no banco de dados SQLite
    return conn

# Função para procurar aluno nas tabelas
def normalizar_nome(nome):
    # Remover acentuação
    nome_normalizado = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
    # Remover espaços extras antes e depois do nome
    return nome_normalizado.strip().lower()

# Função para procurar aluno nas tabelas
def buscar_aluno(conn, nome_aluno):
    nome_aluno_normalizado = normalizar_nome(nome_aluno)  # Normalizar o nome pesquisado
    
    query_candidatos = f"""
        SELECT codigo_estabelecimento, codigo_curso, "Nº Ordem (parcial)", cc, Nome, Nota, Opção, PI, "12º", "10º/11º", estabelecimento, escola, curso, regime_pos_laboral, regime_noturno
        FROM candidatos
        WHERE LOWER(Nome) LIKE '%{nome_aluno_normalizado}%'
    """
    
    query_candidatos_que_foram_colocados = f"""
        SELECT codigo_estabelecimento, codigo_curso, "Nº Ordem (parcial)", cc, Nome, Nota, Opção, PI, "12º", "10º/11º", estabelecimento, escola, curso, regime_pos_laboral, regime_noturno
        FROM candidatos_que_foram_colocados
        WHERE LOWER(Nome) LIKE '%{nome_aluno_normalizado}%'
    """
    
    candidatos = pd.read_sql_query(query_candidatos, conn)
    colocados = pd.read_sql_query(query_candidatos_que_foram_colocados, conn)
    
    return candidatos, colocados
# Função para verificar a senha
def verificar_senha(senha):
    return senha == SENHA_CORRETA

# Função para verificar inatividade
def verificar_inatividade(timeout_sec=900):  # 15 minutos
    current_time = time.time()
    if "ultimo_acesso" in st.session_state:
        if current_time - st.session_state["ultimo_acesso"] > timeout_sec:
            return True
    st.session_state["ultimo_acesso"] = current_time
    return False

# Limitação de tentativas de senha
MAX_TENTATIVAS = 3
if "tentativas_falhas" not in st.session_state:
    st.session_state["tentativas_falhas"] = 0

# Streamlit UI
st.title("Interface de Visualização de Dados com SQL")
st.write("Realize consultas SQL nos dados carregados. Modificações não são permitidas.")

# Campo para digitar a senha
senha_input = st.text_input("Digite a senha para acessar a consulta:", type="password")

# Verifica o número máximo de tentativas
if st.session_state["tentativas_falhas"] >= MAX_TENTATIVAS:
    st.error("Número máximo de tentativas atingido. Tente novamente mais tarde.")
else:
    if senha_input and verificar_senha(senha_input):
        st.session_state["tentativas_falhas"] = 0  # Reseta tentativas em caso de sucesso
        st.success("Senha correta! Você pode buscar as informações dos alunos.")

        # Verifica inatividade
        if verificar_inatividade():
            st.warning("Sua sessão expirou por inatividade. Por favor, insira novamente a senha.")
            senha_input = ""  # Reseta o campo de senha

        # Carregar as tabelas no SQLite
        try:
            conn = carregar_tabelas_no_sqlite(tabelas)
            st.success("Tabelas carregadas com sucesso! Você pode buscar informações de alunos.")

            # Campo para digitar o nome do aluno
            nome_aluno_input = st.text_input("Digite o nome do aluno para pesquisar:")

            if nome_aluno_input:
                # Buscar o aluno nas tabelas
                candidatos, colocados = buscar_aluno(conn, nome_aluno_input)

                # Mostrar os resultados organizados
                if not candidatos.empty:
                    st.write(f"### Informações na Tabela 'Candidatos' para '{nome_aluno_input}':")
                    st.dataframe(candidatos)  # Exibe os dados da tabela 'candidatos'
                else:
                    st.warning(f"Nenhum aluno encontrado na tabela 'Candidatos' para '{nome_aluno_input}'.")

                if not colocados.empty:
                    st.write(f"### Informações na Tabela 'Candidatos que Foram Colocados' para '{nome_aluno_input}':")
                    st.dataframe(colocados)  # Exibe os dados da tabela 'candidatos_que_foram_colocados'
                else:
                    st.warning(f"Nenhum aluno encontrado na tabela 'Candidatos que Foram Colocados' para '{nome_aluno_input}'.")

        except Exception as e:
            st.error(f"Erro ao carregar as tabelas: {e}")
    else:
        # Incrementa as tentativas falhas
        st.session_state["tentativas_falhas"] += 1
        st.error("Senha incorreta. Tente novamente.")
