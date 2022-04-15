from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import time
import cv2
import glob
import os
import numpy as np

PASTA_CAPTCHAS = ".\\CaptchasOriginais"                  # Pasta para salvar as imagens dos captchas obtidos
PASTA_CAPTCHAS_PROCESSADOS = ".\\CaptchasProcessados"    # Pasta para salvar as imagens dos captchas processados
PASTA_CARACTERES = ".\\Caracteres"                       # Pasta para salvar as imagens dos caracteres extraidos dos captchas processados

# Metodo para acessar o site da UVT RN e adquirir imagens dos captchas
# O usuario devera inserir a solução de cada captcha para que o nome da imagem seja a solução
# O metodo encerra quando o usuario digitar "sair"
# O usuario poderá pular o captcha atual digitando "pular"
def PegarCaptchas():

    s=Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=s)
    driver.maximize_window()
    driver.get("https://uvt2.set.rn.gov.br/#/home")
    numero_de_captchas_coletados = 0

    # Adquire captchas ate que o usuario digite sair
    while True:

        driver.find_element_by_id("codeaccess-btn").click()     # Acessa a pagina de login

        # Aguarda pagina de login da UVT RN carregar
        try:
            myElem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'captcha')))
            print("Pagina de login da UVT RN carregou!")
        except TimeoutException:
            print("Pagina de login da UVT RN não carregou!")
            exit(0)

        time.sleep(2)   # Tempo de ajuste para a imagem do captcha de fato aparecer na pagina

        # Adquire a imagem do captcha
        image = driver.find_element_by_xpath('//*[@id="loginBoxes"]/div/div/form/div[3]/div/img')
        src = image.get_attribute('src')

        # Aguarda o usuario digitar a solução do captcha que sera o nome do arquivo imagem
        # O usuario tambem podera digitar alguns comandos para realizar outros comportamentos no algoritmo
        # Ex. "pular" para pular esse captcha
        print("")
        print("Digite o codigo do captcha ou um dos seguintes comandos:")
        print("pular : o algoritmo ignora o captcha atual e vai para o proximo")
        print("sair : o algoritmo ignora o captcha atual e é encerrado")
        nome = input("Digite : ")

        if(nome=="pular"):

            print("Pulando o captcha atual...")

            driver.refresh()    # Atualiza a pagina
            
            # Aguarda a pagina carregar
            try:
                myElem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'codeaccess-btn')))
                print("Pagina da UVT RN carregou")
            except TimeoutException:
                print("Pagina da UVT RN não carregou")
                pass

        elif(nome=="sair"):

            print("Encerrando algoritmo de adquirir captchas...")
            driver.quit()
            break

        else:

            teste = list(nome)
            while(len(teste)!=5):
                print("O captcha tem obrigatoriamente 5 caracteres, por favor insira novamente")
                nome = input("Digite : ")
                nome = nome.upper()
                teste = list(nome)

            urllib.request.urlretrieve(src, PASTA_CAPTCHAS + "\\" + str(nome) + ".png")  # Salva a imagem com a solução descrita pelo usuario

            numero_de_captchas_coletados += 1
            print(numero_de_captchas_coletados, " captchas coletados")
            print("")

            driver.refresh()    # Atualiza a pagina
            
            # Aguarda a pagina carregar
            try:
                myElem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'codeaccess-btn')))
                print("Pagina da UVT RN carregou")
            except TimeoutException:
                print("Pagina da UVT RN não carregou")
                pass
        
     
    print("Algoritmo de adquirir imagens de captchas finalizado")

# Metodo que usa processamento digital de imagens para remover ruidos e interferencias nas imagens dos captchas
def ProcessarCaptchas():

    print("Processamento de imagens iniciado")

    image_files = glob.glob(os.path.join(PASTA_CAPTCHAS, "*"))  # Para cada arquivo de imagem na pasta dos captchas

    for (i, captcha_file) in enumerate(image_files):

        # Adquire o nome do arquivo do captcha
        nome_arquivo = captcha_file.split("\\")[2]
        nome_puro_arquivo = nome_arquivo.split(".")[0]
        caracteres = list(nome_puro_arquivo)
        
        # Abre a imagem e aplica processamento
        img = cv2.imread(captcha_file)    
        img_processada = cv2.dilate(img, np.ones((3, 3), np.uint8), iterations=1)
        img_processada = cv2.cvtColor(img_processada, cv2.COLOR_BGR2GRAY)
        _, img_processada = cv2.threshold(img_processada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        img_processada = cv2.bitwise_not(img_processada)
        img_processada2 = RemoveGroupedPixels(img_processada, 50)

        # Adquire os contornos da imagem
        img_processada2 = img_processada2.astype(np.uint8)
        contours, _ = cv2.findContours(img_processada2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Adquire as regiões da imagem onde estão os contornos
        # Se o contorno estiver na borda da imagem ou muito proximo a ela, o desconsidera como contorno de algum caractere
        char_regions = []
        for contour in contours:
            (x, y, width, height) = cv2.boundingRect(contour)
            if width < 10 or height < 10:
                char_regions = []
            char_regions.append((x, y, width, height))
           
        # Se foi encontrado mais regiões que caracteres, algo deu errado. Nesse caso desconsideramos essa imagem
        if len(caracteres) > 0:
            if len(char_regions) != len(caracteres):
                print("Não foi possivel extrair os caracteres da imagem ", captcha_file)
                os.remove(captcha_file)
                continue
        
        # ordena os contornos obtidos da esquerda para a direita
        char_images = []
        char_images = sorted(char_regions, key=lambda x: x[0])

        # Para cada contorno obtido, adquire a imagem correspondente
        i = 0
        for contorno in char_images:
            img_name = AdquirirNome(PASTA_CARACTERES + "\\" + caracteres[i])
            caractere = img_processada[contorno[1]:contorno[1]+contorno[3], contorno[0]:contorno[0]+contorno[2]]
            caractere = RemoveGroupedPixels(caractere, 100)
            if(ord(caracteres[i])>=65):
                save_folder = ord(caracteres[i])-56 # Conversão do caractere para a pasta respectiva
            else:
                save_folder = caracteres[i]

            cv2.imwrite(PASTA_CARACTERES + "\\" + str(save_folder) + "\\" + str(img_name)+".png", caractere)  
            i+=1

        os.remove(captcha_file) # remove arquivo de captcha utilizado

    print("Processamento de imagens finalizado")

# Obtem o primeiro nome disponivel para salvar um arquivo de imagem em uma pasta onde os arquivo são enumerados
# em ordem crescente : Ex. 1.png, 2.png, ...
def AdquirirNome(folder):

    name = 1
    while os.path.exists(folder + "\\" + str(name) + ".png"):
        name+=1
    return name

def RemoveGroupedPixels(img, group_size):
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img)
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    min_size = group_size
    removed = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            removed[output == i + 1] = 255
    return removed


PegarCaptchas()
ProcessarCaptchas()
