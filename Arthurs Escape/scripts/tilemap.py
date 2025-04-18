import json

import pygame

# Mapeamento de autotile baseado nos vizinhos
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,  # Canto inferior direito
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,  # Borda direita
    tuple(sorted([(-1, 0), (0, 1)])): 2,  # Canto inferior esquerdo
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,  # Borda inferior
    tuple(sorted([(-1, 0), (0, -1)])): 4,  # Canto superior esquerdo
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,  # Borda esquerda
    tuple(sorted([(1, 0), (0, -1)])): 6,  # Canto superior direito
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,  # Borda superior
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,  # Centro
}

# Offsets para verificar vizinhos
NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
# Tiles com física (colisão)
PHYSICS_TILES = {'grass', 'stone'}
# Tipos de tiles que suportam autotile
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game  # Referência ao jogo
        self.tile_size = tile_size  # Tamanho dos tiles
        self.tilemap = {}  # Dicionário de tiles na grid
        self.offgrid_tiles = []  # Tiles fora da grid (decorativos)
        
    def extract(self, id_pairs, keep=False):
        # Extrai tiles que correspondem aos tipos e variantes especificados
        matches = []
        # Verifica tiles offgrid
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
                    
        # Verifica tiles na grid
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size  # Converte para coordenadas de pixel
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        
        return matches  # Retorna os tiles encontrados
    
    def tiles_around(self, pos):
        # Retorna tiles vizinhos a uma posição
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def save(self, path):
        # Salva o tilemap em um arquivo JSON
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
        
    def load(self, path):
        # Carrega o tilemap de um arquivo JSON
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        
    def solid_check(self, pos):
        # Verifica se há um tile sólido em uma posição
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]
    
    def physics_rects_around(self, pos):
        # Retorna retângulos de colisão ao redor de uma posição
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    def autotile(self):
        # Aplica autotile baseado nos vizinhos
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            # Verifica vizinhos em 4 direções
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            # Aplica a variante correta se for um tipo de autotile
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        # Renderiza os tiles
        # Tiles offgrid primeiro (decorativos)
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))
            
        # Tiles na grid (visíveis na câmera)
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))