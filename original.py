from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium import webdriver
from kafka import KafkaProducer
import json



#url_base = 'https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=11&action=2' #UNIVESRIDADES
url_base='https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=12&action=2' # POLITECNICO
nav = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))


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
        
        #print("Universidades encontradas:", lista_universidades)
        
    except Exception as e:
        print(f"Erro ao encontrar ou processar as universidades: {e}")   
    print('Tamanho da lista', len(lista_universidades))
    return lista_universidades  

def universidade(nav, codigo):
    # nav.get('https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=11&action=2') #UNIVERSIDADE
    # #nav.get('https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=12&action=2') #POLITECNICO
    try:
        universidade_select = WebDriverWait(nav, 10).until(
            EC.visibility_of_element_located((By.XPATH, f"//option[@value='{codigo}']"))
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

    cursos_select = WebDriverWait(nav, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//select[@name='CodCurso']"))
    )
    cursos = Select(cursos_select)
    print(cursos)

    for curso in cursos.options:
        curso_nome = curso.text
        curso_valor = curso.get_attribute('value')

        lista_cursos.append({"nome": curso_nome, "codigo": curso_valor})
    return lista_cursos

def lista_colocados(nav, curso_nome, curso_valor, dici_pu):
    try:
        curso_select = WebDriverWait(nav, 20).until(
            EC.visibility_of_element_located((By.XPATH, f"//option[@value='{curso_valor}']"))
        )
        curso_select.click()

        continuar_button = WebDriverWait(nav, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='search' and @value='Continuar']"))
        )
        continuar_button.click()

        # Inicializa a estrutura para armazenar os dados do curso atual
        colocados = []

        # Captura a tabela de colocados
        tabelas_caixa = WebDriverWait(nav, 20).until(
            EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='caixa']"))
        )

        # Processa a tabela se for encontrada
        if len(tabelas_caixa) >= 3:
            tabela_colocados = tabelas_caixa[2]
            linhas_colocados = tabela_colocados.find_elements(By.XPATH, './tbody/tr')
            for linha in linhas_colocados:
                colunas = linha.find_elements(By.XPATH, './td')
                if len(colunas) >= 2:  
                    codigo = colunas[0].text
                    nome = colunas[1].text
                    colocados.append({
                        "codigo": codigo,
                        "nome": nome
                    })
                else:
                    print("Linha de colocado sem colunas suficientes.")
        else:
            print(f"Tabelas insuficientes na página para o curso {curso_nome}.")
        
        # Armazena os colocados no dicionário
        dici_pu[curso_nome] = colocados
        nav.back()
    except Exception as e:
        print(f"Erro ao processar os colocados para o curso {curso_nome}: {e}")
        print("Conteúdo da página:", nav.page_source)  # Adicionado para depuração
    return dici_pu

# URL ORIGINAL :https://dges.gov.pt/coloc/2024/col1listas.asp?CodR=11&action=2
dici_todas_uni={}
universidades = lista_universidades(url_base)

for i in range(0, len(universidades), 2):
    uni_atual=universidades[i]
    codigo_uni=uni_atual['codigo']
    nome_uni=uni_atual['nome']
    dici_todas_uni[codigo_uni] = {
        "nome_universidade": nome_uni,
        "cod_universidade": codigo_uni,
        "cursos": []  
    }
    nav.get(url_base) 
    nav=universidade(nav, codigo_uni)
    lista_cursos=cursos(nav)
    for curso in lista_cursos:
        dici_pu={}
        codigo_curso=curso['codigo']
        nome_curso=curso['nome']
        dici_curso = {
            "nome_curso": nome_curso,
            "codigo_curso": codigo_curso,
            "colocados": []  
        }
        dici_colocados = lista_colocados(nav, nome_curso, codigo_curso, dici_curso)
        if nome_curso in dici_colocados:
            colocados = dici_colocados[nome_curso]
            dici_curso["colocados"].extend(colocados)  

    dici_todas_uni[codigo_uni]["cursos"].append(dici_curso)
    #WebDriverWait(nav, 10).until(EC.presence_of_element_located((By.XPATH, "//select[@name='CodEstab']")))


print(dici_todas_uni)
        

    
    
