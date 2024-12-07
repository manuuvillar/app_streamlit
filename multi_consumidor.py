from confluent_kafka import Consumer
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium import webdriver
import json
import os
from selenium.webdriver.edge.options import Options
from multiprocessing import Process
import random
import tempfile
import logging

ERRO_LOG_FILE = "erros.log"

def configurar_logger():
    """Configura o logger para registrar erros."""
    logging.basicConfig(
        filename=ERRO_LOG_FILE,
        level=logging.ERROR,
        format="%(asctime)s - %(message)s",
        filemode="a",
    )

def registrar_erro(codigo_uni=None, codigo_curso=None, mensagem_erro=""):
    """Registra informações detalhadas de erro no arquivo de log."""
    erro_info = {
        "codigo_universidade": codigo_uni,
        "codigo_curso": codigo_curso,
        "erro": mensagem_erro,
    }
    logging.error(json.dumps(erro_info, ensure_ascii=False, indent=2))
    print(f"Erro registrado: {erro_info}")

# Configuração do Selenium
def iniciar_navegador():
    options = Options()
    options.add_argument('--headless')  # Executar em modo headless
    options.add_argument('--no-sandbox')  # Desabilitar sandbox
    options.add_argument('--disable-dev-shm-usage')  # Usar /tmp para armazenamento temporário
    options.add_argument('--disable-gpu')  # Desabilitar a aceleração de GPU
    options.add_argument('--disable-software-rasterizer')  # Desabilitar o rasterizador de software
    options.add_argument('--disable-extensions')  # Desabilitar extensões, se houver
    options.add_argument('--window-size=1920x1080')

    user_data_dir = tempfile.mkdtemp()  # Diretório temporário exclusivo
    options.add_argument(f'--user-data-dir={user_data_dir}')


    try:
        return webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    except Exception as e:
        print(f"Erro ao iniciar o navegador: {e}")
        registrar_erro(codigo_uni=None, nome_uni=None, mensagem_erro=f"Erro ao iniciar navegador: {str(e)}")
        return None


def salvar_em_json(dados_universidade, pasta="teste"):
    """Salva os dados da universidade em um arquivo JSON."""
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    
    codigo_uni = dados_universidade["codigo_universidade"]
    nome_arquivo = f"{pasta}/universidade_{codigo_uni}.json"
    
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados_universidade, arquivo, ensure_ascii=False, indent=4)
    
    print(f"JSON: Dados da universidade {codigo_uni} salvos em {nome_arquivo}")


def universidade(nav, codigo):
    """Seleciona a universidade pelo código no formulário e carrega sua página."""
    try:
        universidade_select = WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//option[@value='{codigo}']"))
        )
        universidade_select.click()
        
        submit_button = WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='listagem' and @value='Lista de Colocados']"))
        )
        submit_button.click()
        
    except Exception as e:
        print(f"Erro ao carregar a página da universidade com código {codigo}: {e}")
        registrar_erro(codigo_uni=codigo, codigo_curso='-', mensagem_erro=str(e))
    return nav


def cursos(nav):
    """Obtém a lista de cursos disponíveis na universidade."""
    lista_cursos = []
    try:
        cursos_select = WebDriverWait(nav, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//select[@name='CodCurso']"))
        )
        cursos = Select(cursos_select)
        
        for curso in cursos.options:
            curso_nome = curso.text
            curso_valor = curso.get_attribute('value')
            lista_cursos.append({"nome": curso_nome, "codigo": curso_valor})
    except Exception as e:
        print(f"Erro ao obter a lista de cursos: {e}")
        registrar_erro(codigo_uni='-', codigo_curso=curso_valor, mensagem_erro=str(e))
    return lista_cursos


def lista_colocados(nav, codigo_curso):
    """Obtém a lista de alunos colocados no curso."""
    colocados = []
    try:
        curso_select = WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//option[@value='{codigo_curso}']"))
        )
        curso_select.click()
        
        continuar_button = WebDriverWait(nav, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='search' and @value='Continuar']"))
        )
        continuar_button.click()
        
        tabelas_caixa = WebDriverWait(nav, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table[@class='caixa']"))
        )
        
        if len(tabelas_caixa) >= 3:
            tabela_colocados = tabelas_caixa[2]
            linhas_colocados = tabela_colocados.find_elements(By.XPATH, './tbody/tr')
            for linha in linhas_colocados:
                colunas = linha.find_elements(By.XPATH, './td')
                if len(colunas) >= 2:  # Verifica se existem pelo menos duas colunas
                    codigo = colunas[0].text.strip()
                    nome = colunas[1].text.strip()
                    colocados.append({"codigo_aluno": codigo, "nome_aluno": nome})
        nav.back()
    except Exception as e:
        print(f"Erro ao processar os colocados para o curso {codigo_curso}: {e}")
        registrar_erro(codigo_uni='-', codigo_curso=codigo_curso, mensagem_erro=str(e))
    return colocados


def consumir_mensagens(consumer_id):
    """Processa as mensagens Kafka em um consumidor."""
    consumer_conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'universidades-consumer-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'max.poll.interval.ms': 600000
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe(["universidades-tasks"])

    nav = iniciar_navegador()
    print(f"Consumidor {consumer_id} aguardando mensagens...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Erro no consumidor {consumer_id}: {msg.error()}")
                registrar_erro(codigo_uni=codigo_uni, nome_uni=nome_uni, mensagem_erro=str(msg.error()))
                continue

            tarefa = json.loads(msg.value().decode('utf-8'))
            codigo_uni = tarefa['codigo_universidade']
            nome_uni = tarefa['nome_universidade']

            print(f"Consumidor {consumer_id} processando universidade: {nome_uni} (Código: {codigo_uni})")
            nav.get("https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=11&action=2")
            nav = universidade(nav, codigo_uni)
            cursos_disponiveis = cursos(nav)

            dados_universidade = {
                "codigo_universidade": codigo_uni,
                "nome_universidade": nome_uni,
                "cursos": []
            }

            for curso in cursos_disponiveis:
                codigo_curso = curso['codigo']
                nome_curso = curso['nome']
                colocados = lista_colocados(nav, codigo_curso)
                dados_universidade["cursos"].append({
                    "codigo_curso": codigo_curso,
                    "nome_curso": nome_curso,
                    "colocados": colocados
                })

            salvar_em_json(dados_universidade)
            consumer.commit()

    except Exception as e:
        print(f"Erro no consumidor {consumer_id}: {e}")
        registrar_erro(codigo_uni=None, nome_uni=None, mensagem_erro=str(e))
        
    finally:
        print(f"Consumidor {consumer_id} finalizado.")
        nav.quit()
        consumer.close()


if __name__ == "__main__":
    configurar_logger()
    num_consumers = 10
    processes = []

    for i in range(num_consumers):
        process = Process(target=consumir_mensagens, args=(i,))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    print("Todos os consumidores finalizaram suas tarefas.")
