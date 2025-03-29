class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0):
        self.game = game  # Referência ao jogo
        self.type = p_type  # Tipo de partícula ('leaf' ou 'particle')
        self.pos = list(pos)  # Posição [x, y]
        self.velocity = list(velocity)  # Velocidade [x, y]
        # Configura a animação baseada no tipo
        self.animation = self.game.assets['particle/' + p_type].copy()
        self.animation.frame = frame  # Frame inicial
    
    def update(self):
        kill = False
        if self.animation.done:  # Se a animação terminou
            kill = True
        
        # Atualiza a posição
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        
        # Atualiza a animação
        self.animation.update()
        
        return kill  # Indica se a partícula deve ser removida
    
    def render(self, surf, offset=(0, 0)):
        # Renderiza a partícula centralizada na posição
        img = self.animation.img()
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))