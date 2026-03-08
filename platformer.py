import pygame
import sys
import random
import json
import os
import math

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
MARTIAN_GREEN = (100, 200, 100)
MARTIAN_DARK_GREEN = (50, 150, 50)
POWERPACK_COLOR = (255, 215, 0)  # Gold
IMMUNITY_COLOR = (100, 255, 100)  # Light green glow
JETPACK_COLOR = (255, 100, 100)  # Red/orange for jetpack

# Game settings
GROUND_HEIGHT = 150
INITIAL_SCROLL_SPEED = 3
SPEED_INCREASE_RATE = 0.005
WIN_TIME = 60000  # 60 seconds in milliseconds

# Player settings
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 40
JUMP_STRENGTH = 15
JUMP_HOLD_STRENGTH = 0.4  # Additional upward force while holding jump
GRAVITY = 0.6
LEADERBOARD_FILE = "leaderboard.json"

# Powerpack settings
POWERPACK_SIZE = 20
POWERPACK_SPAWN_RATE = 0.003  # Probability per frame
POWERPACK_FALL_SPEED = 3
ABILITY_DURATION = 5000  # 5 seconds in milliseconds

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

class Player:
    def __init__(self):
        self.x = 100
        self.y = WINDOW_HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.velocity_y = 0
        self.on_ground = True
        self.jump_held = False
        self.animation_frame = 0
        self.is_alive = True
        # Active abilities (wallet-based)
        self.immunity_active = False
        self.jetpack_active = False
        self.ability_start_time = 0
        # Wallet/inventory for powerpacks (only shield and jetpack)
        self.wallet = {
            'immunity': 0,
            'jetpack': 0
        }
        # Automatic abilities (activate immediately)
        self.speed_boost_active = False
        self.double_jump_active = False
        self.slow_motion_active = False
        self.double_jumps_used = 0
        self.auto_ability_start_time = 0
        
    def start_jump(self):
        if self.on_ground:
            self.velocity_y = -JUMP_STRENGTH
            self.on_ground = False
            self.jump_held = True
        elif self.double_jump_active and self.double_jumps_used < 1:
            # Double jump ability
            self.velocity_y = -JUMP_STRENGTH * 0.9
            self.double_jumps_used += 1
    
    def continue_jump(self):
        """Continue applying upward force while jump key is held"""
        if not self.on_ground and self.jump_held:
            if self.velocity_y < 0:  # Only apply while moving upward
                self.velocity_y -= JUMP_HOLD_STRENGTH
    
    def release_jump(self):
        self.jump_held = False
    
    def update(self, is_jumping=False, current_time=0):
        # Check if wallet abilities expired
        if current_time - self.ability_start_time > ABILITY_DURATION:
            self.immunity_active = False
            self.jetpack_active = False
        # Check if automatic abilities expired
        if current_time - self.auto_ability_start_time > ABILITY_DURATION:
            self.speed_boost_active = False
            self.double_jump_active = False
            self.slow_motion_active = False
            self.double_jumps_used = 0
        
        # Apply jump hold force if jumping or jetpack active
        if is_jumping and not self.on_ground:
            if self.jetpack_active:
                # Jetpack provides continuous upward thrust
                self.velocity_y = -8
            else:
                self.continue_jump()
        
        # Apply gravity (reduced if slow motion is active)
        gravity_multiplier = 0.5 if self.slow_motion_active else 1.0
        self.velocity_y += GRAVITY * gravity_multiplier
        
        # Reset double jump when on ground
        if self.on_ground:
            self.double_jumps_used = 0
        
        # Update position
        self.y += self.velocity_y
        
        # Check ground collision
        ground_y = WINDOW_HEIGHT - GROUND_HEIGHT - self.height
        if self.y >= ground_y:
            self.y = ground_y
            self.velocity_y = 0
            self.on_ground = True
            self.jump_held = False
        
        # Update animation frame for running
        if self.on_ground:
            self.animation_frame += 1
    
    def add_to_wallet(self, ability_type):
        """Add a powerpack to the wallet"""
        if ability_type in self.wallet:
            self.wallet[ability_type] += 1
    
    def get_active_ability_remaining_time(self, current_time):
        """Get remaining time for active ability in milliseconds"""
        if not (self.immunity_active or self.hover_active or self.jetpack_active):
            return 0
        elapsed = current_time - self.ability_start_time
        remaining = max(0, ABILITY_DURATION - elapsed)
        return remaining
    
    def activate_auto_ability(self, ability_type, current_time):
        """Activate an automatic ability (activates immediately)"""
        self.auto_ability_start_time = current_time
        if ability_type == 'speed_boost':
            self.speed_boost_active = True
        elif ability_type == 'double_jump':
            self.double_jump_active = True
            self.double_jumps_used = 0
        elif ability_type == 'slow_motion':
            self.slow_motion_active = True
    
    def get_active_ability_type(self):
        """Get the type of currently active wallet ability"""
        if self.immunity_active:
            return 'immunity'
        elif self.jetpack_active:
            return 'jetpack'
        return None
    
    def activate_ability(self, ability_type, current_time):
        """Activate a special ability from wallet"""
        # Check if we have the ability in wallet and it's not already active
        if ability_type in self.wallet and self.wallet[ability_type] > 0:
            # Don't activate if already active (prevent stacking)
            if ability_type == 'immunity' and self.immunity_active:
                return
            if ability_type == 'jetpack' and self.jetpack_active:
                return
            
            # Use one from wallet and activate
            self.wallet[ability_type] -= 1
            self.ability_start_time = current_time
            if ability_type == 'immunity':
                self.immunity_active = True
            elif ability_type == 'jetpack':
                self.jetpack_active = True
    
    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)
    
    def draw(self, surface):
        # Draw immunity glow if active
        if self.immunity_active:
            glow_radius = 25
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*IMMUNITY_COLOR, 100), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surface, (self.x + self.width // 2 - glow_radius, self.y + self.height // 2 - glow_radius))
        
        # Determine leg position for running animation (alternates)
        leg_offset = 0
        if self.on_ground:
            # Alternate leg positions every 8 frames
            if (self.animation_frame // 8) % 2 == 0:
                leg_offset = 2
            else:
                leg_offset = -2
        
        # Draw astronaut/martian character with improved graphics
        # Body (suit) with shading
        pygame.draw.rect(surface, WHITE, (self.x, self.y + 15, self.width, self.height - 15))
        # Add subtle shadow/highlight on body
        pygame.draw.line(surface, LIGHT_GRAY, (self.x, self.y + 15), (self.x, self.y + self.height), 2)
        pygame.draw.line(surface, GRAY, (self.x + self.width, self.y + 15), (self.x + self.width, self.y + self.height), 1)
        
        # Helmet with better definition
        pygame.draw.ellipse(surface, WHITE, (self.x - 2, self.y, self.width + 4, 20))
        # Helmet rim/highlight
        pygame.draw.arc(surface, LIGHT_GRAY, (self.x - 2, self.y, self.width + 4, 20), 0, 3.14, 2)
        
        # Draw antennae on top of helmet (improved)
        antenna_y = self.y - 5
        antenna_left_base = (self.x + 8, antenna_y + 2)
        antenna_right_base = (self.x + 22, antenna_y + 2)
        antenna_left_tip = (self.x + 5, antenna_y - 5)
        antenna_right_tip = (self.x + 25, antenna_y - 5)
        
        # Antennae lines with slight curve
        pygame.draw.line(surface, MARTIAN_GREEN, antenna_left_base, antenna_left_tip, 2)
        pygame.draw.line(surface, MARTIAN_GREEN, antenna_right_base, antenna_right_tip, 2)
        # Antennae tips (glowing)
        pygame.draw.circle(surface, MARTIAN_GREEN, antenna_left_tip, 3)
        pygame.draw.circle(surface, MARTIAN_GREEN, antenna_right_tip, 3)
        pygame.draw.circle(surface, YELLOW, antenna_left_tip, 1)
        pygame.draw.circle(surface, YELLOW, antenna_right_tip, 1)
        
        # Visor (tinted, showing martian face inside) - improved with gradient effect
        visor_rect = pygame.Rect(self.x + 2, self.y + 4, self.width - 4, 12)
        # Draw semi-transparent blue visor
        visor_surface = pygame.Surface((self.width - 4, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(visor_surface, (*BLUE, 180), (0, 0, self.width - 4, 12))
        surface.blit(visor_surface, (self.x + 2, self.y + 4))
        # Visor highlight
        pygame.draw.arc(surface, LIGHT_GRAY, (self.x + 2, self.y + 4, self.width - 4, 12), 0, 3.14, 1)
        
        # Draw cute martian face inside helmet (green face)
        face_y = self.y + 8
        face_center_x = self.x + 15
        
        # Face base (green, slightly oval)
        pygame.draw.ellipse(surface, MARTIAN_GREEN, (self.x + 7, face_y, 16, 14))
        
        # Eyes (large cute eyes with shine)
        eye_left_x = self.x + 10
        eye_right_x = self.x + 20
        eye_y = face_y + 3
        
        # Eye whites
        pygame.draw.circle(surface, WHITE, (eye_left_x, eye_y), 4)
        pygame.draw.circle(surface, WHITE, (eye_right_x, eye_y), 4)
        
        # Eye pupils
        pygame.draw.circle(surface, BLACK, (eye_left_x, eye_y), 3)
        pygame.draw.circle(surface, BLACK, (eye_right_x, eye_y), 3)
        
        # Eye shine highlights
        pygame.draw.circle(surface, WHITE, (eye_left_x + 1, eye_y - 1), 1)
        pygame.draw.circle(surface, WHITE, (eye_right_x + 1, eye_y - 1), 1)
        
        # Expression: smile when alive, frown when game over
        mouth_y = face_y + 9
        if self.is_alive:
            # Smile - draw using points for a better curve
            smile_points = []
            for i in range(5):
                x = self.x + 8 + i * 2
                y_offset = int(2 * math.sin(i * math.pi / 4))
                smile_points.append((x, mouth_y + y_offset))
            if len(smile_points) > 1:
                pygame.draw.lines(surface, BLACK, False, smile_points, 2)
        else:
            # Frown - draw inverted curve
            frown_points = []
            for i in range(5):
                x = self.x + 8 + i * 2
                y_offset = -int(2 * math.sin(i * math.pi / 4))
                frown_points.append((x, mouth_y + y_offset))
            if len(frown_points) > 1:
                pygame.draw.lines(surface, BLACK, False, frown_points, 2)
        
        # Oxygen tank on back (or jetpack if active) - improved graphics
        tank_x = self.x - 5
        tank_y = self.y + 20
        if self.jetpack_active:
            # Draw jetpack with enhanced flames
            pygame.draw.rect(surface, JETPACK_COLOR, (tank_x, tank_y, 8, 15))
            pygame.draw.rect(surface, RED, (tank_x + 1, tank_y + 1, 6, 13))
            
            # Enhanced animated flames (multiple flame layers)
            flame_base_y = self.y + 35
            for i in range(2):
                offset_x = i * 4 - 2
                # Outer flame (orange)
                pygame.draw.polygon(surface, ORANGE, [
                    (tank_x + 3 + offset_x, flame_base_y),
                    (tank_x + 1 + offset_x, flame_base_y + 6),
                    (tank_x + 5 + offset_x, flame_base_y + 6)
                ])
                # Inner flame (yellow)
                pygame.draw.polygon(surface, YELLOW, [
                    (tank_x + 3 + offset_x, flame_base_y + 1),
                    (tank_x + 2 + offset_x, flame_base_y + 4),
                    (tank_x + 4 + offset_x, flame_base_y + 4)
                ])
        else:
            # Oxygen tank with metallic look
            pygame.draw.rect(surface, SILVER, (tank_x, tank_y, 8, 15))
            pygame.draw.line(surface, DARK_GRAY, (tank_x + 4, tank_y), (tank_x + 4, tank_y + 15), 1)
            # Tank valve/connection
            pygame.draw.circle(surface, DARK_GRAY, (tank_x + 4, tank_y + 5), 2)
        
        # Arms (swinging for running animation) - improved
        arm_swing = 2 if leg_offset > 0 else -2
        # Left arm
        pygame.draw.rect(surface, WHITE, (self.x - 5, self.y + 25 + arm_swing, 8, 12))
        pygame.draw.circle(surface, WHITE, (self.x - 3, self.y + 28 + arm_swing), 4)  # Hand
        # Right arm
        pygame.draw.rect(surface, WHITE, (self.x + self.width - 3, self.y + 25 - arm_swing, 8, 12))
        pygame.draw.circle(surface, WHITE, (self.x + self.width - 1, self.y + 28 - arm_swing), 4)  # Hand
        
        # Legs (alternating for running) - improved
        # Left leg
        pygame.draw.rect(surface, WHITE, (self.x + 5, self.y + 38 + leg_offset, 8, 12))
        pygame.draw.circle(surface, GRAY, (self.x + 9, self.y + 50 + leg_offset), 5)  # Foot
        # Right leg
        pygame.draw.rect(surface, WHITE, (self.x + 17, self.y + 38 - leg_offset, 8, 12))
        pygame.draw.circle(surface, GRAY, (self.x + 21, self.y + 50 - leg_offset), 5)  # Foot

class PowerPack:
    def __init__(self, x):
        self.x = x
        self.y = -POWERPACK_SIZE
        self.size = POWERPACK_SIZE
        # Wallet-based: immunity, jetpack
        # Auto-activate: speed_boost, double_jump, slow_motion
        self.type = random.choice(['immunity', 'jetpack', 'speed_boost', 'double_jump', 'slow_motion'])
        self.animation_frame = 0
        
    def update(self, scroll_speed):
        self.y += POWERPACK_FALL_SPEED
        self.x -= scroll_speed
        self.animation_frame += 1
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)
    
    def draw(self, surface):
        # Animated glow effect
        glow_size = self.size + int(3 * abs(math.sin(self.animation_frame * 0.1)))
        
        # Draw glow
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*POWERPACK_COLOR, 150), (glow_size, glow_size), glow_size)
        surface.blit(glow_surface, (self.x + self.size // 2 - glow_size, self.y + self.size // 2 - glow_size))
        
        # Draw powerpack
        pygame.draw.rect(surface, POWERPACK_COLOR, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(surface, YELLOW, (self.x + 3, self.y + 3, self.size - 6, self.size - 6))
        
        # Icon based on type
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        if self.type == 'immunity':
            # Shield icon
            pygame.draw.circle(surface, GREEN, (center_x, center_y), 5, 2)
        elif self.type == 'hover':
            # Wings icon
            pygame.draw.circle(surface, BLUE, (center_x - 3, center_y), 2)
            pygame.draw.circle(surface, BLUE, (center_x + 3, center_y), 2)
        elif self.type == 'jetpack':
            # Flame icon
            pygame.draw.polygon(surface, RED, [
                (center_x, center_y - 3),
                (center_x - 2, center_y + 2),
                (center_x + 2, center_y + 2)
            ])

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
            # Draw crater as a depression (moon crater style) - improved
            crater_bottom = ground_y + 25
            # Outer crater rim
            pygame.draw.ellipse(surface, MOON_DARK, (self.x, ground_y - 10, self.width, 30))
            # Inner crater shadow
            pygame.draw.ellipse(surface, DARK_GRAY, (self.x + 5, ground_y - 5, self.width - 10, 20))
            # Deep shadow in center
            pygame.draw.ellipse(surface, BLACK, (self.x + self.width // 3, ground_y, self.width // 3, 10))
            # Rim highlight
            pygame.draw.arc(surface, MOON_LIGHT, (self.x, ground_y - 10, self.width, 30), 0, 3.14, 2)
            
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
            # Highlights for 3D effect
            pygame.draw.circle(surface, LIGHT_GRAY, (self.x + self.width // 2, self.y + 10), 8)
            pygame.draw.circle(surface, WHITE, (self.x + self.width // 2 + 2, self.y + 8), 4)
            # Shadow on bottom
            pygame.draw.polygon(surface, BLACK, [
                (self.x + 5, self.y + 2 * self.height // 3),
                (self.x + self.width // 3, self.y + self.height - 5),
                (self.x + 2 * self.width // 3, self.y + self.height),
                (self.x + self.width - 5, self.y + 2 * self.height // 3)
            ])
            
        elif self.type == 'debris':
            # Draw spaceship debris (angular metal pieces) - improved
            # Main body with metallic look
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
            # Metallic highlights
            pygame.draw.line(surface, WHITE, (self.x + 15, self.y + 12), 
                           (self.x + self.width - 15, self.y + 12), 1)
            # Detail lines and damage
            pygame.draw.line(surface, DARK_GRAY, (self.x + 20, self.y + 15), 
                           (self.x + self.width - 20, self.y + 15), 2)
            pygame.draw.circle(surface, RED, (self.x + self.width // 2, self.y + 25), 4)
            # Scratches/damage marks
            for i in range(3):
                scratch_x = self.x + random.randint(10, self.width - 10)
                pygame.draw.line(surface, DARK_GRAY, (scratch_x, self.y + 10), 
                               (scratch_x + 2, self.y + 18), 1)

def draw_ground(surface, offset_x=0):
    """Draw smooth moon surface similar to sky gradient style"""
    ground_y = WINDOW_HEIGHT - GROUND_HEIGHT
    
    # Draw smooth moon surface with gradient (similar to sky style)
    for y in range(GROUND_HEIGHT):
        # Create gradient from lighter at top to darker at bottom
        factor = y / GROUND_HEIGHT
        r = int(MOON_LIGHT[0] * (1 - factor) + MOON_GRAY[0] * factor)
        g = int(MOON_LIGHT[1] * (1 - factor) + MOON_GRAY[1] * factor)
        b = int(MOON_LIGHT[2] * (1 - factor) + MOON_GRAY[2] * factor)
        pygame.draw.line(surface, (r, g, b), (0, ground_y + y), (WINDOW_WIDTH, ground_y + y))
    
    # Add very subtle texture dots (sparse, like stars in sky)
    static_seed = random.Random(42)  # Fixed seed
    for i in range(20):  # Only a few dots for subtlety
        x = static_seed.randint(0, WINDOW_WIDTH + 200)
        y_pos = static_seed.randint(ground_y + 10, WINDOW_HEIGHT - 10)
        x_pos = (x - offset_x % (WINDOW_WIDTH + 200))
        if x_pos > -10 and x_pos < WINDOW_WIDTH + 10:
            pygame.draw.circle(surface, MOON_DARK, (x_pos, y_pos), 2)

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

def check_powerpack_collision(player, powerpacks):
    """Check if player collected any powerpack, return the type if collected"""
    player_rect = player.get_rect()
    for powerpack in powerpacks:
        if player_rect.colliderect(powerpack.get_rect()):
            return powerpack
    return None

def load_leaderboard():
    """Load leaderboard from file, return top 3 scores"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                scores = json.load(f)
                return sorted(scores, reverse=True)[:3]  # Top 3, highest first
        except:
            return []
    return []

def save_leaderboard(scores):
    """Save leaderboard to file"""
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(scores, f)

def update_leaderboard(new_score):
    """Update leaderboard with new score"""
    scores = load_leaderboard()
    scores.append(new_score)
    scores = sorted(scores, reverse=True)[:3]  # Keep top 3
    save_leaderboard(scores)
    return scores

def main():
    player = Player()
    obstacles = []
    powerpacks = []
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
        
        # Check if jump key is currently held
        keys = pygame.key.get_pressed()
        is_jumping = (keys[pygame.K_SPACE] or keys[pygame.K_UP])
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if not game_over and not game_won:
                        player.start_jump()
                    else:
                        # Restart game
                        player = Player()
                        obstacles = []
                        powerpacks = []
                        scroll_speed = INITIAL_SCROLL_SPEED
                        next_obstacle_x = WINDOW_WIDTH + OBSTACLE_SPAWN_DISTANCE
                        game_start_time = pygame.time.get_ticks()
                        game_over = False
                        game_won = False
                # Number keys to activate abilities from wallet
                if not game_over and not game_won:
                    if event.key == pygame.K_1:
                        # Activate shield/immunity
                        player.activate_ability('immunity', current_time)
                    elif event.key == pygame.K_2:
                        # Activate jetpack
                        player.activate_ability('jetpack', current_time)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    player.release_jump()
        
        if not game_over and not game_won:
            player.is_alive = True
            
            # Increase speed over time (boosted if speed_boost is active)
            base_speed_increase = INITIAL_SCROLL_SPEED + (elapsed_time * SPEED_INCREASE_RATE / 10)
            scroll_speed = base_speed_increase * 1.5 if player.speed_boost_active else base_speed_increase
            # Slow motion reduces speed
            if player.slow_motion_active:
                scroll_speed *= 0.6
            
            # Update ground scroll offset
            ground_offset += scroll_speed
            
            # Check win condition
            if elapsed_time >= WIN_TIME:
                game_won = True
                # Update leaderboard on win (survived full time)
                update_leaderboard(WIN_TIME)
            
            # Spawn powerpacks randomly from sky
            if random.random() < POWERPACK_SPAWN_RATE:
                spawn_x = random.randint(200, WINDOW_WIDTH - 200)
                powerpacks.append(PowerPack(spawn_x))
            
            # Update powerpacks
            powerpacks_to_remove = []
            for powerpack in powerpacks:
                powerpack.update(scroll_speed)
                # Remove if off screen or collected
                if powerpack.y > WINDOW_HEIGHT or powerpack.x + powerpack.size < 0:
                    powerpacks_to_remove.append(powerpack)
            
            for powerpack in powerpacks_to_remove:
                powerpacks.remove(powerpack)
            
            # Check powerpack collision - add to wallet or auto-activate
            collected = check_powerpack_collision(player, powerpacks)
            if collected:
                # Wallet-based: immunity, jetpack
                if collected.type in ['immunity', 'jetpack']:
                    player.add_to_wallet(collected.type)
                else:
                    # Auto-activate: speed_boost, double_jump, slow_motion
                    player.activate_auto_ability(collected.type, current_time)
                powerpacks.remove(collected)
            
            # Update player (pass jump state and current time for hold-to-jump and abilities)
            player.update(is_jumping, current_time)
            
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
            
            # Check collision (ignore if immunity is active)
            if not player.immunity_active and check_collision(player, obstacles):
                game_over = True
                player.is_alive = False
                # Update leaderboard with time survived
                update_leaderboard(elapsed_time)
        else:
            # Reset ground offset when game is over/won
            ground_offset = 0
        
        # Draw everything
        draw_background(screen, stars)
        draw_ground(screen, ground_offset)
        
        # Draw powerpacks
        for powerpack in powerpacks:
            powerpack.draw(screen)
        
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
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
            screen.blit(game_over_text, text_rect)
        elif game_won:
            win_text = font.render("YOU WIN! Press SPACE to play again", True, GREEN)
            text_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
            screen.blit(win_text, text_rect)
        
        # Draw leaderboard only at game start/end
        if game_over or game_won:
            leaderboard = load_leaderboard()
            if leaderboard:
                leaderboard_y = WINDOW_HEIGHT // 2 + 30
                leaderboard_title = pygame.font.Font(None, 28).render("Top 3 Longest Runs:", True, YELLOW)
                text_rect = leaderboard_title.get_rect(center=(WINDOW_WIDTH // 2, leaderboard_y))
                screen.blit(leaderboard_title, text_rect)
                leaderboard_y += 35
                for i, score in enumerate(leaderboard, 1):
                    time_seconds = score / 1000.0
                    rank_text = pygame.font.Font(None, 24).render("{}. {:.1f}s".format(i, time_seconds), True, WHITE)
                    text_rect = rank_text.get_rect(center=(WINDOW_WIDTH // 2, leaderboard_y))
                    screen.blit(rank_text, text_rect)
                    leaderboard_y += 30
        
        # Instructions
        if not game_over and not game_won:
            instruction_text = pygame.font.Font(None, 24).render("Hold SPACE/UP to jump! Press 1/2 to use wallet powerpacks!", True, WHITE)
            screen.blit(instruction_text, (10, WINDOW_HEIGHT - 30))
        
        # Show wallet box and active ability status bar
        if not game_over and not game_won:
            # Draw wallet box (bottom right)
            wallet_box_width = 165
            wallet_box_height = 70
            wallet_box_x = WINDOW_WIDTH - wallet_box_width - 10
            wallet_box_y = WINDOW_HEIGHT - wallet_box_height - 80
            wallet_box_width = 165
            wallet_box_height = 70
            
            # Draw box border and background
            wallet_box = pygame.Rect(wallet_box_x, wallet_box_y, wallet_box_width, wallet_box_height)
            pygame.draw.rect(screen, (40, 40, 40), wallet_box)  # Dark background
            pygame.draw.rect(screen, YELLOW, wallet_box, 2)  # Yellow border
            
            wallet_y = wallet_box_y + 6
            wallet_title = pygame.font.Font(None, 22).render("WALLET", True, YELLOW)
            screen.blit(wallet_title, (wallet_box_x + 5, wallet_y))
            wallet_y += 24
            
            # Display wallet contents
            wallet_text = pygame.font.Font(None, 18).render("1 - Shield: {}".format(player.wallet['immunity']), True, GREEN)
            screen.blit(wallet_text, (wallet_box_x + 5, wallet_y))
            wallet_y += 20
            wallet_text = pygame.font.Font(None, 18).render("2 - Jetpack: {}".format(player.wallet['jetpack']), True, RED)
            screen.blit(wallet_text, (wallet_box_x + 5, wallet_y))
            
            # Show active ability with progress bar
            active_type = player.get_active_ability_type()
            if active_type:
                ability_y = wallet_box_y + wallet_box_height + 8
                
                # Determine ability name and color
                if active_type == 'immunity':
                    ability_name = "SHIELD"
                    ability_color = GREEN
                elif active_type == 'jetpack':
                    ability_name = "JETPACK"
                    ability_color = RED
                
                # Draw ability status box
                status_box_x = wallet_box_x
                status_box_y = ability_y
                status_box_width = wallet_box_width
                status_box_height = 32
                status_box = pygame.Rect(status_box_x, status_box_y, status_box_width, status_box_height)
                pygame.draw.rect(screen, (40, 40, 40), status_box)
                pygame.draw.rect(screen, ability_color, status_box, 2)
                
                # Show ability name
                ability_text = pygame.font.Font(None, 18).render("{} ACTIVE".format(ability_name), True, ability_color)
                screen.blit(ability_text, (status_box_x + 5, status_box_y + 4))
                
                # Calculate and draw progress bar
                remaining_time = player.get_active_ability_remaining_time(current_time)
                progress = remaining_time / ABILITY_DURATION if ABILITY_DURATION > 0 else 0
                
                # Progress bar background
                bar_x = status_box_x + 5
                bar_y = status_box_y + 22
                bar_width = status_box_width - 10
                bar_height = 6
                pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height))
                
                # Progress bar fill
                fill_width = int(bar_width * progress)
                if fill_width > 0:
                    # Color transitions from full to empty
                    color_intensity = int(255 * progress)
                    if active_type == 'immunity':
                        bar_color = (0, color_intensity, 0)
                    elif active_type == 'jetpack':
                        bar_color = (color_intensity, 0, 0)
                    else:  # hover
                        bar_color = (0, 0, color_intensity)
                    pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_width, bar_height))
                
                # Show remaining time in seconds
                time_remaining_sec = remaining_time / 1000.0
                time_text = pygame.font.Font(None, 14).render("{:.1f}s left".format(time_remaining_sec), True, WHITE)
                screen.blit(time_text, (bar_x + bar_width - 45, status_box_y + 5))
        
        # Update the display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(FPS)
    
    # Quit Pygame (after game loop ends)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
