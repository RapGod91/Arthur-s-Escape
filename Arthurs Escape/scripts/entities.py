import sys
import pygame

class PhysicsEntity:
    def __init__(self, game):
        self.game = game
        self.game.entities.append(self)

        self.img = pygame.image.load("data/images/clouds/cloud_1.png")
        self.img.set_colorkey((0, 0, 0))

        self.img_pos = [160, 260]
        self.movement = [False, False]

        self.collision_area = pygame.Rect(50, 50, 300, 50)
        