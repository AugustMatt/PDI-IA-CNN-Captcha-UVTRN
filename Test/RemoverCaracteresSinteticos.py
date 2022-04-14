# Para cada pasta de caracteres, remove os gerados sinteticamente ataves do "ExpansaoDosDados.py"

import glob
import os

# Pasta para salvar as imagens dos caracteres extraidos dos captchas processados
PASTA_CARACTERES = ".\\Caracteres"

# Para cada arquivo de imagem na pasta dos captchas processados
image_files = glob.glob(os.path.join(PASTA_CARACTERES, "*"))

for (i, pasta_caractere) in enumerate(image_files):
    image_files = glob.glob(os.path.join(pasta_caractere, "*"))
    for (j, imagem) in enumerate(image_files):
        if '_synth' in imagem:
            os.remove(imagem)