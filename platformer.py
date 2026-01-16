import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_PURPLE = (20, 10, 30)
SPACE_BLUE = (15, 15, 35)
ORANGE = (255, 140, 0)
RED_ORANGE = (200, 70, 40)
DARK_RED = (150, 50, 30)
GRAY = (128, 128, 128)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (60, 60, 60)
MOON_GRAY = (150, 150, 150)
MOON_LIGHT = (200, 200, 200)
MOON_DARK = (100, 100, 100)
GREEN = (34, 139, 34)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 100)
SILVER = (192, 192, 192)

# Game settings
GROUND_HEIGHT = 150
INITIAL_SCROLL_SPEED = 3
SPEED_INCREASE_RATE = 0.005
WIN_TIME = 60000  # 60 seconds in milliseconds

# Player settings
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 40
JUMP_STRENGTH = 15
GRAVITY = 0.6

# Obstacle settings
OBSTACLE_MIN_WIDTH = 30
OBSTACLE_MAX_WIDTH = 60
OBSTACLE_HEIGHT = 50
OBSTACLE_SPAWN_DISTANCE = 400

# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Planetary Runner - Survive the Martian Terrain!")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Generate stars for background
stars = [(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT - GROUND_HEIGHT), 
          random.choice([1, 1, 1, 2])) for _ in range(100)]

# Generate static moon surface pattern (seed for consistency)
_moon_surface_seed = random.random()
def generate_moon_surface_pattern(width, height):
    """Generate a static moon surface pattern"""
    random.seed(42)  # Fixed seed for consistent pattern
    pattern = []
    for i in range(0, width + 200, 20):  # Extra width for scrolling
        for j in range(0, height, 20):
            if random.random() < 0.3:
                color = random.choice([MOON_LIGHT, MOON_GRAY, MOON_DARK])
                pattern.append((i, j, color))
    random.seed()  # Reset to time-based seed
    return pattern

# Generate moon surface pattern once
moon_surface_pattern = generate_moon_surface_pattern(WINDOW_WIDTH + 200, GROUND_HEIGHT)

class Player:
    def __init__(self):
        self.x = 100
        self.y = WINDOW_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.velocity_y = 0
        self.on_ground = True
        
    def jump(self):
        if self.on_ground:
            self.velocity_y = -JUMP_STRENGTH
            self.on_ground = False
    
    def update(self):
        # Apply gravity (lower gravity on planet)
        self.velocity_y += GRAVITY
        
        # Update position
        self.y += self.velocity_y
        
        # Check ground collision
        ground_y = WINDOW_HEIGHT - GROUND_HEIGHT - self.height
        if self.y >= ground_y:
            self.y = ground_y
            self.velocity_y = 0
            self.on_ground = True
    
    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)
    
    def draw(self, surface):
        # Draw astronaut/martian character
        # Body (suit)
        pygame.draw.rect(surface, WHITE, (self.x, self.y + 15, self.width, self.height - 15))
        # Helmet
        pygame.draw.ellipse(surface, WHITE, (self.x - 2, self.y, self.width + 4, 20))
        # Visor (tinted)
        pygame.draw.ellipse(surface, BLUE, (self.x + 2, self.y + 4, self.width - 4, 12))
        # Oxygen tank on back
        pygame.draw.rect(surface, SILVER, (self.x - 5, self.y + 20, 8, 15))
        # Arms
        pygame.draw.rect(surface, WHITE, (self.x - 5, self.y + 25, 8, 12))
        pygame.draw.rect(surface, WHITE, (self.x + self.width - 3, self.y + 25, 8, 12))
        # Legs
        pygame.draw.rect(surface, WHITE, (self.x + 5, self.y + 38, 8, 12))
        pygame.draw.rect(surface, WHITE, (self.x + 17, self.y + 38, 8, 12))

class Obstacle:
    def __init__(self, x):
        self.type = random.choice(['crater', 'boulder', 'debris'])
        self.width = random.randint(OBSTACLE_MIN_WIDTH, OBSTACLE_MAX_WIDTH)
        self.height = OBSTACLE_HEIGHT
        self.x = x
        self.y = WINDOW_HEIGHT - GROUND_HEIGHT - self.height
        if self.type == 'debris':
            self.width = random.randint(40, 60)
            self.height = random.randint(40, 60)
            self.y = WINDOW_HEIGHT - GROUND_HEIGHT - self.height
        
    def update(self, scroll_speed):
        self.x -= scroll_speed
        
    def get_rect(self):
        if self.type == 'crater':
            # Craters are wider but shorter (sunk into ground)
            return pygame.Rect(self.x, WINDOW_HEIGHT - GROUND_HEIGHT - 20, self.width, 20)
        else:
            return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface):
        ground_y = WINDOW_HEIGHT - GROUND_HEIGHT
        
        if self.type == 'crater':
            # Draw crater as a depression (moon crater style)
            crater_bottom = ground_y + 25
            pygame.draw.ellipse(surface, MOON_DARK, (self.x, ground_y - 10, self.width, 30))
            pygame.draw.ellipse(surface, DARK_GRAY, (self.x + 5, ground_y - 5, self.width - 10, 20))
            # Add depth shadow
            pygame.draw.arc(surface, BLACK, (self.x, ground_y - 10, self.width, 30), 0, 3.14, 2)
            
        elif self.type == 'boulder':
            # Draw boulder as an irregular rock shape
            points = [
                (self.x + self.width // 3, self.y),
                (self.x + 2 * self.width // 3, self.y + 5),
                (self.x + self.width - 5, self.y + self.height // 3),
                (self.x + self.width, self.y + 2 * self.height // 3),
                (self.x + 2 * self.width // 3, self.y + self.height),
                (self.x + self.width // 3, self.y + self.height - 5),
                (self.x + 5, self.y + 2 * self.height // 3),
                (self.x, self.y + self.height // 3),
            ]
            pygame.draw.polygon(surface, DARK_GRAY, points)
            pygame.draw.polygon(surface, GRAY, points)
            # Add highlights
            pygame.draw.circle(surface, LIGHT_GRAY, (self.x + self.width // 2, self.y + 10), 8)
            
        elif self.type == 'debris':
            # Draw spaceship debris (angular metal pieces)
            # Main body
            pygame.draw.polygon(surface, SILVER, [
                (self.x, self.y + self.height),
                (self.x + 15, self.y + 10),
                (self.x + self.width - 15, self.y + 10),
                (self.x + self.width, self.y + self.height)
            ])
            # Jagged top edge
            pygame.draw.polygon(surface, LIGHT_GRAY, [
                (self.x + 15, self.y + 10),
                (self.x + self.width // 3, self.y),
                (self.x + 2 * self.width // 3, self.y + 5),
                (self.x + self.width - 15, self.y + 10)
            ])
            # Add some detail lines
            pygame.draw.line(surface, DARK_GRAY, (self.x + 20, self.y + 15), 
                           (self.x + self.width - 20, self.y + 15), 2)
            pygame.draw.circle(surface, RED, (self.x + self.width // 2, self.y + 25), 3)

def draw_ground(surface, offset_x=0):
    """Draw static moon surface that scrolls smoothly"""
    ground_y = WINDOW_HEIGHT - GROUND_HEIGHT
    
    # Draw base moon surface (grayish moon color)
    pygame.draw.rect(surface, MOON_GRAY, (0, ground_y, WINDOW_WIDTH, GROUND_HEIGHT))
    
    # Draw static moon surface pattern with scroll offset
    pattern_offset = offset_x % 400  # Loop pattern every 400 pixels
    for x, y, color in moon_surface_pattern:
        screen_x = x - pattern_offset
        if screen_x > -50 and screen_x < WINDOW_WIDTH + 50:  # Only draw visible parts
            pygame.draw.ellipse(surface, color, 
                              (screen_x, ground_y + y, 15, 12))
    
    # Draw subtle craters and texture (static)
    static_seed = random.Random(123)  # Fixed seed for consistency
    for i in range(0, WINDOW_WIDTH + 400, 60):
        x_pos = (i - offset_x % 600)
        if x_pos > -60 and x_pos < WINDOW_WIDTH + 60:
            if static_seed.random() < 0.4:
                crater_size = static_seed.randint(8, 15)
                pygame.draw.circle(surface, MOON_DARK, 
                                 (x_pos, ground_y + static_seed.randint(10, GROUND_HEIGHT - 10)), 
                                 crater_size, 1)

def draw_background(surface, stars_list):
    # Space background (dark purple/black)
    surface.fill(SPACE_BLUE)
    
    # Add gradient to horizon
    for y in range(WINDOW_HEIGHT - GROUND_HEIGHT):
        # Slight gradient near horizon
        if y > (WINDOW_HEIGHT - GROUND_HEIGHT) - 50:
            factor = ((WINDOW_HEIGHT - GROUND_HEIGHT) - y) / 50
            r = int(SPACE_BLUE[0] + (RED_ORANGE[0] - SPACE_BLUE[0]) * factor * 0.3)
            g = int(SPACE_BLUE[1] + (RED_ORANGE[1] - SPACE_BLUE[1]) * factor * 0.3)
            b = int(SPACE_BLUE[2] + (RED_ORANGE[2] - SPACE_BLUE[2]) * factor * 0.3)
            pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))
    
    # Draw stars
    for star_x, star_y, size in stars_list:
        if star_y < WINDOW_HEIGHT - GROUND_HEIGHT:
            pygame.draw.circle(surface, WHITE, (star_x, star_y), size)
            if size > 1:
                pygame.draw.circle(surface, YELLOW, (star_x, star_y), size - 1)

def check_collision(player, obstacles):
    player_rect = player.get_rect()
    for obstacle in obstacles:
        if player_rect.colliderect(obstacle.get_rect()):
            return True
    return False

def main():
    player = Player()
    obstacles = []
    scroll_speed = INITIAL_SCROLL_SPEED
    next_obstacle_x = WINDOW_WIDTH + OBSTACLE_SPAWN_DISTANCE
    game_start_time = pygame.time.get_ticks()
    game_over = False
    game_won = False
    ground_offset = 0
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - game_start_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if not game_over and not game_won:
                        player.jump()
                    else:
                        # Restart game
                        player = Player()
                        obstacles = []
                        scroll_speed = INITIAL_SCROLL_SPEED
                        next_obstacle_x = WINDOW_WIDTH + OBSTACLE_SPAWN_DISTANCE
                        game_start_time = pygame.time.get_ticks()
                        game_over = False
                        game_won = False
        
        if not game_over and not game_won:
            # Increase speed over time
            scroll_speed = INITIAL_SCROLL_SPEED + (elapsed_time * SPEED_INCREASE_RATE / 10)
            
            # Update ground scroll offset
            ground_offset += scroll_speed
            
            # Check win condition
            if elapsed_time >= WIN_TIME:
                game_won = True
            
            # Update player
            player.update()
            
            # Spawn obstacles
            if next_obstacle_x <= WINDOW_WIDTH + 100:
                obstacles.append(Obstacle(next_obstacle_x))
                # Random distance for next obstacle
                next_obstacle_x += OBSTACLE_SPAWN_DISTANCE + random.randint(-100, 200)
            
            # Update obstacles
            obstacles_to_remove = []
            for obstacle in obstacles:
                obstacle.update(scroll_speed)
                if obstacle.x + obstacle.width < 0:
                    obstacles_to_remove.append(obstacle)
            
            for obstacle in obstacles_to_remove:
                obstacles.remove(obstacle)
            
            # Update next obstacle position
            next_obstacle_x -= scroll_speed
            
            # Check collision
            if check_collision(player, obstacles):
                game_over = True
        else:
            # Reset ground offset when game is over/won
            ground_offset = 0
        
        # Draw everything
        draw_background(screen, stars)
        draw_ground(screen, ground_offset)
        
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        player.draw(screen)
        
        # Draw timer
        time_remaining = max(0, (WIN_TIME - elapsed_time) / 1000)
        if not game_over and not game_won:
            timer_text = font.render("Time: {:.1f}s".format(time_remaining), True, WHITE)
            speed_text = font.render("Speed: {:.1f}x".format(scroll_speed), True, WHITE)
            screen.blit(timer_text, (10, 10))
            screen.blit(speed_text, (10, 50))
        
        # Draw game over or win message
        if game_over:
            game_over_text = font.render("GAME OVER! Press SPACE to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(game_over_text, text_rect)
        elif game_won:
            win_text = font.render("YOU WIN! Press SPACE to play again", True, GREEN)
            text_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            screen.blit(win_text, text_rect)
        
        # Instructions
        if not game_over and not game_won:
            instruction_text = pygame.font.Font(None, 24).render("Press SPACE or UP ARROW to jump over craters, boulders, and debris!", True, WHITE)
            screen.blit(instruction_text, (10, WINDOW_HEIGHT - 30))
        
        # Update the display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(FPS)
    
    # Quit Pygame (after game loop ends)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
