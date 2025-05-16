import pygame
import sys
import asyncio
import platform
import math
import time # For game_over and victory screens
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
import random # Added import for random

# --- Constants ---
W, H = 640, 400 # Adjusted to match smw_overworld_expanded for consistency
FPS = 60
GRAVITY = 0.55
JUMP_VEL = -10
TILE = 16 # SMB3 TILE size
SCALE = 2 # SMB3 Scale factor (effective tile size TILE * SCALE = 32)
RATE = 22050 # Audio sample rate

# --- Colors ---
# Combined and refined color palette
COLORS = {
    "sky": (110, 180, 240),         # From SMW
    "ground": (155, 118, 83),       # From SMB3
    "block": (198, 109, 43),        # From SMB3 (brick/question block)
    "pipe": (0, 168, 24),           # From SMB3
    "player_small": (255, 0, 0),    # From SMB3 (Mario Red)
    "player_big": (255, 99, 0),     # From SMB3 (Super Mario Orange)
    "player_fire": (255, 255, 255), # From SMB3 (Fire Mario White)
    "goomba": (168, 80, 32),        # From SMB3
    "koopa": (32, 160, 0),          # From SMB3
    "coin": (255, 219, 88),         # From SMB3
    "hud": (255, 255, 255),         # From SMB3 (White for HUD text)
    "pause_bg": (0, 0, 0),          # From SMB3
    # Overworld specific colors from SMW
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (220, 50, 50),           # Overworld Node/Castle
    'GREEN': (60, 220, 60),         # Overworld Node Default
    'BLUE': (50, 90, 220),
    'YELLOW': (240, 220, 70),       # Overworld Switch Node
    'BROWN': (170, 100, 40),        # Platform color from SMW (can be an alternative)
    'GRAY': (120, 120, 120),        # Overworld Path
    'ORANGE': (220, 120, 30),       # Overworld Fortress Node
    'PURPLE': (120, 60, 180),
    'PINK': (255, 150, 190),
    'LIGHT_BLUE': (173, 216, 230),
    'DARK_GREEN': (34, 139, 34),    # Overworld Background from SMB3
}

# --- Sound Generation (from SMB3) ---
def tone(freq: int, ms: int, vol_multiplier: float = 0.5):
    """Generates a pygame.mixer.Sound object for a tone."""
    if pygame.mixer.get_init() is None: # Ensure mixer is initialized
        print("Mixer not initialized for tone generation!")
        return None
    if freq <= 0: # Avoid math domain error for log or issues with zero/negative frequencies
        # Return a short silent sound if frequency is invalid
        return pygame.mixer.Sound(np.zeros((int(RATE * ms / 1000), 1), dtype=np.int16))
    t = np.linspace(0, ms / 1000, int(RATE * ms / 1000), False)
    # Using a square wave for more distinct beeps, similar to classic games
    wave = vol_multiplier * np.sign(np.sin(freq * 2 * np.pi * t))
    sound_array = (wave * 32767).astype(np.int16)[:, np.newaxis] # Ensure 2D for stereo, even if mono content
    return pygame.mixer.Sound(sound_array)

# --- Data Structures (from SMB3) ---
@dataclass
class LevelSpec:
    """Specification for a single level's content."""
    name: str # e.g., "1-1"
    platforms: List[Tuple[int, int, int, int]] # (x, y, width, height) in pixels
    blocks: List[Tuple[int, int]] # (tile_x, tile_y) for breakable/question blocks
    coins: List[Tuple[int, int]] # (tile_x, tile_y)
    enemies: List[Tuple[int, int, str]] # (x, y, type_string) in pixels
    goal: Tuple[int, int] # (x, y) of goal object (e.g., flagpole base) in pixels
    background_color: Tuple[int,int,int] = COLORS["sky"]
    # Add other level-specific properties here: pipes, powerups, etc.

# --- Overworld Map Data (from smw_overworld_expanded) ---
SMW_STYLE_MAP_DATA = [
    {
        'name': "Yoshi's Island", # World 1 (index 0)
        'nodes': [
            {'pos': (60, 300), 'level_id': (0, 0), 'label': "YI 1"},
            {'pos': (120, 270), 'level_id': (0, 1), 'label': "YI 2"},
            {'pos': (90, 220), 'level_id': (0, 2), 'label': "Ylw Switch", 'type': 'switch'},
            {'pos': (180, 240), 'level_id': (0, 3), 'label': "YI 3"},
            {'pos': (240, 270), 'level_id': (0, 4), 'label': "YI 4"},
            {'pos': (300, 300), 'level_id': (0, 5), 'label': "#1 Iggy", 'type': 'castle'},
        ]
    },
    {
        'name': 'Donut Plains', # World 2 (index 1)
        'nodes': [
            {'pos': (60, 180), 'level_id': (1, 0), 'label': "DP 1"},
            {'pos': (120, 150), 'level_id': (1, 1), 'label': "DP 2"},
            {'pos': (90, 100), 'level_id': (1, 2), 'label': "Grn Switch", 'type': 'switch'},
            {'pos': (180, 120), 'level_id': (1, 3), 'label': "DP Secret"},
            {'pos': (240, 150), 'level_id': (1, 4), 'label': "DP 3"},
            {'pos': (300, 180), 'level_id': (1, 5), 'label': "DP 4"},
            {'pos': (360, 150), 'level_id': (1, 6), 'label': "DP Ghost", 'type': 'ghost'},
            {'pos': (420, 180), 'level_id': (1, 7), 'label': "#2 Morton", 'type': 'castle'},
        ]
    },
    {
        'name': 'Vanilla Dome', # World 3 (index 2)
        'nodes': [
            {'pos': (400, 80), 'level_id': (2, 0), 'label': "VD 1"},
            {'pos': (460, 50), 'level_id': (2, 1), 'label': "VD 2"},
            {'pos': (430, 120), 'level_id': (2, 2), 'label': "Red Switch", 'type': 'switch'},
            {'pos': (520, 90), 'level_id': (2, 3), 'label': "VD 3"},
            {'pos': (580, 60), 'level_id': (2, 4), 'label': "VD Ghost", 'type': 'ghost'},
            {'pos': (550, 130), 'level_id': (2, 5), 'label': "#3 Lemmy", 'type': 'castle'},
        ]
    },
    {
        'name': 'Twin Bridges', # World 4 (index 3)
        'nodes': [
            {'pos': (80, 350), 'level_id': (3, 0), 'label': "V.Fortress", 'type':'fortress'},
            {'pos': (150, 320), 'level_id': (3, 1), 'label': "Cookie Mtn"},
            {'pos': (220, 350), 'level_id': (3, 2), 'label': "Butter Br 1"},
            {'pos': (290, 320), 'level_id': (3, 3), 'label': "Butter Br 2"},
            {'pos': (360, 350), 'level_id': (3, 4), 'label': "Cheese Br"},
            {'pos': (430, 320), 'level_id': (3, 5), 'label': "#4 Ludwig", 'type': 'castle'},
        ]
    },
    {
        'name': 'Forest of Illusion', # World 5 (index 4)
        'nodes': [
            {'pos': (500, 250), 'level_id': (4, 0), 'label': "FoI 1"},
            {'pos': (560, 220), 'level_id': (4, 1), 'label': "FoI 2"},
            {'pos': (530, 170), 'level_id': (4, 2), 'label': "Blu Switch", 'type': 'switch'},
            {'pos': (470, 190), 'level_id': (4, 3), 'label': "FoI 3"},
            {'pos': (540, 280), 'level_id': (4, 4), 'label': "FoI Ghost", 'type': 'ghost'},
            {'pos': (590, 200), 'level_id': (4, 5), 'label': "FoI Secret"},
            {'pos': (500, 140), 'level_id': (4, 6), 'label': "#5 Roy", 'type': 'castle'},
        ]
    },
    {
        'name': 'Chocolate Island', # World 6 (index 5)
        'nodes': [
            {'pos': (80, 50), 'level_id': (5, 0), 'label': "CI 1"},
            {'pos': (140, 80), 'level_id': (5, 1), 'label': "CI 2"},
            {'pos': (200, 50), 'level_id': (5, 2), 'label': "CI 3"},
            {'pos': (170, 110), 'level_id': (5, 3), 'label': "CI Ghost", 'type': 'ghost'},
            {'pos': (260, 80), 'level_id': (5, 4), 'label': "CI Secret"},
            {'pos': (320, 50), 'level_id': (5, 5), 'label': "ChocoFort", 'type':'fortress'},
            {'pos': (290, 120), 'level_id': (5, 6), 'label': "#6 Wendy", 'type': 'castle'},
        ]
    },
    {
        'name': 'Valley of Bowser', # World 7 (index 6)
        'nodes': [
            {'pos': (450, 350), 'level_id': (6, 0), 'label': "VB 1"},
            {'pos': (500, 320), 'level_id': (6, 1), 'label': "VB 2"},
            {'pos': (550, 350), 'level_id': (6, 2), 'label': "VB Ghost", 'type':'ghost'},
            {'pos': (500, 380), 'level_id': (6, 3), 'label': "VB Castle", 'type':'fortress'}, # Valley Fortress
            {'pos': (580, 300), 'level_id': (6, 4), 'label': "Bowser's", 'type': 'castle'},
        ]
    },
    {
        'name': 'Star World', # World 8 (index 7)
        'nodes': [
            {'pos': (100, 30), 'level_id': (7, 0), 'label': "SW 1"},
            {'pos': (180, 30), 'level_id': (7, 1), 'label': "SW 2"},
            {'pos': (260, 30), 'level_id': (7, 2), 'label': "SW 3"},
            {'pos': (340, 30), 'level_id': (7, 3), 'label': "SW 4"},
            {'pos': (420, 30), 'level_id': (7, 4), 'label': "SW 5"},
        ]
    },
    {
        'name': 'Special Zone', # World 9 (index 8)
        'nodes': [
            {'pos': (500, 30), 'level_id': (8, 0), 'label': "Gnarly"},
            {'pos': (500, 70), 'level_id': (8, 1), 'label': "Tubular"},
            {'pos': (500, 110), 'level_id': (8, 2), 'label': "WayCool"},
            {'pos': (500, 150), 'level_id': (8, 3), 'label': "Awesome"},
            {'pos': (500, 190), 'level_id': (8, 4), 'label': "Groovy"},
            {'pos': (500, 230), 'level_id': (8, 5), 'label': "Mondo"},
            {'pos': (500, 270), 'level_id': (8, 6), 'label': "Outrage"},
            {'pos': (500, 310), 'level_id': (8, 7), 'label': "Funky"},
        ]
    }
]

# --- Level Specifications ---
GAME_LEVEL_SPECS: Dict[Tuple[int, int], LevelSpec] = {}

def _create_placeholder_level_spec(world_idx: int, node_idx: int, node_data: Dict) -> LevelSpec:
    """Creates a simple placeholder LevelSpec for a given node."""
    level_name = node_data.get('label', f"W{world_idx+1}-N{node_idx+1}")
    platforms = [(0, H - (TILE * SCALE), W * 2, TILE * SCALE)] # Extended ground for scrolling
    
    # Ensure tile coordinates are within reasonable bounds for a level of width W
    # Max tile_x should be less than (Level Width / Tile Size) - some margin
    max_tile_x = (W * 2) // (TILE * SCALE) - 5 
    
    blocks = []
    for _ in range(random.randint(5,10)): # More blocks for a wider level
        bx = random.randint(5, max_tile_x)
        by = random.randint(H // (TILE*SCALE) - 12, H // (TILE*SCALE) - 5) # Blocks higher up
        blocks.append((bx,by))

    coins = []
    for _ in range(random.randint(8,15)): # More coins
        cx = random.randint(5, max_tile_x)
        cy = random.randint(H // (TILE*SCALE) - 15, H // (TILE*SCALE) - 7) # Coins can be higher
        coins.append((cx,cy))

    enemies = []
    for _ in range(random.randint(2,4)): # A few enemies
        etype = random.choice(["goomba", "koopa"])
        ex = random.randint(W // 4, W * 2 - W // 4) # Enemies spread out
        # Ensure enemies spawn on the main ground platform
        enemy_h = TILE * SCALE if etype == "goomba" else TILE * SCALE + TILE//2 * SCALE
        ey = H - (TILE * SCALE) - enemy_h # y position for enemy feet to be on ground
        enemies.append((ex, ey, etype))


    return LevelSpec(
        name=level_name,
        platforms=platforms,
        blocks=blocks,
        coins=coins,
        enemies=enemies,
        goal=(W * 2 - (TILE * SCALE * 3), H - (TILE * SCALE) * 3), # Goal further in
        background_color=random.choice([COLORS["sky"], (100,149,237), (135,206,250)]) # Random sky variant
    )

# Populate GAME_LEVEL_SPECS
smb3_level_definitions = [
    [ # World 1 in SMB3 structure
        LevelSpec("1-1", platforms=[(0, H - 32, W, 32), (W+50, H-32, W, 32)], blocks=[(6, 18), (7, 18), (12, 16), (25,18)], coins=[(10, 14), (14, 14), (27,16)], enemies=[(200, H - 32 - 32, "goomba"), (380, H - 32 - 32, "koopa"), (W+100, H-32-32, "goomba")], goal=(W + W - 60, H - 64)),
        LevelSpec("1-2", platforms=[(0, H - 32, W // 2, 32), (W // 2 + 100, H - 32, W // 2 - 100, 32), (W, H-32, W, 32)], blocks=[(5, 17), (15, 15), (20, 13)], coins=[(8, 15), (18, 13)], enemies=[(150, H - 32 - 32, "goomba"), (450, H - 32 - 32, "koopa")], goal=(W+W-60, H - 64)),
        LevelSpec("1-3", platforms=[(0, H - 32, W, 32), (100, H - 96, 150, 32), (W, H-32, W,32)], blocks=[(8, 16), (9, 16), (10, 16)], coins=[(12, 14), (13, 14)], enemies=[(250, H - 32-32, "goomba"), (350, H - 32-32, "koopa")], goal=(W+W-60, H - 64)),
    ],
    [ # World 2 in SMB3 structure
        LevelSpec("2-1", platforms=[(0, H - 32, W*2, 32)], blocks=[(5, 18), (20,17)], coins=[(10, 16), (25,15)], enemies=[(200, H - 32-32, "goomba")], goal=(W*2 - 60, H - 64))
    ]
]

# Mapping SMB3 style definitions to SMW Overworld nodes
# This needs careful manual mapping.
# Example: (SMW_world_idx, SMW_node_idx) -> smb3_level_definitions[smb3_world_idx][smb3_level_idx_in_world]
level_map_config = {
    (0,0): smb3_level_definitions[0][0], # YI 1 -> SMB3 1-1
    (0,1): smb3_level_definitions[0][1], # YI 2 -> SMB3 1-2
    (0,3): smb3_level_definitions[0][2], # YI 3 -> SMB3 1-3
    (1,0): smb3_level_definitions[1][0], # DP 1 -> SMB3 2-1
}
GAME_LEVEL_SPECS.update(level_map_config)

for world_idx, world_content in enumerate(SMW_STYLE_MAP_DATA):
    for node_data in world_content['nodes']: # No need for node_idx here if using level_id from data
        level_id_tuple = node_data['level_id']
        if level_id_tuple not in GAME_LEVEL_SPECS:
            GAME_LEVEL_SPECS[level_id_tuple] = _create_placeholder_level_spec(level_id_tuple[0], level_id_tuple[1], node_data)

# --- Spatial Grid for Collision ---
class Grid:
    def __init__(self, cell_size=TILE * SCALE * 2):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], List[pygame.Rect]] = {}

    def clear(self):
        self.cells.clear()

    def insert(self, rect: pygame.Rect):
        cx1 = rect.left // self.cell_size
        cy1 = rect.top // self.cell_size
        cx2 = rect.right // self.cell_size
        cy2 = rect.bottom // self.cell_size
        for cx in range(cx1, cx2 + 1):
            for cy in range(cy1, cy2 + 1):
                self.cells.setdefault((cx, cy), []).append(rect)

    def query(self, rect: pygame.Rect) -> List[pygame.Rect]:
        seen = set()
        overlapping_rects = []
        cx1 = rect.left // self.cell_size
        cy1 = rect.top // self.cell_size
        cx2 = rect.right // self.cell_size
        cy2 = rect.bottom // self.cell_size
        for cx in range(cx1, cx2 + 1):
            for cy in range(cy1, cy2 + 1):
                for r in self.cells.get((cx, cy), []):
                    # Convert rect to tuple for hashing
                    r_tuple = (r.x, r.y, r.width, r.height)
                    if r_tuple not in seen:
                        seen.add(r_tuple)
                        overlapping_rects.append(r)
        return overlapping_rects

# --- Main Game Class ---
class IntegratedGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SMW Overworld & SMB3 Levels")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        
        # Initialize mixer with error handling
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            print(f"Failed to initialize Pygame mixer: {e}")
            # Fallback: disable sound or use a dummy sound player
            pygame.mixer.quit() # Ensure it's not partially initialized


        # Sounds (ensure mixer is init'd before calling tone)
        self.BEEP_OW_MOVE = tone(392, 50, 0.3)
        self.BEEP_OW_SELECT = tone(600, 70, 0.4)
        self.BEEP_JUMP = tone(784, 80, 0.35)
        self.BEEP_COIN = tone(1046, 80, 0.3)
        self.BEEP_STOMP = tone(523, 60, 0.4)
        self.BEEP_HURT = tone(262, 120, 0.5)
        self.BEEP_PAUSE = tone(600, 50, 0.3)
        self.BEEP_GAMEOVER = tone(130, 1000, 0.5)
        self.BEEP_VICTORY = tone(1200, 800, 0.5)

        try:
            self.hud_font = pygame.font.Font(None, 24)
            self.ow_node_font = pygame.font.Font(None, 20)
            self.message_font = pygame.font.Font(None, 48)
        except: # Fallback fonts
            self.hud_font = pygame.font.SysFont("sans-serif", 22)
            self.ow_node_font = pygame.font.SysFont("sans-serif", 18)
            self.message_font = pygame.font.SysFont("sans-serif", 46)

        self.game_state = "overworld" # "overworld", "level", "paused", "game_over", "victory"
        self.paused = False # Separate flag for pause state
        self.paused_from_state = "overworld"

        self.smw_map_data = SMW_STYLE_MAP_DATA
        self.current_world_on_map = 0
        self.current_node_on_map = 0
        self.ow_input_delay_timer = 0
        self.ow_input_cooldown = 0.18 # seconds

        self.current_level_spec: Optional[LevelSpec] = None
        self.score = 0
        self.lives = 3
        self.time_left = 300 # seconds
        self.player_state = "small" # "small", "big", "fire"
        self.invincibility_timer = 0 # frames

        self.player_rect = pygame.Rect(0, 0, TILE, TILE + TILE // 2) # Initial default size
        self.player_sizes = {"small": (TILE, TILE + TILE // 2), "big": (TILE, TILE * 2), "fire": (TILE, TILE * 2)}
        self.player_vel = pygame.Vector2(0, 0)
        self.player_on_ground = False
        
        self.camera_offset_x = 0
        self.level_width = W # Default, updated in load_level

        self.platform_rects: List[pygame.Rect] = []
        self.block_rects: List[pygame.Rect] = []
        self.coin_rects: List[pygame.Rect] = []
        self.active_enemies: List[Dict] = []
        self.goal_rect: Optional[pygame.Rect] = None
        self.spatial_grid = Grid(cell_size=TILE * SCALE * 2)

        self._initialize_player_rect()
        self.load_overworld_state()

    def _play_sound(self, sound_obj: Optional[pygame.mixer.Sound]):
        if sound_obj and pygame.mixer.get_init():
            sound_obj.play()

    def _initialize_player_rect(self):
        w, h = self.player_sizes[self.player_state]
        # Ensure player_rect is initialized even if midbottom isn't set yet
        self.player_rect = pygame.Rect(50, H - (TILE*SCALE) - h, w, h)


    def set_player_level_state(self, new_char_state: str):
        if self.player_state == new_char_state and self.player_rect.size != (0,0) : return
        
        old_midbottom = self.player_rect.midbottom
        if self.player_rect.w == 0 : # If uninitialized
            old_midbottom = (50, H - (TILE*SCALE)) 

        self.player_state = new_char_state
        new_w, new_h = self.player_sizes[new_char_state]
        self.player_rect.size = (new_w, new_h)
        self.player_rect.midbottom = old_midbottom

    def load_overworld_state(self):
        self.game_state = "overworld"
        self.paused = False
        print(f"Transitioned to Overworld. Current World: {self.current_world_on_map}, Node: {self.current_node_on_map}")

    def load_level_from_spec(self, spec: LevelSpec):
        self.game_state = "level"
        self.paused = False
        self.current_level_spec = spec
        self.time_left = 300
        self.camera_offset_x = 0

        # Determine level width from platforms (assuming platforms define the extent)
        if spec.platforms:
            min_x = min(p[0] for p in spec.platforms)
            max_x = max(p[0] + p[2] for p in spec.platforms)
            self.level_width = max(W, max_x) # Level width is at least screen width
        else:
            self.level_width = W # Default if no platforms

        self.set_player_level_state("small")
        self.player_rect.midbottom = (TILE * SCALE * 2, H - (TILE * SCALE))
        self.player_vel.update(0, 0)
        self.player_on_ground = False
        self.invincibility_timer = 0

        self.platform_rects = [pygame.Rect(x, y, w, h) for x, y, w, h in spec.platforms]
        self.block_rects = [pygame.Rect(bx * TILE * SCALE, by * TILE * SCALE, TILE * SCALE, TILE * SCALE)
                            for bx, by in spec.blocks]
        self.coin_rects = [pygame.Rect(cx * TILE * SCALE + (TILE*SCALE - TILE)//2, 
                                       cy * TILE * SCALE + (TILE*SCALE - TILE)//2, 
                                       TILE, TILE) 
                           for cx, cy in spec.coins]
        
        self.active_enemies = []
        for ex, ey_bottom, etype in spec.enemies: # Assuming ey is bottom of enemy sprite relative to ground
            enemy_w = TILE * SCALE
            enemy_h = TILE * SCALE if etype == "goomba" else int(TILE * SCALE * 1.5)
            # Place enemy on the main ground platform (H - TILE*SCALE)
            # ey_bottom is the y-coordinate of the bottom of the enemy.
            # So, rect.bottom = ey_bottom. rect.y = ey_bottom - enemy_h
            # We need to ensure ey_bottom is relative to the game world, not just an offset.
            # Let's assume the ey provided in spec.enemies is the desired rect.bottom on the ground.
            # The ground y is H - (TILE*SCALE).
            # So, the enemy rect.bottom should be H - (TILE*SCALE).
            # And rect.y = H - (TILE*SCALE) - enemy_h
            rect_y = H - (TILE*SCALE) - enemy_h
            rect = pygame.Rect(ex, rect_y, enemy_w, enemy_h)
            vel_x = -1 if etype == "goomba" else -1.5
            self.active_enemies.append({"rect": rect, "type": etype, "vel_x": vel_x, "orig_y": rect.y, "state":"walking", "vel_y":0})


        gx, gy = spec.goal
        self.goal_rect = pygame.Rect(gx, gy, TILE * SCALE, TILE * SCALE * 2)

        self.spatial_grid.clear()
        for r in self.platform_rects + self.block_rects:
            self.spatial_grid.insert(r)
        
        print(f"Loaded Level: {spec.name}. Level width: {self.level_width}")

    def update_overworld_map_navigation(self, keys, dt):
        """Handles input for navigating the overworld map."""
        self.ow_input_delay_timer -= dt
        if self.ow_input_delay_timer > 0:
            return

        current_world_nodes = self.smw_map_data[self.current_world_on_map]['nodes']
        num_nodes_in_world = len(current_world_nodes)

        moved = False
        if keys[pygame.K_RIGHT]:
            self.current_node_on_map = (self.current_node_on_map + 1) % num_nodes_in_world
            moved = True
        elif keys[pygame.K_LEFT]:
            self.current_node_on_map = (self.current_node_on_map - 1 + num_nodes_in_world) % num_nodes_in_world
            moved = True
        elif keys[pygame.K_UP]: # Change world (example: up for next world)
            self.current_world_on_map = (self.current_world_on_map + 1) % len(self.smw_map_data)
            self.current_node_on_map = 0 # Reset to first node of new world
            moved = True
        elif keys[pygame.K_DOWN]: # Change world (example: down for prev world)
            self.current_world_on_map = (self.current_world_on_map - 1 + len(self.smw_map_data)) % len(self.smw_map_data)
            self.current_node_on_map = 0 # Reset to first node of new world
            moved = True
        elif keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            selected_node_data = current_world_nodes[self.current_node_on_map]
            level_id_to_load = selected_node_data['level_id']
            if level_id_to_load in GAME_LEVEL_SPECS:
                self._play_sound(self.BEEP_OW_SELECT)
                self.load_level_from_spec(GAME_LEVEL_SPECS[level_id_to_load])
            else:
                print(f"Warning: Level ID {level_id_to_load} not found in GAME_LEVEL_SPECS.")
            moved = True # Reset timer even if level not found

        if moved:
            self._play_sound(self.BEEP_OW_MOVE if not (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) else None)
            self.ow_input_delay_timer = self.ow_input_cooldown


    def update_level_gameplay(self, keys, dt):
        """Handles gameplay logic for a level."""
        if not self.current_level_spec: return

        # Player horizontal movement
        self.player_vel.x = 0
        if keys[pygame.K_LEFT]:
            self.player_vel.x = -300 * dt # Speed units/sec * sec = units
        if keys[pygame.K_RIGHT]:
            self.player_vel.x = 300 * dt

        # Player jump
        if keys[pygame.K_SPACE] and self.player_on_ground:
            self.player_vel.y = JUMP_VEL
            self.player_on_ground = False
            self._play_sound(self.BEEP_JUMP)

        # Apply gravity
        self.player_vel.y += GRAVITY 
        if self.player_vel.y > 15 : self.player_vel.y = 15 # Terminal velocity

        # Move player and handle collisions
        self.player_rect.x += self.player_vel.x
        self.handle_level_collisions('horizontal')
        
        self.player_rect.y += self.player_vel.y
        self.player_on_ground = False # Assume not on ground until collision check proves otherwise
        self.handle_level_collisions('vertical')

        # Camera scrolling
        # Center camera on player, but don't scroll past level boundaries
        target_camera_x = self.player_rect.centerx - W // 2
        self.camera_offset_x = max(0, min(target_camera_x, self.level_width - W))


        # Update enemies
        for enemy in self.active_enemies[:]: # Iterate on a copy for safe removal
            if enemy["state"] == "walking":
                enemy["rect"].x += enemy["vel_x"] * 100 * dt # Enemy speed
                # Basic enemy AI: turn around at platform edges or walls (simplified)
                # This needs more robust collision detection with platforms for enemies
                if enemy["rect"].left < 0 or enemy["rect"].right > self.level_width: # Crude boundary check
                    enemy["vel_x"] *= -1
                
                # Check collision with player
                if self.player_rect.colliderect(enemy["rect"]):
                    if self.player_vel.y > 0 and self.player_rect.bottom < enemy["rect"].centery: # Stomping
                        enemy["state"] = "stomped"
                        self._play_sound(self.BEEP_STOMP)
                        self.player_vel.y = JUMP_VEL * 0.6 # Small bounce
                        self.score += 100
                    elif self.invincibility_timer <= 0: # Player gets hurt
                        self.handle_player_hurt()

            elif enemy["state"] == "stomped":
                # Enemy might disappear after a bit or become a shell
                # For now, just remove them
                self.active_enemies.remove(enemy) # Simplified

        # Collect coins
        for coin_rect in self.coin_rects[:]:
            if self.player_rect.colliderect(coin_rect):
                self.coin_rects.remove(coin_rect)
                self.score += 50
                self._play_sound(self.BEEP_COIN)
        
        # Check goal
        if self.goal_rect and self.player_rect.colliderect(self.goal_rect):
            self.level_complete_transition()
            return # Stop further updates for this frame

        # Invincibility blink/timer
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        # Time limit
        self.time_left -= dt
        if self.time_left <= 0:
            self.handle_player_death() # Or specific time_out logic

        # Player fall off screen
        if self.player_rect.top > H:
             self.handle_player_death()


    def handle_level_collisions(self, direction: str):
        """Handles player collisions with level geometry."""
        collidables = self.spatial_grid.query(self.player_rect) # Get potential colliders

        for rect in collidables: # rect is from platform_rects or block_rects
            if self.player_rect.colliderect(rect):
                if direction == 'horizontal':
                    if self.player_vel.x > 0: # Moving right
                        self.player_rect.right = rect.left
                    elif self.player_vel.x < 0: # Moving left
                        self.player_rect.left = rect.right
                    self.player_vel.x = 0 # Stop horizontal movement
                
                elif direction == 'vertical':
                    if self.player_vel.y > 0: # Moving down
                        self.player_rect.bottom = rect.top
                        self.player_on_ground = True
                    elif self.player_vel.y < 0: # Moving up (hit head)
                        self.player_rect.top = rect.bottom
                        # TODO: Handle hitting blocks from below (break, item, etc.)
                    self.player_vel.y = 0 # Stop vertical movement


    def handle_player_hurt(self):
        """Handles player getting hurt by an enemy."""
        if self.player_state == "big" or self.player_state == "fire":
            self.set_player_level_state("small")
            self.invincibility_timer = FPS * 2 # 2 seconds of invincibility
            self._play_sound(self.BEEP_HURT)
        elif self.player_state == "small":
            self.handle_player_death()

    def handle_player_death(self):
        """Handles player death."""
        self.lives -= 1
        self._play_sound(self.BEEP_HURT) # Or a specific death sound
        if self.lives <= 0:
            self.game_over_transition()
        else:
            # Respawn player at level start (or checkpoint)
            self.invincibility_timer = FPS * 2 # Brief invincibility on respawn
            if self.current_level_spec:
                 self.load_level_from_spec(self.current_level_spec) # Reload current level
            else: # Should not happen, but fallback
                self.load_overworld_state()


    def game_over_transition(self):
        """Transitions to the game over state."""
        self.game_state = "game_over"
        self._play_sound(self.BEEP_GAMEOVER)
        # The game loop will handle drawing the game over screen.
        # After a delay (handled in draw_game_over_screen or main loop), it will go to overworld.

    def level_complete_transition(self):
        """Transitions after completing a level."""
        self.game_state = "victory" # Temporary state for showing a message
        self._play_sound(self.BEEP_VICTORY)
        self.score += int(max(0, self.time_left)) * 10 # Time bonus
        # After a short delay (handled in draw_victory_screen or main loop), go to overworld
        # For now, directly go to overworld for simplicity in this step
        # In a full game, you might show a score tally screen first.
        # self.load_overworld_state() # This will be called after a delay in run_game_loop

    def draw_overworld_map(self):
        """Draws the SMW-style overworld map."""
        self.screen.fill(COLORS['DARK_GREEN']) # Background for overworld

        world_data = self.smw_map_data[self.current_world_on_map]
        nodes = world_data['nodes']

        # Draw paths (simple lines between consecutive nodes for now)
        for i in range(len(nodes) -1):
            # A more sophisticated path system would look at 'connections' in node data
            start_pos = nodes[i]['pos']
            end_pos = nodes[i+1]['pos'] # Simple linear path
            pygame.draw.line(self.screen, COLORS['GRAY'], start_pos, end_pos, 3)

        # Draw nodes
        for i, node in enumerate(nodes):
            pos = node['pos']
            node_type = node.get('type', 'default') # 'default', 'castle', 'switch', 'ghost', 'fortress'
            
            color = COLORS['GREEN'] # Default node color
            if node_type == 'castle': color = COLORS['RED']
            elif node_type == 'switch': color = COLORS['YELLOW']
            elif node_type == 'ghost': color = COLORS['PURPLE']
            elif node_type == 'fortress': color = COLORS['ORANGE']
            
            radius = 12
            if i == self.current_node_on_map: # Highlight current node
                pygame.draw.circle(self.screen, COLORS['WHITE'], pos, radius + 4) # Outer ring
                pygame.draw.circle(self.screen, color, pos, radius)
                # Draw player icon (simple circle) on current node
                player_ow_color = COLORS['player_small']
                pygame.draw.circle(self.screen, player_ow_color, (pos[0], pos[1] - radius - 5), 5)

            else:
                pygame.draw.circle(self.screen, color, pos, radius)

            # Draw node label
            label_text = node.get('label', f"L{node['level_id'][1]}")
            label_surface = self.ow_node_font.render(label_text, True, COLORS['BLACK'])
            label_rect = label_surface.get_rect(center=(pos[0], pos[1] + radius + 10))
            self.screen.blit(label_surface, label_rect)
        
        # Draw current world name
        world_name_surf = self.hud_font.render(f"World: {world_data['name']}", True, COLORS['WHITE'])
        self.screen.blit(world_name_surf, (10,10))


    def draw_level_scene(self):
        """Draws the current level, player, enemies, HUD, etc."""
        if not self.current_level_spec: return
        
        self.screen.fill(self.current_level_spec.background_color)

        # Draw platforms (adjust for camera)
        for p_rect in self.platform_rects:
            adjusted_rect = p_rect.move(-self.camera_offset_x, 0)
            pygame.draw.rect(self.screen, COLORS['ground'], adjusted_rect)
        
        # Draw blocks (adjust for camera)
        for b_rect in self.block_rects:
            adjusted_rect = b_rect.move(-self.camera_offset_x, 0)
            pygame.draw.rect(self.screen, COLORS['block'], adjusted_rect)

        # Draw coins (adjust for camera)
        for c_rect in self.coin_rects:
            adjusted_rect = c_rect.move(-self.camera_offset_x, 0)
            pygame.draw.ellipse(self.screen, COLORS['coin'], adjusted_rect) # Ellipse for coin shape

        # Draw enemies (adjust for camera)
        for enemy in self.active_enemies:
            if enemy["state"] == "walking":
                color = COLORS['goomba'] if enemy['type'] == 'goomba' else COLORS['koopa']
                adjusted_rect = enemy["rect"].move(-self.camera_offset_x, 0)
                pygame.draw.rect(self.screen, color, adjusted_rect)
            # Could add drawing for "stomped" state if desired

        # Draw goal (adjust for camera)
        if self.goal_rect:
            adjusted_goal_rect = self.goal_rect.move(-self.camera_offset_x, 0)
            pygame.draw.rect(self.screen, COLORS['pipe'], adjusted_goal_rect) # Using pipe color for goal

        # Draw player (adjust for camera)
        if self.invincibility_timer <= 0 or (self.invincibility_timer > 0 and self.invincibility_timer % 10 < 5): # Blink effect
            player_color_key = f"player_{self.player_state}"
            player_color = COLORS.get(player_color_key, COLORS["player_small"])
            adjusted_player_rect = self.player_rect.move(-self.camera_offset_x, 0)
            pygame.draw.rect(self.screen, player_color, adjusted_player_rect)

        # Draw HUD
        score_surf = self.hud_font.render(f"Score: {self.score}", True, COLORS['hud'])
        lives_surf = self.hud_font.render(f"Lives: {self.lives}", True, COLORS['hud'])
        time_surf = self.hud_font.render(f"Time: {int(self.time_left)}", True, COLORS['hud'])
        level_name_surf = self.hud_font.render(f"Level: {self.current_level_spec.name}", True, COLORS['hud'])

        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(lives_surf, (W - 100, 10))
        self.screen.blit(time_surf, (W // 2 - 50, 10))
        self.screen.blit(level_name_surf, (10, 30))


    def draw_pause_overlay(self):
        """Draws the pause screen overlay."""
        overlay = pygame.Surface((W, H), pygame.SRCALPHA) # SRCALPHA for transparency
        overlay.fill((0, 0, 0, 180)) # Semi-transparent black
        self.screen.blit(overlay, (0,0))

        pause_text = self.message_font.render("PAUSED", True, COLORS['WHITE'])
        text_rect = pause_text.get_rect(center=(W // 2, H // 2))
        self.screen.blit(pause_text, text_rect)
        
        resume_text = self.hud_font.render("Press P to Resume", True, COLORS['WHITE'])
        resume_rect = resume_text.get_rect(center=(W // 2, H // 2 + 50))
        self.screen.blit(resume_text, resume_rect)

    def draw_current_state_with_pause_overlay(self):
        """Draws the underlying game state then the pause overlay."""
        if self.paused_from_state == "overworld":
            self.draw_overworld_map()
        elif self.paused_from_state == "level":
            self.draw_level_scene()
        # Add other states if they can be paused (e.g., victory screen before transition)
        self.draw_pause_overlay()


    def draw_game_over_screen(self):
        self.screen.fill(COLORS['BLACK'])
        game_over_text = self.message_font.render("GAME OVER", True, COLORS['RED'])
        text_rect = game_over_text.get_rect(center=(W // 2, H // 2))
        self.screen.blit(game_over_text, text_rect)
        
        prompt_text = self.hud_font.render("Press Enter to return to Overworld", True, COLORS['WHITE'])
        prompt_rect = prompt_text.get_rect(center=(W//2, H//2 + 60))
        self.screen.blit(prompt_text, prompt_rect)


    def draw_victory_screen(self):
        self.screen.fill(COLORS['sky']) # Or a victory background
        victory_text = self.message_font.render("LEVEL COMPLETE!", True, COLORS['YELLOW'])
        text_rect = victory_text.get_rect(center=(W // 2, H // 2 - 30))
        self.screen.blit(victory_text, text_rect)

        score_text = self.hud_font.render(f"Final Score for Level: {self.score}", True, COLORS['WHITE']) # Display current total score
        score_rect = score_text.get_rect(center=(W//2, H//2 + 30))
        self.screen.blit(score_text, score_rect)

        prompt_text = self.hud_font.render("Press Enter to Continue", True, COLORS['WHITE'])
        prompt_rect = prompt_text.get_rect(center=(W//2, H//2 + 70))
        self.screen.blit(prompt_text, prompt_rect)


    async def run_game_loop(self):
        running = True
        last_game_over_transition_time = 0
        last_victory_transition_time = 0

        while running:
            dt = self.clock.tick(FPS) / 1000.0 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == "level":
                            self.load_overworld_state()
                        elif self.game_state == "overworld":
                            running = False
                            return
                        elif self.game_state in ["game_over", "victory"]: # Allow Esc to skip these screens
                            self.load_overworld_state()

                    if event.key == pygame.K_p:
                        if self.game_state not in ["game_over", "victory"]: # Don't pause on these screens
                            self.paused = not self.paused
                            if self.paused:
                                self.paused_from_state = self.game_state
                            else:
                                self.game_state = self.paused_from_state # Restore state
                            self._play_sound(self.BEEP_PAUSE)
                    
                    if self.game_state == "game_over" and event.key == pygame.K_RETURN:
                        self.score = 0 # Reset score on game over continue
                        self.lives = 3 # Reset lives
                        self.load_overworld_state()
                    
                    if self.game_state == "victory" and event.key == pygame.K_RETURN:
                        self.load_overworld_state()


            keys = pygame.key.get_pressed()

            if self.paused:
                self.draw_current_state_with_pause_overlay()
            elif self.game_state == "overworld":
                self.update_overworld_map_navigation(keys, dt)
                self.draw_overworld_map()
            elif self.game_state == "level":
                if self.current_level_spec:
                    self.update_level_gameplay(keys, dt)
                    self.draw_level_scene()
                else:
                    self.load_overworld_state() 
            elif self.game_state == "game_over":
                self.draw_game_over_screen()
                # Transition handled by key press (Enter)
            elif self.game_state == "victory":
                self.draw_victory_screen()
                # Transition handled by key press (Enter)

            pygame.display.flip()
            await asyncio.sleep(0) # Yield control for asyncio

        pygame.quit()
        sys.exit()

async def main_async():
    game = IntegratedGame()
    await game.run_game_loop()

if __name__ == '__main__':
    # Ensure Pygame is initialized before any Pygame functions are called globally (like tone)
    # However, IntegratedGame.__init__ handles pygame.init() and pygame.mixer.init()
    # So, direct global calls to tone() before game instantiation might still be an issue
    # if not careful. The current structure seems okay as tones are instance members.
    
    # Fix for macOS if necessary
    if platform.system() == "Darwin": # macOS
        if sys.version_info[0] == 3 and sys.version_info[1] >= 8: # Python 3.8+
            if 'EVENT_NOKQUEUE' not in os.environ:
                 print("Setting os.environ['PYGAME_FORCE_SCALE'] = 'macbookproretina'")
                 print("Setting os.environ['EVENT_NOKQUEUE'] = '1' for macOS compatibility")
                 # os.environ['PYGAME_FORCE_SCALE'] = "macbookproretina" # Example, adjust as needed
                 os.environ['EVENT_NOKQUEUE'] = '1' # Might help with event loop issues on some macOS versions

    # It's better to initialize pygame and mixer inside the class constructor
    # to ensure they are ready when sounds are generated.
    # The `tone` function checks `pg.mixer.get_init()` but it's safer if it's already init'd.

    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Game interrupted by user.")
    finally:
        pygame.quit()
