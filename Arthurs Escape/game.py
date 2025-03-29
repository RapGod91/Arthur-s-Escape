import os
import sys
import math
import random

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self):
        pygame.init()

        # Configuração inicial da janela
        pygame.display.set_caption("Arthur's Escape")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))  # Superfície menor para renderização escalada

        self.clock = pygame.time.Clock()
        
        # Controles de movimento [esquerda, direita]
        self.movement = [False, False]
        
        # Carrega todos os assets do jogo
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }
        
        # Inicializa as nuvens
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        # Inicializa o jogador
        self.player = Player(self, (50, 50), (8, 15))
        
        # Inicializa o tilemap
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Configuração de nível
        self.level = 0
        self.load_level(self.level)
        
        # Efeito de tremor de tela
        self.screenshake = 0
        
    def load_level(self, map_id):
        # Carrega o mapa do nível especificado
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
        # Configura spawners de folhas (para efeitos visuais)
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        # Configura inimigos e spawn points
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:  # Spawn do jogador
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:  # Spawn de inimigos
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
            
        # Inicializa listas de objetos do jogo
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        # Configuração de câmera e estado do jogo
        self.scroll = [0, 0]
        self.dead = 0  # Contador de morte
        self.transition = -30  # Transição entre níveis
        
    def run(self):
        while True:
            # Renderiza o fundo
            self.display.blit(self.assets['background'], (0, 0))
            
            # Atualiza o efeito de tremor de tela
            self.screenshake = max(0, self.screenshake - 1)
            
            # Lógica de transição entre níveis
            if not len(self.enemies):  # Se não há inimigos
                self.transition += 1
                if self.transition > 30:  # Espera 30 frames
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1
            
            # Lógica de morte do jogador
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)  # Recarrega o nível
            
            # Movimento suave da câmera para seguir o jogador
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Spawn de folhas aleatórias
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            # Atualiza e renderiza as nuvens
            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)
            
            # Renderiza o tilemap
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Atualiza e renderiza inimigos
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:  
                    self.enemies.remove(enemy)
            
            # Atualiza e renderiza o jogador (se não estiver morto)
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)
            
            # Atualiza e renderiza projéteis
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]  # Move o projétil
                projectile[2] += 1  # Incrementa o timer
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                # Verifica colisão com o tilemap
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    # Cria efeitos de spark ao colidir
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:  # Remove se existir por muito tempo
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:  # Verifica colisão com o jogador
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.screenshake = max(16, self.screenshake)
                        # Cria efeitos de morte
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            # Atualiza e renderiza sparks
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
            
            # Atualiza e renderiza partículas
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':  # Movimento especial para folhas
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            # Trata eventos de input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True  
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True  
                    if event.key == pygame.K_UP:
                        self.player.jump()  
                    if event.key == pygame.K_x:
                        self.player.dash()  
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False
                        
            # Efeito de transição entre níveis
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            
            # Aplica tremor de tela e renderiza na janela principal
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)  

Game().run()