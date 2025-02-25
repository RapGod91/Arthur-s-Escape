import pygame

pygame.init()

pygame.display.set_caption("Arthur's Escape")

screen = pygame.display.set_mode((800,600))

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    pygame.display.update()
    clock.tick(60)