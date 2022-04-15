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

PASTA_CAPTCHAS = ".\\CaptchasOriginais"                 # Pasta para salvar as imagens dos captchas obtidos
PASTA_CAPTCHAS_PROCESSADOS = ".\\CaptchasProcessados"   # Pasta para salvar as imagens dos captchas processados
PASTA_CARACTERES = ".\\Caracteres"                      # Pasta para salvar as imagens dos caracteres extraidos dos captchas processados


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

        # Acessa a pagina de login
        driver.find_element_by_id("codeaccess-btn").click()

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
        print("Digite o codigo do captcha ou um dos seguintes comandos:")
        print("pular : o algoritmo ignora o captcha atual e vai para o proximo")
        print("sair : o algoritmo ignora o captcha atual e é encerrado")
        nome = input("Digite : ")

        if(nome=="pular"):

            print("Pulando o captcha atual...")

            # Atualiza a pagina
            driver.refresh()
            
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
                teste = list(nome)

            # Salva a imagem com a solução descrita pelo usuario
            urllib.request.urlretrieve(src, PASTA_CAPTCHAS + "\\" + str(nome) + ".png")

            numero_de_captchas_coletados += 1
            print(numero_de_captchas_coletados, " captchas coletados")
            print("")

            # Atualiza a pagina
            driver.refresh()
            
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

        nome_arquivo = captcha_file.split("\\")[2]      # Adquire o nome do arquivo do captcha
        nome_puro_arquivo = nome_arquivo.split(".")[0]  # Nome do arquivo sem a extensão
        caracteres = list(nome_arquivo)                 # Lista com cada caractere do captcha

        img = cv2.imread(captcha_file)                  # Abre a imagem e aplica processamento
        img = cv2.medianBlur(img, 3)                    # Remove ruido sal e pimenta com o filtro gaussiano
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    # Converte a imagem para escala de cinza

        ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # Binariza os pixels da imagem

        # Aplica erosão para reduzir o ruido
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        removed = cv2.erode(thresh, kernel, iterations=1)

        # Encontra os contornos a imagem
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        
        # Se encontrar mais que cinco contornos, pega os 5 maiores contornos
        # Se encontrar menos que cinco contornos, pula o processamento e apaga a imagem atual
        if(len(cnts)>5):
            sorted_cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        elif(len(cnts)<5):
            print("Não consegui encontrar 5 contornos ou mais nessa imagem")
            os.remove(captcha_file)
            continue

        # Corta os contornos obtidos, adquirindo os caracteres
        cropped = []
        for c in sorted_cnts:
            x, y, w, h = cv2.boundingRect(c)
            cropped.append(img[y:y + h, x:x + w])

        # Ajuste de tipo....
        for i in range(0, len(cropped)):
            cropped[i] = cv2.cvtColor(cropped[i], cv2.COLOR_BGR2GRAY)
            ret, aux = cv2.threshold(cropped[i], 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            cropped[i] = aux

        # Remove grupos pequenos de pixels dos caracteres extraidos
        for i in range(0, len(cropped)):
            cropped[i] = RemoveGroupedPixels(cropped[i], 100)

        # Para cada caractere obtido, adquire a imagem correspondente
        i = 0
        for crop in cropped:

            img_name = AdquirirNome(PASTA_CARACTERES + "\\" + caracteres[i])    # Monta parte do caminho para salvar a imagem do caractere
            
            # Monta parte do caminho para salvar a imagem do caractere baseado na tabela ASCII
            if(ord(caracteres[i])>=65):
                save_folder = ord(caracteres[i])-56
            else:
                save_folder = caracteres[i]

            print("extração de caracteres sucedida... salvando em : ", PASTA_CARACTERES + "\\" + str(save_folder) + "\\" + str(img_name)+".png")
            cv2.imwrite(PASTA_CARACTERES + "\\" + str(save_folder) + "\\" + str(img_name)+".png", crop)  
            i+=1


        #os.remove(captcha_file) # Remove o arquivo utilizado para a extração dos caracteres

    print("Processamento de imagens finalizado")

def RemoveGroupedPixels(img, group_size):
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img)
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    min_size = group_size
    removed = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            removed[output == i + 1] = 255
    return removed

# Obtem o primeiro nome disponivel para salvar um arquivo de imagem em uma pasta onde os arquivo são enumerados
# em ordem crescente : Ex. 1.png, 2.png, ...
def AdquirirNome(folder):

    name = 1
    while os.path.exists(folder + "\\" + str(name) + ".png"):
        name+=1
    return name



PegarCaptchas()
ProcessarCaptchas()