import pygame
import math
import array

# Initialize pygame and audio
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Window setup
WIDTH, HEIGHT = 600, 400
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders Lite")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Fonts
FONT = pygame.font.SysFont(None, 24)
BIG_FONT = pygame.font.SysFont(None, 48)

# Game settings
PLAYER_SPEED = 5
BULLET_SPEED = 7
ENEMY_SPEED = 1
ENEMY_DROP = 20
ENEMY_ROWS = 3
ENEMY_COLS = 8
ENEMY_PADDING = 40

clock = pygame.time.Clock()


def create_tone(frequency=440, duration_ms=100, volume=0.5):
    """Return a Sound with a sine wave at the given frequency."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(32767 * volume)
    buf = array.array("h")
    for n in range(n_samples):
        t = n / sample_rate
        sample = int(amplitude * math.sin(2 * math.pi * frequency * t))
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf.tobytes())

# Sound effects
shoot_sound = create_tone(880, 100)
hit_sound = create_tone(440, 150)
lose_sound = create_tone(220, 400)
win_sound = create_tone(660, 300)


class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT - 40, 40, 20)
        self.bullets = []

    def move(self, dx):
        self.rect.x += dx * PLAYER_SPEED
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def shoot(self):
        bullet = pygame.Rect(self.rect.centerx - 2, self.rect.y - 10, 4, 10)
        self.bullets.append(bullet)
        shoot_sound.play()

    def update_bullets(self):
        for bullet in list(self.bullets):
            bullet.y -= BULLET_SPEED
            if bullet.bottom < 0:
                self.bullets.remove(bullet)

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, self.rect)
        for bullet in self.bullets:
            pygame.draw.rect(surface, WHITE, bullet)


class EnemyGroup:
    def __init__(self):
        self.direction = 1
        self.enemies = []
        start_x = ENEMY_PADDING
        start_y = ENEMY_PADDING
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = start_x + col * ENEMY_PADDING
                y = start_y + row * ENEMY_PADDING
                rect = pygame.Rect(x, y, 30, 20)
                self.enemies.append(rect)

    def update(self):
        move_down = False
        for enemy in self.enemies:
            enemy.x += self.direction * ENEMY_SPEED
            if enemy.right >= WIDTH or enemy.left <= 0:
                move_down = True
        if move_down:
            self.direction *= -1
            for enemy in self.enemies:
                enemy.y += ENEMY_DROP

    def draw(self, surface):
        for enemy in self.enemies:
            pygame.draw.rect(surface, RED, enemy)


class ShieldGroup:
    """Protective bumpers/shields that guard the player."""
    def __init__(self):
        self.shields = []
        num_shields = 4
        spacing = WIDTH // (num_shields + 1)
        shield_width = 60
        shield_height = 20
        y = HEIGHT - 80
        for i in range(num_shields):
            x = spacing * (i + 1) - shield_width // 2
            rect = pygame.Rect(x, y, shield_width, shield_height)
            self.shields.append(rect)

    def draw(self, surface):
        for shield in self.shields:
            pygame.draw.rect(surface, WHITE, shield)

    def check_bullet_collision(self, bullet_list):
        """Remove bullets that collide with shields (shields are indestructible for simplicity)."""
        for bullet in list(bullet_list):
            for shield in self.shields:
                if bullet.colliderect(shield):
                    if bullet in bullet_list:
                        bullet_list.remove(bullet)
                    break


def main():
    player = Player()
    enemies = EnemyGroup()
    shields = ShieldGroup()
    score = 0
    state = "playing"  # States: playing, win, game_over

    run = True
    while run:
        clock.tick(60)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if state == "playing" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()

        keys = pygame.key.get_pressed()
        if state == "playing":
            if keys[pygame.K_LEFT]:
                player.move(-1)
            if keys[pygame.K_RIGHT]:
                player.move(1)

        # Game state updates
        if state == "playing":
            player.update_bullets()
            shields.check_bullet_collision(player.bullets)
            enemies.update()

            # Bullet and enemy collision
            for bullet in list(player.bullets):
                for enemy in list(enemies.enemies):
                    if bullet.colliderect(enemy):
                        if bullet in player.bullets:
                            player.bullets.remove(bullet)
                        enemies.enemies.remove(enemy)
                        score += 1
                        hit_sound.play()
                        break

            # Check win condition
            if len(enemies.enemies) == 0:
                state = "win"
                win_sound.play()

            # Check lose condition (aliens reach bottom)
            for enemy in enemies.enemies:
                if enemy.bottom >= HEIGHT:
                    state = "game_over"
                    lose_sound.play()
                    break

        # Rendering
        WINDOW.fill(BLACK)
        if state == "playing":
            player.draw(WINDOW)
            enemies.draw(WINDOW)
            shields.draw(WINDOW)
            score_text = FONT.render(f"Score: {score}", True, WHITE)
            WINDOW.blit(score_text, (10, 10))
        else:
            # Display end-game text
            text = "YOU WIN" if state == "win" else "GAME OVER"
            color = GREEN if state == "win" else RED
            msg = BIG_FONT.render(text, True, color)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            WINDOW.blit(msg, msg_rect)
            score_text = FONT.render(f"Final Score: {score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            WINDOW.blit(score_text, score_rect)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
