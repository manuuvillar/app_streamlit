from confluent_kafka import Producer
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium import webdriver
import json
import time
from selenium.webdriver.edge.options import Options

options = Options()
options.add_argument('--headless')  # Executar em modo headless
options.add_argument('--no-sandbox')  # Desabilitar sandbox
options.add_argument('--disable-dev-shm-usage')  # Usar /tmp para armazenamento temporário
options.add_argument('--disable-gpu')  # Desabilitar a aceleração de GPU
options.add_argument('--disable-software-rasterizer')  # Desabilitar o rasterizador de software
options.add_argument('--disable-extensions')  # Desabilitar extensões, se houver
options.add_argument('--window-size=1920x1080')

def acked(err, msg):
    if err is not None:
        print(f"Falha ao entregar mensagem: {str(msg)}: {str(err)}")
    else:
        print(f"Mensagem enviada: {str(msg.key())} -> {str(msg.value())}")

conf = {'bootstrap.servers': 'localhost:9092', 'client.id': 'politecnico-producer'} #'universidade-producer'
producer = Producer(conf)

# Configuração do Selenium
url_base = 'https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=12&action=2'
nav = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)

def lista_universidades(url):
    lista_universidades = []
    nav.get(url)

    try:
        universidades_select = WebDriverWait(nav, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//select[@name='CodEstab']"))
        )
        universidades = Select(universidades_select)
        
        for uni in universidades.options:
            codigo = uni.get_attribute('value')  # Código da universidade
            nome = uni.text  # Nome da universidade
            if codigo:  # Adiciona apenas se o valor não for vazio
                lista_universidades.append({"codigo": codigo, "nome": nome})
        
    except Exception as e:
        print(f"Erro ao encontrar ou processar as universidades: {e}")   
    return lista_universidades  

# Lógica principal
universidades = lista_universidades(url_base)
for uni in universidades:
    codigo_uni = uni['codigo']
    nome_uni = uni['nome']
    
    # Envia os dados da universidade como mensagem Kafka
    tarefa = {"codigo_universidade": codigo_uni, "nome_universidade": nome_uni}
    producer.produce(
        topic="politecnicos-tasks", #universidades-tasks
        key=codigo_uni,
        value=json.dumps(tarefa),
        callback=acked
    )
    producer.flush()
    time.sleep(1)

nav.quit()
producer.close()
