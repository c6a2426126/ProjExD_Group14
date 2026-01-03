import pygame as pg
import sys
import os

# =====================
# 定数定義
# =====================
WIDTH: int = 1000
HEIGHT: int = 600
FLOOR: int = HEIGHT - 50

# 実行ファイルのあるディレクトリへ移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Mini Street Fighter")
clock = pg.time.Clock()


class Fighter(pg.sprite.Sprite):
    """
    プレイヤーキャラクターを表すクラス。
    移動・ジャンプ・攻撃・防御・しゃがみの状態を管理する。
    """

    def __init__(
        self,
        x: int,
        color: tuple[int, int, int],
        keys: dict[str, int]
    ) -> None:
        """
        Fighterを初期化する。

        Args:
            x: 初期X座標
            color: キャラクターの色
            keys: 操作キー設定
        """
        super().__init__()

        self.color = color
        self.image = pg.Surface((60, 120))
        self.image.fill(color)
        self.rect = self.image.get_rect(bottomleft=(x, FLOOR))

        # 物理パラメータ
        self.vx: int = 0
        self.vy: int = 0
        self.walk_speed: int = 6
        self.on_ground: bool = True

        # ステータス
        self.hp: int = 100
        self.facing: int = 1  # 1:右向き, -1:左向き

        # 入力設定
        self.keys = keys

        # 状態管理
        self.is_guarding: bool = False
        self.is_crouching: bool = False
        self.is_attacking: bool = False
        self.attack_timer: int = 0

    def update(self, key_lst: list[bool], enemy: "Fighter") -> None:
        """
        キャラクターの状態更新を行う。

        Args:
            key_lst: pygame.key.get_pressed() の結果
            enemy: 対戦相手の Fighter
        """
        self.vx = 0
        self.is_guarding = False

        # =====================
        # 攻撃中フレーム管理
        # =====================
        if self.attack_timer > 0:
            self.attack_timer -= 1
        else:
            self.is_attacking = False

        # =====================
        # しゃがみ処理
        # =====================
        if key_lst[self.keys["down"]] and self.on_ground:
            self.is_crouching = True
            self.image = pg.Surface((60, 70))
            self.image.fill(self.color)
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
        else:
            self.is_crouching = False
            self.image = pg.Surface((60, 120))
            self.image.fill(self.color)
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

        # =====================
        # 防御処理（攻撃中は不可）
        # =====================
        if not self.is_attacking:
            # 相手と逆方向の入力を「防御」と判定
            back_key = (
                self.keys["left"]
                if enemy.rect.centerx > self.rect.centerx
                else self.keys["right"]
            )

            if key_lst[back_key]:
                self.is_guarding = True
                # 防御中は移動速度を半減
                self.vx = (
                    -1 if back_key == self.keys["left"] else 1
                ) * (self.walk_speed // 2)

        # =====================
        # 通常移動（防御中は不可）
        # =====================
        if not self.is_guarding:
            if key_lst[self.keys["left"]]:
                self.vx = -self.walk_speed
                self.facing = -1
            if key_lst[self.keys["right"]]:
                self.vx = self.walk_speed
                self.facing = 1

        # =====================
        # ジャンプ
        # =====================
        if key_lst[self.keys["jump"]] and self.on_ground and not self.is_crouching:
            self.vy = -20
            self.on_ground = False

        # =====================
        # 重力・位置更新
        # =====================
        self.vy += 1
        self.rect.x += self.vx
        self.rect.y += self.vy

        # 着地判定
        if self.rect.bottom >= FLOOR:
            self.rect.bottom = FLOOR
            self.vy = 0
            self.on_ground = True


class Attack(pg.sprite.Sprite):
    """
    攻撃判定用のヒットボックスクラス。
    一定フレームで消滅する。
    """

    def __init__(self, fighter: Fighter) -> None:
        super().__init__()

        self.image = pg.Surface((40, 20))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()

        # 向いている方向に攻撃判定を生成
        if fighter.facing == 1:
            self.rect.midleft = fighter.rect.midright
        else:
            self.rect.midright = fighter.rect.midleft

        self.life: int = 10  # 存在フレーム数

    def update(self) -> None:
        """攻撃判定の寿命管理"""
        self.life -= 1
        if self.life <= 0:
            self.kill()


def main() -> None:
    """ゲームのメインループ"""
    attacks = pg.sprite.Group()

    p1 = Fighter(
        200, (0, 0, 255),
        {"left": pg.K_a, "right": pg.K_d, "jump": pg.K_w,
         "down": pg.K_s, "attack": pg.K_f}
    )

    p2 = Fighter(
        700, (255, 0, 0),
        {"left": pg.K_LEFT, "right": pg.K_RIGHT, "jump": pg.K_UP,
         "down": pg.K_DOWN, "attack": pg.K_RCTRL}
    )

    running: bool = True
    while running:
        screen.fill((30, 30, 30))
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            # =====================
            # 攻撃入力
            # 防御中でも攻撃可能（防御キャンセル）
            # =====================
            if event.type == pg.KEYDOWN:
                if event.key == p1.keys["attack"]:
                    p1.is_attacking = True
                    p1.is_guarding = False
                    p1.attack_timer = 10
                    attacks.add(Attack(p1))

                if event.key == p2.keys["attack"]:
                    p2.is_attacking = True
                    p2.is_guarding = False
                    p2.attack_timer = 10
                    attacks.add(Attack(p2))

        # 更新処理
        p1.update(key_lst, p2)
        p2.update(key_lst, p1)
        attacks.update()

        # =====================
        # ダメージ判定
        # 防御中は被ダメージ軽減
        # =====================
        if pg.sprite.spritecollide(p1, attacks, True):
            p1.hp -= 2 if p1.is_guarding else 5

        if pg.sprite.spritecollide(p2, attacks, True):
            p2.hp -= 2 if p2.is_guarding else 5

        # 描画
        screen.blit(p1.image, p1.rect)
        screen.blit(p2.image, p2.rect)
        attacks.draw(screen)

        # 勝敗判定
        if p1.hp <= 0 or p2.hp <= 0:
            font = pg.font.Font(None, 80)
            text = font.render("K.O.", True, (255, 255, 0))
            screen.blit(text, (WIDTH // 2 - 80, HEIGHT // 2 - 40))
            pg.display.update()
            pg.time.delay(2000)
            return

        pg.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
    pg.quit()
    sys.exit()