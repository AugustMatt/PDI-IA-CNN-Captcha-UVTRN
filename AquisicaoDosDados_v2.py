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

# Pasta para salvar as imagens dos captchas obtidos
PASTA_CAPTCHAS = ".\\CaptchasOriginais"

# Pasta para salvar as imagens dos captchas processados
PASTA_CAPTCHAS_PROCESSADOS = ".\\CaptchasProcessados"

# Pasta para salvar as imagens dos caracteres extraidos dos captchas processados
PASTA_CARACTERES = ".\\Caracteres"

def RemoveGroupedPixels(img, group_size):
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img)
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    min_size = group_size
    removed = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            removed[output == i + 1] = 255
    return removed


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

    # Para cada arquivo de imagem na pasta dos captchas
    image_files = glob.glob(os.path.join(PASTA_CAPTCHAS, "*"))

    for (i, captcha_file) in enumerate(image_files):

        # Adquire o nome do arquivo do captcha
        nome_arquivo = captcha_file.split("\\")[2]
        
        # Abre a imagem e aplica processamento
        img = cv2.imread(captcha_file)

        # remove salt and pepper noise
        img = cv2.medianBlur(img, 3)
      
        # convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # apply threshold
        ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # erode image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        removed = cv2.erode(thresh, kernel, iterations=1)

    
        # Salva imagem processada na pasta definida
        cv2.imwrite(PASTA_CAPTCHAS_PROCESSADOS + "//" + nome_arquivo, removed)  

        os.remove(captcha_file)

    print("Processamento de imagens finalizado")

# Metodo para extrair cada caractere dos captchas processados e salvar em sua pasta especifica
def ExtrairCaracteres():

    print("Extração de caracteres iniciado...")
    
    # Para cada arquivo de imagem na pasta dos captchas processados
    image_files = glob.glob(os.path.join(PASTA_CAPTCHAS_PROCESSADOS, "*"))

    for (i, captcha_file) in enumerate(image_files):

        # Adquire uma lista com cada caracte do captcha
        nome_arquivo = captcha_file.split("\\")[2]
        nome_arquivo = nome_arquivo.split(".")[0]
        caracteres = list(nome_arquivo)

        # Abre a imagem
        img = cv2.imread(captcha_file)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)


        # find contours
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        # get the five largest contours
        if(len(cnts)>5):
            sorted_cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        elif(len(cnts)<5):
            #print("Não consegui encontrar 5 contornos ou mais nessa imagem")
            continue

        # Se foi encontrado mais contornos que caracteres, algo deu errado. 
        # Nesse caso desconsideramos essa imagem
        if len(sorted_cnts) != len(caracteres):
            #print("Não foi possivel extrair os caracteres da imagem ", captcha_file)
            os.remove(captcha_file)
            continue

        # crop the five largest contours
        cropped = []
        for c in sorted_cnts:
            x, y, w, h = cv2.boundingRect(c)
            cropped.append(img[y:y + h, x:x + w])
        
        for i in range(0, len(cropped)):
            cropped[i] = cropped[i].astype(np.uint8)
            cv2.imshow('fon', cropped[i])
            cv2.waitKey(0)

        # remove small pixels gruops from each crop
        for i in range(0, len(cropped)):
            cropped[i] = RemoveGroupedPixels(cropped[i], 100)
            
     

        # Para cada contorno obtido, adquire a imagem correspondente
        i = 0
        for crop in cropped:
            img_name = AdquirirNome(PASTA_CARACTERES + "\\" + caracteres[i])
            print(img_name)
            if(ord(caracteres[i])>=65):
                save_folder = ord(caracteres[i])-56 # Conversão do caractere para a pasta respectiva
            else:
                save_folder = caracteres[i]

            cv2.imwrite(PASTA_CARACTERES + "\\" + str(save_folder) + "\\" + str(img_name)+".png", crop)  
            i+=1

        os.remove(captcha_file)
    
    print("Extração de caracteres finalizado...")

# Obtem o primeiro nome disponivel para salvar um arquivo de imagem em uma pasta onde os arquivo são enumerados
# em ordem crescente : Ex. 1.png, 2.png, ...
def AdquirirNome(folder):

    name = 1
    while os.path.exists(folder + "\\" + str(name) + ".png"):
        name+=1
    return name



PegarCaptchas()
ProcessarCaptchas()
ExtrairCaracteres()