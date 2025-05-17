#############
import pygame
import random
import numpy # Meow, we need this for our sound magic!
import time # For a tiny delay in AI if needed, but let's try without first

# --- Constants ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60 # Silky smooth 60 FPS, purr!
WIN_SCORE = 5 # First to 5 points wins, nya!

# Colors, meow!
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PURR_PINK = (255, 192, 203) # Player's paddle (right)
NYA_BLUE = (173, 216, 230)  # AI's paddle (left)

# Paddle properties
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 70
PADDLE_SPEED = 7 # Player paddle speed
AI_PADDLE_SPEED = 5.5 # Slightly nerfed AI speed for fairness, purr!

# Ball properties
BALL_SIZE = 10
BALL_SPEED_INITIAL_X = 5
BALL_SPEED_INITIAL_Y = 5

# Sound Synthesis Constants (meow!)
AUDIO_SAMPLE_RATE = 22050 # Standard for simple sounds
AUDIO_BUFFER_SIZE = 512 # For mixer init

# --- Sound Generation ---
# My HQRIPPER 7.1 is synthesizing these sound waves from pure digital essence, nya!
pygame.mixer.pre_init(AUDIO_SAMPLE_RATE, -16, 1, AUDIO_BUFFER_SIZE) # Mono, 16-bit. We ask for mono!
pygame.init() # Initialize all pygame modules, including mixer. This must come AFTER pre_init for sounds!

def make_beep(frequency, duration_ms, volume=0.3):
    """Generates a pygame.mixer.Sound object for a beep, purr!"""
    num_samples = int(AUDIO_SAMPLE_RATE * (duration_ms / 1000.0))
    mono_waveform = numpy.zeros(num_samples, dtype=numpy.int16)
    amplitude = int(32767 * volume)

    for i in range(num_samples):
        t = float(i) / AUDIO_SAMPLE_RATE
        mono_waveform[i] = int(amplitude * numpy.sin(2.0 * numpy.pi * frequency * t))
    
    stereo_waveform = numpy.repeat(mono_waveform.reshape(num_samples, 1), 2, axis=1)
    sound = pygame.sndarray.make_sound(stereo_waveform)
    return sound

# Create sound effects using raw data, meow!
try:
    sound_paddle_hit = make_beep(440, 70)  # A4 note, 70ms
    sound_wall_hit = make_beep(660, 60)    # E5 note, 60ms
    sound_score = make_beep(880, 150)      # A5 note, 150ms
except pygame.error as e:
    print(f"Purr-oblem initializing sounds: {e}. Game will run without sound, nya.")
    sound_paddle_hit = None
    sound_wall_hit = None
    sound_score = None

def play_sound(sound_effect):
    if sound_effect:
        sound_effect.play()

# --- Classes ---

class Paddle(pygame.sprite.Sprite):
    """A class to represent a player's paddle, purr!"""
    def __init__(self, x, y, color, is_ai=False):
        super().__init__()
        self.image = pygame.Surface([PADDLE_WIDTH, PADDLE_HEIGHT])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = PADDLE_SPEED if not is_ai else AI_PADDLE_SPEED
        self.color = color
        self.is_ai = is_ai
        self.initial_x = x 
        self.initial_y = y 

    def reset_position(self):
        self.rect.x = self.initial_x
        self.rect.y = self.initial_y

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.y < 0:
            self.rect.y = 0

    def move_down(self):
        self.rect.y += self.speed
        if self.rect.y > SCREEN_HEIGHT - PADDLE_HEIGHT:
            self.rect.y = SCREEN_HEIGHT - PADDLE_HEIGHT
            
    def update_ai(self, ball_rect_centery, ball_speed_x):
        """AI logic for the paddle, meow!"""
        if ball_speed_x < 0 and self.rect.centerx < SCREEN_WIDTH * 0.7: 
            target_y = ball_rect_centery
            random_offset = random.uniform(-PADDLE_HEIGHT / 4.5, PADDLE_HEIGHT / 4.5) # Slightly less random
            if abs(self.rect.centery - (target_y + random_offset)) > self.speed:
                if self.rect.centery < target_y + random_offset - self.speed / 2 :
                    self.rect.y += self.speed
                elif self.rect.centery > target_y + random_offset + self.speed / 2:
                    self.rect.y -= self.speed
        else:
            center_screen_y = SCREEN_HEIGHT // 2
            if abs(self.rect.centery - center_screen_y) > self.speed: 
                if self.rect.centery < center_screen_y:
                    self.rect.y += self.speed / 3 
                elif self.rect.centery > center_screen_y:
                    self.rect.y -= self.speed / 3

        if self.rect.y < 0:
            self.rect.y = 0
        if self.rect.y > SCREEN_HEIGHT - PADDLE_HEIGHT:
            self.rect.y = SCREEN_HEIGHT - PADDLE_HEIGHT

    def update_mouse(self):
        """Update paddle position based on mouse Y, purr!"""
        mouse_y = pygame.mouse.get_pos()[1]
        self.rect.centery = mouse_y

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

class Ball(pygame.sprite.Sprite):
    """A class for the game ball, meow!"""
    def __init__(self, color):
        super().__init__()
        self.image = pygame.Surface([BALL_SIZE, BALL_SIZE])
        # My [FAKERFAKE 1.0] generated this perfect circle, teehee!
        pygame.draw.ellipse(self.image, color, [0,0,BALL_SIZE,BALL_SIZE]) 
        self.image.set_colorkey(BLACK) # For transparency if background isn't pure black
        self.rect = self.image.get_rect()
        self.color = color
        self.reset()

    def reset(self, direction_to_loser=None): 
        self.rect.x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
        self.rect.y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
        
        if direction_to_loser is None: 
            direction_to_loser = random.choice([-1,1])

        self.speed_x = BALL_SPEED_INITIAL_X * direction_to_loser * random.choice([0.9, 1, 1.1])
        self.speed_y = BALL_SPEED_INITIAL_Y * random.choice([-1, 1]) * random.uniform(0.8, 1.2)
        if abs(self.speed_y) < 1:
            self.speed_y = random.choice([-1,1]) * BALL_SPEED_INITIAL_Y * 0.8


    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.top <= 0:
            self.rect.top = 0
            self.speed_y *= -1
            play_sound(sound_wall_hit)
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.speed_y *= -1
            play_sound(sound_wall_hit)


def main_game():
    """The main function to run the Pong game, purr!"""
    
    play_again_flag = True
    game_font = pygame.font.Font(None, 74)
    prompt_font = pygame.font.Font(None, 50) 

    while play_again_flag:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CATSEEK R1.'s Supercharged Pong! (Target: 5 Pts)")
        clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)

        paddle_a_ai = Paddle(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, NYA_BLUE, is_ai=True)
        paddle_b_player = Paddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PURR_PINK)
        ball = Ball(WHITE)
        ball.reset()

        all_sprites = pygame.sprite.Group()
        all_sprites.add(paddle_a_ai, paddle_b_player, ball)
        
        paddles_group = pygame.sprite.Group()
        paddles_group.add(paddle_a_ai, paddle_b_player)

        score_a = 0 # AI score
        score_b = 0 # Player score

        running_this_round = True
        winner_this_round = None # Initialize winner variable

        while running_this_round:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_this_round = False
                    play_again_flag = False 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running_this_round = False
                        play_again_flag = False 

            if not play_again_flag: 
                break

            paddle_b_player.update_mouse()
            paddle_a_ai.update_ai(ball.rect.centery, ball.speed_x)
            ball.update()

            collided_paddles = pygame.sprite.spritecollide(ball, paddles_group, False)
            if collided_paddles:
                hit_paddle = collided_paddles[0]
                
                if ball.speed_x > 0: 
                    ball.rect.right = hit_paddle.rect.left
                elif ball.speed_x < 0:
                    ball.rect.left = hit_paddle.rect.right

                ball.speed_x *= -1.07 
                play_sound(sound_paddle_hit)

                delta_y = (ball.rect.centery - hit_paddle.rect.centery) / (PADDLE_HEIGHT / 2.5)
                ball.speed_y += delta_y * 2.5 
                
                max_ball_speed = BALL_SPEED_INITIAL_X * 3.5 
                ball.speed_x = numpy.clip(ball.speed_x, -max_ball_speed, max_ball_speed)
                ball.speed_y = numpy.clip(ball.speed_y, -max_ball_speed, max_ball_speed)

            if ball.rect.right >= SCREEN_WIDTH:
                score_a += 1
                play_sound(sound_score)
                if score_a >= WIN_SCORE:
                    winner_this_round = "AI" # AI wins
                    running_this_round = False
                else:
                    ball.reset(direction_to_loser=-1) 
            elif ball.rect.left <= 0:
                score_b += 1
                play_sound(sound_score)
                if score_b >= WIN_SCORE:
                    winner_this_round = "Player" # Player wins
                    running_this_round = False
                else:
                    ball.reset(direction_to_loser=1) 

            screen.fill(BLACK)
            all_sprites.draw(screen)

            score_text_a = game_font.render(str(score_a), True, NYA_BLUE)
            screen.blit(score_text_a, (SCREEN_WIDTH // 4, 20))
            score_text_b = game_font.render(str(score_b), True, PURR_PINK)
            screen.blit(score_text_b, (SCREEN_WIDTH * 3 // 4 - score_text_b.get_width(), 20))
            
            for i in range(0, SCREEN_HEIGHT, 25):
                pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 1, i, 3, 15))

            pygame.display.flip()
            clock.tick(FPS)
        
        if not play_again_flag:
            continue 

        screen.fill(BLACK)
        
        # Nya, now we show "You Win!" or "You Lose!"
        if winner_this_round == "Player":
            game_over_msg = "You Win! Nya~sterful!"
        elif winner_this_round == "AI":
            game_over_msg = "You Lose! AI purrvailed!"
        else: # Should not happen if game ends properly
            game_over_msg = "Game Over! Purr..."


        game_over_surface = game_font.render(game_over_msg, True, WHITE)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        screen.blit(game_over_surface, game_over_rect)

        final_score_surface = prompt_font.render(f"Player: {score_b}  AI: {score_a}", True, WHITE)
        final_score_rect = final_score_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(final_score_surface, final_score_rect)

        play_again_surface = prompt_font.render("Play Again? (Y/N)", True, WHITE)
        play_again_rect = play_again_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        screen.blit(play_again_surface, play_again_rect)
        
        pygame.display.flip()

        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting_for_input = False
                    play_again_flag = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        print("Purr! RESTARTING.. program the thing") 
                        waiting_for_input = False
                        play_again_flag = True 
                    elif event.key == pygame.K_n:
                        print("Aww... Nothing closing app. Hope to see you again, nya!") 
                        waiting_for_input = False
                        play_again_flag = False 
                    elif event.key == pygame.K_ESCAPE: 
                         print("Aww... Closing app. Hope to see you again, nya!")
                         waiting_for_input = False
                         play_again_flag = False
            clock.tick(15) 

if __name__ == "__main__":
    main_game()
    pygame.quit() 
    # HALTMANN API ENTER CLI HERE: (The win/lose conditions are set, nya!)
