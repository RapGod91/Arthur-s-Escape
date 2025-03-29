import os

import pygame

# Caminho base para imagens
BASE_IMG_PATH = 'data/images/'

def load_image(path):
    # Carrega uma imagem e define preto como cor transparente
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    # Carrega todas as imagens de um diretório
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images  # Lista de imagens
        self.loop = loop  # Se a animação deve loopar
        self.img_duration = img_dur  # Duração de cada frame
        self.done = False  # Se a animação terminou (para não loop)
        self.frame = 0  # Frame atual
    
    def copy(self):
        # Cria uma cópia da animação
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        # Atualiza o frame da animação
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        # Retorna a imagem atual
        return self.images[int(self.frame / self.img_duration)]