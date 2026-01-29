"""
Tower Defence Simulator (TDS) - Улучшенная версия с ботами, боссами, картами и сложностями
"""

import arcade
import json
import os
import math
import random
import csv
from enum import Enum
from datetime import datetime
from typing import List, Tuple, Optional

# ==================== КОНСТАНТЫ ====================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Tower Defence Simulator (TDS)"
TILE_SIZE = 64
UI_HEIGHT = 140
TOWER_BUTTONS_WIDTH = 220  # Ширина панели для кнопок башен

# Приятные цвета интерфейса
UI_BACKGROUND = (50, 60, 90, 240)
UI_BUTTON_NORMAL = (80, 100, 150, 220)
UI_BUTTON_HOVER = (100, 130, 180, 240)
UI_BUTTON_SELECTED = (120, 160, 210, 255)
TEXT_COLOR = (240, 240, 255, 255)
TEXT_SHADOW = (30, 30, 50, 255)

# Яркие цвета башен для лучшего различения
ARCHER_COLOR = (70, 200, 255)      # Яркий синий треугольник
CANNON_COLOR = (255, 100, 100)    # Яркий красный квадрат
MAGE_COLOR = (200, 100, 255)      # Яркий фиолетовый круг

# Цвета врагов
SLIME_COLOR = (102, 205, 170)
ORC_COLOR = (255, 165, 0)
GOBLIN_COLOR = (144, 238, 144)
SKELETON_COLOR = (220, 220, 220)
KNIGHT_COLOR = (70, 130, 180)
BOSS_DRAGON_COLOR = (220, 20, 60)      # Яркий красный дракон
BOSS_GIANT_COLOR = (160, 82, 45)       # Коричневый гигант
BOSS_WIZARD_COLOR = (138, 43, 226)     # Фиолетовый маг

# Цвета снарядов
ARCHER_PROJECTILE = (100, 200, 255)
CANNON_PROJECTILE = (255, 165, 0)
MAGE_PROJECTILE = (200, 150, 255)

# Игровые константы
STARTING_MONEY_EASY = 500
STARTING_MONEY_NORMAL = 350
STARTING_MONEY_HARD = 200
STARTING_LIVES_EASY = 40
STARTING_LIVES_NORMAL = 25
STARTING_LIVES_HARD = 15
BASE_DAMAGE = 5

# ==================== ENUMS ====================
class TowerType(Enum):
    ARCHER = "archer"
    CANNON = "cannon"
    MAGE = "mage"

class EnemyType(Enum):
    SLIME = "slime"
    ORC = "orc"
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    KNIGHT = "knight"
    BOSS_DRAGON = "boss_dragon"
    BOSS_GIANT = "boss_giant"
    BOSS_WIZARD = "boss_wizard"

class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"

class MapType(Enum):
    MAP1 = "map1"
    MAP2 = "map2"
    MAP3 = "map3"

# ==================== СИСТЕМА ЧАСТИЦ ====================
class ParticleSystem:
    def __init__(self):
        self.particles = []

    def create_explosion(self, x, y, color=None, count=20):
        color = color or (255, 165, 0)
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'dx': random.uniform(-3, 3),
                'dy': random.uniform(-3, 3),
                'size': random.uniform(2, 6),
                'color': color,
                'life': random.uniform(0.5, 1.5),
                'max_life': random.uniform(0.5, 1.5)
            })

    def create_trail(self, x, y, color=None):
        color = color or (200, 200, 200)
        self.particles.append({
            'x': x, 'y': y,
            'dx': random.uniform(-1, 1),
            'dy': random.uniform(-1, 1),
            'size': random.uniform(1, 3),
            'color': color,
            'life': random.uniform(0.2, 0.5),
            'max_life': random.uniform(0.2, 0.5)
        })

    def update(self, delta_time):
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= delta_time
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self):
        for particle in self.particles:
            life_ratio = max(0, particle['life'] / particle['max_life'])
            alpha = int(255 * life_ratio)
            alpha = max(0, min(255, alpha))
            color = (*particle['color'][:3], alpha)
            arcade.draw_circle_filled(
                particle['x'], particle['y'],
                particle['size'], color
            )

# ==================== КЛАССЫ ПРОЕКТИЛЕЙ ====================
class Projectile(arcade.Sprite):
    def __init__(self, x, y, target, damage, speed=8.0, color=(255, 255, 255), scale=0.5, shape="circle"):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.color = color
        self.scale = scale
        self.shape = shape  # "circle", "triangle", "square"
        self.homing = True
        self.homing_strength = 0.1

        # Создаем текстуру в зависимости от формы
        if shape == "circle":
            self.texture = arcade.make_circle_texture(12, color)
        elif shape == "triangle":
            self.texture = arcade.make_soft_circle_texture(12, color, center_alpha=255, outer_alpha=0)
        else:  # square
            self.texture = arcade.make_soft_square_texture(12, color, center_alpha=255, outer_alpha=0)

        if target:
            self.update_movement()

    def update_movement(self):
        if self.target and self.target.health > 0:
            dx = self.target.center_x - self.center_x
            dy = self.target.center_y - self.center_y
            distance = max(0.1, math.sqrt(dx**2 + dy**2))
            self.change_x = (dx / distance) * self.speed
            self.change_y = (dy / distance) * self.speed
            self.angle = math.degrees(math.atan2(dy, dx))

    def update(self):
        if self.homing and self.target and self.target.health > 0:
            dx = self.target.center_x - self.center_x
            dy = self.target.center_y - self.center_y
            distance = max(0.1, math.sqrt(dx**2 + dy**2))

            target_dx = (dx / distance) * self.speed
            target_dy = (dy / distance) * self.speed

            self.change_x += (target_dx - self.change_x) * self.homing_strength
            self.change_y += (target_dy - self.change_y) * self.homing_strength

            current_speed = math.sqrt(self.change_x**2 + self.change_y**2)
            if current_speed > 0:
                self.change_x = (self.change_x / current_speed) * self.speed
                self.change_y = (self.change_y / current_speed) * self.speed

            self.angle = math.degrees(math.atan2(self.change_y, self.change_x))

        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += 10

# ==================== КЛАССЫ ВРАГОВ ====================
class Enemy(arcade.Sprite):
    def __init__(self, enemy_type, path_points, level=1, difficulty=Difficulty.NORMAL):
        super().__init__()
        self.enemy_type = enemy_type
        self.path_points = path_points
        self.path_index = 0
        self.level = level
        self.difficulty = difficulty
        self.alive = True

        # Модификаторы сложности
        difficulty_multiplier = {
            Difficulty.EASY: 0.9,
            Difficulty.NORMAL: 1.0,
            Difficulty.HARD: 1.5
        }
        multiplier = difficulty_multiplier[difficulty]

        if enemy_type == EnemyType.SLIME:
            self.color = SLIME_COLOR
            self.health = int((60 + level * 15) * multiplier)
            self.max_health = int((60 + level * 15) * multiplier)
            self.speed = 0.8 * (1.2 if difficulty == Difficulty.EASY else 0.9 if difficulty == Difficulty.HARD else 1.0)
            self.bounty = int((15 + level * 3) * multiplier)
            self.scale = 0.8
            texture_size = 22
        elif enemy_type == EnemyType.ORC:
            self.color = ORC_COLOR
            self.health = int((120 + level * 20) * multiplier)
            self.max_health = int((120 + level * 20) * multiplier)
            self.speed = 0.6 * (1.1 if difficulty == Difficulty.EASY else 0.9 if difficulty == Difficulty.HARD else 1.0)
            self.bounty = int((25 + level * 5) * multiplier)
            self.scale = 0.9
            texture_size = 26
        elif enemy_type == EnemyType.GOBLIN:
            self.color = GOBLIN_COLOR
            self.health = int((40 + level * 8) * multiplier)
            self.max_health = int((40 + level * 8) * multiplier)
            self.speed = 1.3 * (1.2 if difficulty == Difficulty.EASY else 0.9 if difficulty == Difficulty.HARD else 1.0)
            self.bounty = int((20 + level * 3) * multiplier)
            self.scale = 0.7
            texture_size = 20
        elif enemy_type == EnemyType.SKELETON:
            self.color = SKELETON_COLOR
            self.health = int((150 + level * 25) * multiplier)
            self.max_health = int((150 + level * 25) * multiplier)
            self.speed = 0.9 * (1.1 if difficulty == Difficulty.EASY else 0.9 if difficulty == Difficulty.HARD else 1.0)
            self.bounty = int((35 + level * 6) * multiplier)
            self.scale = 0.85
            texture_size = 24
        elif enemy_type == EnemyType.KNIGHT:
            self.color = KNIGHT_COLOR
            self.health = int((250 + level * 35) * multiplier)
            self.max_health = int((250 + level * 35) * multiplier)
            self.speed = 0.5 * (1.1 if difficulty == Difficulty.EASY else 0.9 if difficulty == Difficulty.HARD else 1.0)
            self.bounty = int((60 + level * 8) * multiplier)
            self.scale = 1.0
            texture_size = 30
        elif enemy_type == EnemyType.BOSS_DRAGON:
            self.color = BOSS_DRAGON_COLOR
            self.health = int((1200 + level * 150) * multiplier)
            self.max_health = int((1200 + level * 150) * multiplier)
            self.speed = 0.4
            self.bounty = int((400 + level * 50) * multiplier)
            self.scale = 1.5
            texture_size = 50
        elif enemy_type == EnemyType.BOSS_GIANT:
            self.color = BOSS_GIANT_COLOR
            self.health = int((1800 + level * 200) * multiplier)
            self.max_health = int((1800 + level * 200) * multiplier)
            self.speed = 0.3
            self.bounty = int((500 + level * 60) * multiplier)
            self.scale = 1.7
            texture_size = 55
        elif enemy_type == EnemyType.BOSS_WIZARD:
            self.color = BOSS_WIZARD_COLOR
            self.health = int((900 + level * 120) * multiplier)
            self.max_health = int((900 + level * 120) * multiplier)
            self.speed = 0.5
            self.bounty = int((450 + level * 55) * multiplier)
            self.scale = 1.4
            texture_size = 45

        self.texture = arcade.make_circle_texture(texture_size, self.color)

        if path_points:
            self.center_x, self.center_y = path_points[0]

    def update(self):
        if not self.alive:
            return

        if self.path_index < len(self.path_points):
            target_x, target_y = self.path_points[self.path_index]
            dx = target_x - self.center_x
            dy = target_y - self.center_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 2:
                self.center_x += (dx / distance) * self.speed
                self.center_y += (dy / distance) * self.speed
                if dx != 0:
                    self.angle = math.degrees(math.atan2(dy, dx))
            else:
                self.path_index += 1

    def has_reached_end(self):
        return self.path_index >= len(self.path_points)

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def draw_health_bar(self):
        if self.health < self.max_health:
            bar_width = 60 if self.enemy_type.value.startswith('boss') else 50
            bar_height = 8 if self.enemy_type.value.startswith('boss') else 5
            health_percent = self.health / self.max_health

            left = self.center_x - bar_width // 2
            right = self.center_x + bar_width // 2
            bottom = self.center_y + self.height // 2 + 20 - bar_height // 2
            top = self.center_y + self.height // 2 + 20 + bar_height // 2

            arcade.draw_lrbt_rectangle_filled(
                left, right, bottom, top,
                (60, 60, 60, 200)
            )

            if health_percent > 0:
                right_health = left + bar_width * health_percent
                health_color = (
                    (100, 255, 100) if health_percent > 0.6 else
                    (255, 255, 100) if health_percent > 0.3 else
                    (255, 100, 100)
                )
                arcade.draw_lrbt_rectangle_filled(
                    left, right_health, bottom, top,
                    health_color
                )

# ==================== КЛАССЫ БАШЕН ====================
class Tower(arcade.Sprite):
    def __init__(self, tower_type, x, y):
        super().__init__()
        self.tower_type = tower_type
        self.center_x = x
        self.center_y = y
        self.level = 1
        self.fire_timer = 0
        self.target = None
        self.max_level = 5  # Увеличили максимальный уровень улучшения
        self.shape = None  # Будет определена ниже

        if tower_type == TowerType.ARCHER:
            self.color = ARCHER_COLOR
            self.damage = 25
            self.range = 220
            self.fire_rate = 1.5
            self.cost = 120
            self.projectile_speed = 14.0
            self.projectile_color = ARCHER_PROJECTILE
            self.projectile_shape = "triangle"
            self.shape = "triangle"
        elif tower_type == TowerType.CANNON:
            self.color = CANNON_COLOR
            self.damage = 50
            self.range = 180
            self.fire_rate = 1.0
            self.cost = 250
            self.projectile_speed = 10.0
            self.projectile_color = CANNON_PROJECTILE
            self.projectile_shape = "square"
            self.shape = "square"
        elif tower_type == TowerType.MAGE:
            self.color = MAGE_COLOR
            self.damage = 20
            self.range = 200
            self.fire_rate = 2.0
            self.cost = 180
            self.projectile_speed = 11.0
            self.projectile_color = MAGE_PROJECTILE
            self.projectile_shape = "circle"
            self.shape = "circle"

        self.scale = 0.9

    def find_target(self, enemies):
        closest = None
        closest_distance = self.range

        for enemy in enemies:
            if not enemy.alive or enemy.health <= 0:
                continue
            distance = math.sqrt((self.center_x - enemy.center_x)**2 +
                               (self.center_y - enemy.center_y)**2)
            if distance < closest_distance:
                closest = enemy
                closest_distance = distance

        self.target = closest
        return closest

    def can_attack(self):
        return self.fire_timer >= 1.0 / self.fire_rate

    def update(self, delta_time, enemies, projectiles, sound_manager, particle_system):
        self.fire_timer += delta_time

        if not self.target or not self.target.alive or self.target.health <= 0:
            self.find_target(enemies)
        elif self.target:
            distance = math.sqrt((self.center_x - self.target.center_x)**2 +
                               (self.center_y - self.target.center_y)**2)
            if distance > self.range:
                self.find_target(enemies)

        if self.target and self.can_attack() and self.target.alive:
            distance = math.sqrt((self.center_x - self.target.center_x)**2 +
                               (self.center_y - self.target.center_y)**2)
            if distance <= self.range:
                self.attack(projectiles, sound_manager, particle_system)
                self.fire_timer = 0

    def attack(self, projectiles, sound_manager, particle_system):
        projectile = Projectile(
            self.center_x, self.center_y,
            self.target, self.damage,
            self.projectile_speed, self.projectile_color, 0.8, self.projectile_shape
        )
        projectiles.append(projectile)

        if sound_manager:
            if self.tower_type == TowerType.ARCHER:
                sound_manager.play_sound("shoot", volume=0.3)
            elif self.tower_type == TowerType.CANNON:
                sound_manager.play_sound("explosion", volume=0.3)
            else:
                sound_manager.play_sound("magic", volume=0.3)

        if particle_system:
            angle = math.atan2(self.target.center_y - self.center_y,
                             self.target.center_x - self.center_x)
            muzzle_x = self.center_x + math.cos(angle) * 35
            muzzle_y = self.center_y + math.sin(angle) * 35
            particle_system.create_explosion(muzzle_x, muzzle_y, self.projectile_color, 8)

    def draw(self):
        """Отрисовка башни с разными формами и яркими цветами"""
        if self.shape == "triangle":
            # Рисуем треугольник с градиентом
            points = [
                (self.center_x, self.center_y + 30),  # Верхняя точка
                (self.center_x - 25, self.center_y - 20),  # Левая нижняя
                (self.center_x + 25, self.center_y - 20)   # Правая нижняя
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 3)

            # Внутренний треугольник для объема
            inner_points = [
                (self.center_x, self.center_y + 15),
                (self.center_x - 15, self.center_y - 10),
                (self.center_x + 15, self.center_y - 10)
            ]
            arcade.draw_polygon_filled(inner_points, (min(255, self.color[0] + 50),
                                                      min(255, self.color[1] + 50),
                                                      min(255, self.color[2] + 50)))

            # Уровень башни в центре
            if self.level > 1:
                level_color = (255, 255, 100) if self.level == 2 else (255, 220, 50) if self.level == 3 else (255, 180, 30) if self.level == 4 else (255, 140, 20)
                arcade.draw_circle_filled(self.center_x, self.center_y - 5, 10, level_color)
                arcade.draw_text(str(self.level), self.center_x, self.center_y - 10,
                               (0, 0, 0), 12, anchor_x="center", anchor_y="center", bold=True)

        elif self.shape == "square":
            # Рисуем квадрат с градиентом
            half_size = 25
            points = [
                (self.center_x - half_size, self.center_y - half_size),  # Левый нижний
                (self.center_x + half_size, self.center_y - half_size),  # Правый нижний
                (self.center_x + half_size, self.center_y + half_size),  # Правый верхний
                (self.center_x - half_size, self.center_y + half_size)   # Левый верхний
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 3)

            # Внутренний квадрат для объема
            inner_half = 15
            inner_points = [
                (self.center_x - inner_half, self.center_y - inner_half),
                (self.center_x + inner_half, self.center_y - inner_half),
                (self.center_x + inner_half, self.center_y + inner_half),
                (self.center_x - inner_half, self.center_y + inner_half)
            ]
            arcade.draw_polygon_filled(inner_points, (min(255, self.color[0] + 50),
                                                      min(255, self.color[1] + 50),
                                                      min(255, self.color[2] + 50)))

            # Уровень башни в центре
            if self.level > 1:
                level_color = (255, 255, 100) if self.level == 2 else (255, 220, 50) if self.level == 3 else (255, 180, 30) if self.level == 4 else (255, 140, 20)
                arcade.draw_circle_filled(self.center_x, self.center_y, 10, level_color)
                arcade.draw_text(str(self.level), self.center_x, self.center_y - 1,
                               (0, 0, 0), 12, anchor_x="center", anchor_y="center", bold=True)

        else:  # circle
            # Рисуем круг с градиентом
            arcade.draw_circle_filled(self.center_x, self.center_y, 30, self.color)
            arcade.draw_circle_outline(self.center_x, self.center_y, 30, (255, 255, 255), 3)

            # Внутренний круг для объема
            arcade.draw_circle_filled(self.center_x, self.center_y, 20,
                                     (min(255, self.color[0] + 50),
                                      min(255, self.color[1] + 50),
                                      min(255, self.color[2] + 50)))

            # Уровень башни в центре
            if self.level > 1:
                level_color = (255, 255, 100) if self.level == 2 else (255, 220, 50) if self.level == 3 else (255, 180, 30) if self.level == 4 else (255, 140, 20)
                arcade.draw_circle_filled(self.center_x, self.center_y, 10, level_color)
                arcade.draw_text(str(self.level), self.center_x, self.center_y - 1,
                               (0, 0, 0), 12, anchor_x="center", anchor_y="center", bold=True)

    def draw_range(self):
        arcade.draw_circle_outline(
            self.center_x, self.center_y,
            self.range, (*self.color[:3], 150), 3
        )

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            self.damage = int(self.damage * 1.6)
            self.range *= 1.25
            self.fire_rate *= 1.15
            return self.cost // 2  # Стоимость улучшения
        return 0  # Уже максимальный уровень

# ==================== МЕНЕДЖЕР ЗВУКОВ ====================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music = {}
        self.music_player = None
        self.enabled = True
        self.sound_volume = 0.3
        self.music_volume = 0.2
        self.load_sounds()

    def load_sounds(self):
        try:
            self.sounds["shoot"] = arcade.load_sound(":resources:sounds/laser1.wav")
            self.sounds["explosion"] = arcade.load_sound(":resources:sounds/explosion2.wav")
            self.sounds["build"] = arcade.load_sound(":resources:sounds/coin1.wav")
            self.sounds["upgrade"] = arcade.load_sound(":resources:sounds/upgrade1.wav")
            self.sounds["enemy_die"] = arcade.load_sound(":resources:sounds/hit3.wav")
            self.sounds["click"] = arcade.load_sound(":resources:sounds/coin1.wav")
            self.sounds["magic"] = arcade.load_sound(":resources:sounds/upgrade4.wav")
            self.sounds["wave_start"] = arcade.load_sound(":resources:sounds/upgrade5.wav")
            self.sounds["lose_life"] = arcade.load_sound(":resources:sounds/error2.wav")
            self.sounds["boss_spawn"] = arcade.load_sound(":resources:sounds/rockHit2.wav")

            self.music["menu"] = arcade.load_sound(":resources:music/funkyrobot.mp3")
            self.music["game"] = arcade.load_sound(":resources:music/1918.mp3")
        except Exception as e:
            print(f"Ошибка загрузки звуков: {e}")

    def play_sound(self, sound_name, volume=None):
        if not self.enabled or sound_name not in self.sounds:
            return None
        vol = volume or self.sound_volume
        return self.sounds[sound_name].play(volume=vol)

    def play_music(self, music_name, volume=None):
        if not self.enabled or music_name not in self.music:
            return

        if self.music_player:
            self.music_player.pause()

        vol = volume or self.music_volume
        self.music_player = self.music[music_name].play(volume=vol, loop=True)

    def stop_music(self):
        if self.music_player:
            self.music_player.pause()
            self.music_player = None

# ==================== МЕНЕДЖЕР СОХРАНЕНИЙ ====================
class SaveManager:
    def __init__(self):
        self.save_file = "data/save.json"
        self.scores_file = "data/scores.csv"
        os.makedirs("data", exist_ok=True)

    def save_game(self, data):
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def load_game(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
        return None

    def save_score(self, name, score, level, waves, difficulty, map_name):
        try:
            with open(self.scores_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([name, score, level, waves, difficulty, map_name, datetime.now().strftime("%Y-%m-%d %H:%M")])
            return True
        except Exception as e:
            print(f"Ошибка сохранения рекорда: {e}")
            return False

    def load_scores(self):
        scores = []
        if os.path.exists(self.scores_file):
            with open(self.scores_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 7:
                        try:
                            scores.append({
                                "name": row[0],
                                "score": int(row[1]),
                                "level": int(row[2]),
                                "waves": int(row[3]),
                                "difficulty": row[4],
                                "map_name": row[5],
                                "date": row[6]
                            })
                        except ValueError:
                            continue
        return sorted(scores, key=lambda x: x["score"], reverse=True)[:10]

# ==================== ПРЕДСТАВЛЕНИЯ ====================
class MenuView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.selected = 0
        self.menu_items = ["НОВАЯ ИГРА", "ПРОДОЛЖИТЬ", "РЕКОРДЫ", "НАСТРОЙКИ", "ВЫХОД"]
        self.background_y = 0
        self.title_alpha = 255
        self.title_direction = -1
        self.title_text = None
        self.subtitle_text = None
        self.menu_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))
        self.window.sound_manager.play_music("menu")

        self.title_text = arcade.Text(
            "Tower Defence Simulator",
            self.window.width // 2,
            self.window.height - 150,
            (100, 200, 255, self.title_alpha),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        self.subtitle_text = arcade.Text(
            "Защити свою базу от врагов!",
            self.window.width // 2,
            self.window.height - 220,
            (200, 220, 255),
            24,
            anchor_x="center",
            anchor_y="center"
        )

        self.menu_texts = []
        for i, item in enumerate(self.menu_items):
            y = self.window.height // 2 - i * 60
            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            text = arcade.Text(
                item,
                self.window.width // 2,
                y,
                color,
                32,
                anchor_x="center",
                anchor_y="center",
                bold=(i == self.selected)
            )
            self.menu_texts.append(text)

        self.control_text = arcade.Text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Выход • F11: Полный экран",
            self.window.width // 2,
            50,
            (180, 190, 210),
            18,
            anchor_x="center",
            anchor_y="center"
        )

    def on_draw(self):
        self.clear()

        self.background_y = (self.background_y + 0.5) % self.window.height

        self.title_alpha += self.title_direction * 2
        if self.title_alpha <= 150 or self.title_alpha >= 255:
            self.title_direction *= -1

        self.title_text.color = (100, 200, 255, self.title_alpha)

        arcade.draw_text(
            "Tower Defence Simulator",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60, self.title_alpha),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        self.title_text.draw()

        arcade.draw_text(
            "Защити свою базу от врагов!",
            self.window.width // 2 + 1,
            self.window.height - 221,
            (30, 40, 60),
            24,
            anchor_x="center",
            anchor_y="center"
        )
        self.subtitle_text.draw()

        for i, item in enumerate(self.menu_items):
            y = self.window.height // 2 - i * 60

            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        self.window.width // 2, y, 350, 50
                    ),
                    UI_BUTTON_SELECTED
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(
                        self.window.width // 2, y, 350, 50
                    ),
                    (255, 220, 100), 3
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            self.menu_texts[i].color = color
            self.menu_texts[i].bold = (i == self.selected)

            arcade.draw_text(
                item,
                self.window.width // 2 + 1,
                y - 1,
                TEXT_SHADOW,
                32,
                anchor_x="center",
                anchor_y="center",
                bold=(i == self.selected)
            )
            self.menu_texts[i].draw()

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Выход • F11: Полный экран",
            self.window.width // 2 + 1, 49,
            TEXT_SHADOW,
            18,
            anchor_x="center",
            anchor_y="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.menu_items)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.menu_items)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.select_item()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

    def select_item(self):
        self.window.sound_manager.play_sound("click", volume=0.3)

        if self.selected == 0:
            self.window.show_view(DifficultyView(self.window))
        elif self.selected == 1:
            saved = self.window.save_manager.load_game()
            if saved:
                game_view = GameView(self.window)
                game_view.load_save(saved)
                self.window.show_view(game_view)
            else:
                self.window.show_view(DifficultyView(self.window))
        elif self.selected == 2:
            self.window.show_view(HighScoresView(self.window))
        elif self.selected == 3:
            self.window.show_view(SettingsView(self.window))
        elif self.selected == 4:
            arcade.close_window()

    def on_mouse_motion(self, x, y, dx, dy):
        for i in range(len(self.menu_items)):
            item_y = self.window.height // 2 - i * 60
            if abs(x - self.window.width // 2) < 175 and abs(y - item_y) < 25:
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.menu_items)):
                item_y = self.window.height // 2 - i * 60
                if abs(x - self.window.width // 2) < 175 and abs(y - item_y) < 25:
                    self.selected = i
                    self.select_item()
                    break

class DifficultyView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.selected = 0
        self.difficulties = ["ЛЁГКИЙ", "СРЕДНИЙ", "СЛОЖНЫЙ"]
        self.difficulty_descriptions = [
            "Больше жизней и денег,\nвраги слабее",
            "Стандартные настройки",
            "Меньше жизней и денег,\nвраги сильнее"
        ]
        self.title_text = None
        self.difficulty_texts = []
        self.desc_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

        self.title_text = arcade.Text(
            "ВЫБЕРИТЕ СЛОЖНОСТЬ",
            self.window.width // 2, self.window.height - 150,
            (100, 200, 255), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.difficulty_texts = []
        self.desc_texts = []
        for i, diff in enumerate(self.difficulties):
            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            text = arcade.Text(
                diff,
                self.window.width // 2, self.window.height // 2 - i * 120,
                color, 36,
                anchor_x="center", anchor_y="center"
            )
            self.difficulty_texts.append(text)

            desc_color = (180, 190, 210) if i == self.selected else (150, 160, 180)
            desc_text = arcade.Text(
                self.difficulty_descriptions[i],
                self.window.width // 2, self.window.height // 2 - i * 120 - 50,
                desc_color, 20,
                anchor_x="center", anchor_y="center",
                align="center"
            )
            self.desc_texts.append(desc_text)

        self.control_text = arcade.Text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 20,
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ СЛОЖНОСТЬ",
            self.window.width // 2 + 2, self.window.height - 152,
            TEXT_SHADOW, 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        self.title_text.draw()

        for i, text in enumerate(self.difficulty_texts):
            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 120,
                        400, 80
                    ),
                    UI_BUTTON_SELECTED
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 120,
                        400, 80
                    ),
                    (255, 220, 100), 3
                )

            arcade.draw_text(
                text.text,
                text.x + 1, text.y - 1,
                TEXT_SHADOW, text.font_size,
                anchor_x="center", anchor_y="center"
            )
            text.draw()

            arcade.draw_text(
                self.desc_texts[i].text,
                self.desc_texts[i].x + 1, self.desc_texts[i].y - 1,
                TEXT_SHADOW, self.desc_texts[i].font_size,
                anchor_x="center", anchor_y="center",
                align="center"
            )
            self.desc_texts[i].draw()

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2 + 1, 99,
            TEXT_SHADOW, 20,
            anchor_x="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.difficulties)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.difficulties)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.window.sound_manager.play_sound("click", volume=0.3)
            difficulty_map = {
                0: Difficulty.EASY,
                1: Difficulty.NORMAL,
                2: Difficulty.HARD
            }
            difficulty = difficulty_map[self.selected]
            self.window.show_view(MapSelectionView(self.window, difficulty))
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.window))
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_mouse_motion(self, x, y, dx, dy):
        for i in range(len(self.difficulties)):
            item_y = self.window.height // 2 - i * 120
            if abs(x - self.window.width // 2) < 200 and abs(y - item_y) < 40:
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.difficulties)):
                item_y = self.window.height // 2 - i * 120
                if abs(x - self.window.width // 2) < 200 and abs(y - item_y) < 40:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.3)
                    difficulty_map = {
                        0: Difficulty.EASY,
                        1: Difficulty.NORMAL,
                        2: Difficulty.HARD
                    }
                    difficulty = difficulty_map[self.selected]
                    self.window.show_view(MapSelectionView(self.window, difficulty))
                    break

class MapSelectionView(arcade.View):
    def __init__(self, window, difficulty):
        super().__init__()
        self.window = window
        self.difficulty = difficulty
        self.selected = 0
        self.maps = ["КАРТА 1 (Простая)", "КАРТА 2 (Средняя)", "КАРТА 3 (Сложная)"]
        self.map_descriptions = [
            "Одна дорога, простая защита",
            "Несколько поворотов, сложнее",
            "Два старта, развилки, очень сложно!"
        ]
        self.title_text = None
        self.map_texts = []
        self.desc_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

        self.title_text = arcade.Text(
            "ВЫБЕРИТЕ КАРТУ",
            self.window.width // 2, self.window.height - 150,
            (100, 200, 255), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.map_texts = []
        self.desc_texts = []
        for i, map_name in enumerate(self.maps):
            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            text = arcade.Text(
                map_name,
                self.window.width // 2, self.window.height // 2 - i * 120,
                color, 36,
                anchor_x="center", anchor_y="center"
            )
            self.map_texts.append(text)

            desc_color = (180, 190, 210) if i == self.selected else (150, 160, 180)
            desc_text = arcade.Text(
                self.map_descriptions[i],
                self.window.width // 2, self.window.height // 2 - i * 120 - 50,
                desc_color, 20,
                anchor_x="center", anchor_y="center",
                align="center"
            )
            self.desc_texts.append(desc_text)

        self.control_text = arcade.Text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 20,
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ КАРТУ",
            self.window.width // 2 + 2, self.window.height - 152,
            TEXT_SHADOW, 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        self.title_text.draw()

        for i, text in enumerate(self.map_texts):
            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 120,
                        450, 80
                    ),
                    UI_BUTTON_SELECTED
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 120,
                        450, 80
                    ),
                    (255, 220, 100), 3
                )

            arcade.draw_text(
                text.text,
                text.x + 1, text.y - 1,
                TEXT_SHADOW, text.font_size,
                anchor_x="center", anchor_y="center"
            )
            text.draw()

            arcade.draw_text(
                self.desc_texts[i].text,
                self.desc_texts[i].x + 1, self.desc_texts[i].y - 1,
                TEXT_SHADOW, self.desc_texts[i].font_size,
                anchor_x="center", anchor_y="center",
                align="center"
            )
            self.desc_texts[i].draw()

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2 + 1, 99,
            TEXT_SHADOW, 20,
            anchor_x="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.maps)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.maps)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.window.sound_manager.play_sound("click", volume=0.3)
            map_map = {
                0: MapType.MAP1,
                1: MapType.MAP2,
                2: MapType.MAP3
            }
            selected_map = map_map[self.selected]
            game_view = GameView(self.window, self.difficulty, selected_map)
            game_view.setup()
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            self.window.show_view(DifficultyView(self.window))
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

    def on_mouse_motion(self, x, y, dx, dy):
        for i in range(len(self.maps)):
            item_y = self.window.height // 2 - i * 120
            if abs(x - self.window.width // 2) < 225 and abs(y - item_y) < 40:
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.maps)):
                item_y = self.window.height // 2 - i * 120
                if abs(x - self.window.width // 2) < 225 and abs(y - item_y) < 40:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.3)
                    map_map = {
                        0: MapType.MAP1,
                        1: MapType.MAP2,
                        2: MapType.MAP3
                    }
                    selected_map = map_map[self.selected]
                    game_view = GameView(self.window, self.difficulty, selected_map)
                    game_view.setup()
                    self.window.show_view(game_view)
                    break

class GameView(arcade.View):
    def __init__(self, window, difficulty=Difficulty.NORMAL, map_type=MapType.MAP1):
        super().__init__()
        self.window = window
        self.difficulty = difficulty
        self.map_type = map_type

        # Игровые списки
        self.enemy_list = arcade.SpriteList()
        self.tower_list = []  # Теперь не SpriteList, чтобы использовать кастомную отрисовку
        self.projectile_list = arcade.SpriteList()
        self.tower_spots = []

        # Статистика в зависимости от сложности
        if difficulty == Difficulty.EASY:
            self.money = STARTING_MONEY_EASY
            self.lives = STARTING_LIVES_EASY
        elif difficulty == Difficulty.NORMAL:
            self.money = STARTING_MONEY_NORMAL
            self.lives = STARTING_LIVES_NORMAL
        else:  # HARD
            self.money = STARTING_MONEY_HARD
            self.lives = STARTING_LIVES_HARD

        self.score = 0
        self.wave = 0
        self.wave_timer = 0
        self.selected_tower_type = TowerType.ARCHER
        self.wave_active = False
        self.enemies_spawned = 0
        self.total_enemies = 0

        # Системы
        self.particle_system = ParticleSystem()
        self.path_points = []
        self.path_points2 = []  # Второй путь для карты 3
        self.start_pos = None
        self.end_pos = None

        # Интерфейс
        self.showing_range = None
        self.selected_tower = None
        self.game_over = False
        self.victory = False

        # Волны с боссами (15 волн)
        self.waves = self.generate_waves()

        # Анимация
        self.base_pulse = 0
        self.base_pulse_dir = 1

        # Текст для интерфейса
        self.money_text = None
        self.lives_text = None
        self.score_text = None
        self.wave_text = None
        self.difficulty_text = None
        self.tower_texts = []
        self.instruction_text = None
        self.wave_ready_text = None
        self.wave_start_text = None
        self.game_over_text = None
        self.victory_text = None

        # Для кнопок башен
        self.tower_buttons = []  # Список кнопок: (rect, tower_type)

        # Смещение для центрирования карты
        self.map_offset_x = 0
        self.map_offset_y = 0

    def generate_waves(self):
        """Генерация 15 сложных волн в зависимости от сложности"""
        base_waves = [
            # Волна 1-5: обычные враги
            {"slime": 12, "orc": 0, "goblin": 0, "skeleton": 0, "knight": 0, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 0},
            {"slime": 15, "orc": 5, "goblin": 8, "skeleton": 0, "knight": 0, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 0},
            {"slime": 20, "orc": 8, "goblin": 12, "skeleton": 5, "knight": 0, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 0},
            {"slime": 25, "orc": 12, "goblin": 15, "skeleton": 8, "knight": 3, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 0},
            {"slime": 20, "orc": 15, "goblin": 20, "skeleton": 12, "knight": 8, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 0},

            # Волна 6-8: появляются боссы
            {"slime": 25, "orc": 20, "goblin": 25, "skeleton": 15, "knight": 12, "boss_dragon": 1, "boss_giant": 0, "boss_wizard": 0},
            {"slime": 30, "orc": 25, "goblin": 30, "skeleton": 20, "knight": 15, "boss_dragon": 0, "boss_giant": 1, "boss_wizard": 0},
            {"slime": 35, "orc": 30, "goblin": 35, "skeleton": 25, "knight": 18, "boss_dragon": 0, "boss_giant": 0, "boss_wizard": 1},

            # Волна 9-12: сложные волны с несколькими боссами
            {"slime": 40, "orc": 35, "goblin": 40, "skeleton": 30, "knight": 22, "boss_dragon": 1, "boss_giant": 1, "boss_wizard": 0},
            {"slime": 45, "orc": 40, "goblin": 45, "skeleton": 35, "knight": 25, "boss_dragon": 1, "boss_giant": 0, "boss_wizard": 1},
            {"slime": 50, "orc": 45, "goblin": 50, "skeleton": 40, "knight": 28, "boss_dragon": 0, "boss_giant": 1, "boss_wizard": 1},
            {"slime": 55, "orc": 50, "goblin": 55, "skeleton": 45, "knight": 30, "boss_dragon": 1, "boss_giant": 1, "boss_wizard": 0},

            # Волна 13-15: экстремальные волны
            {"slime": 60, "orc": 55, "goblin": 60, "skeleton": 50, "knight": 35, "boss_dragon": 2, "boss_giant": 0, "boss_wizard": 1},
            {"slime": 65, "orc": 60, "goblin": 65, "skeleton": 55, "knight": 38, "boss_dragon": 1, "boss_giant": 2, "boss_wizard": 1},
            {"slime": 70, "orc": 65, "goblin": 70, "skeleton": 60, "knight": 40, "boss_dragon": 2, "boss_giant": 2, "boss_wizard": 2},
        ]

        # Модификаторы для сложности
        if self.difficulty == Difficulty.EASY:
            for wave in base_waves:
                for key in wave:
                    if key.startswith("boss"):
                        wave[key] = max(0, wave[key] - 1)  # Меньше боссов
                    elif wave[key] > 0:
                        wave[key] = int(wave[key] * 0.9)  # Меньше обычных врагов
        elif self.difficulty == Difficulty.HARD:
            for wave in base_waves:
                for key in wave:
                    if wave[key] > 0:
                        wave[key] = int(wave[key] * 1.5)  # Больше врагов

        return base_waves

    def setup(self):
        """Настройка игры"""
        self.load_map()
        self.window.sound_manager.play_music("game")

        # Создаем текст для интерфейса
        self.create_ui_text()

        # Создаем кнопки для башен
        self.create_tower_buttons()

    def create_tower_buttons(self):
        """Создание кнопок для выбора башен (вертикально справа)"""
        self.tower_buttons = []
        tower_data = [
            (TowerType.ARCHER, "Лучник", "120💰", ARCHER_COLOR, "triangle"),
            (TowerType.CANNON, "Пушка", "250💰", CANNON_COLOR, "square"),
            (TowerType.MAGE, "Маг", "180💰", MAGE_COLOR, "circle")
        ]

        button_width = 180
        button_height = 80
        start_x = self.window.width - TOWER_BUTTONS_WIDTH + 20  # Отступ от правого края
        start_y = self.window.height - UI_HEIGHT - 150  # Чуть ниже UI

        for i, (tower_type, name, cost, color, shape) in enumerate(tower_data):
            button_y = start_y - i * (button_height + 20)  # Вертикальное расположение
            button_rect = arcade.rect.XYWH(start_x, button_y, button_width, button_height)
            self.tower_buttons.append((button_rect, tower_type, name, cost, color, shape))

    def create_ui_text(self):
        """Создание текстовых объектов для интерфейса"""
        # Основная статистика
        diff_text = "Лёгкий" if self.difficulty == Difficulty.EASY else "Средний" if self.difficulty == Difficulty.NORMAL else "Сложный"
        diff_color = (100, 255, 100) if self.difficulty == Difficulty.EASY else (255, 255, 100) if self.difficulty == Difficulty.NORMAL else (255, 100, 100)

        map_text = "Карта 1" if self.map_type == MapType.MAP1 else "Карта 2" if self.map_type == MapType.MAP2 else "Карта 3"

        self.difficulty_text = arcade.Text(
            f"Сложность: {diff_text} | {map_text}",
            self.window.width - 200, self.window.height - 50,
            diff_color, 20,
            anchor_x="center",
            bold=True
        )

        self.money_text = arcade.Text(
            f"💰: {self.money}",
            100, self.window.height - 50,
            (255, 215, 0), 28,
            anchor_x="center",
            bold=True
        )

        self.lives_text = arcade.Text(
            f"❤️: {self.lives}",
            300, self.window.height - 50,
            (255, 100, 100), 28,
            anchor_x="center",
            bold=True
        )

        self.score_text = arcade.Text(
            f"Очки: {self.score}",
            500, self.window.height - 50,
            TEXT_COLOR, 28,
            anchor_x="center",
            bold=True
        )

        self.wave_text = arcade.Text(
            f"Волна: {self.wave + 1}/{len(self.waves)}",
            700, self.window.height - 50,
            TEXT_COLOR, 28,
            anchor_x="center",
            bold=True
        )

        # Инструкция
        self.instruction_text = arcade.Text(
            "Выберите башню справа и кликните на клетку для постройки • Пробел: следующая волна • ESC: пауза • F11: Полный экран",
            self.window.width // 2, 40,
            (180, 190, 210), 18,
            anchor_x="center",
            bold=True
        )

        # Сообщения
        self.wave_ready_text = arcade.Text(
            f"Волна {self.wave + 1} готова!",
            self.window.width // 2, self.window.height // 2,
            (255, 220, 100), 36,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.wave_start_text = arcade.Text(
            "Нажмите ПРОБЕЛ для начала волны",
            self.window.width // 2, self.window.height // 2 - 50,
            TEXT_COLOR, 24,
            anchor_x="center", anchor_y="center"
        )

        self.game_over_text = arcade.Text(
            "ИГРА ОКОНЧЕНА!",
            self.window.width // 2, self.window.height // 2,
            (255, 100, 100), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.victory_text = arcade.Text(
            "ПОБЕДА!",
            self.window.width // 2, self.window.height // 2,
            (100, 255, 100), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

    def load_map(self):
        """Загрузка карты в зависимости от выбранного типа"""
        if self.map_type == MapType.MAP1:
            level_map = [
                "T T T T T T T T T T T T T T T T T T T T",
                "T T T T T T T T T T T T T T T T T T T T",
                "T # # # # # # # # # # # # # # # # # # E",
                "T # T T T T T T T T T T T T T T T T T T",
                "T # T T T T T T T T T T T T T T T T T T",
                "T # T T T T T T T T T T T T T T T T T T",
                "T # # # # T T T T # # # # # T T T T T T",
                "T T T T # T T T T # T T T # T T T T T T",
                "T T T T # T T T T # T T T # T T T T T T",
                "T T T T # T T T T # T T T # T T T T T T",
                "T T T T # # # # # # T T T # # # # # # T",
                "T T T T T T T T T T T T T T T T T T # T",
                "T # # # # # # # # # # # # # # # # # # T",
                "T # T T T T T T T T T T T T T T T T T T",
                "T # # # # # # # # # # # # # # # # # # S",
            ]
        elif self.map_type == MapType.MAP2:
            level_map = [
                "T T T E T T T T T T T T T T T T T T T T",
                "T T T # # # # # # # # # # # # # # # T T",
                "T T T T T T T T T T T T T T T T T # T T",
                "T T T T T T T T T T T T T T T T T # T T",
                "T T T T T T T T T T T T T T T T T # T T",
                "T T T T T T T T T T T T T T T T T # T T",
                "T T T T T T T T T T T T # # # # # # T T",
                "T T T T T T # # # # # # # T T T T T T T",
                "T T T T T T # T T T T T T T T T T T T T",
                "T T # # # # # T T T T T T T T T T T T T",
                "T T # T T T T T T T T T T T T T T T T T",
                "T T # T T T # # # # # # # # # # # T T T",
                "T T # T T T # T T T T T T T T T # # T T",
                "T T # # # # # T T T T T T T T T T # T T",
                "T T T T T T T T T T T T T T T T T # # S"
            ]
        else:  # MAP3
            level_map = [
                "T T T E T T T T T T T T T T T T T T T T",
                "T T T # # # # # # # # # # # # # # # T T",
                "T T T # T T T T T T T T T T T T T # T T",
                "T T T # T T T T T T T T T T T T T # T T",
                "T T T # # # # # # # # # # T T T T # T T",
                "T T T T T T T T T T T T # T T T T # T T",
                "T T T T T T T T T T T T # # # # # # T T",
                "T T T T T T # # # # # # # T T T T T T T",
                "T T T T T T # T # T T T T T T T T T T T",
                "T T # # # # # T # T T T T T T T T T T T",
                "T T # T T T T T # T T T T T T T T T T T",
                "T T # T T T T T # # # # # # # # # T T T",
                "T T # T T T T T T T T T T T T T # # T T",
                "T T # T T T T T T T T T T T T T T # T T",
                "T T S T T T T T T T T T T T T T T # # S"
            ]

        rows = len(level_map)
        cols = len(level_map[0].split())

        # Рассчитываем размеры карты
        map_width = cols * TILE_SIZE
        map_height = rows * TILE_SIZE

        # Рассчитываем доступное пространство для карты (левая часть экрана)
        available_width = self.window.width - TOWER_BUTTONS_WIDTH
        available_height = self.window.height - UI_HEIGHT

        # Вычисляем смещения для центрирования карты
        self.map_offset_x = (available_width - map_width) // 2
        self.map_offset_y = (available_height - map_height) // 2

        # Сначала находим все точки пути и их координаты
        path_cells = []
        self.tower_spots = []

        # Список для всех стартов
        start_positions = []

        for y in range(rows):
            row = level_map[y].split()
            for x in range(cols):
                cell = row[x]
                pos_x = x * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_x
                pos_y = y * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_y

                if cell == 'S':
                    start_positions.append((pos_x, pos_y))
                    path_cells.append((x, y, 'S', pos_x, pos_y))
                elif cell == 'E':
                    self.end_pos = (pos_x, pos_y)
                    path_cells.append((x, y, 'E', pos_x, pos_y))
                elif cell == '#':
                    path_cells.append((x, y, '#', pos_x, pos_y))
                elif cell == 'T':
                    # Учитываем правую панель с кнопками
                    if pos_x < self.window.width - TOWER_BUTTONS_WIDTH:
                        self.tower_spots.append((pos_x, pos_y))

        # Устанавливаем стартовые позиции
        if start_positions:
            self.start_pos = start_positions[0]
            if len(start_positions) > 1:
                # Для карты 3 используем второй старт
                pass  # Оставляем для будущего использования

        # Создаем пути с использованием оригинального алгоритма поиска ближайших соседей
        if self.start_pos and self.end_pos:
            # Создаем словарь для быстрого доступа к точкам по координатам
            points_dict = {(x, y): (pos_x, pos_y) for x, y, cell_type, pos_x, pos_y in path_cells}

            # Для карты 3 создаем два пути
            if self.map_type == MapType.MAP3:
                self.create_paths_for_map3(points_dict, path_cells)
            else:
                # Для карт 1 и 2 создаем один путь
                self.create_single_path(points_dict, path_cells)

        # Если пути не созданы, создаем простые пути
        if not self.path_points:
            if self.start_pos and self.end_pos:
                self.path_points = [self.start_pos, self.end_pos]
            else:
                # Запасные позиции
                if not self.start_pos:
                    self.start_pos = (TILE_SIZE * 2 + self.map_offset_x, TILE_SIZE * 13 + self.map_offset_y)
                if not self.end_pos:
                    self.end_pos = (TILE_SIZE * 19 + self.map_offset_x, TILE_SIZE * 2 + self.map_offset_y)
                self.path_points = [self.start_pos, self.end_pos]

    def create_single_path(self, points_dict, path_cells):
        """Создание одного пути для карт 1 и 2"""
        # Находим старт и финиш
        start_cell = next(((x, y) for x, y, cell_type, _, _ in path_cells if cell_type == 'S'), None)
        end_cell = next(((x, y) for x, y, cell_type, _, _ in path_cells if cell_type == 'E'), None)

        if start_cell and end_cell:
            current = start_cell
            self.path_points = [points_dict[current]]
            visited = {current}

            # Направления: вправо, влево, вниз, вверх
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

            while current != end_cell:
                found_next = False

                # Ищем соседнюю клетку пути
                for dx, dy in directions:
                    next_x = current[0] + dx
                    next_y = current[1] + dy
                    next_point = (next_x, next_y)

                    if next_point in points_dict and next_point not in visited:
                        current = next_point
                        self.path_points.append(points_dict[current])
                        visited.add(current)
                        found_next = True
                        break

                if not found_next:
                    # Если не нашли путь, просто соединяем старт и финиш
                    self.path_points = [self.start_pos, self.end_pos]
                    break

    def create_paths_for_map3(self, points_dict, path_cells):
        """Создание путей для карты 3 (с двумя стартами)"""
        # Находим все старты и финиши
        start_cells = [(x, y) for x, y, cell_type, _, _ in path_cells if cell_type == 'S']
        end_cell = next(((x, y) for x, y, cell_type, _, _ in path_cells if cell_type == 'E'), None)

        if start_cells and end_cell:
            # Создаем путь от первого старта
            if len(start_cells) >= 1:
                current = start_cells[0]
                self.path_points = [points_dict[current]]
                visited = {current}

                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

                while current != end_cell:
                    found_next = False

                    for dx, dy in directions:
                        next_x = current[0] + dx
                        next_y = current[1] + dy
                        next_point = (next_x, next_y)

                        if next_point in points_dict and next_point not in visited:
                            current = next_point
                            self.path_points.append(points_dict[current])
                            visited.add(current)
                            found_next = True
                            break

                    if not found_next:
                        break

            # Создаем путь от второго старта (если есть)
            if len(start_cells) >= 2:
                current = start_cells[1]
                self.path_points2 = [points_dict[current]]
                visited = {current}

                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

                while current != end_cell:
                    found_next = False

                    for dx, dy in directions:
                        next_x = current[0] + dx
                        next_y = current[1] + dy
                        next_point = (next_x, next_y)

                        if next_point in points_dict and next_point not in visited:
                            current = next_point
                            self.path_points2.append(points_dict[current])
                            visited.add(current)
                            found_next = True
                            break

                    if not found_next:
                        break

    def on_draw(self):
        self.clear()

        # Фон игрового поля (левая часть)
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width - TOWER_BUTTONS_WIDTH, 0, self.window.height - UI_HEIGHT,
            (60, 70, 90)
        )

        # Правая панель для кнопок башен
        arcade.draw_lrbt_rectangle_filled(
            self.window.width - TOWER_BUTTONS_WIDTH, self.window.width, 0, self.window.height - UI_HEIGHT,
            (45, 55, 75)
        )

        # Разделительная линия
        arcade.draw_line(
            self.window.width - TOWER_BUTTONS_WIDTH, 0,
            self.window.width - TOWER_BUTTONS_WIDTH, self.window.height - UI_HEIGHT,
            (80, 90, 110), 3
        )

        # Рисуем сетку только на игровом поле с учетом смещения
        grid_start_x = self.map_offset_x
        grid_start_y = self.map_offset_y
        grid_width = 20 * TILE_SIZE
        grid_height = 15 * TILE_SIZE

        for x in range(0, grid_width + TILE_SIZE, TILE_SIZE):
            arcade.draw_line(
                grid_start_x + x, grid_start_y,
                grid_start_x + x, grid_start_y + grid_height,
                (40, 45, 55), 1
            )
        for y in range(0, grid_height + TILE_SIZE, TILE_SIZE):
            arcade.draw_line(
                grid_start_x, grid_start_y + y,
                grid_start_x + grid_width, grid_start_y + y,
                (40, 45, 55), 1
            )

        # Рисуем путь (пути)
        if len(self.path_points) > 1:
            for i in range(len(self.path_points) - 1):
                x1, y1 = self.path_points[i]
                x2, y2 = self.path_points[i + 1]
                arcade.draw_line(x1, y1, x2, y2, (80, 90, 110), TILE_SIZE - 10)

        # Рисуем второй путь для карты 3
        if self.map_type == MapType.MAP3 and len(self.path_points2) > 1:
            for i in range(len(self.path_points2) - 1):
                x1, y1 = self.path_points2[i]
                x2, y2 = self.path_points2[i + 1]
                arcade.draw_line(x1, y1, x2, y2, (90, 100, 120), TILE_SIZE - 10)

        # Рисуем старт и финиш
        if self.start_pos:
            start_x, start_y = self.start_pos
            arcade.draw_circle_filled(start_x, start_y, TILE_SIZE // 2, (100, 200, 100))
            start_text = arcade.Text(
                "СТАРТ", start_x, start_y, (240, 240, 240), 12,
                anchor_x="center", anchor_y="center"
            )
            start_text.draw()

        # Анимированная база
        if self.end_pos:
            end_x, end_y = self.end_pos
            self.base_pulse += self.base_pulse_dir * 0.1
            if self.base_pulse > 1.0 or self.base_pulse < 0.5:
                self.base_pulse_dir *= -1

            pulse_size = TILE_SIZE // 2 * (0.8 + 0.2 * self.base_pulse)
            arcade.draw_circle_filled(end_x, end_y, pulse_size, (200, 100, 100))
            base_text = arcade.Text(
                "БАЗА", end_x, end_y, (240, 240, 240), 12,
                anchor_x="center", anchor_y="center"
            )
            base_text.draw()

        # Рисуем места для башен
        for spot in self.tower_spots:
            sx, sy = spot
            arcade.draw_rect_outline(
                arcade.rect.XYWH(sx, sy, TILE_SIZE - 10, TILE_SIZE - 10),
                (100, 120, 150), 2
            )

        # Рисуем игровые объекты
        self.projectile_list.draw()
        self.enemy_list.draw()

        # Рисуем башни (кастомная отрисовка)
        for tower in self.tower_list:
            tower.draw()

        self.particle_system.draw()

        # Рисуем полоски здоровья врагов
        for enemy in self.enemy_list:
            enemy.draw_health_bar()

        # Радиус выбранной башни
        if self.showing_range:
            self.showing_range.draw_range()

        # Панель интерфейса
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, self.window.height - UI_HEIGHT, self.window.height,
            UI_BACKGROUND
        )

        # Верхняя граница UI
        arcade.draw_line(
            0, self.window.height - UI_HEIGHT,
            self.window.width, self.window.height - UI_HEIGHT,
            (80, 100, 150), 3
        )

        # Обновляем и рисуем статистику
        diff_text = "Лёгкий" if self.difficulty == Difficulty.EASY else "Средний" if self.difficulty == Difficulty.NORMAL else "Сложный"
        diff_color = (100, 255, 100) if self.difficulty == Difficulty.EASY else (255, 255, 100) if self.difficulty == Difficulty.NORMAL else (255, 100, 100)

        map_text = "Карта 1" if self.map_type == MapType.MAP1 else "Карта 2" if self.map_type == MapType.MAP2 else "Карта 3"
        self.difficulty_text.text = f"Сложность: {diff_text} | {map_text}"
        self.difficulty_text.color = diff_color

        self.money_text.text = f"💰: {self.money}"
        self.lives_text.text = f"❤️: {self.lives}"
        self.score_text.text = f"Очки: {self.score}"
        self.wave_text.text = f"Волна: {self.wave + 1}/{len(self.waves)}"

        # Тени текста статистики
        arcade.draw_text(
            f"💰: {self.money}", 101, self.window.height - 51, TEXT_SHADOW, 28,
            anchor_x="center", bold=True
        )
        arcade.draw_text(
            f"❤️: {self.lives}", 301, self.window.height - 51, TEXT_SHADOW, 28,
            anchor_x="center", bold=True
        )
        arcade.draw_text(
            f"Очки: {self.score}", 501, self.window.height - 51, TEXT_SHADOW, 28,
            anchor_x="center", bold=True
        )
        arcade.draw_text(
            f"Волна: {self.wave + 1}/{len(self.waves)}", 701, self.window.height - 51, TEXT_SHADOW, 28,
            anchor_x="center", bold=True
        )
        arcade.draw_text(
            f"Сложность: {diff_text} | {map_text}", self.window.width - 199, self.window.height - 51, TEXT_SHADOW, 20,
            anchor_x="center", bold=True
        )

        self.difficulty_text.draw()
        self.money_text.draw()
        self.lives_text.draw()
        self.score_text.draw()
        self.wave_text.draw()

        # Рисуем кнопки выбора башен (вертикально справа)
        for button_rect, tower_type, name, cost, color, shape in self.tower_buttons:
            # Определяем цвет кнопки
            if tower_type == self.selected_tower_type:
                button_color = UI_BUTTON_SELECTED
                border_color = (255, 220, 100)
            else:
                button_color = UI_BUTTON_NORMAL
                border_color = (100, 120, 150)

            # Рисуем кнопку
            arcade.draw_rect_filled(button_rect, button_color)
            arcade.draw_rect_outline(button_rect, border_color, 3)

            # Добавляем небольшую тень
            shadow_rect = arcade.rect.XYWH(
                button_rect.x, button_rect.y - 2,
                button_rect.width, button_rect.height
            )
            arcade.draw_rect_filled(shadow_rect, (0, 0, 0, 50))

            # Рисуем иконку башни (разные формы)
            icon_x = button_rect.x - button_rect.width / 2 + 35
            icon_y = button_rect.y

            if shape == "triangle":
                # Треугольник
                points = [
                    (icon_x, icon_y + 18),  # Верхняя точка
                    (icon_x - 15, icon_y - 12),  # Левая нижняя
                    (icon_x + 15, icon_y - 12)   # Правая нижняя
                ]
                arcade.draw_polygon_filled(points, color)
                arcade.draw_polygon_outline(points, (255, 255, 255), 2)
            elif shape == "square":
                # Квадрат
                half_size = 15
                points = [
                    (icon_x - half_size, icon_y - half_size),  # Левый нижний
                    (icon_x + half_size, icon_y - half_size),  # Правый нижний
                    (icon_x + half_size, icon_y + half_size),  # Правый верхний
                    (icon_x - half_size, icon_y + half_size)   # Левый верхний
                ]
                arcade.draw_polygon_filled(points, color)
                arcade.draw_polygon_outline(points, (255, 255, 255), 2)
            else:  # circle
                # Круг
                arcade.draw_circle_filled(icon_x, icon_y, 18, color)
                arcade.draw_circle_outline(icon_x, icon_y, 18, (255, 255, 255), 2)

            # Рисуем название башни
            arcade.draw_text(
                name,
                button_rect.x - button_rect.width / 2 + 75,
                button_rect.y + 15,
                TEXT_COLOR, 20,
                anchor_x="left", anchor_y="center",
                bold=(tower_type == self.selected_tower_type)
            )

            # Рисуем стоимость
            arcade.draw_text(
                cost,
                button_rect.x - button_rect.width / 2 + 75,
                button_rect.y - 15,
                (255, 215, 0), 18,
                anchor_x="left", anchor_y="center"
            )

        # Сообщения
        if self.game_over:
            arcade.draw_text(
                "ИГРА ОКОНЧЕНА!",
                self.window.width // 2 + 2, self.window.height // 2 - 2,
                TEXT_SHADOW, 48,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            self.game_over_text.draw()

            game_over_subtext = arcade.Text(
                "Нажмите ESC для выхода в меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )
            game_over_subtext.draw()

        elif self.victory:
            arcade.draw_text(
                "ПОБЕДА!",
                self.window.width // 2 + 2, self.window.height // 2 - 2,
                TEXT_SHADOW, 48,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            self.victory_text.draw()

            victory_subtext = arcade.Text(
                "Нажмите ESC для выхода в меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )
            victory_subtext.draw()

        elif not self.wave_active and self.wave < len(self.waves):
            self.wave_ready_text.text = f"Волна {self.wave + 1} готова!"

            arcade.draw_text(
                f"Волна {self.wave + 1} готова!",
                self.window.width // 2 + 1, self.window.height // 2 - 1,
                TEXT_SHADOW, 36,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            self.wave_ready_text.draw()

            arcade.draw_text(
                "Нажмите ПРОБЕЛ для начала волны",
                self.window.width // 2 + 1, self.window.height // 2 - 51,
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center"
            )
            self.wave_start_text.draw()

        # Инструкция
        arcade.draw_text(
            "Выберите башню справа и кликните на клетку для постройки • Пробел: следующая волна • ESC: пауза • F11: Полный экран",
            self.window.width // 2 + 1, 39,
            TEXT_SHADOW, 18,
            anchor_x="center"
        )
        self.instruction_text.draw()

    def on_update(self, delta_time):
        if self.game_over or self.victory:
            return

        # Обновление врагов
        for enemy in self.enemy_list:
            enemy.update()
            if enemy.has_reached_end():
                self.lives -= BASE_DAMAGE
                self.enemy_list.remove(enemy)
                self.window.sound_manager.play_sound("lose_life", volume=0.3)
                if self.lives <= 0:
                    self.game_over = True

        # Обновление башен
        for tower in self.tower_list:
            tower.update(
                delta_time,
                self.enemy_list,
                self.projectile_list,
                self.window.sound_manager,
                self.particle_system
            )

        # Обновление снарядов и проверка столкновений
        for projectile in self.projectile_list[:]:
            projectile.update()

            if projectile.target and not projectile.target.alive:
                closest = None
                closest_distance = float('inf')
                for enemy in self.enemy_list:
                    if enemy.alive:
                        distance = math.sqrt(
                            (projectile.center_x - enemy.center_x)**2 +
                            (projectile.center_y - enemy.center_y)**2
                        )
                        if distance < closest_distance:
                            closest = enemy
                            closest_distance = distance

                if closest:
                    projectile.target = closest
                    projectile.update_movement()

            # Проверка столкновений
            hit_list = arcade.check_for_collision_with_list(projectile, self.enemy_list)
            if hit_list:
                for enemy in hit_list:
                    if enemy.alive and enemy.take_damage(projectile.damage):
                        # Враг убит
                        self.money += enemy.bounty
                        self.score += enemy.bounty * 10
                        self.enemy_list.remove(enemy)
                        self.particle_system.create_explosion(
                            enemy.center_x, enemy.center_y,
                            (255, 165, 0), 15
                        )
                        self.window.sound_manager.play_sound("enemy_die", volume=0.4)
                if projectile in self.projectile_list:
                    self.projectile_list.remove(projectile)

        # Обновление частиц
        self.particle_system.update(delta_time)

        # Проверка завершения волны
        if not self.enemy_list and self.enemies_spawned >= self.total_enemies and self.wave_active:
            self.wave_active = False
            self.wave_timer = 0
            self.enemies_spawned = 0
            self.total_enemies = 0

            # Проверка победы
            if self.wave >= len(self.waves):
                self.victory = True

        # Таймер между волнами
        if not self.wave_active and self.wave < len(self.waves):
            self.wave_timer += delta_time

    def start_wave(self):
        if self.wave < len(self.waves):
            self.wave_active = True
            wave_data = self.waves[self.wave]
            self.window.sound_manager.play_sound("wave_start", volume=0.5)

            # Подсчет общего количества врагов
            self.total_enemies = sum(wave_data.values())
            self.enemies_spawned = 0

            # Спавн врагов с задержкой
            enemy_types = []
            for enemy_type, count in wave_data.items():
                if enemy_type == "slime":
                    enemy_types.extend([EnemyType.SLIME] * count)
                elif enemy_type == "orc":
                    enemy_types.extend([EnemyType.ORC] * count)
                elif enemy_type == "goblin":
                    enemy_types.extend([EnemyType.GOBLIN] * count)
                elif enemy_type == "skeleton":
                    enemy_types.extend([EnemyType.SKELETON] * count)
                elif enemy_type == "knight":
                    enemy_types.extend([EnemyType.KNIGHT] * count)
                elif enemy_type == "boss_dragon":
                    enemy_types.extend([EnemyType.BOSS_DRAGON] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.5)
                elif enemy_type == "boss_giant":
                    enemy_types.extend([EnemyType.BOSS_GIANT] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.5)
                elif enemy_type == "boss_wizard":
                    enemy_types.extend([EnemyType.BOSS_WIZARD] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.5)

            random.shuffle(enemy_types)

            # Увеличенный интервал между врагами (1.2 секунды вместо 0.8)
            for i, enemy_type in enumerate(enemy_types):
                arcade.schedule(lambda dt, etype=enemy_type: self.spawn_enemy(etype), i * 1.2)

            self.wave += 1

    def spawn_enemy(self, enemy_type):
        if self.enemies_spawned < self.total_enemies:
            # Для карты 3 используем оба пути
            if self.map_type == MapType.MAP3 and self.path_points2:
                # Случайно выбираем путь для врага
                path = random.choice([self.path_points, self.path_points2])
                enemy = Enemy(enemy_type, path, self.wave, self.difficulty)
            else:
                enemy = Enemy(enemy_type, self.path_points, self.wave, self.difficulty)

            enemy.center_x, enemy.center_y = self.start_pos
            self.enemy_list.append(enemy)
            self.enemies_spawned += 1

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over or self.victory:
            return

        # Проверяем клик по кнопкам выбора башен (справа)
        for button_rect, tower_type, name, cost, color, shape in self.tower_buttons:
            if (button_rect.x - button_rect.width/2 <= x <= button_rect.x + button_rect.width/2 and
                button_rect.y - button_rect.height/2 <= y <= button_rect.y + button_rect.height/2):
                self.selected_tower_type = tower_type
                self.window.sound_manager.play_sound("click", volume=0.3)
                return

        # Игнорируем клики по интерфейсу и правой панели
        if y > self.window.height - UI_HEIGHT or x > self.window.width - TOWER_BUTTONS_WIDTH:
            return

        # Поиск места для башни
        for spot in self.tower_spots:
            sx, sy = spot
            if (abs(x - sx) < TILE_SIZE//2 and
                abs(y - sy) < TILE_SIZE//2):

                occupied = False
                for tower in self.tower_list:
                    if (abs(tower.center_x - sx) < 10 and
                        abs(tower.center_y - sy) < 10):
                        occupied = True
                        self.selected_tower = tower
                        break

                if not occupied:
                    # Строим башню
                    cost = 0
                    if self.selected_tower_type == TowerType.ARCHER:
                        cost = 120
                    elif self.selected_tower_type == TowerType.CANNON:
                        cost = 250
                    else:
                        cost = 180

                    if self.money >= cost:
                        tower = Tower(self.selected_tower_type, sx, sy)
                        self.tower_list.append(tower)
                        self.money -= cost
                        self.window.sound_manager.play_sound("build", volume=0.4)
                        self.selected_tower = tower
                else:
                    # Улучшаем существующую башню
                    if self.selected_tower.level < self.selected_tower.max_level:
                        upgrade_cost = self.selected_tower.cost // 2
                        if self.money >= upgrade_cost:
                            self.money -= upgrade_cost
                            self.selected_tower.upgrade()
                            self.window.sound_manager.play_sound("upgrade", volume=0.4)
                break

    def on_mouse_motion(self, x, y, dx, dy):
        # Проверяем наведение на кнопки башен
        for button_rect, tower_type, name, cost, color, shape in self.tower_buttons:
            if (button_rect.x - button_rect.width/2 <= x <= button_rect.x + button_rect.width/2 and
                button_rect.y - button_rect.height/2 <= y <= button_rect.y + button_rect.height/2):
                break

        if y > self.window.height - UI_HEIGHT or x > self.window.width - TOWER_BUTTONS_WIDTH:
            self.showing_range = None
            return

        self.showing_range = None
        for tower in self.tower_list:
            if (abs(x - tower.center_x) < 32 and
                abs(y - tower.center_y) < 32):
                self.showing_range = tower
                break

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.game_over or self.victory:
                # Сохраняем результат
                if self.victory:
                    map_name = "Карта 1" if self.map_type == MapType.MAP1 else "Карта 2" if self.map_type == MapType.MAP2 else "Карта 3"
                    self.window.save_manager.save_score("Игрок", self.score, 1, self.wave, self.difficulty.value, map_name)
                self.window.show_view(MenuView(self.window))
            else:
                self.window.show_view(PauseView(self.window, self))
        elif key == arcade.key.SPACE:
            if not self.wave_active and self.wave < len(self.waves):
                self.start_wave()
        elif key == arcade.key.S:
            self.save_game()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
            # Пересоздаем UI элементы для нового размера окна
            self.create_ui_text()
            self.create_tower_buttons()
            self.load_map()  # Перезагружаем карту с новыми смещениями

    def save_game(self):
        data = {
            "money": self.money,
            "lives": self.lives,
            "score": self.score,
            "wave": self.wave,
            "difficulty": self.difficulty.value,
            "map_type": self.map_type.value,
            "towers": [(t.tower_type.value, t.center_x, t.center_y, t.level)
                      for t in self.tower_list]
        }
        if self.window.save_manager.save_game(data):
            print("Игра сохранена!")

    def load_save(self, data):
        self.money = data.get("money", STARTING_MONEY_NORMAL)
        self.lives = data.get("lives", STARTING_LIVES_NORMAL)
        self.score = data.get("score", 0)
        self.wave = data.get("wave", 0)
        diff_value = data.get("difficulty", Difficulty.NORMAL.value)
        self.difficulty = Difficulty(diff_value)

        map_value = data.get("map_type", MapType.MAP1.value)
        self.map_type = MapType(map_value)

        # Восстанавливаем башни
        for t_data in data.get("towers", []):
            if len(t_data) == 4:
                t_type_str, x, y, level = t_data
                try:
                    tower = Tower(TowerType(t_type_str), x, y)
                    tower.level = level
                    # Устанавливаем параметры в зависимости от уровня
                    for _ in range(level - 1):
                        tower.upgrade()
                    self.tower_list.append(tower)
                except ValueError:
                    continue

        # Загружаем карту
        self.load_map()
        self.create_ui_text()
        self.create_tower_buttons()

class PauseView(arcade.View):
    def __init__(self, window, game_view):
        super().__init__()
        self.window = window
        self.game_view = game_view
        self.selected = 0
        self.options = ["ПРОДОЛЖИТЬ", "СОХРАНИТЬ ИГРУ", "ГЛАВНОЕ МЕНЮ"]
        self.pause_text = None
        self.option_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

        self.pause_text = arcade.Text(
            "ПАУЗА",
            self.window.width // 2, self.window.height // 2 + 100,
            (100, 200, 255), 64,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.option_texts = []
        for i, text in enumerate(self.options):
            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            text_obj = arcade.Text(
                text,
                self.window.width // 2, self.window.height // 2 - i * 60,
                color, 36,
                anchor_x="center", anchor_y="center",
                bold=(i == self.selected)
            )
            self.option_texts.append(text_obj)

        self.control_text = arcade.Text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC: продолжить • F11: Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 20,
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        # Рисуем затемненную версию игры
        self.game_view.on_draw()

        # Затемнение
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height,
            (0, 0, 0, 180)
        )

        # Рисуем меню паузы поверх
        arcade.draw_text(
            "ПАУЗА",
            self.window.width // 2 + 2, self.window.height // 2 + 98,
            TEXT_SHADOW, 64,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        self.pause_text.draw()

        for i, text in enumerate(self.option_texts):
            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 60,
                        350, 50
                    ),
                    UI_BUTTON_SELECTED
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 60,
                        350, 50
                    ),
                    (255, 220, 100), 2
                )

            # Обновляем цвет текста в зависимости от выбора
            text.color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            text.bold = (i == self.selected)

            arcade.draw_text(
                text.text,
                text.x + 1, text.y - 1,
                TEXT_SHADOW, text.font_size,
                anchor_x="center", anchor_y="center",
                bold=text.bold
            )
            text.draw()

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC: продолжить • F11: Полный экран",
            self.window.width // 2 + 1, 99,
            TEXT_SHADOW, 20,
            anchor_x="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.options)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.options)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.select_option()
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.game_view)
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

    def select_option(self):
        self.window.sound_manager.play_sound("click", volume=0.3)

        if self.selected == 0:  # Продолжить
            self.window.show_view(self.game_view)
        elif self.selected == 1:  # Сохранить игру
            self.game_view.save_game()
            self.window.sound_manager.play_sound("build", volume=0.3)
        elif self.selected == 2:  # Главное меню
            self.window.show_view(MenuView(self.window))

    def on_mouse_motion(self, x, y, dx, dy):
        for i in range(len(self.options)):
            item_y = self.window.height // 2 - i * 60
            if abs(x - self.window.width // 2) < 175 and abs(y - item_y) < 25:
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.options)):
                item_y = self.window.height // 2 - i * 60
                if abs(x - self.window.width // 2) < 175 and abs(y - item_y) < 25:
                    self.selected = i
                    self.select_option()
                    break

class HighScoresView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.scores = self.window.save_manager.load_scores()
        self.title_text = None
        self.header_texts = []
        self.score_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

        self.title_text = arcade.Text(
            "ТАБЛИЦА РЕКОРДОВ",
            self.window.width // 2, self.window.height - 100,
            (255, 220, 100), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        headers = ["Место", "Имя", "Очки", "Сложность", "Карта", "Волна", "Дата"]
        positions = [60, 140, 220, 320, 420, 520, 650]
        self.header_texts = []

        for i, header in enumerate(headers):
            text = arcade.Text(
                header,
                positions[i], self.window.height - 180,
                (100, 200, 255), 18,
                bold=True
            )
            self.header_texts.append(text)

        self.score_texts = []
        for i, score in enumerate(self.scores[:10]):
            y = self.window.height - 230 - i * 40
            color = (255, 220, 100) if i == 0 else (220, 220, 255)

            diff_text = "Лёгкий" if score["difficulty"] == "easy" else "Средний" if score["difficulty"] == "normal" else "Сложный"
            diff_color = (100, 255, 100) if score["difficulty"] == "easy" else (255, 255, 100) if score["difficulty"] == "normal" else (255, 100, 100)

            texts = [
                arcade.Text(str(i + 1), 60, y, color, 16),
                arcade.Text(score["name"], 140, y, color, 16),
                arcade.Text(str(score["score"]), 220, y, color, 16),
                arcade.Text(diff_text, 320, y, diff_color, 14),
                arcade.Text(score["map_name"], 420, y, color, 14),
                arcade.Text(str(score["waves"]), 520, y, color, 16),
                arcade.Text(score["date"], 650, y, color, 12)
            ]
            self.score_texts.append(texts)

        self.control_text = arcade.Text(
            "Нажмите ESC для выхода • F11: Полный экран",
            self.window.width // 2, 50,
            (180, 190, 210), 20,
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ТАБЛИЦА РЕКОРДОВ",
            self.window.width // 2 + 2, self.window.height - 102,
            TEXT_SHADOW, 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        self.title_text.draw()

        arcade.draw_line(
            60, self.window.height - 150,
            self.window.width - 60, self.window.height - 150,
            (80, 100, 150), 2
        )

        for text in self.header_texts:
            arcade.draw_text(
                text.text,
                text.x + 1, text.y - 1,
                TEXT_SHADOW, text.font_size,
                bold=True
            )
            text.draw()

        if not self.scores:
            no_scores_text = arcade.Text(
                "Рекордов пока нет!",
                self.window.width // 2, self.window.height // 2,
                (200, 200, 200), 36,
                anchor_x="center", anchor_y="center"
            )
            no_scores_text.draw()
        else:
            for row in self.score_texts:
                for text in row:
                    arcade.draw_text(
                        text.text,
                        text.x + 1, text.y - 1,
                        TEXT_SHADOW, text.font_size
                    )
                    text.draw()

        arcade.draw_text(
            "Нажмите ESC для выхода • F11: Полный экран",
            self.window.width // 2 + 1, 49,
            TEXT_SHADOW, 20,
            anchor_x="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.window))
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

class SettingsView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.selected = 0
        self.options = [
            ("Звук", self.window.sound_manager.enabled),
            ("Музыка", self.window.sound_manager.music_player is not None)
        ]
        self.title_text = None
        self.option_texts = []
        self.control_text = None

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

        self.title_text = arcade.Text(
            "НАСТРОЙКИ",
            self.window.width // 2, self.window.height - 100,
            (100, 200, 255), 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        self.option_texts = []
        for i, (name, value) in enumerate(self.options):
            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            status = "ВКЛ" if value else "ВЫКЛ"
            text = arcade.Text(
                f"{name}: {status}",
                self.window.width // 2, self.window.height // 2 - i * 80,
                color, 36,
                anchor_x="center", anchor_y="center"
            )
            self.option_texts.append(text)

        self.control_text = arcade.Text(
            "↑↓ Выбрать • ENTER Изменить • ESC Выход • F11: Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 20,
            anchor_x="center"
        )

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "НАСТРОЙКИ",
            self.window.width // 2 + 2, self.window.height - 102,
            TEXT_SHADOW, 48,
            anchor_x="center", anchor_y="center",
            bold=True
        )
        self.title_text.draw()

        for i, (name, value) in enumerate(self.options):
            status = "ВКЛ" if value else "ВЫКЛ"
            self.option_texts[i].text = f"{name}: {status}"
            self.option_texts[i].color = (255, 220, 100) if i == self.selected else (220, 220, 255)

            if i == self.selected:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 80,
                        300, 60
                    ),
                    UI_BUTTON_SELECTED
                )
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(
                        self.window.width // 2, self.window.height // 2 - i * 80,
                        300, 60
                    ),
                    (255, 220, 100), 2
                )

            arcade.draw_text(
                f"{name}: {status}",
                self.window.width // 2 + 1, self.window.height // 2 - i * 80 - 1,
                TEXT_SHADOW, 36,
                anchor_x="center", anchor_y="center"
            )

        for text in self.option_texts:
            text.draw()

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Изменить • ESC Выход • F11: Полный экран",
            self.window.width // 2 + 1, 99,
            TEXT_SHADOW, 20,
            anchor_x="center"
        )
        self.control_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.options)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.options)
            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ENTER:
            name, value = self.options[self.selected]
            self.options[self.selected] = (name, not value)

            if name == "Звук":
                self.window.sound_manager.enabled = not value
            elif name == "Музыка":
                if value:
                    self.window.sound_manager.stop_music()
                else:
                    self.window.sound_manager.play_music("menu")

            self.window.sound_manager.play_sound("click", volume=0.2)
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.window))
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

# ==================== ОСНОВНОЕ ОКНО ====================
class TowerDefenceSimulator(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)
        self.sound_manager = SoundManager()
        self.save_manager = SaveManager()

    def setup(self):
        menu_view = MenuView(self)
        self.show_view(menu_view)

# ==================== ЗАПУСК ====================
def main():
    try:
        window = TowerDefenceSimulator()
        window.setup()
        arcade.run()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()