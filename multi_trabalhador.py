from confluent_kafka import Consumer
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from multiprocessing import Queue, Process
import json
import os
import time

# Configuração do Selenium
def iniciar_navegador():
    options = Options()
    options.add_argument('--headless')  # Executar em modo headless
    options.add_argument('--no-sandbox')  # Desabilitar sandbox
    options.add_argument('--disable-dev-shm-usage')  # Usar /tmp para armazenamento temporário
    options.add_argument('--disable-gpu')  # Desabilitar a aceleração de GPU
    options.add_argument('--disable-software-rasterizer')  # Desabilitar o rasterizador de software
    options.add_argument('--disable-extensions')  # Desabilitar extensões
    options.add_argument('--window-size=1920x1080')
    return webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)


def salvar_em_json(dados_universidade, pasta="dados_universidades"):
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    
    codigo_uni = dados_universidade["codigo_universidade"]
    nome_arquivo = f"{pasta}/universidade_{codigo_uni}.json"
    
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados_universidade, arquivo, ensure_ascii=False, indent=4)
    
    print(f"JSON: Dados da universidade {codigo_uni} salvos em {nome_arquivo}")


def universidade(nav, codigo):
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
    return nav


def cursos(nav):
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
    return lista_cursos

def lista_colocados(nav, codigo_curso):
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
                if len(colunas) >= 2:
                    codigo = colunas[0].text.strip()
                    nome = colunas[1].text.strip()
                    colocados.append({"codigo_aluno": codigo, "nome_aluno": nome})
        nav.back()
    except Exception as e:
        print(f"Erro ao processar os colocados para o curso {codigo_curso}: {e}")
    return colocados


def kafka_consumer(queue, consumer_id):
    consumer_conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'universidade-consumer-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'max.poll.interval.ms': 600000,  # Aumentar tempo de processamento
        'max.poll.records': 5  # Processar 5 mensagens por vez
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe(["universidade-tasks"])
    print(f"Consumidor {consumer_id} aguardando mensagens...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Erro no consumidor {consumer_id}: {msg.error()}")
                continue

            tarefa = json.loads(msg.value().decode('utf-8'))
            queue.put(tarefa)
            consumer.commit()  # Commit após adicionar à fila
    finally:
        consumer.close()

# Trabalhador para processar mensagens
def processar_mensagens(queue):
    nav = iniciar_navegador()
    print("Trabalhador iniciado...")
    try:
        while True:
            if not queue.empty():
                tarefa = queue.get()
                codigo_uni = tarefa['codigo_universidade']
                nome_uni = tarefa['nome_universidade']

                print(f"Processando universidade: {nome_uni} (Código: {codigo_uni})")
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
            else:
                time.sleep(0.1)
    finally:
        nav.quit()

if __name__ == "__main__":
    task_queue = Queue()
    processes = []

    # Consumidor Kafka
    consumer_process = Process(target=kafka_consumer, args=(task_queue, 0))
    consumer_process.start()
    processes.append(consumer_process)

    # Trabalhadores
    num_workers = 10
    for _ in range(num_workers):
        worker_process = Process(target=processar_mensagens, args=(task_queue,))
        worker_process.start()
        processes.append(worker_process)

    for process in processes:
        process.join()
