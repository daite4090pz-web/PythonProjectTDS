"""
Tower Defence Simulator 2.0 - Модернизированная версия
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
from collections import deque

# ==================== КОНСТАНТЫ ====================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Башня Обороны: Легендарная Защита"
TILE_SIZE = 64
UI_HEIGHT = 140
TOWER_BUTTONS_WIDTH = 220
UPGRADE_MENU_WIDTH = 280
MAX_TOWERS = 30

# Приятные цвета интерфейса
UI_BACKGROUND = (40, 45, 70, 240)
UI_BUTTON_NORMAL = (70, 90, 140, 220)
UI_BUTTON_HOVER = (90, 120, 170, 240)
UI_BUTTON_SELECTED = (110, 150, 200, 255)
UPGRADE_BUTTON_COLOR = (90, 170, 90, 220)
UPGRADE_BUTTON_HOVER = (110, 200, 110, 240)
UPGRADE_BUTTON_DISABLED = (70, 90, 70, 180)
TEXT_COLOR = (240, 240, 255, 255)
TEXT_SHADOW = (20, 20, 40, 255)

# Современные цвета башен
SNIPER_COLOR = (100, 200, 255)      # Синий снайпер
ARTILLERY_COLOR = (255, 120, 80)    # Оранжевая артиллерия
LASER_COLOR = (180, 100, 255)       # Фиолетовый лазер
ROCKET_COLOR = (255, 200, 50)       # Жёлтые ракеты
TESLA_COLOR = (50, 255, 200)        # Бирюзовая тесла
FREEZER_COLOR = (100, 150, 255)     # Голубой мороз
POISON_COLOR = (50, 205, 50)        # Зеленый яд
BUFF_COLOR = (255, 150, 50)         # Оранжевый бустер

# Цвета врагов в стиле RPG
SLIME_COLOR = (102, 205, 170)       # Зеленый слизень
BLUE_SLIME_COLOR = (100, 150, 255)  # Синий слизень
WOLF_COLOR = (139, 137, 137)        # Серый волк
SKELETON_COLOR = (220, 220, 220)    # Белый скелет
KNIGHT_COLOR = (192, 192, 192)      # Серебряный рыцарь
GOLDEN_KNIGHT_COLOR = (255, 215, 0) # Золотой рыцарь
NECROMANCER_COLOR = (75, 0, 130)    # Темно-фиолетовый некромант
DRAGON_COLOR = (220, 20, 60)        # Красный дракон
GIANT_COLOR = (139, 69, 19)         # Коричневый великан
WIZARD_COLOR = (138, 43, 226)       # Фиолетовый маг
DEMON_COLOR = (178, 34, 34)         # Темно-красный демон

# Цвета снарядов
SNIPER_PROJECTILE = (100, 200, 255)
ARTILLERY_PROJECTILE = (255, 165, 0)
LASER_PROJECTILE = (200, 150, 255)
ROCKET_PROJECTILE = (255, 220, 100)
TESLA_PROJECTILE = (100, 255, 220)
FREEZER_PROJECTILE = (150, 200, 255)
POISON_PROJECTILE = (50, 255, 50)
BUFF_PROJECTILE = (255, 200, 100)

# Игровые константы
STARTING_MONEY_EASY = 650
STARTING_MONEY_NORMAL = 350
STARTING_MONEY_HARD = 250
STARTING_LIVES_EASY = 100
STARTING_LIVES_NORMAL = 50
STARTING_LIVES_HARD = 1
BASE_DAMAGE = 8
WAVE_AUTO_START_DELAY = 15  # Секунды до автоматического старта следующей волны

# ==================== ENUMS ====================
class TowerType(Enum):
    SNIPER = "sniper"
    ARTILLERY = "artillery"
    LASER = "laser"
    ROCKET = "rocket"
    TESLA = "tesla"
    FREEZER = "freezer"
    POISON = "poison"
    BUFF = "buff"


class EnemyType(Enum):
    SLIME = "slime"
    BLUE_SLIME = "blue_slime"
    WOLF = "wolf"
    SKELETON = "skeleton"
    KNIGHT = "knight"
    GOLDEN_KNIGHT = "golden_knight"
    NECROMANCER = "necromancer"
    DRAGON = "dragon"
    GIANT = "giant"
    WIZARD = "wizard"
    DEMON = "demon"


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class MapType(Enum):
    FOREST = "forest"
    CITY = "city"
    HELL = "hell"
    MYSTIC_FOREST = "mystic_forest"


# ==================== КЛАСС ВСПЛЫВАЮЩЕГО ТЕКСТА ====================
class FloatingText:
    def __init__(self, x, y, text, color=(255, 50, 50), duration=1.0, size=28):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.time = 0
        self.alpha = 255
        self.size = size
        self.velocity_y = 1.5

    def update(self, delta_time):
        self.time += delta_time
        self.y += self.velocity_y
        self.alpha = max(0, int(255 * (1 - self.time / self.duration)))

    def draw(self):
        if self.alpha > 0:
            arcade.draw_text(
                self.text, self.x, self.y,
                (*self.color, self.alpha),
                self.size, bold=True,
                anchor_x="center", anchor_y="center"
            )


# ==================== СИСТЕМА ЧАСТИЦ ====================
class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.max_particles = 100

    def create_explosion(self, x, y, color=None, count=5):
        if len(self.particles) > self.max_particles - 10:
            return

        color = color or (255, 165, 0)
        for _ in range(min(count, 5)):
            self.particles.append({
                'x': x, 'y': y,
                'dx': random.uniform(-1.5, 1.5),
                'dy': random.uniform(-1.5, 1.5),
                'size': random.uniform(1.0, 3.0),
                'color': color,
                'life': random.uniform(0.2, 0.6),
                'max_life': random.uniform(0.2, 0.6)
            })

    def create_trail(self, x, y, color=None):
        if len(self.particles) > self.max_particles - 3:
            return

        color = color or (200, 200, 200)
        if random.random() > 0.8:
            self.particles.append({
                'x': x, 'y': y,
                'dx': random.uniform(-0.3, 0.3),
                'dy': random.uniform(-0.3, 0.3),
                'size': random.uniform(0.5, 1.5),
                'color': color,
                'life': random.uniform(0.1, 0.2),
                'max_life': random.uniform(0.1, 0.2)
            })

    def create_chain_lightning(self, points, color):
        if len(self.particles) > self.max_particles - 10:
            return

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            segments = max(2, int(distance / 8))

            for j in range(segments):
                t = j / segments
                offset_x = random.uniform(-3, 3)
                offset_y = random.uniform(-3, 3)
                px = x1 + (x2 - x1) * t + offset_x
                py = y1 + (y2 - y1) * t + offset_y

                self.particles.append({
                    'x': px, 'y': py,
                    'dx': 0, 'dy': 0,
                    'size': random.uniform(0.8, 2.0),
                    'color': color,
                    'life': random.uniform(0.08, 0.15),
                    'max_life': random.uniform(0.08, 0.15)
                })

    def update(self, delta_time):
        dead_particles = []
        for i, particle in enumerate(self.particles):
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['life'] -= delta_time
            if particle['life'] <= 0:
                dead_particles.append(i)

        for i in reversed(dead_particles):
            if i < len(self.particles):
                self.particles.pop(i)

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
    def __init__(self, x, y, target, damage, speed=12.0, color=(255, 255, 255),
                 scale=0.5, shape="circle", homing=True, aoe_radius=0,
                 is_critical=False, effect_type=None, effect_value=0):
        super().__init__()
        self.target = target  # Важно: инициализировать target

        # Явное преобразование всех числовых параметров
        self.center_x = self._to_float(x)
        self.center_y = self._to_float(y)
        self.damage = self._to_float(damage)
        self.speed = self._to_float(speed)
        self.scale = self._to_float(scale)
        self.aoe_radius = self._to_float(aoe_radius)

        self.color = color
        self.shape = shape
        self.homing = homing
        self.homing_strength = 0.15
        self.aoe_damage_percent = 0.5
        self.penetration = 1
        self.is_critical = is_critical
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.projectile_size = 15.0

        # Угол для вращения снарядов
        self.angle = 0.0
        self.change_x = 0.0
        self.change_y = 0.0

        if target:
            self.update_movement()

    def _to_float(self, value):
        """Безопасное преобразование в float"""
        try:
            if isinstance(value, (list, tuple)):
                return float(value[0])
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def update_movement(self):
        if self.target and hasattr(self.target, 'health') and self.target.health > 0:
            dx = self.target.center_x - self.center_x
            dy = self.target.center_y - self.center_y
            distance = max(0.1, math.sqrt(dx ** 2 + dy ** 2))

            # Предикция движения цели
            if hasattr(self.target, 'change_x') and hasattr(self.target, 'change_y'):
                if self.target.change_x != 0 or self.target.change_y != 0:
                    target_speed = math.sqrt(self.target.change_x ** 2 + self.target.change_y ** 2)
                    time_to_hit = distance / self.speed
                    future_x = self.target.center_x + self.target.change_x * time_to_hit * 0.5
                    future_y = self.target.center_y + self.target.change_y * time_to_hit * 0.5
                    dx = future_x - self.center_x
                    dy = future_y - self.center_y
                    distance = max(0.1, math.sqrt(dx ** 2 + dy ** 2))

            self.change_x = (dx / distance) * self.speed
            self.change_y = (dy / distance) * self.speed
            self.angle = math.degrees(math.atan2(dy, dx))

    def update(self):
        if self.homing and self.target and hasattr(self.target, 'health') and self.target.health > 0:
            dx = self.target.center_x - self.center_x
            dy = self.target.center_y - self.center_y
            distance = max(0.1, math.sqrt(dx ** 2 + dy ** 2))

            # Сильное наведение для точного попадания
            target_dx = (dx / distance) * self.speed
            target_dy = (dy / distance) * self.speed

            self.change_x += (target_dx - self.change_x) * self.homing_strength * 2
            self.change_y += (target_dy - self.change_y) * self.homing_strength * 2

            current_speed = math.sqrt(self.change_x ** 2 + self.change_y ** 2)
            if current_speed > 0:
                self.change_x = (self.change_x / current_speed) * self.speed
                self.change_y = (self.change_y / current_speed) * self.speed

            self.angle = math.degrees(math.atan2(self.change_y, self.change_x))

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Вращение снарядов
        if self.shape == "rocket":
            self.angle += 15
        elif self.shape == "triangle":
            self.angle += 5

    def draw(self):
        """Отрисовка снаряда"""
        # Безопасное получение координат
        try:
            x = float(self.center_x)
            y = float(self.center_y)
        except (TypeError, ValueError):
            # Если координаты не числа, используем 0
            x = 0.0
            y = 0.0

        # Безопасное получение размеров
        try:
            projectile_size = float(self.projectile_size)
        except (TypeError, ValueError):
            projectile_size = 15.0

        try:
            scale = float(self.scale)
        except (TypeError, ValueError):
            scale = 0.5

        size = projectile_size * scale

        # Безопасное получение угла
        try:
            angle = float(self.angle)
        except (TypeError, ValueError):
            angle = 0.0

        if self.shape == "circle":
            arcade.draw_circle_filled(x, y, size / 2, self.color)
        elif self.shape == "triangle":
            # Треугольник
            height = size
            half_width = size / 2

            # Вычисляем точки треугольника с учетом угла
            angle_rad = math.radians(angle)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            top = (x + height / 2 * sin_a, y + height / 2 * cos_a)
            left = (x - half_width * cos_a - height / 4 * sin_a,
                    y + half_width * sin_a - height / 4 * cos_a)
            right = (x + half_width * cos_a - height / 4 * sin_a,
                     y - half_width * sin_a - height / 4 * cos_a)

            points = [top, left, right]
            arcade.draw_polygon_filled(points, self.color)
        elif self.shape == "rocket":
            # Ракета - прямоугольник с пламём
            half_width = size / 2
            half_height = half_width * 0.6

            # Основная часть ракеты
            arcade.draw_rectangle_filled(x, y,
                                         half_width * 2, half_height * 2,
                                         self.color, angle)

            # Пламя
            flame_length = half_height
            flame_points = [
                (x - half_width * 0.7, y - half_height),
                (x + half_width * 0.7, y - half_height),
                (x, y - half_height - flame_length)
            ]
            arcade.draw_polygon_filled(flame_points, (255, 165, 0))
        elif self.shape == "snowflake":
            # Снежинка
            radius = size / 3
            arcade.draw_circle_filled(x, y, radius, self.color)

            # Лучи снежинки
            for i in range(6):
                ray_angle = i * 60 + angle
                length = size / 2
                x2 = x + math.cos(math.radians(ray_angle)) * length
                y2 = y + math.sin(math.radians(ray_angle)) * length
                arcade.draw_line(x, y, x2, y2, (200, 230, 255), 2)
        elif self.shape == "drop":
            # Капля - круг с острым концом
            radius = size / 3
            arcade.draw_circle_filled(x, y, radius, self.color)

            # Острый конец капли
            drop_points = [(x, y + radius * 1.5),
                           (x - radius, y),
                           (x + radius, y)]
            arcade.draw_polygon_filled(drop_points, self.color)
        elif self.shape == "buff":
            # Бустер
            radius = size / 2
            arcade.draw_circle_filled(x, y, radius, self.color)
            arcade.draw_circle_outline(x, y, radius, (255, 255, 200), 2)

            # Стрелка вверх
            arrow_height = radius * 0.8
            arrow_width = radius * 0.5
            arrow_points = [
                (x, y + arrow_height),
                (x - arrow_width, y - arrow_height * 0.3),
                (x - arrow_width * 0.3, y - arrow_height * 0.3),
                (x - arrow_width * 0.3, y - arrow_height),
                (x + arrow_width * 0.3, y - arrow_height),
                (x + arrow_width * 0.3, y - arrow_height * 0.3),
                (x + arrow_width, y - arrow_height * 0.3)
            ]
            arcade.draw_polygon_filled(arrow_points, (255, 255, 200))
        else:
            # По умолчанию рисуем круг
            arcade.draw_circle_filled(x, y, size / 2, self.color)

        # Если крит, рисуем эффект
        if self.is_critical:
            crit_radius = size * 1.3
            arcade.draw_circle_outline(x, y, crit_radius, (255, 255, 100, 150), 2)


# ==================== КЛАССЫ ВРАГОВ ====================
class Enemy(arcade.Sprite):
    def __init__(self, enemy_type, path_points, level=1,
                 difficulty=Difficulty.NORMAL):
        super().__init__()
        self.enemy_type = enemy_type
        self.path_points = path_points
        self.path_index = 0
        self.level = level
        self.difficulty = difficulty
        self.alive = True
        self.health = 0
        self.max_health = 0
        self.slow_timer = 0
        self.slow_factor = 1.0
        self.poison_timer = 0
        self.poison_damage = 0
        self.buff_timer = 0
        self.buff_factor = 1.0
        self.change_x = 0
        self.change_y = 0

        difficulty_multiplier = {
            Difficulty.EASY: 0.8,
            Difficulty.NORMAL: 1.2,
            Difficulty.HARD: 1.6
        }
        multiplier = difficulty_multiplier[difficulty]

        enemy_stats = {
            EnemyType.SLIME: {
                'color': SLIME_COLOR,
                'health': (120 + level * 25) * multiplier,
                'speed': 1.4,
                'bounty': (12 + level * 2),
                'scale': 0.8,
                'size': 22,
                'name': "Слизень"
            },
            EnemyType.BLUE_SLIME: {
                'color': BLUE_SLIME_COLOR,
                'health': (220 + level * 35) * multiplier,
                'speed': 1.0,
                'bounty': (18 + level * 3),
                'scale': 0.85,
                'size': 24,
                'name': "Синий слизень"
            },
            EnemyType.WOLF: {
                'color': WOLF_COLOR,
                'health': (130 + level * 30) * multiplier,
                'speed': 1.8,
                'bounty': (16 + level * 3),
                'scale': 0.75,
                'size': 23,
                'name': "Волк"
            },
            EnemyType.SKELETON: {
                'color': SKELETON_COLOR,
                'health': (290 + level * 40) * multiplier,
                'speed': 1.0,
                'bounty': (25 + level * 5),
                'scale': 0.85,
                'size': 24,
                'name': "Скелет"
            },
            EnemyType.KNIGHT: {
                'color': KNIGHT_COLOR,
                'health': (420 + level * 60) * multiplier,
                'speed': 0.7,
                'bounty': (35 + level * 7),
                'scale': 1.0,
                'size': 30,
                'name': "Рыцарь",
                'armor': 0.2
            },
            EnemyType.GOLDEN_KNIGHT: {
                'color': GOLDEN_KNIGHT_COLOR,
                'health': (780 + level * 80) * multiplier,
                'speed': 0.5,
                'bounty': (45 + level * 9),
                'scale': 1.1,
                'size': 32,
                'name': "Золотой рыцарь",
                'armor': 0.3
            },
            EnemyType.NECROMANCER: {
                'color': NECROMANCER_COLOR,
                'health': (350 + level * 50) * multiplier,
                'speed': 0.3,
                'bounty': (40 + level * 8),
                'scale': 0.9,
                'size': 26,
                'name': "Некромант",
                'evasion': 0.15
            },
            EnemyType.DRAGON: {
                'color': DRAGON_COLOR,
                'health': (3400 + level * 250) * multiplier,
                'speed': 0.35,
                'bounty': (250 + level * 30),
                'scale': 1.5,
                'size': 50,
                'name': "Дракон"
            },
            EnemyType.GIANT: {
                'color': GIANT_COLOR,
                'health': (5000 + level * 350) * multiplier,
                'speed': 0.25,
                'bounty': (300 + level * 35),
                'scale': 1.7,
                'size': 55,
                'name': "Великан"
            },
            EnemyType.WIZARD: {
                'color': WIZARD_COLOR,
                'health': (1600 + level * 180) * multiplier,
                'speed': 0.55,
                'bounty': (220 + level * 25),
                'scale': 1.4,
                'size': 45,
                'name': "Волшебник"
            },
            EnemyType.DEMON: {
                'color': DEMON_COLOR,
                'health': (8800 + level * 300) * multiplier,
                'speed': 0.15,
                'bounty': (320 + level * 40),
                'scale': 1.6,
                'size': 52,
                'name': "Демон"
            }
        }

        stats = enemy_stats[enemy_type]
        self.color = stats['color']
        self.health = int(stats['health'])
        self.max_health = int(stats['health'])
        self.speed = stats['speed']
        self.bounty = int(stats['bounty'])
        self.scale = stats['scale']
        self.armor = stats.get('armor', 0)
        self.evasion = stats.get('evasion', 0)
        self.name = stats['name']
        texture_size = stats['size']

        self.texture = arcade.make_circle_texture(texture_size, self.color)

        if path_points:
            self.center_x, self.center_y = path_points[0]

    def update(self, delta_time):
        if not self.alive:
            return

        # Обновление эффектов
        if self.slow_timer > 0:
            self.slow_timer -= delta_time
            if self.slow_timer <= 0:
                self.slow_factor = 1.0

        if self.poison_timer > 0:
            self.poison_timer -= delta_time
            if self.poison_timer > 0:
                poison_interval = 1.0
                if hasattr(self, '_last_poison_time'):
                    self._last_poison_time += delta_time
                    if self._last_poison_time >= poison_interval:
                        self.health -= self.poison_damage
                        self._last_poison_time = 0
                        if self.health <= 0:
                            self.alive = False
                else:
                    self._last_poison_time = 0

        if self.buff_timer > 0:
            self.buff_timer -= delta_time
            if self.buff_timer <= 0:
                self.buff_factor = 1.0

        if not self.alive:
            return

        if self.path_index < len(self.path_points):
            target_x, target_y = self.path_points[self.path_index]
            dx = target_x - self.center_x
            dy = target_y - self.center_y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 2:
                speed = self.speed * self.slow_factor * self.buff_factor
                move_x = (dx / distance) * speed
                move_y = (dy / distance) * speed

                self.center_x += move_x
                self.center_y += move_y
                self.change_x = move_x
                self.change_y = move_y

                if dx != 0:
                    self.angle = math.degrees(math.atan2(dy, dx))
            else:
                self.path_index += 1

    def has_reached_end(self):
        return self.path_index >= len(self.path_points)

    def take_damage(self, damage, is_critical=False, effect_type=None, effect_value=0):
        if random.random() < self.evasion:
            return False, is_critical, False

        actual_damage = damage * (1 - self.armor)
        self.health -= actual_damage

        effect_applied = False

        if effect_type == "slow":
            self.slow_timer = 3.0
            self.slow_factor = max(0.3, 1.0 - effect_value)
            effect_applied = True
        elif effect_type == "poison":
            self.poison_timer = 5.0
            self.poison_damage = effect_value
            effect_applied = True
        elif effect_type == "buff":
            self.buff_timer = 0  # Эффект бафа только на башни, не на врагов

        if self.health <= 0:
            self.alive = False
            return True, is_critical, effect_applied
        return False, is_critical, effect_applied

    def draw_health_bar(self):
        if self.health < self.max_health:
            is_boss = self.enemy_type in [EnemyType.DRAGON, EnemyType.GIANT,
                                         EnemyType.WIZARD, EnemyType.DEMON]
            bar_width = 60 if is_boss else 50
            bar_height = 8 if is_boss else 5
            health_percent = self.health / self.max_health

            left = self.center_x - bar_width // 2
            bottom = self.center_y + self.height // 2 + 20 - bar_height // 2

            arcade.draw_lrbt_rectangle_filled(
                left, left + bar_width, bottom, bottom + bar_height,
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
                    left, right_health, bottom, bottom + bar_height,
                    health_color
                )

    def draw(self):
        """Отрисовка врага как цветного круга"""
        if self.alive:
            # Безопасное получение координат
            try:
                x = float(self.center_x)
                y = float(self.center_y)
                width = float(self.width)
            except (TypeError, ValueError):
                x = 0.0
                y = 0.0
                width = 40.0

            # Рисуем основной круг врага
            arcade.draw_circle_filled(x, y, width / 2, self.color)

            # Рисуем контур
            arcade.draw_circle_outline(x, y, width / 2, (255, 255, 255), 2)

    def get_name(self):
        return self.name


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
        self.max_level = 4
        self.shape = None
        self.base_damage = 0
        self.base_range = 0
        self.base_fire_rate = 0
        self.upgrade_cost = 0
        self.special_ability = None
        self.buff_multiplier = 1.0
        self.buff_timer = 0

        # Настройки для всех башен
        if tower_type == TowerType.SNIPER:
            self.color = SNIPER_COLOR
            self.base_damage = 30
            self.base_range = 320
            self.base_fire_rate = 1.5
            self.cost = 180
            self.projectile_speed = 24.0
            self.projectile_color = SNIPER_PROJECTILE
            self.projectile_shape = "triangle"
            self.shape = "triangle"
            self.upgrade_cost = 90
            self.special_ability = "crit_chance"
            self.crit_chance = 0.25
            self.crit_multiplier = 2.5
            self.penetration = 2

        elif tower_type == TowerType.ARTILLERY:
            self.color = ARTILLERY_COLOR
            self.base_damage = 65
            self.base_range = 250
            self.base_fire_rate = 0.9
            self.cost = 350
            self.projectile_speed = 14.0
            self.projectile_color = ARTILLERY_PROJECTILE
            self.projectile_shape = "square"
            self.shape = "square"
            self.upgrade_cost = 175
            self.special_ability = "splash_damage"
            self.splash_radius = 80
            self.splash_damage_percent = 0.6

        elif tower_type == TowerType.LASER:
            self.color = LASER_COLOR
            self.base_damage = 22
            self.base_range = 260
            self.base_fire_rate = 2.8
            self.cost = 270
            self.projectile_speed = 20.0
            self.projectile_color = LASER_PROJECTILE
            self.projectile_shape = "circle"
            self.shape = "circle"
            self.upgrade_cost = 135
            self.special_ability = "chain_lightning"
            self.chain_targets = 4
            self.chain_damage_reduction = 0.65

        elif tower_type == TowerType.ROCKET:
            self.color = ROCKET_COLOR
            self.base_damage = 40
            self.base_range = 220
            self.base_fire_rate = 1.7
            self.cost = 310
            self.projectile_speed = 10.0
            self.projectile_color = ROCKET_PROJECTILE
            self.projectile_shape = "rocket"
            self.shape = "rocket"
            self.upgrade_cost = 155
            self.special_ability = "homing_missiles"
            self.missile_count = 3
            self.homing_strength = 0.2

        elif tower_type == TowerType.TESLA:
            self.color = TESLA_COLOR
            self.base_damage = 15
            self.base_range = 200
            self.base_fire_rate = 3.5
            self.cost = 330
            self.projectile_speed = 30.0
            self.projectile_color = TESLA_PROJECTILE
            self.projectile_shape = "lightning"
            self.shape = "lightning"
            self.upgrade_cost = 165
            self.special_ability = "tesla_coil"
            self.max_targets = 5
            self.damage_reduction = 0.75

        elif tower_type == TowerType.FREEZER:
            self.color = FREEZER_COLOR
            self.base_damage = 15
            self.base_range = 180
            self.base_fire_rate = 1.2
            self.cost = 220
            self.projectile_speed = 18.0
            self.projectile_color = FREEZER_PROJECTILE
            self.projectile_shape = "snowflake"
            self.shape = "snowflake"
            self.upgrade_cost = 110
            self.special_ability = "slow_enemies"
            self.slow_amount = 0.5
            self.slow_duration = 3.0

        elif tower_type == TowerType.POISON:
            self.color = POISON_COLOR
            self.base_damage = 12
            self.base_range = 190
            self.base_fire_rate = 1.8
            self.cost = 200
            self.projectile_speed = 16.0
            self.projectile_color = POISON_PROJECTILE
            self.projectile_shape = "drop"
            self.shape = "drop"
            self.upgrade_cost = 100
            self.special_ability = "poison_dot"
            self.poison_dps = 10
            self.poison_duration = 5.0

        elif tower_type == TowerType.BUFF:
            self.color = BUFF_COLOR
            self.base_damage = 8
            self.base_range = 160
            self.base_fire_rate = 2.0
            self.cost = 240
            self.projectile_speed = 22.0
            self.projectile_color = BUFF_PROJECTILE
            self.projectile_shape = "buff"
            self.shape = "buff"
            self.upgrade_cost = 120
            self.special_ability = "buff_towers"
            self.buff_amount = 0.3
            self.buff_duration = 6.0
            self.buff_range = 120

        self.damage = self.base_damage
        self.range = self.base_range
        self.fire_rate = self.base_fire_rate
        self.scale = 1.0

    def find_target(self, enemies):
        if self.tower_type == TowerType.TESLA and self.level >= 2:
            return self.find_multiple_targets(enemies)

        closest = None
        closest_distance = float('inf')

        for enemy in enemies:
            if not enemy.alive or enemy.health <= 0:
                continue
            distance = math.sqrt(
                (self.center_x - enemy.center_x)**2 +
                (self.center_y - enemy.center_y)**2
            )
            if distance < self.range and distance < closest_distance:
                closest = enemy
                closest_distance = distance

        self.target = closest
        return closest

    def find_multiple_targets(self, enemies):
        targets = []
        max_targets = self.max_targets

        for enemy in enemies:
            if not enemy.alive or enemy.health <= 0:
                continue
            distance = math.sqrt(
                (self.center_x - enemy.center_x)**2 +
                (self.center_y - enemy.center_y)**2
            )
            if distance <= self.range:
                targets.append((enemy, distance))

        targets.sort(key=lambda x: x[1])
        return [target[0] for target in targets[:max_targets]]

    def can_attack(self):
        return self.fire_timer >= 1.0 / (self.fire_rate * self.buff_multiplier)

    def update(self, delta_time, enemies, projectiles, sound_manager,
               particle_system, towers):
        # Обновление бафа
        if self.buff_timer > 0:
            self.buff_timer -= delta_time
            if self.buff_timer <= 0:
                self.buff_multiplier = 1.0

        self.fire_timer += delta_time

        if self.tower_type == TowerType.TESLA:
            if self.can_attack():
                self.attack_tesla(enemies, sound_manager, particle_system)
                self.fire_timer = 0
            return

        if not self.target or not self.target.alive or self.target.health <= 0:
            self.find_target(enemies)
        elif self.target:
            distance = math.sqrt(
                (self.center_x - self.target.center_x)**2 +
                (self.center_y - self.target.center_y)**2
            )
            if distance > self.range:
                self.find_target(enemies)

        if self.target and self.can_attack() and self.target.alive:
            distance = math.sqrt(
                (self.center_x - self.target.center_x)**2 +
                (self.center_y - self.target.center_y)**2
            )
            if distance <= self.range:
                self.attack(projectiles, sound_manager, particle_system, towers)
                self.fire_timer = 0

    def attack(self, projectiles, sound_manager, particle_system, towers):
        if self.tower_type == TowerType.ROCKET:
            for _ in range(self.missile_count):
                self.create_projectile(projectiles, sound_manager, particle_system, towers)
        else:
            self.create_projectile(projectiles, sound_manager, particle_system, towers)

    def create_projectile(self, projectiles, sound_manager, particle_system, towers):
        actual_damage = self.damage * self.buff_multiplier
        is_critical = False
        effect_type = None
        effect_value = 0

        if self.tower_type == TowerType.SNIPER and random.random() < self.crit_chance:
            actual_damage *= self.crit_multiplier
            is_critical = True

        elif self.tower_type == TowerType.FREEZER:
            effect_type = "slow"
            effect_value = self.slow_amount

        elif self.tower_type == TowerType.POISON:
            effect_type = "poison"
            effect_value = self.poison_dps

        elif self.tower_type == TowerType.BUFF:
            effect_type = "buff"
            effect_value = self.buff_amount

        projectile = Projectile(
            self.center_x, self.center_y,
            self.target, actual_damage,
            self.projectile_speed, self.projectile_color,
            0.8, self.projectile_shape,
            self.tower_type in [TowerType.ROCKET, TowerType.BUFF],
            self.splash_radius if self.tower_type == TowerType.ARTILLERY else 0,
            is_critical=is_critical,
            effect_type=effect_type,
            effect_value=effect_value
        )

        if self.tower_type == TowerType.ROCKET:
            projectile.homing_strength = self.homing_strength
        if self.tower_type == TowerType.ARTILLERY:
            projectile.aoe_damage_percent = self.splash_damage_percent

        projectiles.append(projectile)

        sound_map = {
            TowerType.SNIPER: "shoot",
            TowerType.ARTILLERY: "explosion",
            TowerType.LASER: "magic",
            TowerType.ROCKET: "explosion",
            TowerType.TESLA: "magic",
            TowerType.FREEZER: "magic",
            TowerType.POISON: "magic",
            TowerType.BUFF: "build"
        }

        sound_name = sound_map.get(self.tower_type, "shoot")
        sound_manager.play_sound(sound_name, volume=0.3)

        if particle_system:
            angle = math.atan2(
                self.target.center_y - self.center_y,
                self.target.center_x - self.center_x
            )
            muzzle_x = self.center_x + math.cos(angle) * 35
            muzzle_y = self.center_y + math.sin(angle) * 35

            if self.tower_type == TowerType.LASER:
                particle_system.create_explosion(muzzle_x, muzzle_y, self.projectile_color, 3)
            else:
                particle_system.create_explosion(muzzle_x, muzzle_y, self.projectile_color, 4)

    def attack_tesla(self, enemies, sound_manager, particle_system):
        targets = self.find_multiple_targets(enemies)
        if not targets:
            return

        for i, target in enumerate(targets):
            if not target.alive:
                continue

            damage = self.damage * (self.damage_reduction ** i) * self.buff_multiplier
            died, is_critical, _ = target.take_damage(damage)
            if died:
                pass

        sound_manager.play_sound("magic", volume=0.3)

    def apply_buff(self, buff_amount, buff_duration):
        self.buff_multiplier = 1.0 + buff_amount
        self.buff_timer = buff_duration

    def draw(self):
        # Отрисовка основы башни
        if self.shape == "triangle":
            points = [
                (self.center_x, self.center_y + 32),
                (self.center_x - 26, self.center_y - 20),
                (self.center_x + 26, self.center_y - 20)
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 2)

            inner_points = [
                (self.center_x, self.center_y + 16),
                (self.center_x - 16, self.center_y - 10),
                (self.center_x + 16, self.center_y - 10)
            ]
            arcade.draw_polygon_filled(
                inner_points,
                (min(255, self.color[0] + 60),
                 min(255, self.color[1] + 60),
                 min(255, self.color[2] + 60))
            )

        elif self.shape == "square":
            half_size = 26
            points = [
                (self.center_x - half_size, self.center_y - half_size),
                (self.center_x + half_size, self.center_y - half_size),
                (self.center_x + half_size, self.center_y + half_size),
                (self.center_x - half_size, self.center_y + half_size)
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 2)

            arcade.draw_lrbt_rectangle_filled(
                self.center_x - (half_size // 2) // 2,
                self.center_x + (half_size // 2) // 2,
                self.center_y + half_size + 10 - 10,
                self.center_y + half_size + 10 + 10,
                (200, 200, 200)
            )

        elif self.shape == "circle":
            arcade.draw_circle_filled(self.center_x, self.center_y, 32, self.color)
            arcade.draw_circle_outline(
                self.center_x, self.center_y, 32, (255, 255, 255), 2
            )

            arcade.draw_circle_filled(
                self.center_x, self.center_y, 20,
                (min(255, self.color[0] + 50),
                 min(255, self.color[1] + 50),
                 min(255, self.color[2] + 50))
            )

        elif self.shape == "rocket":
            arcade.draw_lrbt_rectangle_filled(
                self.center_x - 25,
                self.center_x + 25,
                self.center_y - 20,
                self.center_y + 20,
                self.color
            )

            for i in range(2):
                offset = (i - 0.5) * 20
                arcade.draw_lrbt_rectangle_filled(
                    self.center_x + offset - 4,
                    self.center_x + offset + 4,
                    self.center_y + 25 - 15,
                    self.center_y + 25 + 15,
                    (200, 200, 200)
                )

        elif self.shape == "lightning":
            arcade.draw_circle_filled(self.center_x, self.center_y, 28, self.color)

            for i in range(3):
                angle = self.fire_timer * 200 + i * 120
                length = 20 + math.sin(self.fire_timer * 10 + i) * 5
                x2 = self.center_x + math.cos(math.radians(angle)) * length
                y2 = self.center_y + math.sin(math.radians(angle)) * length
                arcade.draw_line(
                    self.center_x, self.center_y, x2, y2,
                    (255, 255, 200), 2
                )

        elif self.shape == "snowflake":
            arcade.draw_circle_filled(self.center_x, self.center_y, 28, self.color)
            arcade.draw_circle_outline(self.center_x, self.center_y, 28, (200, 230, 255), 2)

            for i in range(6):
                angle = i * 60
                x1 = self.center_x + math.cos(math.radians(angle)) * 15
                y1 = self.center_y + math.sin(math.radians(angle)) * 15
                x2 = self.center_x + math.cos(math.radians(angle)) * 35
                y2 = self.center_y + math.sin(math.radians(angle)) * 35
                arcade.draw_line(x1, y1, x2, y2, (200, 230, 255), 3)

        elif self.shape == "drop":
            arcade.draw_circle_filled(self.center_x, self.center_y, 25, self.color)
            arcade.draw_circle_outline(self.center_x, self.center_y, 25, (100, 255, 100), 2)

            points = [
                (self.center_x, self.center_y + 30),
                (self.center_x - 15, self.center_y),
                (self.center_x + 15, self.center_y)
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (100, 255, 100), 2)

        elif self.shape == "buff":
            arcade.draw_circle_filled(self.center_x, self.center_y, 30, self.color)
            arcade.draw_circle_outline(self.center_x, self.center_y, 30, (255, 220, 100), 2)

            arcade.draw_text("↑", self.center_x, self.center_y,
                           (255, 255, 200), 24,
                           anchor_x="center", anchor_y="center", bold=True)

        # Отрисовка уровня башни
        if self.level > 1:
            level_color = (
                (255, 255, 100) if self.level == 2 else
                (255, 220, 50) if self.level == 3 else
                (255, 150, 30) if self.level == 4 else
                (255, 80, 0)
            )
            arcade.draw_circle_filled(
                self.center_x, self.center_y - 25, 10, level_color
            )
            arcade.draw_text(
                str(self.level), self.center_x, self.center_y - 28,
                (0, 0, 0), 12,
                anchor_x="center", anchor_y="center", bold=True
            )

        # Отрисовка бафа
        if self.buff_multiplier > 1.0:
            arcade.draw_circle_outline(
                self.center_x, self.center_y, 40,
                (255, 200, 50, 150), 3
            )

    def draw_range(self):
        arcade.draw_circle_outline(
            self.center_x, self.center_y,
            self.range, (*self.color[:3], 120), 2
        )

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1

            upgrade_multipliers = {
                1: 1.0,
                2: 1.6,
                3: 2.4,
                4: 3.2
            }

            multiplier = upgrade_multipliers[self.level]
            self.damage = int(self.base_damage * multiplier)
            self.range = int(self.base_range * (1.25 ** (self.level - 1)))
            self.fire_rate = self.base_fire_rate * (1.3 ** (self.level - 1))
            self.upgrade_cost = int(self.upgrade_cost * 1.8)

            if self.tower_type == TowerType.SNIPER:
                self.crit_chance = 0.25 + (self.level - 1) * 0.08
                self.crit_multiplier = 2.5 + (self.level - 1) * 0.5

            elif self.tower_type == TowerType.ARTILLERY:
                self.splash_radius = 80 + (self.level - 1) * 25
                self.splash_damage_percent = 0.6 + (self.level - 1) * 0.15

            elif self.tower_type == TowerType.LASER:
                self.chain_targets = 4 + (self.level - 1) * 2

            elif self.tower_type == TowerType.ROCKET:
                self.missile_count = 3 + (self.level - 1)
                self.homing_strength = 0.2 + (self.level - 1) * 0.08

            elif self.tower_type == TowerType.TESLA:
                self.max_targets = 5 + (self.level - 1) * 3

            elif self.tower_type == TowerType.FREEZER:
                self.slow_amount = 0.5 + (self.level - 1) * 0.15
                if self.slow_amount > 0.8:
                    self.slow_amount = 0.8
                self.slow_duration = 3.0 + (self.level - 1) * 1.0

            elif self.tower_type == TowerType.POISON:
                self.poison_dps = 10 + (self.level - 1) * 5
                self.poison_duration = 5.0 + (self.level - 1) * 1.0

            elif self.tower_type == TowerType.BUFF:
                self.buff_amount = 0.3 + (self.level - 1) * 0.15
                self.buff_duration = 6.0 + (self.level - 1) * 2.0
                self.buff_range = 120 + (self.level - 1) * 30

            return self.upgrade_cost
        return 0

    def get_next_upgrade_stats(self):
        if self.level < self.max_level:
            next_level = self.level + 1
            multiplier = {
                2: 1.6, 3: 2.4, 4: 3.2
            }.get(next_level, 1.0)

            next_damage = int(self.base_damage * multiplier)
            next_range = int(self.base_range * (1.25 ** (next_level - 1)))
            next_fire_rate = self.base_fire_rate * (1.3 ** (next_level - 1))

            return {
                'damage': next_damage,
                'range': next_range,
                'fire_rate': next_fire_rate,
                'cost': int(self.upgrade_cost * 1.8)
            }
        return None

    def get_tower_name(self):
        names = {
            TowerType.SNIPER: "Снайпер",
            TowerType.ARTILLERY: "Артиллерия",
            TowerType.LASER: "Лазерная",
            TowerType.ROCKET: "Ракетная",
            TowerType.TESLA: "Тесла",
            TowerType.FREEZER: "Мороз",
            TowerType.POISON: "Яд",
            TowerType.BUFF: "Бустер"
        }
        return names.get(self.tower_type, "Башня")


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
                writer.writerow([
                    name, score, level, waves, difficulty, map_name,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ])
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
        self.menu_items = [
            "НОВАЯ ИГРА", "ЗАГРУЗИТЬ", "РЕКОРДЫ", "НАСТРОЙКИ", "ВЫХОД"
        ]
        self.background_y = 0
        self.title_alpha = 255
        self.title_direction = -1

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))
        self.window.sound_manager.play_music("menu")

    def on_draw(self):
        self.clear()

        self.background_y = (self.background_y + 0.5) % self.window.height

        self.title_alpha += self.title_direction * 2
        if self.title_alpha <= 150 or self.title_alpha >= 255:
            self.title_direction *= -1

        title_color = (100, 200, 255, self.title_alpha)

        arcade.draw_text(
            "БАШНЯ ОБОРОНЫ: ЛЕГЕНДАРНАЯ ЗАЩИТА",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "БАШНЯ ОБОРОНЫ: ЛЕГЕНДАРНАЯ ЗАЩИТА",
            self.window.width // 2,
            self.window.height - 150,
            title_color,
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        arcade.draw_text(
            "Защитите королевство от темных сил!",
            self.window.width // 2 + 1,
            self.window.height - 221,
            (30, 40, 60),
            24,
            anchor_x="center",
            anchor_y="center"
        )
        arcade.draw_text(
            "Защитите королевство от темных сил!",
            self.window.width // 2,
            self.window.height - 220,
            (200, 220, 255),
            24,
            anchor_x="center",
            anchor_y="center"
        )

        for i, item in enumerate(self.menu_items):
            y = self.window.height // 2 - i * 60

            if i == self.selected:
                arcade.draw_lrbt_rectangle_filled(
                    self.window.width // 2 - 175,
                    self.window.width // 2 + 175,
                    y - 25,
                    y + 25,
                    UI_BUTTON_SELECTED
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.window.width // 2 - 175,
                    self.window.width // 2 + 175,
                    y - 25,
                    y + 25,
                    (255, 220, 100),
                    3
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)

            arcade.draw_text(
                item,
                self.window.width // 2 + 1,
                y - 1,
                (30, 40, 60),
                32,
                anchor_x="center",
                anchor_y="center",
                bold=(i == self.selected)
            )
            arcade.draw_text(
                item,
                self.window.width // 2,
                y,
                color,
                32,
                anchor_x="center",
                anchor_y="center",
                bold=(i == self.selected)
            )

        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Выход • F11 Полный экран",
            self.window.width // 2 + 1,
            49,
            (30, 40, 60),
            18,
            anchor_x="center",
            anchor_y="center"
        )
        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Выход • F11 Полный экран",
            self.window.width // 2,
            50,
            (180, 190, 210),
            18,
            anchor_x="center",
            anchor_y="center"
        )

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
            if (abs(x - self.window.width // 2) < 175 and
                    abs(y - item_y) < 25):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.menu_items)):
                item_y = self.window.height // 2 - i * 60
                if (abs(x - self.window.width // 2) < 175 and
                        abs(y - item_y) < 25):
                    self.selected = i
                    self.select_item()
                    break


class DifficultyView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.selected = 0
        self.difficulties = ["НОВИЧОК", "ВОИН", "ЛЕГЕНДА"]
        self.difficulty_descriptions = [
            "Для первого знакомства с игрой",
            "Сбалансированный вызов для опытных игроков",
            "Испытание для настоящих мастеров"
        ]

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ УРОВЕНЬ СЛОЖНОСТИ",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ВЫБЕРИТЕ УРОВЕНЬ СЛОЖНОСТИ",
            self.window.width // 2,
            self.window.height - 150,
            (100, 200, 255),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        for i, diff in enumerate(self.difficulties):
            y = self.window.height // 2 - i * 120

            if i == self.selected:
                arcade.draw_lrbt_rectangle_filled(
                    self.window.width // 2 - 200,
                    self.window.width // 2 + 200,
                    y - 40,
                    y + 40,
                    UI_BUTTON_SELECTED
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.window.width // 2 - 200,
                    self.window.width // 2 + 200,
                    y - 40,
                    y + 40,
                    (255, 220, 100),
                    3
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            desc_color = ((180, 190, 210) if i == self.selected else (150, 160, 180))

            arcade.draw_text(
                diff,
                self.window.width // 2 + 1,
                y - 1,
                (30, 40, 60),
                36,
                anchor_x="center",
                anchor_y="center"
            )
            arcade.draw_text(
                diff,
                self.window.width // 2,
                y,
                color,
                36,
                anchor_x="center",
                anchor_y="center"
            )

            arcade.draw_text(
                self.difficulty_descriptions[i],
                self.window.width // 2 + 1,
                y - 51,
                (30, 40, 60),
                20,
                anchor_x="center",
                anchor_y="center",
                align="center"
            )
            arcade.draw_text(
                self.difficulty_descriptions[i],
                self.window.width // 2,
                y - 50,
                desc_color,
                20,
                anchor_x="center",
                anchor_y="center",
                align="center"
            )

        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Назад • F11 Полный экран",
            self.window.width // 2 + 1,
            99,
            (30, 40, 60),
            20,
            anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Назад • F11 Полный экран",
            self.window.width // 2,
            100,
            (180, 190, 210),
            20,
            anchor_x="center"
        )

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
            if (abs(x - self.window.width // 2) < 200 and abs(y - item_y) < 40):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.difficulties)):
                item_y = self.window.height // 2 - i * 120
                if (abs(x - self.window.width // 2) < 200 and abs(y - item_y) < 40):
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
        self.maps = ["ВОЛШЕБНЫЙ ЛЕС", "КРЕПОСТЬ", "ПУСТЫНЯ", "МИСТИЧЕСКИЙ ЛЕС"]
        self.map_descriptions = [
            "Зеленые тропы среди древних деревьев",
            "Каменные стены и укрепленные проходы",
            "Раскаленные пески и огненные дороги",
            "Зачарованные тропы в фиолетовых сумерках"
        ]

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ ЛОКАЦИЮ",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ВЫБЕРИТЕ ЛОКАЦИЮ",
            self.window.width // 2,
            self.window.height - 150,
            (100, 200, 255),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        for i, map_name in enumerate(self.maps):
            y = self.window.height // 2 - i * 120

            if i == self.selected:
                arcade.draw_lrbt_rectangle_filled(
                    self.window.width // 2 - 225,
                    self.window.width // 2 + 225,
                    y - 40,
                    y + 40,
                    UI_BUTTON_SELECTED
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.window.width // 2 - 225,
                    self.window.width // 2 + 225,
                    y - 40,
                    y + 40,
                    (255, 220, 100),
                    3
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)
            desc_color = ((180, 190, 210) if i == self.selected else (150, 160, 180))

            arcade.draw_text(
                map_name,
                self.window.width // 2 + 1,
                y - 1,
                (30, 40, 60),
                36,
                anchor_x="center",
                anchor_y="center"
            )
            arcade.draw_text(
                map_name,
                self.window.width // 2,
                y,
                color,
                36,
                anchor_x="center",
                anchor_y="center"
            )

            arcade.draw_text(
                self.map_descriptions[i],
                self.window.width // 2 + 1,
                y - 51,
                (30, 40, 60),
                20,
                anchor_x="center",
                anchor_y="center",
                align="center"
            )
            arcade.draw_text(
                self.map_descriptions[i],
                self.window.width // 2,
                y - 50,
                desc_color,
                20,
                anchor_x="center",
                anchor_y="center",
                align="center"
            )

        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Назад • F11 Полный экран",
            self.window.width // 2 + 1,
            99,
            (30, 40, 60),
            20,
            anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Назад • F11 Полный экран",
            self.window.width // 2,
            100,
            (180, 190, 210),
            20,
            anchor_x="center"
        )

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
                0: MapType.FOREST,
                1: MapType.CITY,
                2: MapType.HELL,
                3: MapType.MYSTIC_FOREST
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
            if (abs(x - self.window.width // 2) < 225 and abs(y - item_y) < 40):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.maps)):
                item_y = self.window.height // 2 - i * 120
                if (abs(x - self.window.width // 2) < 225 and abs(y - item_y) < 40):
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.3)
                    map_map = {
                        0: MapType.FOREST,
                        1: MapType.CITY,
                        2: MapType.HELL,
                        3: MapType.MYSTIC_FOREST
                    }
                    selected_map = map_map[self.selected]
                    game_view = GameView(self.window, self.difficulty, selected_map)
                    game_view.setup()
                    self.window.show_view(game_view)
                    break


class GameView(arcade.View):
    def __init__(self, window, difficulty=Difficulty.NORMAL,
                 map_type=MapType.FOREST):
        super().__init__()
        self.window = window
        self.difficulty = difficulty
        self.map_type = map_type

        self.enemy_list = []
        self.tower_list = []
        self.projectile_list = []
        self.tower_spots = []

        if difficulty == Difficulty.EASY:
            self.money = STARTING_MONEY_EASY
            self.lives = STARTING_LIVES_EASY
        elif difficulty == Difficulty.NORMAL:
            self.money = STARTING_MONEY_NORMAL
            self.lives = STARTING_LIVES_NORMAL
        else:
            self.money = STARTING_MONEY_HARD
            self.lives = STARTING_LIVES_HARD

        self.score = 0
        self.wave = 0
        self.wave_timer = 0
        self.selected_tower_type = TowerType.SNIPER
        self.wave_active = False
        self.enemies_spawned = 0
        self.total_enemies = 0

        self.particle_system = ParticleSystem()
        self.path_points = []
        self.path_points2 = []
        self.path_points3 = []
        self.start_positions = []
        self.end_pos = None

        self.showing_range = None
        self.selected_tower = None
        self.game_over = False
        self.victory = False
        self.show_upgrade_menu = False
        self.upgrade_menu_rect = None
        self.upgrade_button_rect = None
        self.sell_button_rect = None

        self.waves = self.generate_waves()

        self.base_pulse = 0
        self.base_pulse_dir = 1

        self.map_offset_x = 0
        self.map_offset_y = 0

        self.tower_buttons = []
        self.wave_button_rect = None
        self.wave_button_hover = False

        self.last_enemy_count = 0
        self.update_counter = 0

        self.floating_texts = []
        self.hovered_enemy = None
        self.auto_wave_start_delay = WAVE_AUTO_START_DELAY
        self.wave_start_countdown = 0

        self.tower_limit = MAX_TOWERS

    def generate_waves(self):
        base_waves = [
            {"slime": 8, "blue_slime": 2, "wolf": 1, "skeleton": 0,
             "knight": 0, "golden_knight": 0, "necromancer": 0,
             "dragon": 0, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 10, "blue_slime": 4, "wolf": 1, "skeleton": 0,
             "knight": 0, "golden_knight": 0, "necromancer": 0,
             "dragon": 0, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 17, "blue_slime": 6, "wolf": 2, "skeleton": 2,
             "knight": 1, "golden_knight": 0, "necromancer": 0,
             "dragon": 0, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 25, "blue_slime": 15, "wolf": 5, "skeleton": 6,
             "knight": 2, "golden_knight": 1, "necromancer": 0,
             "dragon": 0, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 35, "blue_slime": 18, "wolf": 12, "skeleton": 10,
             "knight": 6, "golden_knight": 2, "necromancer": 1,
             "dragon": 0, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 30, "blue_slime": 20, "wolf": 15, "skeleton": 12,
             "knight": 8, "golden_knight": 3, "necromancer": 2,
             "dragon": 1, "giant": 0, "wizard": 0, "demon": 0},
            {"slime": 35, "blue_slime": 22, "wolf": 18, "skeleton": 15,
             "knight": 10, "golden_knight": 4, "necromancer": 3,
             "dragon": 0, "giant": 1, "wizard": 0, "demon": 0},
            {"slime": 40, "blue_slime": 25, "wolf": 20, "skeleton": 18,
             "knight": 12, "golden_knight": 5, "necromancer": 4,
             "dragon": 0, "giant": 0, "wizard": 1, "demon": 0},
            {"slime": 45, "blue_slime": 28, "wolf": 22, "skeleton": 20,
             "knight": 14, "golden_knight": 6, "necromancer": 5,
             "dragon": 1, "giant": 1, "wizard": 0, "demon": 0},
            {"slime": 50, "blue_slime": 30, "wolf": 25, "skeleton": 22,
             "knight": 16, "golden_knight": 7, "necromancer": 6,
             "dragon": 0, "giant": 0, "wizard": 1, "demon": 1},
        ]

        if self.difficulty == Difficulty.EASY:
            for wave in base_waves:
                for key in wave:
                    if key in ["dragon", "giant", "wizard", "demon"]:
                        wave[key] = max(0, wave[key] - 1)
                    elif wave[key] > 0:
                        wave[key] = int(wave[key] * 0.7)
        elif self.difficulty == Difficulty.HARD:
            for wave in base_waves:
                for key in wave:
                    if wave[key] > 0:
                        wave[key] = int(wave[key] * 1.5)

        return base_waves

    def setup(self):
        self.load_map()
        self.window.sound_manager.play_music("game")
        self.create_tower_buttons()
        self.create_wave_button()

    def create_tower_buttons(self):
        self.tower_buttons = []
        tower_data = [
            (TowerType.SNIPER, "Снайпер", "180💰", SNIPER_COLOR, "triangle"),
            (TowerType.ARTILLERY, "Артиллерия", "350💰", ARTILLERY_COLOR, "square"),
            (TowerType.LASER, "Лазерная", "270💰", LASER_COLOR, "circle"),
            (TowerType.ROCKET, "Ракетная", "310💰", ROCKET_COLOR, "rocket"),
            (TowerType.TESLA, "Тесла", "330💰", TESLA_COLOR, "lightning"),
            (TowerType.FREEZER, "Мороз", "220💰", FREEZER_COLOR, "snowflake"),
            (TowerType.POISON, "Яд", "200💰", POISON_COLOR, "drop"),
            (TowerType.BUFF, "Бустер", "240💰", BUFF_COLOR, "buff")
        ]

        button_width = 180
        button_height = 80
        start_x = self.window.width - TOWER_BUTTONS_WIDTH + 20
        start_y = self.window.height - UI_HEIGHT - 150

        for i, (tower_type, name, cost, color, shape) in enumerate(tower_data):
            button_y = start_y - i * (button_height + 15)
            button_rect = (start_x, button_y, button_width, button_height)
            self.tower_buttons.append(
                (button_rect, tower_type, name, cost, color, shape)
            )

    def create_wave_button(self):
        button_width = 200
        button_height = 60
        button_x = self.window.width // 2
        button_y = self.window.height - UI_HEIGHT - 40
        self.wave_button_rect = (button_x - button_width//2,
                                 button_y - button_height//2,
                                 button_width, button_height)

    def find_path_bfs(self, start, end, points_dict):
        if start not in points_dict or end not in points_dict:
            return None

        queue = deque()
        queue.append([start])
        visited = set([start])

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end:
                return path

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                next_cell = (current[0] + dx, current[1] + dy)
                if next_cell in points_dict and next_cell not in visited:
                    visited.add(next_cell)
                    new_path = list(path)
                    new_path.append(next_cell)
                    queue.append(new_path)

        return None

    def load_map(self):
        if self.map_type == MapType.FOREST:
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
        elif self.map_type == MapType.CITY:
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
        elif self.map_type == MapType.HELL:
            level_map = [
                "T T T E T T T T T T T T T T T T T T T T",
                "T T T # T T T T T T T T T T T T T T T T",
                "T T T # T T T T T T T T T T T T T T T T",
                "T T T # T T T T T T T T T T T T T T T T",
                "T T T # # # # # # # # # # T T T T T T T",
                "T T T T T T T T T T T T # T T T T T T T",
                "T T T T T T T T T T T T # T T T T T T T",
                "T T T T T T # # # # # # # T T T T T T T",
                "T T T T T T # T # T T T T T T T T T T T",
                "T T # # # # # T # T T T T T T T T T T T",
                "T T # T T T T T # T T T T T T T T T T T",
                "T T # T T T T T # # # # # # # # # T T T",
                "T T # T T T T T T T T T T T T T # # T T",
                "T T # T T T T T T T T T T T T T T # T T",
                "T T S T T T T T T T T T T T T T T # # S"
            ]
        else:  # MYSTIC_FOREST
            level_map = [
                "T T T T T T T T T T T T T T T T T T T T",
                "T E # # # # # # # T T T T T T T T T T T",
                "T T T T T T T T # T T T T T T T T T T T",
                "T T T T T T # # # # # T T T T T T T T T",
                "T T T T T T # T T T # T T T T T T T T T",
                "T T # # # # # T T T # T T T T T T T T T",
                "T T # T T T T T T T # T T T T T T T T T",
                "T T # T T T T T T T # # # # # # # # # S",
                "T T # T T T T T T T T T T T T T T T T T",
                "S # # # # # # # # T T T T T T T T T T T",
                "T T T T T T T T # T T T T T T T T T T T",
                "T T T T T T T T # # # # # # # # # T T T",
                "T T T T T T T T T T T T T T T T # # # T",
                "T T T T T T T T T T T T T T T T T T # T",
                "T T T T T T T T T T T T T T T T T T # S"
            ]

        rows = len(level_map)
        cols = len(level_map[0].split())

        map_width = cols * TILE_SIZE
        map_height = rows * TILE_SIZE

        available_width = self.window.width - TOWER_BUTTONS_WIDTH
        available_height = self.window.height - UI_HEIGHT

        self.map_offset_x = (available_width - map_width) // 2
        self.map_offset_y = (available_height - map_height) // 2

        path_cells = []
        self.tower_spots = []
        self.start_positions = []
        self.end_pos = None

        points_dict = {}

        for y in range(rows):
            row = level_map[y].split()
            for x in range(cols):
                cell = row[x]
                pos_x = x * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_x
                pos_y = y * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_y

                if cell == 'S':
                    self.start_positions.append((x, y))
                    path_cells.append((x, y, 'S', pos_x, pos_y))
                    points_dict[(x, y)] = (pos_x, pos_y)
                elif cell == 'E':
                    self.end_pos = (x, y, pos_x, pos_y)
                    path_cells.append((x, y, 'E', pos_x, pos_y))
                    points_dict[(x, y)] = (pos_x, pos_y)
                elif cell == '#':
                    path_cells.append((x, y, '#', pos_x, pos_y))
                    points_dict[(x, y)] = (pos_x, pos_y)
                elif cell == 'T':
                    if pos_x < self.window.width - TOWER_BUTTONS_WIDTH:
                        self.tower_spots.append((pos_x, pos_y))

        if self.map_type == MapType.MYSTIC_FOREST and len(self.start_positions) >= 3:
            self.create_paths_for_mystic_forest(points_dict)
        elif self.map_type == MapType.HELL and len(self.start_positions) >= 2:
            self.create_paths_for_map3(points_dict)
        else:
            self.create_single_path(points_dict)

        if not self.path_points:
            if self.start_positions and self.end_pos:
                start_pos = points_dict[self.start_positions[0]]
                end_pos = (self.end_pos[2], self.end_pos[3])
                self.path_points = [start_pos, end_pos]
            else:
                if not self.start_positions:
                    start_pos = (
                        TILE_SIZE * 2 + self.map_offset_x,
                        TILE_SIZE * 13 + self.map_offset_y
                    )
                else:
                    start_pos = points_dict[self.start_positions[0]]
                if not self.end_pos:
                    end_pos = (
                        TILE_SIZE * 19 + self.map_offset_x,
                        TILE_SIZE * 2 + self.map_offset_y
                    )
                else:
                    end_pos = (self.end_pos[2], self.end_pos[3])
                self.path_points = [start_pos, end_pos]

    def create_single_path(self, points_dict):
        if not self.start_positions or not self.end_pos:
            return

        start_cell = self.start_positions[0]
        end_cell = (self.end_pos[0], self.end_pos[1])

        path = self.find_path_bfs(start_cell, end_cell, points_dict)

        if path:
            self.path_points = [points_dict[cell] for cell in path]
        else:
            if self.start_positions and self.end_pos:
                start_pos = points_dict[self.start_positions[0]]
                end_pos = (self.end_pos[2], self.end_pos[3])
                self.path_points = [start_pos, end_pos]

    def create_paths_for_map3(self, points_dict):
        if len(self.start_positions) < 2 or not self.end_pos:
            return

        end_cell = (self.end_pos[0], self.end_pos[1])

        start_cell1 = self.start_positions[0]
        path1 = self.find_path_bfs(start_cell1, end_cell, points_dict)

        if path1:
            self.path_points = [points_dict[cell] for cell in path1]
        else:
            start_pos = points_dict[start_cell1]
            end_pos = (self.end_pos[2], self.end_pos[3])
            self.path_points = [start_pos, end_pos]

        start_cell2 = self.start_positions[1]
        path2 = self.find_path_bfs(start_cell2, end_cell, points_dict)

        if path2:
            self.path_points2 = [points_dict[cell] for cell in path2]
        else:
            start_pos = points_dict[start_cell2]
            end_pos = (self.end_pos[2], self.end_pos[3])
            self.path_points2 = [start_pos, end_pos]

    def create_paths_for_mystic_forest(self, points_dict):
        if len(self.start_positions) < 3 or not self.end_pos:
            return

        end_cell = (self.end_pos[0], self.end_pos[1])

        # Первый путь
        start_cell1 = self.start_positions[0]
        path1 = self.find_path_bfs(start_cell1, end_cell, points_dict)
        if path1:
            self.path_points = [points_dict[cell] for cell in path1]
        else:
            self.path_points = [points_dict[start_cell1], (self.end_pos[2], self.end_pos[3])]

        # Второй путь
        start_cell2 = self.start_positions[1]
        path2 = self.find_path_bfs(start_cell2, end_cell, points_dict)
        if path2:
            self.path_points2 = [points_dict[cell] for cell in path2]
        else:
            self.path_points2 = [points_dict[start_cell2], (self.end_pos[2], self.end_pos[3])]

        # Третий путь
        start_cell3 = self.start_positions[2]
        path3 = self.find_path_bfs(start_cell3, end_cell, points_dict)
        if path3:
            self.path_points3 = [points_dict[cell] for cell in path3]
        else:
            self.path_points3 = [points_dict[start_cell3], (self.end_pos[2], self.end_pos[3])]

    def on_draw(self):
        self.clear()

        if self.map_type == MapType.FOREST:
            bg_color = (30, 90, 40)
            path_color = (101, 67, 33)
        elif self.map_type == MapType.CITY:
            bg_color = (60, 60, 70)
            path_color = (80, 80, 90)
        elif self.map_type == MapType.HELL:
            bg_color = (90, 30, 30)
            path_color = (255, 69, 0)
        else:  # MYSTIC_FOREST
            bg_color = (75, 0, 130)
            path_color = (169, 169, 169)

        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width - TOWER_BUTTONS_WIDTH,
            0,
            self.window.height - UI_HEIGHT,
            bg_color
        )

        arcade.draw_lrbt_rectangle_filled(
            self.window.width - TOWER_BUTTONS_WIDTH,
            self.window.width,
            0,
            self.window.height - UI_HEIGHT,
            (45, 55, 75)
        )

        arcade.draw_line(
            self.window.width - TOWER_BUTTONS_WIDTH, 0,
            self.window.width - TOWER_BUTTONS_WIDTH,
            self.window.height - UI_HEIGHT,
            (80, 90, 110), 3
        )

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

        if len(self.path_points) > 1:
            for i in range(len(self.path_points) - 1):
                x1, y1 = self.path_points[i]
                x2, y2 = self.path_points[i + 1]
                arcade.draw_line(x1, y1, x2, y2, path_color, TILE_SIZE - 10)

        if self.map_type == MapType.HELL and len(self.path_points2) > 1:
            for i in range(len(self.path_points2) - 1):
                x1, y1 = self.path_points2[i]
                x2, y2 = self.path_points2[i + 1]
                arcade.draw_line(x1, y1, x2, y2, (255, 140, 0), TILE_SIZE - 10)

        if self.map_type == MapType.MYSTIC_FOREST:
            if len(self.path_points2) > 1:
                for i in range(len(self.path_points2) - 1):
                    x1, y1 = self.path_points2[i]
                    x2, y2 = self.path_points2[i + 1]
                    arcade.draw_line(x1, y1, x2, y2, (150, 150, 150), TILE_SIZE - 10)

            if len(self.path_points3) > 1:
                for i in range(len(self.path_points3) - 1):
                    x1, y1 = self.path_points3[i]
                    x2, y2 = self.path_points3[i + 1]
                    arcade.draw_line(x1, y1, x2, y2, (200, 200, 200), TILE_SIZE - 10)

        if self.start_positions:
            for i, (x, y) in enumerate(self.start_positions):
                start_x = x * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_x
                start_y = y * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_y
                arcade.draw_circle_filled(
                    start_x, start_y, TILE_SIZE // 2, (100, 200, 100)
                )
                arcade.draw_text(
                    f"ВХОД {i + 1}", start_x, start_y,
                    (240, 240, 240), 12,
                    anchor_x="center", anchor_y="center"
                )

        if self.end_pos:
            end_x, end_y = self.end_pos[2], self.end_pos[3]
            self.base_pulse += self.base_pulse_dir * 0.1
            if self.base_pulse > 1.0 or self.base_pulse < 0.5:
                self.base_pulse_dir *= -1

            pulse_size = TILE_SIZE // 2 * (0.8 + 0.2 * self.base_pulse)
            arcade.draw_circle_filled(end_x, end_y, pulse_size, (200, 100, 100))
            arcade.draw_text(
                "ЗАМОК", end_x, end_y, (240, 240, 240), 12,
                anchor_x="center", anchor_y="center"
            )

        for spot in self.tower_spots:
            sx, sy = spot
            arcade.draw_lrbt_rectangle_outline(
                sx - (TILE_SIZE - 10) // 2,
                sx + (TILE_SIZE - 10) // 2,
                sy - (TILE_SIZE - 10) // 2,
                sy + (TILE_SIZE - 10) // 2,
                (100, 120, 150),
                2
            )

        # Рисуем снаряды
        for projectile in self.projectile_list:
            projectile.draw()

        # Рисуем врагов
        for enemy in self.enemy_list:
            enemy.draw()

        # Рисуем башни
        for tower in self.tower_list:
            tower.draw()

        self.particle_system.draw()

        for enemy in self.enemy_list:
            enemy.draw_health_bar()

        if self.showing_range:
            self.showing_range.draw_range()

        for text in self.floating_texts:
            text.draw()

        if self.hovered_enemy and self.hovered_enemy.alive:
            self.draw_enemy_info(self.hovered_enemy)

        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width,
            self.window.height - UI_HEIGHT,
            self.window.height,
            UI_BACKGROUND
        )

        arcade.draw_line(
            0, self.window.height - UI_HEIGHT,
            self.window.width, self.window.height - UI_HEIGHT,
            (80, 100, 150), 3
        )

        diff_text = (
            "Новичок" if self.difficulty == Difficulty.EASY else
            "Воин" if self.difficulty == Difficulty.NORMAL else
            "Легенда"
        )
        diff_color = (
            (100, 255, 100) if self.difficulty == Difficulty.EASY else
            (255, 255, 100) if self.difficulty == Difficulty.NORMAL else
            (255, 100, 100)
        )

        map_text = (
            "Волшебный лес" if self.map_type == MapType.FOREST else
            "Крепость" if self.map_type == MapType.CITY else
            "Пустыня" if self.map_type == MapType.HELL else
            "Мистический лес"
        )

        # Сдвинул UI элементы вправо на 100 пикселей
        arcade.draw_text(
            f"Золото: {self.money}💰", 201, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Золото: {self.money}💰", 200, self.window.height - 50,
            (255, 215, 0), 28, anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"Жизни: {self.lives}❤️", 401, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Жизни: {self.lives}❤️", 400, self.window.height - 50,
            (255, 100, 100), 28, anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"Очки: {self.score}", 601, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Очки: {self.score}", 600, self.window.height - 50,
            TEXT_COLOR, 28, anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"Башни: {len(self.tower_list)}/{self.tower_limit}",
            801, self.window.height - 51,
            TEXT_SHADOW, 24, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Башни: {len(self.tower_list)}/{self.tower_limit}",
            800, self.window.height - 50,
            (100, 200, 255), 24, anchor_x="center", anchor_y="center", bold=True
        )

        if self.wave_button_rect:
            bx, by, bw, bh = self.wave_button_rect
            button_color = (UI_BUTTON_SELECTED if self.wave_button_hover
                           else UI_BUTTON_NORMAL)

            if not self.wave_active and self.wave < len(self.waves):
                if self.wave_start_countdown > 0:
                    button_text = f"АВТОСТАРТ: {int(self.wave_start_countdown)}"
                    text_color = (255, 200, 100)
                else:
                    button_text = "ЗАПУСТИТЬ ВОЛНУ"
                    text_color = (255, 220, 100)
            else:
                button_text = "ВОЛНА АКТИВНА"
                text_color = (200, 200, 200)

            arcade.draw_lrbt_rectangle_filled(
                bx, bx + bw,
                by, by + bh,
                button_color
            )

            arcade.draw_lrbt_rectangle_outline(
                bx, bx + bw,
                by, by + bh,
                ((255, 220, 100) if self.wave_button_hover
                       else (100, 120, 150)),
                3
            )

            arcade.draw_text(
                button_text,
                bx + bw//2 + 1, by + bh//2 - 1,
                TEXT_SHADOW, 22,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                button_text,
                bx + bw//2, by + bh//2,
                text_color, 22,
                anchor_x="center", anchor_y="center", bold=True
            )

            wave_info = f"Волна: {self.wave + 1}/{len(self.waves)}"
            arcade.draw_text(
                wave_info,
                bx + bw//2 + 1, by - 35,
                TEXT_SHADOW, 20,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                wave_info,
                bx + bw//2, by - 36,
                TEXT_COLOR, 20,
                anchor_x="center", anchor_y="center", bold=True
            )

        for (x, y, width, height), tower_type, name, cost, color, shape in \
                self.tower_buttons:

            if tower_type == self.selected_tower_type:
                button_color = UI_BUTTON_SELECTED
                border_color = (255, 220, 100)
            else:
                button_color = UI_BUTTON_NORMAL
                border_color = (100, 120, 150)

            arcade.draw_lrbt_rectangle_filled(
                x - width // 2,
                x + width // 2,
                y - height // 2,
                y + height // 2,
                button_color
            )
            arcade.draw_lrbt_rectangle_outline(
                x - width // 2,
                x + width // 2,
                y - height // 2,
                y + height // 2,
                border_color,
                3
            )

            shadow_y = y - 2
            arcade.draw_lrbt_rectangle_filled(
                x - width // 2,
                x + width // 2,
                shadow_y - height // 2,
                shadow_y + height // 2,
                (0, 0, 0, 50)
            )

            icon_x = x - width / 2 + 35
            icon_y = y

            if shape == "triangle":
                points = [
                    (icon_x, icon_y + 18),
                    (icon_x - 15, icon_y - 12),
                    (icon_x + 15, icon_y - 12)
                ]
                arcade.draw_polygon_filled(points, color)
                arcade.draw_polygon_outline(points, (255, 255, 255), 2)
            elif shape == "square":
                half_size = 15
                points = [
                    (icon_x - half_size, icon_y - half_size),
                    (icon_x + half_size, icon_y - half_size),
                    (icon_x + half_size, icon_y + half_size),
                    (icon_x - half_size, icon_y + half_size)
                ]
                arcade.draw_polygon_filled(points, color)
                arcade.draw_polygon_outline(points, (255, 255, 255), 2)
            elif shape == "rocket":
                arcade.draw_lrbt_rectangle_filled(
                    icon_x - 12,
                    icon_x + 12,
                    icon_y - 8,
                    icon_y + 8,
                    color
                )
                arcade.draw_lrbt_rectangle_filled(
                    icon_x - 5,
                    icon_x + 5,
                    icon_y + 8,
                    icon_y + 18,
                    (200, 200, 200)
                )
            elif shape == "lightning":
                arcade.draw_circle_filled(icon_x, icon_y, 15, color)
                for i in range(3):
                    angle = i * 120
                    x2 = icon_x + math.cos(math.radians(angle)) * 12
                    y2 = icon_y + math.sin(math.radians(angle)) * 12
                    arcade.draw_line(
                        icon_x, icon_y, x2, y2,
                        (255, 255, 200), 2
                    )
            elif shape == "snowflake":
                arcade.draw_circle_filled(icon_x, icon_y, 15, color)
                for i in range(6):
                    angle = i * 60
                    x1 = icon_x + math.cos(math.radians(angle)) * 8
                    y1 = icon_y + math.sin(math.radians(angle)) * 8
                    x2 = icon_x + math.cos(math.radians(angle)) * 20
                    y2 = icon_y + math.sin(math.radians(angle)) * 20
                    arcade.draw_line(x1, y1, x2, y2, (200, 230, 255), 2)
            elif shape == "drop":
                arcade.draw_circle_filled(icon_x, icon_y, 12, color)
                points = [
                    (icon_x, icon_y + 15),
                    (icon_x - 10, icon_y),
                    (icon_x + 10, icon_y)
                ]
                arcade.draw_polygon_filled(points, color)
            elif shape == "buff":
                arcade.draw_circle_filled(icon_x, icon_y, 15, color)
                arcade.draw_text("↑", icon_x, icon_y,
                               (255, 255, 200), 18,
                               anchor_x="center", anchor_y="center", bold=True)
            else:
                arcade.draw_circle_filled(icon_x, icon_y, 18, color)
                arcade.draw_circle_outline(icon_x, icon_y, 18, (255, 255, 255), 2)

            arcade.draw_text(
                name,
                x - width / 2 + 75, y + 15,
                TEXT_COLOR, 18,
                anchor_x="left", anchor_y="center",
                bold=(tower_type == self.selected_tower_type)
            )

            arcade.draw_text(
                cost,
                x - width / 2 + 75, y - 15,
                (255, 215, 0), 16,
                anchor_x="left", anchor_y="center"
            )

        if self.show_upgrade_menu and self.selected_tower:
            self.draw_upgrade_menu()

        if self.game_over:
            overlay = (0, 0, 0, 180)
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width, 0, self.window.height, overlay
            )

            arcade.draw_text(
                "ПОРАЖЕНИЕ",
                self.window.width // 2 + 2, self.window.height // 2 - 2,
                TEXT_SHADOW, 48,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                "ПОРАЖЕНИЕ",
                self.window.width // 2, self.window.height // 2,
                (255, 100, 100), 48,
                anchor_x="center", anchor_y="center", bold=True
            )

            arcade.draw_text(
                "ESC - Вернуться в главное меню",
                self.window.width // 2 + 1, self.window.height // 2 - 61,
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "ESC - Вернуться в главное меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )

        elif self.victory:
            overlay = (0, 0, 0, 180)
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width, 0, self.window.height, overlay
            )

            arcade.draw_text(
                "ПОБЕДА!",
                self.window.width // 2 + 2, self.window.height // 2 - 2,
                TEXT_SHADOW, 48,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                "ПОБЕДА!",
                self.window.width // 2, self.window.height // 2,
                (100, 255, 100), 48,
                anchor_x="center", anchor_y="center", bold=True
            )

            arcade.draw_text(
                "ESC - Вернуться в главное меню",
                self.window.width // 2 + 1, self.window.height // 2 - 61,
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "ESC - Вернуться в главное меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )

        arcade.draw_text(
            "Выберите башню и кликните на свободную клетку • ESC Пауза • F11 Полный экран",
            self.window.width // 2 + 1, 39,
            TEXT_SHADOW, 16, anchor_x="center"
        )
        arcade.draw_text(
            "Выберите башню и кликните на свободную клетку • ESC Пауза • F11 Полный экран",
            self.window.width // 2, 40,
            (180, 190, 210), 16, anchor_x="center", bold=True
        )

    def draw_enemy_info(self, enemy):
        info_x = enemy.center_x
        info_y = enemy.center_y + 60
        width = 180
        height = 80

        arcade.draw_lrbt_rectangle_filled(
            info_x - width // 2,
            info_x + width // 2,
            info_y - height // 2,
            info_y + height // 2,
            (0, 0, 0, 200)
        )

        arcade.draw_lrbt_rectangle_outline(
            info_x - width // 2,
            info_x + width // 2,
            info_y - height // 2,
            info_y + height // 2,
            (255, 255, 255),
            2
        )

        enemy_name = enemy.get_name()
        arcade.draw_text(
            enemy_name,
            info_x, info_y + 20,
            (255, 255, 255), 20,
            anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"Уровень: {enemy.level}",
            info_x, info_y - 5,
            (200, 200, 255), 16,
            anchor_x="center", anchor_y="center"
        )

        health_percent = enemy.health / enemy.max_health
        health_color = (
            (100, 255, 100) if health_percent > 0.6 else
            (255, 255, 100) if health_percent > 0.3 else
            (255, 100, 100)
        )

        arcade.draw_text(
            f"HP: {int(enemy.health)}/{int(enemy.max_health)}",
            info_x, info_y - 25,
            health_color, 16,
            anchor_x="center", anchor_y="center"
        )

        arcade.draw_text(
            f"Награда: {enemy.bounty}💰",
            info_x, info_y - 45,
            (255, 215, 0), 16,
            anchor_x="center", anchor_y="center"
        )

    def draw_upgrade_menu(self):
        if not self.selected_tower:
            return

        menu_x = (self.window.width - TOWER_BUTTONS_WIDTH -
                  UPGRADE_MENU_WIDTH + 50)
        menu_y = UI_HEIGHT + 300  # Немного увеличили высоту
        menu_width = UPGRADE_MENU_WIDTH - 50
        menu_height = 410  # Увеличили высоту для кнопки продажи

        self.upgrade_menu_rect = (menu_x, menu_y - menu_height,
                                  menu_width, menu_height)

        # Фон меню с градиентом
        arcade.draw_lrbt_rectangle_filled(
            menu_x,
            menu_x + menu_width,
            menu_y - menu_height,
            menu_y,
            (50, 60, 85, 250)
        )

        # Верхняя часть с градиентом
        arcade.draw_lrbt_rectangle_filled(
            menu_x,
            menu_x + menu_width,
            menu_y - 40,
            menu_y,
            (70, 90, 140, 250)
        )

        # Рамка меню
        arcade.draw_lrbt_rectangle_outline(
            menu_x,
            menu_x + menu_width,
            menu_y - menu_height,
            menu_y,
            (255, 220, 100),
            3
        )

        # Иконка башни слева
        icon_x = menu_x + 40
        icon_y = menu_y - 70

        # Рисуем иконку башни
        if self.selected_tower.shape == "triangle":
            points = [
                (icon_x, icon_y + 25),
                (icon_x - 20, icon_y - 15),
                (icon_x + 20, icon_y - 15)
            ]
            arcade.draw_polygon_filled(points, self.selected_tower.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 2)
        elif self.selected_tower.shape == "square":
            half = 20
            points = [
                (icon_x - half, icon_y - half),
                (icon_x + half, icon_y - half),
                (icon_x + half, icon_y + half),
                (icon_x - half, icon_y + half)
            ]
            arcade.draw_polygon_filled(points, self.selected_tower.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 2)
        elif self.selected_tower.shape == "circle":
            arcade.draw_circle_filled(icon_x, icon_y, 25, self.selected_tower.color)
            arcade.draw_circle_outline(icon_x, icon_y, 25, (255, 255, 255), 2)
        elif self.selected_tower.shape == "rocket":
            arcade.draw_rectangle_filled(icon_x, icon_y, 50, 30, self.selected_tower.color)
        else:
            arcade.draw_circle_filled(icon_x, icon_y, 25, self.selected_tower.color)

        # Название башни и уровень
        tower_name = self.selected_tower.get_tower_name()

        arcade.draw_text(
            f"«{tower_name}»",
            menu_x + menu_width // 2 + 1, menu_y - 15,
            TEXT_SHADOW, 20,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"«{tower_name}»",
            menu_x + menu_width // 2, menu_y - 16,
            (255, 220, 100), 20,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Уровень башни с иконкой
        level_x = menu_x + menu_width - 40
        level_color = (
            (150, 200, 255) if self.selected_tower.level == 1 else
            (100, 255, 100) if self.selected_tower.level == 2 else
            (255, 255, 100) if self.selected_tower.level == 3 else
            (255, 150, 50) if self.selected_tower.level == 4 else
            (255, 80, 80)
        )

        arcade.draw_circle_filled(level_x, menu_y - 70, 18, level_color)
        arcade.draw_text(
            str(self.selected_tower.level), level_x, menu_y - 74,
            (0, 0, 0), 14,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Текущие характеристики
        stats_y = menu_y - 90
        stats = [
            ("УРОН", f"{self.selected_tower.damage}", (255, 100, 100)),
            ("ДАЛЬНОСТЬ", f"{int(self.selected_tower.range)}", (100, 200, 255)),
            ("СКОРОСТЬ", f"{self.selected_tower.fire_rate:.1f}/сек", (100, 255, 100)),
            ("УРОВЕНЬ", f"{self.selected_tower.level}/{self.selected_tower.max_level}", (255, 220, 100))
        ]

        for i, (label, value, color) in enumerate(stats):
            # Метка
            arcade.draw_text(
                label,
                menu_x + 85, stats_y - i * 28,
                (180, 190, 210), 14,
                anchor_x="left", anchor_y="center"
            )
            # Значение
            arcade.draw_text(
                value,
                menu_x + menu_width - 20, stats_y - i * 28,
                color, 14,
                anchor_x="right", anchor_y="center", bold=True
            )

        # Линия разделения
        arcade.draw_line(
            menu_x + 10, menu_y - 187,
            menu_x + menu_width - 10, menu_y - 187,
            (80, 90, 110), 2
        )

        # Информация об улучшении
        if self.selected_tower.level < self.selected_tower.max_level:
            next_stats = self.selected_tower.get_next_upgrade_stats()
            if next_stats:
                upgrade_cost = next_stats['cost']

                # Заголовок улучшения
                arcade.draw_text(
                    "УЛУЧШЕНИЕ",
                    menu_x + menu_width // 2 + 1, menu_y - 195,
                    TEXT_SHADOW, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )
                arcade.draw_text(
                    "УЛУЧШЕНИЕ",
                    menu_x + menu_width // 2, menu_y - 196,
                    (100, 255, 100), 16,
                    anchor_x="center", anchor_y="center", bold=True
                )

                # Новые характеристики
                future_y = menu_y - 215
                future_stats = [
                    (f"→ Урон: {next_stats['damage']}",
                     f"+{next_stats['damage'] - self.selected_tower.damage}",
                     (100, 255, 100)),
                    (f"→ Дальность: {int(next_stats['range'])}",
                     f"+{int(next_stats['range'] - self.selected_tower.range)}",
                     (150, 200, 255)),
                    (f"→ Скорость: {next_stats['fire_rate']:.1f}/сек",
                     f"+{next_stats['fire_rate'] - self.selected_tower.fire_rate:.1f}",
                     (100, 255, 150))
                ]

                for i, (label, diff, color) in enumerate(future_stats):
                    arcade.draw_text(
                        label,
                        menu_x + 15, future_y - i * 22,
                        (220, 220, 240), 12,
                        anchor_x="left", anchor_y="center"
                    )
                    arcade.draw_text(
                        diff,
                        menu_x + menu_width - 20, future_y - i * 22,
                        color, 12,
                        anchor_x="right", anchor_y="center", bold=True
                    )

                # Кнопка улучшения
                button_x = menu_x + menu_width // 2
                button_y = menu_y - 300
                button_width = 180
                button_height = 40

                self.upgrade_button_rect = (button_x - button_width // 2,
                                            button_y - button_height // 2,
                                            button_width, button_height)

                can_afford = self.money >= upgrade_cost
                button_color = (UPGRADE_BUTTON_COLOR if can_afford
                                else UPGRADE_BUTTON_DISABLED)

                # Фон кнопки
                arcade.draw_lrbt_rectangle_filled(
                    button_x - button_width // 2,
                    button_x + button_width // 2,
                    button_y - button_height // 2,
                    button_y + button_height // 2,
                    button_color
                )

                # Тень кнопки
                arcade.draw_lrbt_rectangle_filled(
                    button_x - button_width // 2 + 2,
                    button_x + button_width // 2 + 2,
                    button_y - button_height // 2 - 2,
                    button_y + button_height // 2 - 2,
                    (0, 0, 0, 50)
                )

                # Рамка кнопки
                border_color = ((100, 255, 100) if can_afford
                                else (150, 150, 150))
                arcade.draw_lrbt_rectangle_outline(
                    button_x - button_width // 2,
                    button_x + button_width // 2,
                    button_y - button_height // 2,
                    button_y + button_height // 2,
                    border_color,
                    2
                )

                # Текст кнопки
                button_text = f"УЛУЧШИТЬ: {upgrade_cost}💰"
                text_color = (TEXT_COLOR if can_afford else (150, 150, 150))

                arcade.draw_text(
                    button_text,
                    button_x + 1, button_y - 1,
                    TEXT_SHADOW, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )
                arcade.draw_text(
                    button_text,
                    button_x, button_y,
                    text_color, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )

                # Иконка улучшения
                arcade.draw_text(
                    "↑", button_x - 70, button_y,
                    (100, 255, 100), 20,
                    anchor_x="center", anchor_y="center", bold=True
                )
        else:
            # Максимальный уровень
            max_y = menu_y - 220
            arcade.draw_text(
                "🏆 МАКСИМАЛЬНЫЙ УРОВЕНЬ 🏆",
                menu_x + menu_width // 2 + 1, max_y - 1,
                TEXT_SHADOW, 16,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                "🏆 МАКСИМАЛЬНЫЙ УРОВЕНЬ 🏆",
                menu_x + menu_width // 2, max_y,
                (255, 215, 0), 16,
                anchor_x="center", anchor_y="center", bold=True
            )

            # Информация о достижении
            arcade.draw_text(
                "Эта башня достигла своего",
                menu_x + menu_width // 2 + 1, menu_y - 245,
                TEXT_SHADOW, 12,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "Эта башня достигла своего",
                menu_x + menu_width // 2, menu_y - 246,
                (200, 220, 255), 12,
                anchor_x="center", anchor_y="center"
            )

            arcade.draw_text(
                "максимального потенциала!",
                menu_x + menu_width // 2 + 1, menu_y - 265,
                TEXT_SHADOW, 12,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "максимального потенциала!",
                menu_x + menu_width // 2, menu_y - 266,
                (200, 220, 255), 12,
                anchor_x="center", anchor_y="center"
            )

        # Кнопка продажи (всегда доступна)
        sell_button_x = menu_x + menu_width // 2
        sell_button_y = menu_y - menu_height + 35
        sell_button_width = 160
        sell_button_height = 36

        self.sell_button_rect = (sell_button_x - sell_button_width // 2,
                                 sell_button_y - sell_button_height // 2,
                                 sell_button_width, sell_button_height)

        # Расчет стоимости продажи (60% от общей стоимости)
        sell_value = int(self.selected_tower.cost * 0.6)
        for _ in range(self.selected_tower.level - 1):
            sell_value += int(self.selected_tower.upgrade_cost * 0.6)

        # Фон кнопки продажи
        arcade.draw_lrbt_rectangle_filled(
            sell_button_x - sell_button_width // 2,
            sell_button_x + sell_button_width // 2,
            sell_button_y - sell_button_height // 2,
            sell_button_y + sell_button_height // 2,
            (180, 60, 60, 220)
        )

        # Тень кнопки продажи
        arcade.draw_lrbt_rectangle_filled(
            sell_button_x - sell_button_width // 2 + 2,
            sell_button_x + sell_button_width // 2 + 2,
            sell_button_y - sell_button_height // 2 - 2,
            sell_button_y + sell_button_height // 2 - 2,
            (0, 0, 0, 50)
        )

        # Рамка кнопки продажи
        arcade.draw_lrbt_rectangle_outline(
            sell_button_x - sell_button_width // 2,
            sell_button_x + sell_button_width // 2,
            sell_button_y - sell_button_height // 2,
            sell_button_y + sell_button_height // 2,
            (255, 180, 180),
            2
        )

        # Текст кнопки продажи
        sell_text = f"ПРОДАТЬ: {sell_value}💰"
        arcade.draw_text(
            sell_text,
            sell_button_x + 1, sell_button_y - 1,
            TEXT_SHADOW, 15,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            sell_text,
            sell_button_x, sell_button_y,
            (255, 220, 220), 15,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Иконка продажи
        arcade.draw_text(
            "💰", sell_button_x - 55, sell_button_y,
            (255, 215, 0), 18,
            anchor_x="center", anchor_y="center", bold=True
        )

    def on_update(self, delta_time):
        if self.game_over or self.victory:
            return

        for text in self.floating_texts[:]:
            text.update(delta_time)
            if text.time >= text.duration:
                self.floating_texts.remove(text)

        # Обновление врагов
        for enemy in self.enemy_list[:]:
            enemy.update(delta_time)
            if not enemy.alive:
                self.money += enemy.bounty
                self.score += enemy.bounty * 10
                self.enemy_list.remove(enemy)
                self.particle_system.create_explosion(
                    enemy.center_x, enemy.center_y,
                    (255, 165, 0), 4
                )
                self.window.sound_manager.play_sound("enemy_die", volume=0.3)
                continue
            if enemy.has_reached_end():
                self.lives -= BASE_DAMAGE
                self.enemy_list.remove(enemy)
                self.window.sound_manager.play_sound("lose_life", volume=0.25)
                if self.lives <= 0:
                    self.game_over = True

        self.update_counter += 1
        update_towers = (self.update_counter % 2 == 0 or
                        len(self.enemy_list) < 20)

        # Обновление башен с передачей списка башен для бустеров
        for tower in self.tower_list:
            if update_towers:
                if tower.tower_type == TowerType.TESLA:
                    tower.update(
                        delta_time,
                        self.enemy_list,
                        self.projectile_list,
                        self.window.sound_manager,
                        self.particle_system,
                        self.tower_list
                    )
                else:
                    tower.update(
                        delta_time,
                        self.enemy_list,
                        self.projectile_list,
                        self.window.sound_manager,
                        self.particle_system,
                        self.tower_list
                    )
            else:
                tower.fire_timer += delta_time

        # Обновление снарядов
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

            hit_list = []
            for enemy in self.enemy_list:
                if enemy.alive:
                    distance = math.sqrt(
                        (projectile.center_x - enemy.center_x)**2 +
                        (projectile.center_y - enemy.center_y)**2
                    )
                    if distance < 25:  # Увеличил радиус коллизии
                        hit_list.append(enemy)

            if hit_list:
                # Для артиллерии: AOE повреждение
                if projectile.aoe_radius > 0:
                    main_target = hit_list[0]
                    # Урон основному врагу
                    died, is_critical, effect_applied = main_target.take_damage(
                        projectile.damage,
                        projectile.is_critical,
                        projectile.effect_type,
                        projectile.effect_value
                    )

                    if died:
                        self.money += main_target.bounty
                        self.score += main_target.bounty * 10
                        self.enemy_list.remove(main_target)
                        self.particle_system.create_explosion(
                            main_target.center_x, main_target.center_y,
                            (255, 165, 0), 4
                        )
                        self.window.sound_manager.play_sound("enemy_die", volume=0.3)

                    if is_critical:
                        self.floating_texts.append(
                            FloatingText(
                                main_target.center_x,
                                main_target.center_y + 30,
                                "КРИТ!",
                                (255, 50, 50),
                                duration=0.8,
                                size=28
                            )
                        )

                    # Урон по области
                    for enemy in self.enemy_list:
                        if enemy.alive and enemy != main_target:
                            distance = math.sqrt(
                                (projectile.center_x - enemy.center_x)**2 +
                                (projectile.center_y - enemy.center_y)**2
                            )
                            if distance <= projectile.aoe_radius:
                                aoe_damage = projectile.damage * projectile.aoe_damage_percent
                                aoe_died, aoe_critical, _ = enemy.take_damage(
                                    aoe_damage,
                                    False,
                                    projectile.effect_type,
                                    projectile.effect_value
                                )

                                if aoe_died:
                                    self.money += enemy.bounty
                                    self.score += enemy.bounty * 10
                                    self.enemy_list.remove(enemy)
                                    self.particle_system.create_explosion(
                                        enemy.center_x, enemy.center_y,
                                        (255, 165, 0), 3
                                    )
                                    self.window.sound_manager.play_sound("enemy_die", volume=0.25)

                else:
                    # Обычный урон одному врагу
                    for enemy in hit_list:
                        if enemy.alive:
                            died, is_critical, effect_applied = enemy.take_damage(
                                projectile.damage,
                                projectile.is_critical,
                                projectile.effect_type,
                                projectile.effect_value
                            )

                            if died:
                                self.money += enemy.bounty
                                self.score += enemy.bounty * 10
                                self.enemy_list.remove(enemy)
                                self.particle_system.create_explosion(
                                    enemy.center_x, enemy.center_y,
                                    (255, 165, 0), 4
                                )
                                self.window.sound_manager.play_sound("enemy_die", volume=0.3)

                            if is_critical:
                                self.floating_texts.append(
                                    FloatingText(
                                        enemy.center_x,
                                        enemy.center_y + 30,
                                        "КРИТ!",
                                        (255, 50, 50),
                                        duration=0.8,
                                        size=28
                                    )
                                )

                            # Применение эффекта бафа к башням
                            if projectile.effect_type == "buff":
                                for tower in self.tower_list:
                                    if tower != self.selected_tower:  # Не бафаем себя
                                        distance = math.sqrt(
                                            (tower.center_x - enemy.center_x)**2 +
                                            (tower.center_y - enemy.center_y)**2
                                        )
                                        if distance <= tower.buff_range:
                                            tower.apply_buff(projectile.effect_value, 6.0)
                                            self.floating_texts.append(
                                                FloatingText(
                                                    tower.center_x,
                                                    tower.center_y + 40,
                                                    f"+{int(projectile.effect_value*100)}%",
                                                    (255, 200, 50),
                                                    duration=1.0,
                                                    size=20
                                                )
                                            )

                            if effect_applied and projectile.effect_type == "slow":
                                self.floating_texts.append(
                                    FloatingText(
                                        enemy.center_x,
                                        enemy.center_y + 20,
                                        "ЗАМЕДЛЕН!",
                                        (100, 150, 255),
                                        duration=1.0,
                                        size=20
                                    )
                                )
                            elif effect_applied and projectile.effect_type == "poison":
                                self.floating_texts.append(
                                    FloatingText(
                                        enemy.center_x,
                                        enemy.center_y + 20,
                                        "ОТРАВЛЕН!",
                                        (50, 255, 50),
                                        duration=1.0,
                                        size=20
                                    )
                                )

                if projectile in self.projectile_list:
                    self.projectile_list.remove(projectile)

        self.particle_system.update(delta_time)

        if len(self.projectile_list) > 150:
            self.projectile_list = self.projectile_list[-100:]

        if (not self.wave_active and
                self.enemies_spawned >= self.total_enemies and
                len(self.enemy_list) == 0 and
                self.wave < len(self.waves)):

            if self.wave_start_countdown <= 0:
                self.wave_start_countdown = self.auto_wave_start_delay
            else:
                self.wave_start_countdown -= delta_time

                if self.wave_start_countdown <= 0:
                    self.start_wave()
        else:
            self.wave_start_countdown = 0

        if (not self.enemy_list and
                self.enemies_spawned >= self.total_enemies and
                self.wave_active):
            self.wave_active = False
            self.wave_timer = 0
            self.enemies_spawned = 0
            self.total_enemies = 0

            if self.wave >= len(self.waves):
                self.victory = True

        if not self.wave_active and self.wave < len(self.waves):
            self.wave_timer += delta_time

    def start_wave(self):
        if self.wave < len(self.waves):
            self.wave_active = True
            self.wave_start_countdown = 0
            wave_data = self.waves[self.wave]
            self.window.sound_manager.play_sound("wave_start", volume=0.4)

            self.total_enemies = sum(wave_data.values())
            self.enemies_spawned = 0

            enemy_types = []
            for enemy_type, count in wave_data.items():
                if enemy_type == "slime":
                    enemy_types.extend([EnemyType.SLIME] * count)
                elif enemy_type == "blue_slime":
                    enemy_types.extend([EnemyType.BLUE_SLIME] * count)
                elif enemy_type == "wolf":
                    enemy_types.extend([EnemyType.WOLF] * count)
                elif enemy_type == "skeleton":
                    enemy_types.extend([EnemyType.SKELETON] * count)
                elif enemy_type == "knight":
                    enemy_types.extend([EnemyType.KNIGHT] * count)
                elif enemy_type == "golden_knight":
                    enemy_types.extend([EnemyType.GOLDEN_KNIGHT] * count)
                elif enemy_type == "necromancer":
                    enemy_types.extend([EnemyType.NECROMANCER] * count)
                elif enemy_type == "dragon":
                    enemy_types.extend([EnemyType.DRAGON] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.4)
                elif enemy_type == "giant":
                    enemy_types.extend([EnemyType.GIANT] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.4)
                elif enemy_type == "wizard":
                    enemy_types.extend([EnemyType.WIZARD] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.4)
                elif enemy_type == "demon":
                    enemy_types.extend([EnemyType.DEMON] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound("boss_spawn", volume=0.4)

            random.shuffle(enemy_types)

            for i, enemy_type in enumerate(enemy_types):
                arcade.schedule(
                    lambda dt, etype=enemy_type: self.spawn_enemy(etype),
                    i * 1.2  # Уменьшил интервал между спавном
                )

            self.wave += 1

    def spawn_enemy(self, enemy_type):
        if self.enemies_spawned < self.total_enemies:
            paths = []
            if self.map_type == MapType.MYSTIC_FOREST:
                paths = [self.path_points, self.path_points2, self.path_points3]
            elif self.map_type == MapType.HELL:
                paths = [self.path_points, self.path_points2]
            else:
                paths = [self.path_points]

            paths = [p for p in paths if len(p) > 0]

            if paths:
                path = random.choice(paths)
                start_pos = path[0] if path else None

                if path and start_pos:
                    enemy = Enemy(enemy_type, path, self.wave, self.difficulty)
                    enemy.center_x, enemy.center_y = start_pos
                    self.enemy_list.append(enemy)
                    self.enemies_spawned += 1

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_over or self.victory:
            return

        if self.wave_button_rect:
            bx, by, bw, bh = self.wave_button_rect
            if (bx <= x <= bx + bw and by <= y <= by + bh):
                if not self.wave_active and self.wave < len(self.waves):
                    self.start_wave()
                    self.window.sound_manager.play_sound("click", volume=0.25)
                return

        if self.show_upgrade_menu and self.upgrade_button_rect:
            ux, uy, uw, uh = self.upgrade_button_rect
            if (ux <= x <= ux + uw and uy <= y <= uy + uh):
                if (self.selected_tower and
                    self.selected_tower.level < self.selected_tower.max_level):
                    next_stats = self.selected_tower.get_next_upgrade_stats()
                    if next_stats and self.money >= next_stats['cost']:
                        self.money -= next_stats['cost']
                        self.selected_tower.upgrade()
                        self.window.sound_manager.play_sound("upgrade", volume=0.3)
                        self.show_upgrade_menu = False
                return
            # Обработка кнопки продажи в меню улучшения
        if self.show_upgrade_menu and hasattr(self, 'sell_button_rect') and self.sell_button_rect:
            sx, sy, sw, sh = self.sell_button_rect
            if (sx <= x <= sx + sw and sy <= y <= sy + sh):
                if self.selected_tower:
                    # Расчет стоимости продажи
                    sell_value = int(self.selected_tower.cost * 0.6)
                    for _ in range(self.selected_tower.level - 1):
                        sell_value += int(self.selected_tower.upgrade_cost * 0.6)

                    # Удаляем башню и даем деньги
                    self.tower_list.remove(self.selected_tower)
                    self.money += sell_value
                    self.window.sound_manager.play_sound("build", volume=0.3)

                    # Создаем эффект продажи
                    self.floating_texts.append(
                        FloatingText(
                            self.selected_tower.center_x,
                            self.selected_tower.center_y + 50,
                            f"+{sell_value}💰",
                            (255, 215, 0),
                            duration=1.5,
                            size=24
                        )
                    )

                    # Создаем частицы продажи
                    self.particle_system.create_explosion(
                        self.selected_tower.center_x,
                        self.selected_tower.center_y,
                        (255, 215, 0), 8
                    )

                    # Закрываем меню улучшения
                    self.show_upgrade_menu = False
                    self.selected_tower = None
                return


        for (bx, by, width, height), tower_type, name, cost, color, shape in \
                self.tower_buttons:
            if (bx - width/2 <= x <= bx + width/2 and
                    by - height/2 <= y <= by + height/2):
                self.selected_tower_type = tower_type
                self.show_upgrade_menu = False
                self.window.sound_manager.play_sound("click", volume=0.25)
                return

        if self.show_upgrade_menu and self.upgrade_menu_rect:
            mx, my, mw, mh = self.upgrade_menu_rect
            if not (mx <= x <= mx + mw and my <= y <= my + mh):
                self.show_upgrade_menu = False
                return

        if (y > self.window.height - UI_HEIGHT or
                x > self.window.width - TOWER_BUTTONS_WIDTH):
            return

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
                        self.show_upgrade_menu = True
                        self.window.sound_manager.play_sound("click", volume=0.2)
                        break

                if not occupied:
                    if len(self.tower_list) >= self.tower_limit:
                        return

                    # Получаем стоимость выбранной башни
                    temp_tower = Tower(self.selected_tower_type, 0, 0)
                    cost = temp_tower.cost

                    if self.money >= cost:
                        tower = Tower(self.selected_tower_type, sx, sy)
                        self.tower_list.append(tower)
                        self.money -= cost
                        self.window.sound_manager.play_sound("build", volume=0.3)
                        self.selected_tower = tower
                        self.show_upgrade_menu = True
                break

    def on_mouse_motion(self, x, y, dx, dy):
        if self.wave_button_rect:
            bx, by, bw, bh = self.wave_button_rect
            self.wave_button_hover = (bx <= x <= bx + bw and by <= y <= by + bh)

        self.hovered_enemy = None

        if not (y > self.window.height - UI_HEIGHT or
                x > self.window.width - TOWER_BUTTONS_WIDTH):
            for enemy in self.enemy_list:
                if enemy.alive and (abs(x - enemy.center_x) < enemy.width/2 and
                        abs(y - enemy.center_y) < enemy.height/2):
                    self.hovered_enemy = enemy
                    break

        for (bx, by, width, height), tower_type, name, cost, color, shape in \
                self.tower_buttons:
            if (bx - width/2 <= x <= bx + width/2 and
                    by - height/2 <= y <= by + height/2):
                break

        if (y > self.window.height - UI_HEIGHT or
                x > self.window.width - TOWER_BUTTONS_WIDTH):
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
                if self.victory:
                    map_name = (
                        "Волшебный лес" if self.map_type == MapType.FOREST else
                        "Крепость" if self.map_type == MapType.CITY else
                        "Пустыня" if self.map_type == MapType.HELL else
                        "Мистический лес"
                    )
                    self.window.save_manager.save_score(
                        "Игрок", self.score, 1, self.wave,
                        self.difficulty.value, map_name
                    )
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
            self.create_tower_buttons()
            self.create_wave_button()
            self.load_map()

    def save_game(self):
        data = {
            "money": self.money,
            "lives": self.lives,
            "score": self.score,
            "wave": self.wave,
            "difficulty": self.difficulty.value,
            "map_type": self.map_type.value,
            "towers": [
                (t.tower_type.value, t.center_x, t.center_y, t.level)
                for t in self.tower_list
            ]
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

        map_value = data.get("map_type", MapType.FOREST.value)
        self.map_type = MapType(map_value)

        for t_data in data.get("towers", []):
            if len(t_data) == 4:
                t_type_str, x, y, level = t_data
                try:
                    tower = Tower(TowerType(t_type_str), x, y)
                    tower.level = level
                    for _ in range(level - 1):
                        tower.upgrade()
                    self.tower_list.append(tower)
                except ValueError:
                    continue

        self.load_map()
        self.create_tower_buttons()
        self.create_wave_button()


class PauseView(arcade.View):
    def __init__(self, window, game_view):
        super().__init__()
        self.window = window
        self.game_view = game_view
        self.selected = 0
        self.options = ["ПРОДОЛЖИТЬ", "СОХРАНИТЬ ИГРУ", "В ГЛАВНОЕ МЕНЮ"]
        self.show_hints = True

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        self.game_view.on_draw()

        overlay = (0, 0, 0, 180)
        arcade.draw_lrbt_rectangle_filled(0, self.window.width, 0, self.window.height, overlay)

        arcade.draw_text(
            "ПАУЗА",
            self.window.width // 2 + 2,
            self.window.height // 2 + 98,
            (30, 40, 60),
            56,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ПАУЗА",
            self.window.width // 2,
            self.window.height // 2 + 100,
            (100, 200, 255),
            56,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        for i, text in enumerate(self.options):
            y = self.window.height // 2 - i * 60

            if i == self.selected:
                arcade.draw_lrbt_rectangle_filled(
                    self.window.width // 2 - 175,
                    self.window.width // 2 + 175,
                    y - 25,
                    y + 25,
                    UI_BUTTON_SELECTED
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.window.width // 2 - 175,
                    self.window.width // 2 + 175,
                    y - 25,
                    y + 25,
                    (255, 220, 100),
                    2
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)

            arcade.draw_text(
                text,
                self.window.width // 2 + 1, y - 1,
                (30, 40, 60), 32,
                anchor_x="center", anchor_y="center",
                bold=(i == self.selected)
            )
            arcade.draw_text(
                text,
                self.window.width // 2, y,
                color, 32,
                anchor_x="center", anchor_y="center",
                bold=(i == self.selected)
            )

        if self.show_hints:
            hints = [
                "=== ПОДСКАЗКИ ===",
                "• Клик на клетку - построить башню",
                "• Клик на башню - улучшить её",
                "• Пробел - запустить следующую волну",
                "• S - сохранить игру",
                "• F11 - переключить полный экран",
                "• ESC - пауза/меню",
                "• Наведите на врага - увидите характеристики",
                "=== НОВЫЕ БАШНИ ===",
                "• Мороз - замедляет врагов",
                "• Яд - наносит периодический урон",
                "• Бустер - усиливает соседние башни"
            ]

            hint_y = 350
            for i, hint in enumerate(hints):
                color = (255, 220, 100) if i == 0 or i == 8 else (200, 220, 255)
                size = 20 if i == 0 or i == 8 else 16

                arcade.draw_text(
                    hint,
                    self.window.width // 2 + 1, hint_y - i * 28 - 1,
                    (30, 40, 60), size,
                    anchor_x="center", anchor_y="center",
                    bold=(i == 0 or i == 8)
                )
                arcade.draw_text(
                    hint,
                    self.window.width // 2, hint_y - i * 28,
                    color, size,
                    anchor_x="center", anchor_y="center",
                    bold=(i == 0 or i == 8)
                )

        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Продолжить • H Подсказки • F11 Полный экран",
            self.window.width // 2 + 1, 99,
            (30, 40, 60), 18, anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбор • ENTER Подтвердить • ESC Продолжить • H Подсказки • F11 Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 18, anchor_x="center"
        )

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
        elif key == arcade.key.H:
            self.show_hints = not self.show_hints
            self.window.sound_manager.play_sound("click", volume=0.2)

    def select_option(self):
        self.window.sound_manager.play_sound("click", volume=0.3)

        if self.selected == 0:
            self.window.show_view(self.game_view)
        elif self.selected == 1:
            self.game_view.save_game()
            self.window.sound_manager.play_sound("build", volume=0.3)
        elif self.selected == 2:
            self.window.show_view(MenuView(self.window))

    def on_mouse_motion(self, x, y, dx, dy):
        for i in range(len(self.options)):
            item_y = self.window.height // 2 - i * 60
            if (abs(x - self.window.width // 2) < 175 and
                    abs(y - item_y) < 25):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.options)):
                item_y = self.window.height // 2 - i * 60
                if (abs(x - self.window.width // 2) < 175 and
                        abs(y - item_y) < 25):
                    self.selected = i
                    self.select_option()
                    break


class HighScoresView(arcade.View):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.scores = self.window.save_manager.load_scores()

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ТАБЛИЦА ЛИДЕРОВ",
            self.window.width // 2 + 2,
            self.window.height - 102,
            (30, 40, 60),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ТАБЛИЦА ЛИДЕРОВ",
            self.window.width // 2,
            self.window.height - 100,
            (255, 220, 100),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        arcade.draw_line(
            60, self.window.height - 150,
            self.window.width - 60, self.window.height - 150,
            (80, 100, 150), 2
        )

        headers = ["Место", "Имя", "Очки", "Сложность", "Локация", "Волна", "Дата"]
        positions = [60, 140, 220, 320, 420, 520, 650]

        for i, header in enumerate(headers):
            arcade.draw_text(
                header,
                positions[i] + 1, self.window.height - 181,
                (30, 40, 60), 16, bold=True
            )
            arcade.draw_text(
                header,
                positions[i], self.window.height - 180,
                (100, 200, 255), 16, bold=True
            )

        if not self.scores:
            arcade.draw_text(
                "Рекордов пока нет!",
                self.window.width // 2, self.window.height // 2,
                (200, 200, 200), 32,
                anchor_x="center", anchor_y="center"
            )
        else:
            for i, score in enumerate(self.scores[:10]):
                y = self.window.height - 230 - i * 40
                color = (255, 220, 100) if i == 0 else (220, 220, 255)

                diff_text = (
                    "Новичок" if score["difficulty"] == "easy" else
                    "Воин" if score["difficulty"] == "normal" else
                    "Легенда"
                )
                diff_color = (
                    (100, 255, 100) if score["difficulty"] == "easy" else
                    (255, 255, 100) if score["difficulty"] == "normal" else
                    (255, 100, 100)
                )

                texts = [
                    (str(i + 1), 60, y, color),
                    (score["name"], 140, y, color),
                    (str(score["score"]), 220, y, color),
                    (diff_text, 320, y, diff_color),
                    (score["map_name"], 420, y, color),
                    (str(score["waves"]), 520, y, color),
                    (score["date"], 650, y, color)
                ]

                for text, x, y_pos, col in texts:
                    arcade.draw_text(text, x + 1, y_pos - 1, (30, 40, 60), 14)
                    arcade.draw_text(text, x, y_pos, col, 14)

        arcade.draw_text(
            "ESC - Вернуться в главное меню • F11 Полный экран",
            self.window.width // 2 + 1, 49,
            (30, 40, 60), 18, anchor_x="center"
        )
        arcade.draw_text(
            "ESC - Вернуться в главное меню • F11 Полный экран",
            self.window.width // 2, 50,
            (180, 190, 210), 18, anchor_x="center"
        )

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
            ("ЗВУКИ", self.window.sound_manager.enabled),
            ("МУЗЫКА", self.window.sound_manager.music_player is not None)
        ]

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "НАСТРОЙКИ",
            self.window.width // 2 + 2,
            self.window.height - 102,
            (30, 40, 60),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "НАСТРОЙКИ",
            self.window.width // 2,
            self.window.height - 100,
            (100, 200, 255),
            42,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        for i, (name, value) in enumerate(self.options):
            y = self.window.height // 2 - i * 80
            status = "ВКЛЮЧЕНО" if value else "ВЫКЛЮЧЕНО"

            if i == self.selected:
                arcade.draw_lrbt_rectangle_filled(
                    self.window.width // 2 - 150,
                    self.window.width // 2 + 150,
                    y - 30,
                    y + 30,
                    UI_BUTTON_SELECTED
                )
                arcade.draw_lrbt_rectangle_outline(
                    self.window.width // 2 - 150,
                    self.window.width // 2 + 150,
                    y - 30,
                    y + 30,
                    (255, 220, 100),
                    2
                )

            color = (255, 220, 100) if i == self.selected else (220, 220, 255)

            arcade.draw_text(
                f"{name}: {status}",
                self.window.width // 2 + 1, y - 1,
                (30, 40, 60), 32,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                f"{name}: {status}",
                self.window.width // 2, y,
                color, 32,
                anchor_x="center", anchor_y="center"
            )

        arcade.draw_text(
            "↑↓ Выбор • ENTER Изменить • ESC Выход • F11 Полный экран",
            self.window.width // 2 + 1, 99,
            (30, 40, 60), 18, anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбор • ENTER Изменить • ESC Выход • F11 Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 18, anchor_x="center"
        )

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

            if name == "ЗВУКИ":
                self.window.sound_manager.enabled = not value
            elif name == "МУЗЫКА":
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