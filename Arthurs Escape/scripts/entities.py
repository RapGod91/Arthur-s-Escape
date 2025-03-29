import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game  # Referência ao jogo principal
        self.type = e_type  # Tipo de entidade ('player' ou 'enemy')
        self.pos = list(pos)  # Posição [x, y]
        self.size = size  # Tamanho [width, height]
        self.velocity = [0, 0]  # Velocidade [x, y]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}  # Colisões
        
        # Configuração de animação
        self.action = ''  # Ação atual
        self.anim_offset = (-3, -3)  # Offset da animação
        self.flip = False  # Se a imagem deve ser virada
        self.set_action('idle')  # Define a ação inicial
        
        self.last_movement = [0, 0]  # Último movimento
    
    def rect(self):
        # Retorna um retângulo representando a entidade
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        # Muda a animação se for diferente da atual
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        # Reseta as colisões
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        # Calcula o movimento do frame
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        # Movimento em X e detecção de colisão
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:  # Colisão à direita
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:  # Colisão à esquerda
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        # Movimento em Y e detecção de colisão
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:  # Colisão abaixo
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:  # Colisão acima
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        # Define a direção do flip baseado no movimento
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        # Aplica gravidade
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        # Reseta a velocidade Y se estiver no chão ou teto
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        # Atualiza a animação
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        # Renderiza a entidade com flip se necessário
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        
        self.walking = 0  # Timer para andar
        
    def update(self, tilemap, movement=(0, 0)):
        # Comportamento do inimigo
        if self.walking:
            # Verifica se pode continuar andando na direção atual
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):  # Bateu em uma parede
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:  # Borda de plataforma
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            # Atira se o jogador estiver perto
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):  # Mesma altura
                    if (self.flip and dis[0] < 0):  # Jogador à esquerda
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):  # Jogador à direita
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        elif random.random() < 0.01:  # Chance de começar a andar
            self.walking = random.randint(40, 110)
        
        super().update(tilemap, movement=movement)
        
        # Define a animação baseada no movimento
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        # Colisão com dash do jogador
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                # Cria efeitos de morte
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True  # Indica que o inimigo foi morto
            
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        
        # Renderiza a arma do inimigo
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0  # Tempo no ar
        self.jumps = 1  # Número de pulos disponíveis
        self.wall_slide = False  # Se está deslizando na parede
        self.dashing = 0  # Timer de dash
    
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        
        # Morte por ficar muito tempo no ar
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        # Reseta pulos e air_time quando toca o chão
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        # Lógica de wall slide
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        # Define a animação baseada no estado
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        # Efeitos de dash
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        # Atualiza o timer de dash
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        # Aplica o movimento do dash
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            # Efeitos de partículas
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
        # Fricção
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        # Não renderiza durante o dash (para efeito visual)
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            
    def jump(self):
        # Lógica de pulo
        if self.wall_slide:  # Wall jump
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -3
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -3
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:  # Pulo normal
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        # Inicia o dash
        if not self.dashing:
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60