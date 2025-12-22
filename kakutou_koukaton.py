import pygame as pg
import sys
import os

# =====================
# 初期設定
# =====================
WIDTH, HEIGHT = 1000, 600
FLOOR = HEIGHT - 50
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Mini Street Fighter")
clock = pg.time.Clock()

# =====================
# Fighter クラス
# =====================
class Fighter(pg.sprite.Sprite):
    def __init__(self, x, keys):
        super().__init__()

        # ===== 画像（サイズ手動調整）=====
        self.idle_r = pg.transform.scale(
            pg.image.load("fig/manfighter.png").convert_alpha(), (150, 200)  #画像の大きさ設定
        )
        self.idle_l = pg.transform.flip(self.idle_r, True, False)

        self.punch_r = pg.transform.scale(
            pg.image.load("fig/manfighter_punch.png").convert_alpha(), (150, 200)  #画像の大きさ設定
        )
        self.punch_l = pg.transform.flip(self.punch_r, True, False)

        self.kick_r = pg.transform.scale(
            pg.image.load("fig/manfighter_kick.png").convert_alpha(), (190, 200)  #画像の大きさ設定
        )
        self.kick_l = pg.transform.flip(self.kick_r, True, False)

        self.image = self.idle_r
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, FLOOR)

        self.vx = 0
        self.vy = 0
        self.on_ground = True
        self.hp = 100

        self.keys = keys
        self.facing = 1

        # ===== タイマー =====
        self.attack_timer = 0      # 技中
        self.recover_timer = 0     # 技後硬直（1秒）
        self.knockback_vx = 0      # ノックバック速度

    def update(self, key_lst):
        self.vx = 0

        # ===== 行動可能判定 =====
        can_move = (self.attack_timer == 0 and self.recover_timer == 0)

        if can_move:
            if key_lst[self.keys["left"]]:
                self.vx = -6
                self.facing = -1
            if key_lst[self.keys["right"]]:
                self.vx = 6
                self.facing = 1

            if key_lst[self.keys["jump"]] and self.on_ground:
                self.vy = -20
                self.on_ground = False

        # ===== 技タイマー =====
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.recover_timer = 20  #  1/3秒硬直
        elif self.recover_timer > 0:
            self.recover_timer -= 1
        else:
            self.image = self.idle_r if self.facing == 1 else self.idle_l

        # ===== 重力 =====
        self.vy += 1
        self.rect.x += self.vx + self.knockback_vx
        self.rect.y += self.vy

        if self.rect.bottom >= FLOOR:
            self.rect.bottom = FLOOR
            self.vy = 0
            self.on_ground = True
            
        # ===== ノックバック減衰 =====
        if self.knockback_vx != 0:
            self.knockback_vx *= 0.85  # 徐々に減速
            if abs(self.knockback_vx) < 0.5:
                self.knockback_vx = 0

    def do_attack(self, atk_type, attacks, hurtboxes, opponent):
        if self.attack_timer > 0 or self.recover_timer > 0:
            return

        if atk_type == "punch":
            self.image = self.punch_r if self.facing == 1 else self.punch_l
            self.attack_timer = 12
        else:
            self.image = self.kick_r if self.facing == 1 else self.kick_l
            self.attack_timer = 16

        attacks.add(Attack(self, atk_type))
        hurtboxes.add(HurtBox(opponent, atk_type))


# =====================
# 攻撃判定（HitBox）
# =====================
class Attack(pg.sprite.Sprite):
    DATA = {
        "punch": {"size": (40, 20), "life": 8, "damage": 5},
        "kick":  {"size": (60, 25), "life": 10, "damage": 8},
    }

    OFFSET_Y = {
        "punch": -10,
        "kick": 30
    }

    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter

        w, h = self.DATA[atk_type]["size"]
        self.image = pg.Surface((w, h), pg.SRCALPHA)
        self.image.fill((255, 0, 0, 150))

        self.rect = self.image.get_rect()

        if fighter.facing == 1:
            self.rect.left = fighter.rect.right + 10
        else:
            self.rect.right = fighter.rect.left - 10

        self.rect.centery = fighter.rect.centery + self.OFFSET_Y[atk_type]

        self.life = self.DATA[atk_type]["life"]
        self.damage = self.DATA[atk_type]["damage"]

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            

# =====================
# ノックバック関数
# =====================
def apply_knockback(victim, attacker, damage):
    """
    ダメージを受けたファイターにノックバックを適用する
    
    Args:
        victim: ダメージを受けたファイター
        attacker: 攻撃したファイター
        damage: 与えたダメージ量
    """
    knockback_dir = 1 if attacker.facing == 1 else -1
    knockback_speed = knockback_dir * damage * 0.8
    victim.knockback_vx += knockback_speed
    victim.recover_timer = 15


# =====================
# くらい判定（HurtBox）
# =====================
class HurtBox(pg.sprite.Sprite):
    SIZE = {
        "punch": (60, 30),
        "kick":  (80, 40)
    }

    OFFSET_Y = {
        "punch": -10,
        "kick": 30
    }

    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter

        w, h = self.SIZE[atk_type]
        self.image = pg.Surface((w, h), pg.SRCALPHA)
        self.image.fill((0, 0, 255, 100))

        self.rect = self.image.get_rect()

        if fighter.facing == 1:
            self.rect.left = fighter.rect.right
        else:
            self.rect.right = fighter.rect.left

        self.rect.centery = fighter.rect.centery + self.OFFSET_Y[atk_type]

        self.life = 20  # 攻撃判定より長い

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            

# =====================
# HPバー描画
# =====================
def draw_hp(screen, fighter, x):
    pg.draw.rect(screen, (255, 0, 0), (x, 20, 300, 20))
    pg.draw.rect(screen, (0, 255, 0), (x, 20, 3 * fighter.hp, 20))


# =====================
# ダメージ判定関数
# =====================
def check_damage(attacks, hurtboxes):
    """
    攻撃判定とくらい判定の衝突をチェックし、ダメージを適用する
    
    Args:
        attacks: 攻撃判定のスプライトグループ
        hurtboxes: くらい判定のスプライトグループ
    """
    for atk in attacks:
        for hb in hurtboxes:
            if atk.owner != hb.owner and atk.rect.colliderect(hb.rect):
                hb.owner.hp -= atk.damage
                apply_knockback(hb.owner, atk.owner, atk.damage)
                atk.kill()
                return  # 1フレームに1ヒットまで


# =====================
# メイン
# =====================
def main():
    attacks = pg.sprite.Group()
    hurtboxes = pg.sprite.Group()

    p1 = Fighter(200, {
        "left": pg.K_a,
        "right": pg.K_d,
        "jump": pg.K_w,
        "punch": pg.K_c,
        "kick": pg.K_v
    })

    p2 = Fighter(700, {
        "left": pg.K_LEFT,
        "right": pg.K_RIGHT,
        "jump": pg.K_UP,
        "punch": pg.K_PERIOD,
        "kick": pg.K_SLASH
    })

    fighters = pg.sprite.Group(p1, p2)

    while True:
        screen.fill((30, 30, 30))
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                if event.key == p1.keys["punch"]:
                    p1.do_attack("punch", attacks, hurtboxes, p2)
                if event.key == p1.keys["kick"]:
                    p1.do_attack("kick", attacks, hurtboxes, p2)

                if event.key == p2.keys["punch"]:
                    p2.do_attack("punch", attacks, hurtboxes, p1)
                if event.key == p2.keys["kick"]:
                    p2.do_attack("kick", attacks, hurtboxes, p1)

        fighters.update(key_lst)
        attacks.update()
        hurtboxes.update()

        # 攻撃 × くらい判定
        check_damage(attacks, hurtboxes)

        # 描画
        pg.draw.rect(screen, (80, 160, 80), (0, FLOOR, WIDTH, HEIGHT))
        fighters.draw(screen)
        attacks.draw(screen)
        hurtboxes.draw(screen)
        
        draw_hp(screen, p1, 50)
        draw_hp(screen, p2, WIDTH - 350)

        # 勝敗判定
        if p1.hp <= 0 or p2.hp <= 0:
            font = pg.font.Font(None, 80)
            text = font.render("K.O.", True, (255, 255, 0))
            screen.blit(text, (WIDTH//2 - 80, HEIGHT//2 - 40))
            pg.display.update()
            pg.time.delay(2000)
            return

        pg.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()