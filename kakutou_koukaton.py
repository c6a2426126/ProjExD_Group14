# ==============================================
# Pygame 共通基本コード一式（単一ファイル）
# 6人開発・初期段階向け / 再利用前提
# ==============================================

import math
import os
import random
import sys
import time
import pygame as pg
# =====================
# 設定（config相当）
# =====================
WIDTH = 1100
HEIGHT = 650
FPS = 60
BG_COLOR = (255, 255, 255)
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# =====================
# ユーティリティ関数
# =====================

def check_bound(rect: pg.Rect) -> tuple[bool, bool]:
    """
    Rectが画面内に収まっているか判定
    戻り値: (横方向OK, 縦方向OK)
    """
    x_ok = 0 <= rect.left and rect.right <= WIDTH
    y_ok = 0 <= rect.top and rect.bottom <= HEIGHT
    return x_ok, y_ok


# =====================
# Entity（全キャラ共通基底）
# =====================

class Entity(pg.sprite.Sprite):
    def __init__(self, image: pg.Surface, pos: tuple[int, int]):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.hp = 100
        self.alive = True

    def take_damage(self, amount: int):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def update(self):
        pass


# =====================
# 当たり判定
# =====================

def hit_check(attacker, defender, damage: int = 1):
    """
    attacker.attack_rect が存在し、 defender.rect と衝突したらダメージ
    """
    if not hasattr(attacker, "attack_rect"):
        return
    atk = attacker.attack_rect
    if atk and atk.colliderect(defender.rect):
        defender.take_damage(damage)


# =====================
# UI（HPバーなど）
# =====================

class HPBar:
    def __init__(self, pos: tuple[int, int], size=(200, 20), max_hp=100):
        self.pos = pos
        self.size = size
        self.max_hp = max_hp

    def draw(self, screen: pg.Surface, hp: int):
        ratio = max(hp, 0) / self.max_hp
        bg = pg.Rect(*self.pos, *self.size)
        fg = pg.Rect(*self.pos, int(self.size[0] * ratio), self.size[1])
        pg.draw.rect(screen, (80, 80, 80), bg)
        pg.draw.rect(screen, (0, 200, 0), fg)


# =====================
# Game（ゲームループ中核）
# =====================

class Game:
    def __init__(self, screen: pg.Surface):
        self.screen = screen
        self.clock = pg.time.Clock()
        self.sprites = pg.sprite.Group()
        self.running = True

    def update(self):
        self.sprites.update()

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.sprites.draw(self.screen)
        pg.display.update()

    def run(self):
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

            self.update()
            self.draw()
            self.clock.tick(FPS)


# =====================
# main（起動・動作確認）
# =====================

def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Pygame Game Base Framework")

    game = Game(screen)

    # 仮プレイヤー（白い四角）
    surf = pg.Surface((50, 80))
    surf.fill((220, 220, 220))
    player = Entity(surf, (WIDTH // 2, HEIGHT // 2))
    game.sprites.add(player)

    # 仮HPバー
    hp_bar = HPBar((20, 20))

    while game.running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                game.running = False

        game.update()
        game.screen.fill(BG_COLOR)
        game.sprites.draw(game.screen)
        hp_bar.draw(game.screen, player.hp)
        pg.display.update()
        game.clock.tick(FPS)

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
