"""
Tower Defence Simulator (TDS) - Модернизированная версия
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
SCREEN_TITLE = "Tower Defence Simulator 2.0"
TILE_SIZE = 64
UI_HEIGHT = 140
TOWER_BUTTONS_WIDTH = 220
UPGRADE_MENU_WIDTH = 280

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

# Цвета врагов
SLIME_COLOR = (102, 205, 170)
ORC_COLOR = (255, 165, 0)
GOBLIN_COLOR = (144, 238, 144)
SKELETON_COLOR = (200, 200, 200)
KNIGHT_COLOR = (80, 140, 200)
TANK_COLOR = (100, 100, 120)        # Новый враг - Танк
NINJA_COLOR = (30, 30, 50)          # Новый враг - Ниндзя
BOSS_DRAGON_COLOR = (220, 20, 60)
BOSS_GIANT_COLOR = (160, 82, 45)
BOSS_WIZARD_COLOR = (138, 43, 226)
BOSS_CYBER_COLOR = (0, 255, 255)    # Новый босс - Кибер-монстр

# Цвета снарядов
SNIPER_PROJECTILE = (100, 200, 255)
ARTILLERY_PROJECTILE = (255, 165, 0)
LASER_PROJECTILE = (200, 150, 255)
ROCKET_PROJECTILE = (255, 220, 100)
TESLA_PROJECTILE = (100, 255, 220)

# Игровые константы
STARTING_MONEY_EASY = 300
STARTING_MONEY_NORMAL = 220
STARTING_MONEY_HARD = 180
STARTING_LIVES_EASY = 35
STARTING_LIVES_NORMAL = 25
STARTING_LIVES_HARD = 18
BASE_DAMAGE = 8
WAVE_AUTO_START_DELAY = 15  # Секунды до автоматического старта следующей волны

# ==================== ENUMS ====================
class TowerType(Enum):
    SNIPER = "sniper"          # Бывший лучник
    ARTILLERY = "artillery"    # Бывшая пушка
    LASER = "laser"           # Бывший маг
    ROCKET = "rocket"         # Новая башня
    TESLA = "tesla"           # Новая башня


class EnemyType(Enum):
    SLIME = "slime"
    ORC = "orc"
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    KNIGHT = "knight"
    TANK = "tank"             # Новый враг
    NINJA = "ninja"           # Новый враг
    BOSS_DRAGON = "boss_dragon"
    BOSS_GIANT = "boss_giant"
    BOSS_WIZARD = "boss_wizard"
    BOSS_CYBER = "boss_cyber"  # Новый босс


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class MapType(Enum):
    FOREST = "forest"
    CITY = "city"
    HELL = "hell"
    CYBER = "cyber"  # Новая карта


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
        self.velocity_y = 1.5  # Скорость всплывания

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
        self.max_particles = 200

    def create_explosion(self, x, y, color=None, count=8):
        if len(self.particles) > self.max_particles - 20:
            return

        color = color or (255, 165, 0)
        for _ in range(min(count, 10)):
            self.particles.append({
                'x': x, 'y': y,
                'dx': random.uniform(-2, 2),
                'dy': random.uniform(-2, 2),
                'size': random.uniform(1.5, 4),
                'color': color,
                'life': random.uniform(0.3, 1.0),
                'max_life': random.uniform(0.3, 1.0)
            })

    def create_trail(self, x, y, color=None):
        if len(self.particles) > self.max_particles - 5:
            return

        color = color or (200, 200, 200)
        if random.random() > 0.7:
            self.particles.append({
                'x': x, 'y': y,
                'dx': random.uniform(-0.5, 0.5),
                'dy': random.uniform(-0.5, 0.5),
                'size': random.uniform(0.8, 2),
                'color': color,
                'life': random.uniform(0.15, 0.3),
                'max_life': random.uniform(0.15, 0.3)
            })

    def create_chain_lightning(self, points, color):
        if len(self.particles) > self.max_particles - 20:
            return

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            segments = max(3, int(distance / 5))

            for j in range(segments):
                t = j / segments
                offset_x = random.uniform(-5, 5)
                offset_y = random.uniform(-5, 5)
                px = x1 + (x2 - x1) * t + offset_x
                py = y1 + (y2 - y1) * t + offset_y

                self.particles.append({
                    'x': px, 'y': py,
                    'dx': 0, 'dy': 0,
                    'size': random.uniform(1, 3),
                    'color': color,
                    'life': random.uniform(0.1, 0.2),
                    'max_life': random.uniform(0.1, 0.2)
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
    def __init__(self, x, y, target, damage, speed=8.0, color=(255, 255, 255),
                 scale=0.5, shape="circle", homing=True, aoe_radius=0,
                 is_critical=False):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.color = color
        self.scale = scale
        self.shape = shape
        self.homing = homing
        self.homing_strength = 0.1
        self.aoe_radius = aoe_radius
        self.penetration = 1
        self.is_critical = is_critical  # Флаг критического удара

        if shape == "circle":
            self.texture = arcade.make_circle_texture(10, color)
        elif shape == "triangle":
            self.texture = arcade.make_soft_circle_texture(
                10, color, center_alpha=255, outer_alpha=0
            )
        elif shape == "rocket":
            self.texture = arcade.make_soft_square_texture(
                12, color, center_alpha=255, outer_alpha=0
            )
        else:
            self.texture = arcade.make_soft_square_texture(
                10, color, center_alpha=255, outer_alpha=0
            )

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
        if self.shape == "rocket":
            self.angle += 15
        else:
            self.angle += 8


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

        difficulty_multiplier = {
            Difficulty.EASY: 1.3,
            Difficulty.NORMAL: 1.8,
            Difficulty.HARD: 2.5
        }
        multiplier = difficulty_multiplier[difficulty]

        enemy_stats = {
            EnemyType.SLIME: {
                'color': SLIME_COLOR,
                'health': (120 + level * 25) * multiplier,
                'speed': 0.9,
                'bounty': (12 + level * 2) * 0.7,
                'scale': 0.8,
                'size': 22
            },
            EnemyType.ORC: {
                'color': ORC_COLOR,
                'health': (220 + level * 35) * multiplier,
                'speed': 0.7,
                'bounty': (18 + level * 4) * 0.8,
                'scale': 0.9,
                'size': 26
            },
            EnemyType.GOBLIN: {
                'color': GOBLIN_COLOR,
                'health': (75 + level * 15) * multiplier,
                'speed': 1.4,
                'bounty': (14 + level * 2) * 0.6,
                'scale': 0.7,
                'size': 20
            },
            EnemyType.SKELETON: {
                'color': SKELETON_COLOR,
                'health': (270 + level * 40) * multiplier,
                'speed': 1.0,
                'bounty': (25 + level * 5) * 0.9,
                'scale': 0.85,
                'size': 24
            },
            EnemyType.KNIGHT: {
                'color': KNIGHT_COLOR,
                'health': (420 + level * 60) * multiplier,
                'speed': 0.6,
                'bounty': (35 + level * 7) * 1.0,
                'scale': 1.0,
                'size': 30
            },
            EnemyType.TANK: {
                'color': TANK_COLOR,
                'health': (500 + level * 80) * multiplier,
                'speed': 0.4,
                'bounty': (40 + level * 8) * 1.1,
                'scale': 1.1,
                'size': 35,
                'armor': 0.3
            },
            EnemyType.NINJA: {
                'color': NINJA_COLOR,
                'health': (90 + level * 20) * multiplier,
                'speed': 1.8,
                'bounty': (20 + level * 3) * 0.9,
                'scale': 0.75,
                'size': 18,
                'evasion': 0.2
            },
            EnemyType.BOSS_DRAGON: {
                'color': BOSS_DRAGON_COLOR,
                'health': (2200 + level * 250) * multiplier,
                'speed': 0.45,
                'bounty': (250 + level * 30) * 1.2,
                'scale': 1.5,
                'size': 50
            },
            EnemyType.BOSS_GIANT: {
                'color': BOSS_GIANT_COLOR,
                'health': (3000 + level * 350) * multiplier,
                'speed': 0.35,
                'bounty': (300 + level * 35) * 1.3,
                'scale': 1.7,
                'size': 55
            },
            EnemyType.BOSS_WIZARD: {
                'color': BOSS_WIZARD_COLOR,
                'health': (1600 + level * 180) * multiplier,
                'speed': 0.55,
                'bounty': (220 + level * 25) * 1.1,
                'scale': 1.4,
                'size': 45
            },
            EnemyType.BOSS_CYBER: {
                'color': BOSS_CYBER_COLOR,
                'health': (2800 + level * 300) * multiplier,
                'speed': 0.5,
                'bounty': (320 + level * 40) * 1.4,
                'scale': 1.6,
                'size': 52
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
        texture_size = stats['size']

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

    def take_damage(self, damage, is_critical=False):
        """
        Наносит урон врагу.
        Возвращает кортеж: (умер ли враг, был ли удар критическим)
        """
        if random.random() < self.evasion:
            return False, is_critical

        actual_damage = damage * (1 - self.armor)
        self.health -= actual_damage
        if self.health <= 0:
            self.alive = False
            return True, is_critical
        return False, is_critical

    def draw_health_bar(self):
        if self.health < self.max_health:
            is_boss = self.enemy_type.value.startswith('boss')
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

    def get_name(self):
        """Возвращает русское название врага"""
        names = {
            EnemyType.SLIME: "Слизень",
            EnemyType.ORC: "Орк",
            EnemyType.GOBLIN: "Гоблин",
            EnemyType.SKELETON: "Скелет",
            EnemyType.KNIGHT: "Рыцарь",
            EnemyType.TANK: "Танк",
            EnemyType.NINJA: "Ниндзя",
            EnemyType.BOSS_DRAGON: "Дракон",
            EnemyType.BOSS_GIANT: "Гигант",
            EnemyType.BOSS_WIZARD: "Волшебник",
            EnemyType.BOSS_CYBER: "Кибер-монстр"
        }
        return names.get(self.enemy_type, "Враг")


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

        if tower_type == TowerType.SNIPER:
            self.color = SNIPER_COLOR
            self.base_damage = 25
            self.base_range = 280
            self.base_fire_rate = 1.2
            self.cost = 160
            self.projectile_speed = 16.0
            self.projectile_color = SNIPER_PROJECTILE
            self.projectile_shape = "triangle"
            self.shape = "triangle"
            self.upgrade_cost = 80
            self.special_ability = "crit_chance"
            self.crit_chance = 0.15
            self.crit_multiplier = 2.0

        elif tower_type == TowerType.ARTILLERY:
            self.color = ARTILLERY_COLOR
            self.base_damage = 50
            self.base_range = 220
            self.base_fire_rate = 0.8
            self.cost = 320
            self.projectile_speed = 9.0
            self.projectile_color = ARTILLERY_PROJECTILE
            self.projectile_shape = "square"
            self.shape = "square"
            self.upgrade_cost = 160
            self.special_ability = "splash_damage"
            self.splash_radius = 60
            self.splash_damage_percent = 0.5

        elif tower_type == TowerType.LASER:
            self.color = LASER_COLOR
            self.base_damage = 18
            self.base_range = 240
            self.base_fire_rate = 2.5
            self.cost = 240
            self.projectile_speed = 12.0
            self.projectile_color = LASER_PROJECTILE
            self.projectile_shape = "circle"
            self.shape = "circle"
            self.upgrade_cost = 120
            self.special_ability = "chain_lightning"
            self.chain_targets = 3
            self.chain_damage_reduction = 0.7

        elif tower_type == TowerType.ROCKET:
            self.color = ROCKET_COLOR
            self.base_damage = 35
            self.base_range = 200
            self.base_fire_rate = 1.5
            self.cost = 280
            self.projectile_speed = 7.0
            self.projectile_color = ROCKET_PROJECTILE
            self.projectile_shape = "rocket"
            self.shape = "rocket"
            self.upgrade_cost = 140
            self.special_ability = "homing_missiles"
            self.missile_count = 2
            self.homing_strength = 0.15

        elif tower_type == TowerType.TESLA:
            self.color = TESLA_COLOR
            self.base_damage = 12
            self.base_range = 180
            self.base_fire_rate = 3.0
            self.cost = 300
            self.projectile_speed = 20.0
            self.projectile_color = TESLA_PROJECTILE
            self.projectile_shape = "lightning"
            self.shape = "lightning"
            self.upgrade_cost = 150
            self.special_ability = "tesla_coil"
            self.max_targets = 4
            self.damage_reduction = 0.8

        self.damage = self.base_damage
        self.range = self.base_range
        self.fire_rate = self.base_fire_rate
        self.scale = 1.0

    def find_target(self, enemies):
        if self.tower_type == TowerType.TESLA and self.level >= 2:
            return self.find_multiple_targets(enemies)

        closest = None
        closest_distance = self.range

        for enemy in enemies:
            if not enemy.alive or enemy.health <= 0:
                continue
            distance = math.sqrt(
                (self.center_x - enemy.center_x)**2 +
                (self.center_y - enemy.center_y)**2
            )
            if distance < closest_distance:
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
        return self.fire_timer >= 1.0 / self.fire_rate

    def update(self, delta_time, enemies, projectiles, sound_manager,
               particle_system):
        self.fire_timer += delta_time

        if self.tower_type == TowerType.TESLA:
            if self.can_attack():
                self.attack_tesla(projectiles, sound_manager, particle_system, enemies)
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
                self.attack(projectiles, sound_manager, particle_system)
                self.fire_timer = 0

    def attack(self, projectiles, sound_manager, particle_system):
        if self.tower_type == TowerType.ROCKET and self.level >= 2:
            for _ in range(self.missile_count):
                self.create_projectile(projectiles, sound_manager, particle_system)
        else:
            self.create_projectile(projectiles, sound_manager, particle_system)

    def create_projectile(self, projectiles, sound_manager, particle_system):
        actual_damage = self.damage
        is_critical = False

        if self.tower_type == TowerType.SNIPER and random.random() < self.crit_chance:
            actual_damage *= self.crit_multiplier
            is_critical = True  # Устанавливаем флаг критического удара

        projectile = Projectile(
            self.center_x, self.center_y,
            self.target, actual_damage,
            self.projectile_speed, self.projectile_color,
            0.8, self.projectile_shape,
            self.tower_type == TowerType.ROCKET,
            self.splash_radius if self.tower_type == TowerType.ARTILLERY else 0,
            is_critical=is_critical  # Передаем флаг критического удара
        )

        if self.tower_type == TowerType.ROCKET:
            projectile.homing_strength = self.homing_strength

        projectiles.append(projectile)

        sound_map = {
            TowerType.SNIPER: "shoot",
            TowerType.ARTILLERY: "explosion",
            TowerType.LASER: "magic",
            TowerType.ROCKET: "explosion",
            TowerType.TESLA: "magic"
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
                particle_system.create_explosion(
                    muzzle_x, muzzle_y, self.projectile_color, 4
                )
            else:
                particle_system.create_explosion(
                    muzzle_x, muzzle_y, self.projectile_color, 6
                )

    def attack_tesla(self, projectiles, sound_manager, particle_system, enemies):
        targets = self.find_multiple_targets(enemies)
        if not targets:
            return

        for target in targets:
            damage = self.damage * (self.damage_reduction ** (targets.index(target)))
            died, _ = target.take_damage(damage)

        sound_manager.play_sound("magic", volume=0.3)

    def draw(self):
        if self.shape == "triangle":
            points = [
                (self.center_x, self.center_y + 32),
                (self.center_x - 26, self.center_y - 20),
                (self.center_x + 26, self.center_y - 20)
            ]
            arcade.draw_polygon_filled(points, self.color)
            arcade.draw_polygon_outline(points, (255, 255, 255), 3)

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
            arcade.draw_polygon_outline(points, (255, 255, 255), 3)

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
                self.center_x, self.center_y, 32, (255, 255, 255), 3
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

            for i in range(self.missile_count):
                offset = (i - (self.missile_count - 1) / 2) * 20
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
                2: 1.5,
                3: 2.2,
                4: 3.0
            }

            multiplier = upgrade_multipliers[self.level]
            self.damage = int(self.base_damage * multiplier)
            self.range = int(self.base_range * (1.2 ** (self.level - 1)))
            self.fire_rate = self.base_fire_rate * (1.25 ** (self.level - 1))
            self.upgrade_cost = int(self.upgrade_cost * 1.6)

            if self.tower_type == TowerType.SNIPER:
                self.crit_chance = 0.15 + (self.level - 1) * 0.05
                self.crit_multiplier = 2.0 + (self.level - 1) * 0.5

            elif self.tower_type == TowerType.ARTILLERY:
                self.splash_radius = 60 + (self.level - 1) * 20
                self.splash_damage_percent = 0.5 + (self.level - 1) * 0.1

            elif self.tower_type == TowerType.LASER:
                self.chain_targets = 3 + (self.level - 1)

            elif self.tower_type == TowerType.ROCKET:
                self.missile_count = 2 + (self.level - 1)
                self.homing_strength = 0.15 + (self.level - 1) * 0.05

            elif self.tower_type == TowerType.TESLA:
                self.max_targets = 4 + (self.level - 1) * 2

            return self.upgrade_cost
        return 0

    def get_next_upgrade_stats(self):
        if self.level < self.max_level:
            next_level = self.level + 1
            multiplier = {
                2: 1.5, 3: 2.2, 4: 3.0
            }.get(next_level, 1.0)

            next_damage = int(self.base_damage * multiplier)
            next_range = int(self.base_range * (1.2 ** (next_level - 1)))
            next_fire_rate = self.base_fire_rate * (1.25 ** (next_level - 1))

            return {
                'damage': next_damage,
                'range': next_range,
                'fire_rate': next_fire_rate,
                'cost': int(self.upgrade_cost * 1.6)
            }
        return None

    def get_tower_name(self):
        names = {
            TowerType.SNIPER: "Снайпер",
            TowerType.ARTILLERY: "Артиллерия",
            TowerType.LASER: "Лазерная",
            TowerType.ROCKET: "Ракетная",
            TowerType.TESLA: "Тесла"
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
            self.sounds["shoot"] = arcade.load_sound(
                ":resources:sounds/laser1.wav"
            )
            self.sounds["explosion"] = arcade.load_sound(
                ":resources:sounds/explosion2.wav"
            )
            self.sounds["build"] = arcade.load_sound(
                ":resources:sounds/coin1.wav"
            )
            self.sounds["upgrade"] = arcade.load_sound(
                ":resources:sounds/upgrade1.wav"
            )
            self.sounds["enemy_die"] = arcade.load_sound(
                ":resources:sounds/hit3.wav"
            )
            self.sounds["click"] = arcade.load_sound(
                ":resources:sounds/coin1.wav"
            )
            self.sounds["magic"] = arcade.load_sound(
                ":resources:sounds/upgrade4.wav"
            )
            self.sounds["wave_start"] = arcade.load_sound(
                ":resources:sounds/upgrade5.wav"
            )
            self.sounds["lose_life"] = arcade.load_sound(
                ":resources:sounds/error2.wav"
            )
            self.sounds["boss_spawn"] = arcade.load_sound(
                ":resources:sounds/rockHit2.wav"
            )

            self.music["menu"] = arcade.load_sound(
                ":resources:music/funkyrobot.mp3"
            )
            self.music["game"] = arcade.load_sound(
                ":resources:music/1918.mp3"
            )
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
        self.music_player = self.music[music_name].play(
            volume=vol, loop=True
        )

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
            with open(self.scores_file, 'a', newline='',
                      encoding='utf-8') as f:
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
            "НОВАЯ ИГРА", "ПРОДОЛЖИТЬ", "РЕКОРДЫ", "НАСТРОЙКИ", "ВЫХОД"
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
            "Tower Defence Simulator 2.0",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "Tower Defence Simulator 2.0",
            self.window.width // 2,
            self.window.height - 150,
            title_color,
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        arcade.draw_text(
            "Защити свою базу от врагов!",
            self.window.width // 2 + 1,
            self.window.height - 221,
            (30, 40, 60),
            24,
            anchor_x="center",
            anchor_y="center"
        )
        arcade.draw_text(
            "Защити свою базу от врагов!",
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
            "↑↓ Выбрать • ENTER Подтвердить • ESC Выход • F11: Полный экран",
            self.window.width // 2 + 1,
            49,
            (30, 40, 60),
            18,
            anchor_x="center",
            anchor_y="center"
        )
        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Выход • F11: Полный экран",
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
        self.difficulties = ["ЛЁГКИЙ", "СРЕДНИЙ", "СЛОЖНЫЙ"]
        self.difficulty_descriptions = [
            "Больше жизней и денег, враги слабее",
            "Стандартные настройки",
            "Меньше жизней и денег, враги сильнее"
        ]

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ СЛОЖНОСТЬ",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ВЫБЕРИТЕ СЛОЖНОСТЬ",
            self.window.width // 2,
            self.window.height - 150,
            (100, 200, 255),
            48,
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
            desc_color = (
                (180, 190, 210) if i == self.selected else (150, 160, 180)
            )

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
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2 + 1,
            99,
            (30, 40, 60),
            20,
            anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
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
            if (abs(x - self.window.width // 2) < 200 and
                    abs(y - item_y) < 40):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.difficulties)):
                item_y = self.window.height // 2 - i * 120
                if (abs(x - self.window.width // 2) < 200 and
                        abs(y - item_y) < 40):
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.3)
                    difficulty_map = {
                        0: Difficulty.EASY,
                        1: Difficulty.NORMAL,
                        2: Difficulty.HARD
                    }
                    difficulty = difficulty_map[self.selected]
                    self.window.show_view(
                        MapSelectionView(self.window, difficulty)
                    )
                    break


class MapSelectionView(arcade.View):
    def __init__(self, window, difficulty):
        super().__init__()
        self.window = window
        self.difficulty = difficulty
        self.selected = 0
        self.maps = ["ЛЕС (Forest)", "ГОРОД (City)", "АД (Hell)", "КИБЕР (Cyber)"]
        self.map_descriptions = [
            "Зеленая тема, коричневые тропинки",
            "Серая тема, асфальтовые дороги",
            "Красная тема, огненные дороги",
            "Синяя тема, неоновые дороги"
        ]

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "ВЫБЕРИТЕ КАРТУ",
            self.window.width // 2 + 2,
            self.window.height - 152,
            (30, 40, 60),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ВЫБЕРИТЕ КАРТУ",
            self.window.width // 2,
            self.window.height - 150,
            (100, 200, 255),
            48,
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
            desc_color = (
                (180, 190, 210) if i == self.selected else (150, 160, 180)
            )

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
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
            self.window.width // 2 + 1,
            99,
            (30, 40, 60),
            20,
            anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбрать • ENTER Подтвердить • ESC Назад • F11: Полный экран",
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
                3: MapType.CYBER
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
            if (abs(x - self.window.width // 2) < 225 and
                    abs(y - item_y) < 40):
                if self.selected != i:
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.1)
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            for i in range(len(self.maps)):
                item_y = self.window.height // 2 - i * 120
                if (abs(x - self.window.width // 2) < 225 and
                        abs(y - item_y) < 40):
                    self.selected = i
                    self.window.sound_manager.play_sound("click", volume=0.3)
                    map_map = {
                        0: MapType.FOREST,
                        1: MapType.CITY,
                        2: MapType.HELL,
                        3: MapType.CYBER
                    }
                    selected_map = map_map[self.selected]
                    game_view = GameView(
                        self.window, self.difficulty, selected_map
                    )
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

        self.enemy_list = arcade.SpriteList()
        self.tower_list = []
        self.projectile_list = arcade.SpriteList()
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
        self.start_positions = []
        self.end_pos = None

        self.showing_range = None
        self.selected_tower = None
        self.game_over = False
        self.victory = False
        self.show_upgrade_menu = False
        self.upgrade_menu_rect = None
        self.upgrade_button_rect = None

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

        # Новые переменные для дополнительных функций
        self.floating_texts = []  # Для всплывающего текста "Крит"
        self.hovered_enemy = None  # Для отслеживания наведения на врага
        self.auto_wave_start_delay = WAVE_AUTO_START_DELAY  # Задержка автозапуска волны
        self.wave_start_countdown = 0  # Таймер до автозапуска

    def generate_waves(self):
        base_waves = [
            {"slime": 15, "orc": 0, "goblin": 5, "skeleton": 0, "knight": 0,
             "tank": 0, "ninja": 3, "boss_dragon": 0, "boss_giant": 0,
             "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 20, "orc": 8, "goblin": 10, "skeleton": 0, "knight": 0,
             "tank": 2, "ninja": 5, "boss_dragon": 0, "boss_giant": 0,
             "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 25, "orc": 12, "goblin": 15, "skeleton": 5, "knight": 0,
             "tank": 3, "ninja": 8, "boss_dragon": 0, "boss_giant": 0,
             "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 30, "orc": 15, "goblin": 18, "skeleton": 8, "knight": 2,
             "tank": 5, "ninja": 10, "boss_dragon": 0, "boss_giant": 0,
             "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 25, "orc": 18, "goblin": 20, "skeleton": 12,
             "knight": 4, "tank": 6, "ninja": 12, "boss_dragon": 0,
             "boss_giant": 0, "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 30, "orc": 20, "goblin": 25, "skeleton": 15,
             "knight": 6, "tank": 8, "ninja": 15, "boss_dragon": 1,
             "boss_giant": 0, "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 35, "orc": 22, "goblin": 28, "skeleton": 18,
             "knight": 8, "tank": 10, "ninja": 18, "boss_dragon": 0,
             "boss_giant": 1, "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 40, "orc": 25, "goblin": 35, "skeleton": 22,
             "knight": 10, "tank": 12, "ninja": 20, "boss_dragon": 0,
             "boss_giant": 0, "boss_wizard": 1, "boss_cyber": 0},
            {"slime": 45, "orc": 28, "goblin": 38, "skeleton": 25,
             "knight": 12, "tank": 15, "ninja": 22, "boss_dragon": 1,
             "boss_giant": 1, "boss_wizard": 0, "boss_cyber": 0},
            {"slime": 50, "orc": 32, "goblin": 45, "skeleton": 28,
             "knight": 15, "tank": 18, "ninja": 25, "boss_dragon": 1,
             "boss_giant": 0, "boss_wizard": 1, "boss_cyber": 0},
            {"slime": 55, "orc": 35, "goblin": 48, "skeleton": 30,
             "knight": 18, "tank": 20, "ninja": 28, "boss_dragon": 0,
             "boss_giant": 1, "boss_wizard": 1, "boss_cyber": 0},
            {"slime": 60, "orc": 40, "goblin": 55, "skeleton": 35,
             "knight": 22, "tank": 22, "ninja": 30, "boss_dragon": 2,
             "boss_giant": 0, "boss_wizard": 1, "boss_cyber": 1},
            {"slime": 65, "orc": 45, "goblin": 60, "skeleton": 40,
             "knight": 25, "tank": 25, "ninja": 32, "boss_dragon": 1,
             "boss_giant": 2, "boss_wizard": 1, "boss_cyber": 1},
            {"slime": 70, "orc": 50, "goblin": 65, "skeleton": 45,
             "knight": 28, "tank": 28, "ninja": 35, "boss_dragon": 2,
             "boss_giant": 2, "boss_wizard": 2, "boss_cyber": 1},
        ]

        if self.difficulty == Difficulty.EASY:
            for wave in base_waves:
                for key in wave:
                    if key.startswith("boss"):
                        wave[key] = max(0, wave[key] - 1)
                    elif wave[key] > 0:
                        wave[key] = int(wave[key] * 0.7)
        elif self.difficulty == Difficulty.HARD:
            for wave in base_waves:
                for key in wave:
                    if wave[key] > 0:
                        wave[key] = int(wave[key] * 2.0)

        return base_waves

    def setup(self):
        self.load_map()
        self.window.sound_manager.play_music("game")
        self.create_tower_buttons()
        self.create_wave_button()

    def create_tower_buttons(self):
        self.tower_buttons = []
        tower_data = [
            (TowerType.SNIPER, "Снайпер", "160💰", SNIPER_COLOR, "triangle"),
            (TowerType.ARTILLERY, "Артиллерия", "320💰", ARTILLERY_COLOR, "square"),
            (TowerType.LASER, "Лазерная", "240💰", LASER_COLOR, "circle"),
            (TowerType.ROCKET, "Ракетная", "280💰", ROCKET_COLOR, "rocket"),
            (TowerType.TESLA, "Тесла", "300💰", TESLA_COLOR, "lightning")
        ]

        button_width = 180
        button_height = 80
        start_x = self.window.width - TOWER_BUTTONS_WIDTH + 20
        start_y = self.window.height - UI_HEIGHT - 150

        for i, (tower_type, name, cost, color, shape) in enumerate(tower_data):
            button_y = start_y - i * (button_height + 20)
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
        else:  # CYBER
            level_map = [
                "T T T E T T T T T T T T T T T T T T T T",
                "T T T # T T T T T T T T T T T T T T T T",
                "T T T # T T T T T T T T T T T T T T T T",
                "T T T # # # # # # # T T T T T T T T T T",
                "T T T T T T T T T # T T T T T T T T T T",
                "T T T T T T # # # # # # # T T T T T T T",
                "T T T T T T # T T T T T # T T T T T T T",
                "T T # # # # # T T T T T # T T T T T T T",
                "T T # T T T T T T T T T # T T T T T T T",
                "T T # T T T T T T T T T # # # # # T T T",
                "T T # T T T T T T T T T T T T T # T T T",
                "T T # # # # # # # T T T T T T T # T T T",
                "T T T T T T T T # T T T T T T T # T T T",
                "T T T T T T T T # # # # # # # # # T T T",
                "T T T T T T T T T T T T T T T T T # # S"
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

        if self.map_type == MapType.HELL and len(self.start_positions) >= 2:
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
        else:  # CYBER
            bg_color = (20, 25, 40)
            path_color = (0, 255, 255)

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
                arcade.draw_line(x1, y1, x2, y2, (255, 140, 0),
                                 TILE_SIZE - 10)

        if self.start_positions:
            for i, (x, y) in enumerate(self.start_positions):
                start_x = x * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_x
                start_y = y * TILE_SIZE + TILE_SIZE // 2 + self.map_offset_y
                arcade.draw_circle_filled(
                    start_x, start_y, TILE_SIZE // 2, (100, 200, 100)
                )
                arcade.draw_text(
                    f"СТАРТ {i+1}", start_x, start_y,
                    (240, 240, 240), 12,
                    anchor_x="center", anchor_y="center"
                )

        if self.end_pos:
            end_x, end_y = self.end_pos[2], self.end_pos[3]
            self.base_pulse += self.base_pulse_dir * 0.1
            if self.base_pulse > 1.0 or self.base_pulse < 0.5:
                self.base_pulse_dir *= -1

            pulse_size = TILE_SIZE // 2 * (0.8 + 0.2 * self.base_pulse)
            arcade.draw_circle_filled(end_x, end_y, pulse_size,
                                      (200, 100, 100))
            arcade.draw_text(
                "БАЗА", end_x, end_y, (240, 240, 240), 12,
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

        if len(self.projectile_list) < 100:
            self.projectile_list.draw()

        self.enemy_list.draw()

        for tower in self.tower_list:
            tower.draw()

        self.particle_system.draw()

        for enemy in self.enemy_list:
            enemy.draw_health_bar()

        if self.showing_range:
            self.showing_range.draw_range()

        # Отрисовка всплывающего текста
        for text in self.floating_texts:
            text.draw()

        # Отрисовка информации о враге при наведении
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
            "Лёгкий" if self.difficulty == Difficulty.EASY else
            "Средний" if self.difficulty == Difficulty.NORMAL else
            "Сложный"
        )
        diff_color = (
            (100, 255, 100) if self.difficulty == Difficulty.EASY else
            (255, 255, 100) if self.difficulty == Difficulty.NORMAL else
            (255, 100, 100)
        )

        map_text = (
            "Лес" if self.map_type == MapType.FOREST else
            "Город" if self.map_type == MapType.CITY else
            "Ад" if self.map_type == MapType.HELL else
            "Кибер"
        )

        arcade.draw_text(
            f"💰: {self.money}", 101, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"💰: {self.money}", 100, self.window.height - 50,
            (255, 215, 0), 28, anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"❤️: {self.lives}", 301, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"❤️: {self.lives}", 300, self.window.height - 50,
            (255, 100, 100), 28, anchor_x="center", anchor_y="center", bold=True
        )

        arcade.draw_text(
            f"Очки: {self.score}", 501, self.window.height - 51,
            TEXT_SHADOW, 28, anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Очки: {self.score}", 500, self.window.height - 50,
            TEXT_COLOR, 28, anchor_x="center", anchor_y="center", bold=True
        )

        if self.wave_button_rect:
            bx, by, bw, bh = self.wave_button_rect
            button_color = (UI_BUTTON_SELECTED if self.wave_button_hover
                           else UI_BUTTON_NORMAL)

            if not self.wave_active and self.wave < len(self.waves):
                if self.wave_start_countdown > 0:
                    button_text = f"АВТО: {int(self.wave_start_countdown)}"
                    text_color = (255, 200, 100)
                else:
                    button_text = "СТАРТ ВОЛНЫ"
                    text_color = (255, 220, 100)
            else:
                button_text = "ВОЛНА ИДЁТ"
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
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center", bold=True
            )

            arcade.draw_text(
                button_text,
                bx + bw//2, by + bh//2,
                text_color, 24,
                anchor_x="center", anchor_y="center", bold=True
            )

            wave_info = f"Волна: {self.wave + 1}/{len(self.waves)}"
            arcade.draw_text(
                wave_info,
                bx + bw//2 + 1, by - 35,
                TEXT_SHADOW, 22,
                anchor_x="center", anchor_y="center", bold=True
            )

            arcade.draw_text(
                wave_info,
                bx + bw//2, by - 36,
                TEXT_COLOR, 22,
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
            else:
                arcade.draw_circle_filled(icon_x, icon_y, 18, color)
                arcade.draw_circle_outline(icon_x, icon_y, 18,
                                           (255, 255, 255), 2)

            arcade.draw_text(
                name,
                x - width / 2 + 75, y + 15,
                TEXT_COLOR, 20,
                anchor_x="left", anchor_y="center",
                bold=(tower_type == self.selected_tower_type)
            )

            arcade.draw_text(
                cost,
                x - width / 2 + 75, y - 15,
                (255, 215, 0), 18,
                anchor_x="left", anchor_y="center"
            )

        if self.show_upgrade_menu and self.selected_tower:
            self.draw_upgrade_menu()

        if self.game_over:
            arcade.draw_text(
                "ИГРА ОКОНЧЕНА!",
                self.window.width // 2 + 2, self.window.height // 2 - 2,
                TEXT_SHADOW, 48,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                "ИГРА ОКОНЧЕНА!",
                self.window.width // 2, self.window.height // 2,
                (255, 100, 100), 48,
                anchor_x="center", anchor_y="center", bold=True
            )

            arcade.draw_text(
                "Нажмите ESC для выхода в меню",
                self.window.width // 2 + 1, self.window.height // 2 - 61,
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "Нажмите ESC для выхода в меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )

        elif self.victory:
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
                "Нажмите ESC для выхода в меню",
                self.window.width // 2 + 1, self.window.height // 2 - 61,
                TEXT_SHADOW, 24,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "Нажмите ESC для выхода в меню",
                self.window.width // 2, self.window.height // 2 - 60,
                TEXT_COLOR, 24,
                anchor_x="center", anchor_y="center"
            )

        arcade.draw_text(
            ("Выберите башню справа и кликните на клетку для постройки • "
             "ESC: пауза • F11: Полный экран"),
            self.window.width // 2 + 1, 39,
            TEXT_SHADOW, 18, anchor_x="center"
        )
        arcade.draw_text(
            ("Выберите башню справа и кликните на клетку для постройки • "
             "ESC: пауза • F11: Полный экран"),
            self.window.width // 2, 40,
            (180, 190, 210), 18, anchor_x="center", bold=True
        )

    def draw_enemy_info(self, enemy):
        """Отрисовывает информацию о враге при наведении мыши"""
        info_x = enemy.center_x
        info_y = enemy.center_y + 60  # Над врагом
        width = 180
        height = 80

        # Фон
        arcade.draw_lrbt_rectangle_filled(
            info_x - width // 2,
            info_x + width // 2,
            info_y - height // 2,
            info_y + height // 2,
            (0, 0, 0, 200)
        )

        # Рамка
        arcade.draw_lrbt_rectangle_outline(
            info_x - width // 2,
            info_x + width // 2,
            info_y - height // 2,
            info_y + height // 2,
            (255, 255, 255),
            2
        )

        # Имя врага
        enemy_name = enemy.get_name()
        arcade.draw_text(
            enemy_name,
            info_x, info_y + 20,
            (255, 255, 255), 20,
            anchor_x="center", anchor_y="center", bold=True
        )

        # Уровень
        arcade.draw_text(
            f"Уровень: {enemy.level}",
            info_x, info_y - 5,
            (200, 200, 255), 16,
            anchor_x="center", anchor_y="center"
        )

        # Здоровье
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

        # Награда
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
        menu_y = UI_HEIGHT + 250
        menu_width = UPGRADE_MENU_WIDTH - 50
        menu_height = 240

        self.upgrade_menu_rect = (menu_x, menu_y - menu_height,
                                  menu_width, menu_height)

        arcade.draw_lrbt_rectangle_filled(
            menu_x,
            menu_x + menu_width,
            menu_y - menu_height,
            menu_y,
            UI_BACKGROUND
        )

        arcade.draw_lrbt_rectangle_outline(
            menu_x,
            menu_x + menu_width,
            menu_y - menu_height,
            menu_y,
            (255, 220, 100),
            3
        )

        tower_name = self.selected_tower.get_tower_name()
        arcade.draw_text(
            f"Улучшение: {tower_name}",
            menu_x + menu_width//2 + 1, menu_y - 25,
            TEXT_SHADOW, 20,
            anchor_x="center", anchor_y="center", bold=True
        )
        arcade.draw_text(
            f"Улучшение: {tower_name}",
            menu_x + menu_width//2, menu_y - 26,
            (255, 220, 100), 20,
            anchor_x="center", anchor_y="center", bold=True
        )

        level_text = (f"Уровень: {self.selected_tower.level}/"
                      f"{self.selected_tower.max_level}")
        arcade.draw_text(
            level_text,
            menu_x + menu_width//2 + 1, menu_y - 50,
            TEXT_SHADOW, 16,
            anchor_x="center", anchor_y="center"
        )
        arcade.draw_text(
            level_text,
            menu_x + menu_width//2, menu_y - 51,
            TEXT_COLOR, 16,
            anchor_x="center", anchor_y="center"
        )

        stats_y = menu_y - 75
        stats = [
            f"Урон: {self.selected_tower.damage}",
            f"Дальность: {int(self.selected_tower.range)}",
            f"Скорость: {self.selected_tower.fire_rate:.1f}/сек"
        ]

        for i, stat in enumerate(stats):
            arcade.draw_text(
                stat,
                menu_x + 15, stats_y - i * 22,
                TEXT_COLOR, 14,
                anchor_x="left", anchor_y="center"
            )

        if self.selected_tower.level < self.selected_tower.max_level:
            next_stats = self.selected_tower.get_next_upgrade_stats()
            if next_stats:
                upgrade_cost = next_stats['cost']
                button_x = menu_x + menu_width//2
                button_y = menu_y - 155
                button_width = 160
                button_height = 36

                self.upgrade_button_rect = (button_x - button_width//2,
                                            button_y - button_height//2,
                                            button_width, button_height)

                can_afford = self.money >= upgrade_cost
                button_color = (UPGRADE_BUTTON_COLOR if can_afford
                                else UPGRADE_BUTTON_DISABLED)

                arcade.draw_lrbt_rectangle_filled(
                    button_x - button_width//2,
                    button_x + button_width//2,
                    button_y - button_height//2,
                    button_y + button_height//2,
                    button_color
                )

                arcade.draw_lrbt_rectangle_outline(
                    button_x - button_width//2,
                    button_x + button_width//2,
                    button_y - button_height//2,
                    button_y + button_height//2,
                    ((255, 220, 100) if can_afford
                           else (150, 150, 150)),
                    2
                )

                button_text = f"УЛУЧШИТЬ: {upgrade_cost}💰"
                arcade.draw_text(
                    button_text,
                    button_x + 1, button_y - 1,
                    TEXT_SHADOW, 16,
                    anchor_x="center", anchor_y="center", bold=True
                )
                arcade.draw_text(
                    button_text,
                    button_x, button_y,
                    (TEXT_COLOR if can_afford else (150, 150, 150)), 16,
                    anchor_x="center", anchor_y="center", bold=True
                )

                future_y = menu_y - 195
                future_stats = [
                    f"Новый урон: {next_stats['damage']}",
                    f"Новая дальность: {int(next_stats['range'])}",
                    f"Новая скорость: {next_stats['fire_rate']:.1f}/сек"
                ]

                for i, stat in enumerate(future_stats):
                    arcade.draw_text(
                        stat,
                        menu_x + 15, future_y - i * 18,
                        (100, 255, 100), 12,
                        anchor_x="left", anchor_y="center"
                    )
        else:
            max_y = menu_y - 155
            arcade.draw_text(
                "МАКСИМАЛЬНЫЙ УРОВЕНЬ",
                menu_x + menu_width//2 + 1, max_y - 1,
                TEXT_SHADOW, 18,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                "МАКСИМАЛЬНЫЙ УРОВЕНЬ",
                menu_x + menu_width//2, max_y,
                (255, 220, 50), 18,
                anchor_x="center", anchor_y="center", bold=True
            )

    def on_update(self, delta_time):
        if self.game_over or self.victory:
            return

        # Обновление всплывающего текста
        for text in self.floating_texts[:]:
            text.update(delta_time)
            if text.time >= text.duration:
                self.floating_texts.remove(text)

        for enemy in self.enemy_list:
            enemy.update()
            if enemy.has_reached_end():
                self.lives -= BASE_DAMAGE
                self.enemy_list.remove(enemy)
                self.window.sound_manager.play_sound("lose_life", volume=0.25)
                if self.lives <= 0:
                    self.game_over = True

        self.update_counter += 1
        update_towers = (self.update_counter % 2 == 0 or
                        len(self.enemy_list) < 20)

        for tower in self.tower_list:
            if update_towers:
                tower.update(
                    delta_time,
                    self.enemy_list,
                    self.projectile_list,
                    self.window.sound_manager,
                    self.particle_system
                )
            else:
                tower.fire_timer += delta_time

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

            hit_list = arcade.check_for_collision_with_list(
                projectile, self.enemy_list
            )
            if hit_list:
                for enemy in hit_list:
                    if enemy.alive:
                        died, is_critical = enemy.take_damage(
                            projectile.damage,
                            projectile.is_critical
                        )
                        if died:
                            self.money += enemy.bounty
                            self.score += enemy.bounty * 10
                            self.enemy_list.remove(enemy)
                            self.particle_system.create_explosion(
                                enemy.center_x, enemy.center_y,
                                (255, 165, 0), 10
                            )
                            self.window.sound_manager.play_sound(
                                "enemy_die", volume=0.3
                            )
                        # Если был критический удар, показываем текст
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
                if projectile in self.projectile_list:
                    self.projectile_list.remove(projectile)

        self.particle_system.update(delta_time)

        if len(self.projectile_list) > 100:
            self.projectile_list = self.projectile_list[-80:]

        # Логика автозапуска волны
        if (not self.wave_active and
                self.enemies_spawned >= self.total_enemies and
                len(self.enemy_list) == 0 and
                self.wave < len(self.waves)):

            if self.wave_start_countdown <= 0:
                # Устанавливаем таймер на 15 секунд
                self.wave_start_countdown = self.auto_wave_start_delay
            else:
                self.wave_start_countdown -= delta_time

                # Если таймер истек, запускаем волну
                if self.wave_start_countdown <= 0:
                    self.start_wave()
        else:
            # Сбрасываем таймер, если волна активна или враги еще есть
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
            self.wave_start_countdown = 0  # Сбрасываем таймер
            wave_data = self.waves[self.wave]
            self.window.sound_manager.play_sound("wave_start", volume=0.4)

            self.total_enemies = sum(wave_data.values())
            self.enemies_spawned = 0

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
                elif enemy_type == "tank":
                    enemy_types.extend([EnemyType.TANK] * count)
                elif enemy_type == "ninja":
                    enemy_types.extend([EnemyType.NINJA] * count)
                elif enemy_type == "boss_dragon":
                    enemy_types.extend([EnemyType.BOSS_DRAGON] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound(
                            "boss_spawn", volume=0.4
                        )
                elif enemy_type == "boss_giant":
                    enemy_types.extend([EnemyType.BOSS_GIANT] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound(
                            "boss_spawn", volume=0.4
                        )
                elif enemy_type == "boss_wizard":
                    enemy_types.extend([EnemyType.BOSS_WIZARD] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound(
                            "boss_spawn", volume=0.4
                        )
                elif enemy_type == "boss_cyber":
                    enemy_types.extend([EnemyType.BOSS_CYBER] * count)
                    if count > 0:
                        self.window.sound_manager.play_sound(
                            "boss_spawn", volume=0.4
                        )

            random.shuffle(enemy_types)

            for i, enemy_type in enumerate(enemy_types):
                arcade.schedule(
                    lambda dt, etype=enemy_type: self.spawn_enemy(etype),
                    i * 1.5
                )

            self.wave += 1

    def spawn_enemy(self, enemy_type):
        if self.enemies_spawned < self.total_enemies:
            if (self.map_type == MapType.HELL and
                    len(self.path_points2) > 0):
                if random.choice([True, False]):
                    path = self.path_points
                    start_pos = (
                        self.path_points[0] if self.path_points else None
                    )
                else:
                    path = self.path_points2
                    start_pos = (
                        self.path_points2[0] if self.path_points2 else None
                    )
            else:
                path = self.path_points
                start_pos = (
                    self.path_points[0] if self.path_points else None
                )

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
                        self.window.sound_manager.play_sound("upgrade",
                                                             volume=0.3)
                        self.show_upgrade_menu = False
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
                        self.window.sound_manager.play_sound("click",
                                                             volume=0.2)
                        break

                if not occupied:
                    cost = 0
                    if self.selected_tower_type == TowerType.SNIPER:
                        cost = 160
                    elif self.selected_tower_type == TowerType.ARTILLERY:
                        cost = 320
                    elif self.selected_tower_type == TowerType.LASER:
                        cost = 240
                    elif self.selected_tower_type == TowerType.ROCKET:
                        cost = 280
                    else:
                        cost = 300

                    if self.money >= cost:
                        tower = Tower(self.selected_tower_type, sx, sy)
                        self.tower_list.append(tower)
                        self.money -= cost
                        self.window.sound_manager.play_sound("build",
                                                             volume=0.3)
                        self.selected_tower = tower
                        self.show_upgrade_menu = True
                break

    def on_mouse_motion(self, x, y, dx, dy):
        # Обновление состояния кнопки волны
        if self.wave_button_rect:
            bx, by, bw, bh = self.wave_button_rect
            self.wave_button_hover = (bx <= x <= bx + bw and by <= y <= by + bh)

        # Сброс информации о наведении на врага
        self.hovered_enemy = None

        # Проверка наведения на врага
        if not (y > self.window.height - UI_HEIGHT or
                x > self.window.width - TOWER_BUTTONS_WIDTH):
            for enemy in self.enemy_list:
                if enemy.alive and (abs(x - enemy.center_x) < enemy.width/2 and
                        abs(y - enemy.center_y) < enemy.height/2):
                    self.hovered_enemy = enemy
                    break

        # Проверка наведения на кнопки башен
        for (bx, by, width, height), tower_type, name, cost, color, shape in \
                self.tower_buttons:
            if (bx - width/2 <= x <= bx + width/2 and
                    by - height/2 <= y <= by + height/2):
                break

        if (y > self.window.height - UI_HEIGHT or
                x > self.window.width - TOWER_BUTTONS_WIDTH):
            self.showing_range = None
            return

        # Показ радиуса башни
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
                        "Лес" if self.map_type == MapType.FOREST else
                        "Город" if self.map_type == MapType.CITY else
                        "Ад" if self.map_type == MapType.HELL else
                        "Кибер"
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
        self.options = ["ПРОДОЛЖИТЬ", "СОХРАНИТЬ ИГРУ", "ГЛАВНОЕ МЕНЮ"]
        self.show_hints = True

    def on_show_view(self):
        arcade.set_background_color((40, 45, 60))

    def on_draw(self):
        self.clear()

        self.game_view.on_draw()

        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width,
            0,
            self.window.height,
            (0, 0, 0, 180)
        )

        arcade.draw_text(
            "ПАУЗА",
            self.window.width // 2 + 2,
            self.window.height // 2 + 98,
            (30, 40, 60),
            64,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ПАУЗА",
            self.window.width // 2,
            self.window.height // 2 + 100,
            (100, 200, 255),
            64,
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
                (30, 40, 60), 36,
                anchor_x="center", anchor_y="center",
                bold=(i == self.selected)
            )
            arcade.draw_text(
                text,
                self.window.width // 2, y,
                color, 36,
                anchor_x="center", anchor_y="center",
                bold=(i == self.selected)
            )

        if self.show_hints:
            hints = [
                "=== ПОДСКАЗКИ ===",
                "• Клик на клетку - построить башню",
                "• Клик на башню - улучшить её",
                "• Пробел - начать следующую волну",
                "• S - сохранить игру",
                "• F11 - полный экран",
                "• ESC - пауза/меню",
                "• Наведи на врага - увидишь его характеристики"
            ]

            hint_y = 350
            for i, hint in enumerate(hints):
                color = (255, 220, 100) if i == 0 else (200, 220, 255)
                size = 22 if i == 0 else 18

                arcade.draw_text(
                    hint,
                    self.window.width // 2 + 1, hint_y - i * 28 - 1,
                    (30, 40, 60), size,
                    anchor_x="center", anchor_y="center",
                    bold=(i == 0)
                )
                arcade.draw_text(
                    hint,
                    self.window.width // 2, hint_y - i * 28,
                    color, size,
                    anchor_x="center", anchor_y="center",
                    bold=(i == 0)
                )

        arcade.draw_text(
            ("↑↓ Выбрать • ENTER Подтвердить • ESC: продолжить • "
             "H: Подсказки • F11: Полный экран"),
            self.window.width // 2 + 1, 99,
            (30, 40, 60), 20, anchor_x="center"
        )
        arcade.draw_text(
            ("↑↓ Выбрать • ENTER Подтвердить • ESC: продолжить • "
             "H: Подсказки • F11: Полный экран"),
            self.window.width // 2, 100,
            (180, 190, 210), 20, anchor_x="center"
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
            "ТАБЛИЦА РЕКОРДОВ",
            self.window.width // 2 + 2,
            self.window.height - 102,
            (30, 40, 60),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "ТАБЛИЦА РЕКОРДОВ",
            self.window.width // 2,
            self.window.height - 100,
            (255, 220, 100),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        arcade.draw_line(
            60, self.window.height - 150,
            self.window.width - 60, self.window.height - 150,
            (80, 100, 150), 2
        )

        headers = ["Место", "Имя", "Очки", "Сложность", "Карта", "Волна",
                   "Дата"]
        positions = [60, 140, 220, 320, 420, 520, 650]

        for i, header in enumerate(headers):
            arcade.draw_text(
                header,
                positions[i] + 1, self.window.height - 181,
                (30, 40, 60), 18, bold=True
            )
            arcade.draw_text(
                header,
                positions[i], self.window.height - 180,
                (100, 200, 255), 18, bold=True
            )

        if not self.scores:
            arcade.draw_text(
                "Рекордов пока нет!",
                self.window.width // 2, self.window.height // 2,
                (200, 200, 200), 36,
                anchor_x="center", anchor_y="center"
            )
        else:
            for i, score in enumerate(self.scores[:10]):
                y = self.window.height - 230 - i * 40
                color = (255, 220, 100) if i == 0 else (220, 220, 255)

                diff_text = (
                    "Лёгкий" if score["difficulty"] == "easy" else
                    "Средний" if score["difficulty"] == "normal" else
                    "Сложный"
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
                    arcade.draw_text(
                        text, x + 1, y_pos - 1, (30, 40, 60), 14
                    )
                    arcade.draw_text(text, x, y_pos, col, 14)

        arcade.draw_text(
            "Нажмите ESC для выхода • F11: Полный экран",
            self.window.width // 2 + 1, 49,
            (30, 40, 60), 20, anchor_x="center"
        )
        arcade.draw_text(
            "Нажмите ESC для выхода • F11: Полный экран",
            self.window.width // 2, 50,
            (180, 190, 210), 20, anchor_x="center"
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
            ("Звук", self.window.sound_manager.enabled),
            ("Музыка", self.window.sound_manager.music_player is not None)
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
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )
        arcade.draw_text(
            "НАСТРОЙКИ",
            self.window.width // 2,
            self.window.height - 100,
            (100, 200, 255),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        for i, (name, value) in enumerate(self.options):
            y = self.window.height // 2 - i * 80
            status = "ВКЛ" if value else "ВЫКЛ"

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
                (30, 40, 60), 36,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                f"{name}: {status}",
                self.window.width // 2, y,
                color, 36,
                anchor_x="center", anchor_y="center"
            )

        arcade.draw_text(
            "↑↓ Выбрать • ENTER Изменить • ESC Выход • F11: Полный экран",
            self.window.width // 2 + 1, 99,
            (30, 40, 60), 20, anchor_x="center"
        )
        arcade.draw_text(
            "↑↓ Выбрать • ENTER Изменить • ESC Выход • F11: Полный экран",
            self.window.width // 2, 100,
            (180, 190, 210), 20, anchor_x="center"
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
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
                         fullscreen=True)
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