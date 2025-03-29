import math

import pygame

class Spark:
    def __init__(self, pos, angle, speed):
        self.pos = list(pos)  # Posição [x, y]
        self.angle = angle  # Direção do spark
        self.speed = speed  # Velocidade
    
    def update(self):
        # Move o spark baseado no ângulo e velocidade
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed
        
        # Reduz a velocidade gradualmente
        self.speed = max(0, self.speed - 0.1)
        return not self.speed  # Retorna True quando o spark deve ser removido
    
    def render(self, surf, offset=(0, 0)):
        # Define os pontos para renderizar um polígono em forma de raio
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]
        
        # Desenha o polígono branco
        pygame.draw.polygon(surf, (255, 255, 255), render_points)