import tensorflow as tf
from tensorflow.keras.models import load_model
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
from imutils import paths, resize


def resize_to_fit(image, width, height):
    """
    A helper function to resize an image to fit within a given size
    :param image: image to resize
    :param width: desired width in pixels
    :param height: desired height in pixels
    :return: the resized image
    """

    # grab the dimensions of the image, then initialize
    # the padding values
    (h, w) = image.shape[:2]

    # if the width is greater than the height then resize along
    # the width
    if w > h:
        image = resize(image, width=width)

    # otherwise, the height is greater than the width so resize
    # along the height
    else:
        image = resize(image, height=height)

    # determine the padding values for the width and height to
    # obtain the target dimensions
    padW = int((width - image.shape[1]) / 2.0)
    padH = int((height - image.shape[0]) / 2.0)

    # pad the image then apply one more resizing to handle any
    # rounding issues
    image = cv2.copyMakeBorder(image, padH, padH, padW, padW, cv2.BORDER_REPLICATE)
    image = cv2.resize(image, (width, height))

    # return the pre-processed image
    return image

model = load_model(r".\captcha_model.hdf5")

s=Service(ChromeDriverManager().install())  
driver = webdriver.Chrome(service=s)
driver.maximize_window()
driver.get("https://uvt2.set.rn.gov.br/#/home")
numero_de_captchas_coletados = 0

# Adquire captchas e tenta resolver indefinidadmente
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

    # Salva a imagem com a solução descrita pelo usuario
    urllib.request.urlretrieve(src, "captcha.png")

    # Abre a imagem e aplica processamento
    img = cv2.imread("captcha.png")    
    img_processada = cv2.dilate(img, np.ones((3, 3), np.uint8), iterations=1)
    img_processada = cv2.cvtColor(img_processada, cv2.COLOR_BGR2GRAY)
    _, img_processada = cv2.threshold(img_processada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    img_processada = cv2.bitwise_not(img_processada)
    
    nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(img_processada, connectivity=8)
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    min_size = 50
    img_processada2 = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            img_processada2[output == i + 1] = 255

    # Salva imagem processada na pasta definida
    cv2.imwrite("captcha_processado.png", img_processada2)  

     # Abre a imagem em escala de cinza e aplica uma binarização (necessario para usar função de contorno)
    img = cv2.imread("captcha_processado.png", cv2.IMREAD_GRAYSCALE)
    ret, img_processada = cv2.threshold(img, 127, 255, 0)

    # Adquire os contornos da imagem
    img_processada = img_processada.astype(np.uint8)
    contours, _ = cv2.findContours(img_processada.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Adquire as regiões da imagem onde estão os contornos
    # Se o contorno estiver na borda da imagem ou muito proximo a ela, o desconsidera como contorno de algum 
    # caractere
    char_regions = []
    for contour in contours:
        (x, y, width, height) = cv2.boundingRect(contour)
        if width < 10 or height < 10:
            char_regions = []
        char_regions.append((x, y, width, height))

    # Se foi encontrado mais regiões que caracteres, algo deu errado. Nesse caso desconsideramos essa imagem
    char_images = []
    if len(char_regions) != 5:
        print("Não foi possivel extrair os caracteres da imagem. Indo ao proximo")
        driver.refresh()
        continue
    
    char_images = sorted(char_regions, key=lambda x: x[0])

    # Para cada contorno obtido, adquire a imagem correspondente e teste o modelo
    caracteres = []
    j=0
    for contorno in char_images:
        caractere = img_processada[contorno[1]:contorno[1]+contorno[3], contorno[0]:contorno[0]+contorno[2]]
        #caractere = resize_to_fit(caractere, 60, 60)
        caractere = cv2.resize(caractere, (60, 60))
        #caractere = np.array(caractere, dtype="float") / 255.0
        #caractere = np.expand_dims(caractere, axis=2)
        cv2.imwrite(str(j)+".png", caractere)
        j+=1
        caractere = caractere.reshape(1, 60, 60, 1)
        caracteres.append(caractere)
    
    result = []
    predictions = []

    for caractere in caracteres:
        prediction = model.predict(caractere)
        predictions.append(prediction[0])

    aux = []
    percentage = []

    for pred in predictions:
        print("Predição: ", pred)
        index = np.where(pred == np.amax(pred))[0][0]
        percentage.append(pred[index])
        aux.append(index)
        if(index<9):
            result.append(index)
        else:
            result.append(chr(index+56))

    print(aux)
    print("porcentagem do resultado: ", percentage)
    print("resultado : ", result)
    op = input("Digite next para continuar ou sair para encerrar: ")

    

    if(op == "next"):
        driver.refresh()
    elif(op == "sair"):
        driver.quit()
        exit(0)
    
        

