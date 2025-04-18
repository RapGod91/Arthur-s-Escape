import sys
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

# Fator de escala para renderização
RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        pygame.init()

        # Configuração inicial da janela
        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))  

        self.clock = pygame.time.Clock()
        
        # Carrega os assets do jogo
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners'),
        }
        
        # Controles de movimento [esquerda, direita, cima, baixo]
        self.movement = [False, False, False, False]
        
        # Inicializa o tilemap
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Tenta carregar um mapa existente
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass
        
        # Posição da câmera
        self.scroll = [0, 0]
        
        # Lista de grupos de tiles e seleção atual
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        
        # Estados de clique e teclas
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True  # Se True, coloca tiles na grid
        
    def run(self):
        while True:
            self.display.fill((0, 0, 0))  # Limpa a tela
            
            # Atualiza a posição da câmera baseada no movimento
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Renderiza o tilemap
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Prepara a imagem do tile atual para visualização
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)  # Define transparência
            
            # Obtém a posição do mouse e calcula a posição do tile
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            # Mostra o tile atual na posição do mouse
            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)
            
            # Adiciona ou remove tiles
            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            
            # Mostra o tile atual no canto
            self.display.blit(current_tile_img, (5, 5))
            
            # Trata eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Botão esquerdo
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:  # Botão direito
                        self.right_clicking = True
                    if self.shift:  # Roda variantes com shift
                        if event.button == 4:  # Scroll up
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:  # Scroll down
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:  # Roda grupos sem shift
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True  
                    if event.key == pygame.K_d:
                        self.movement[1] = True  
                    if event.key == pygame.K_w:
                        self.movement[2] = True  
                    if event.key == pygame.K_s:
                        self.movement[3] = True  
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid  # Alterna entre ongrid/offgrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()  # Aplica autotile
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')  # Salva o mapa
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
            
            # Renderiza a tela
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)  

Editor().run()