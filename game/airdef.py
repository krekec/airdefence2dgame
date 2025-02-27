import random
import math
import sys
import pygame
from explosion_effects import ExplosionEffect

pygame.init()
pygame.mixer.init()


screen_width = 1020
screen_height = 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Protect the sky")
clock = pygame.time.Clock()

white = (255, 255, 255)
BUTTON_COLOR = (0, 0, 0)
BUTTON_PADDING = 20

font_main = pygame.font.SysFont(None, 48)
score_font = pygame.font.SysFont(None, 24)
fuse_font = pygame.font.SysFont(None, 28)

score = 0
fuse_distance = 100
angle_20mm = 0
angle_88mm = 0
MAX_ANGLE_20MM = 40
MIN_ANGLE_20MM = -90
MAX_ANGLE_88MM = 70
MIN_ANGLE_88MM = 0

last_88mm_fire_time = 0
last_20mm_fire_time = 0
fire_delay_88mm = 1000
fire_delay_20mm = 500

planes = []
bullets = []
spawn_timer = 0
heart_image = pygame.image.load("heart.png").convert_alpha()
heart_image = pygame.transform.scale(heart_image, (30, 30))  


PLANE_SPEED_RANGE = (2, 5)


tree_images = [
    pygame.image.load("drevo1.png").convert_alpha(),
    pygame.image.load("drevo2.png").convert_alpha(),
    pygame.image.load("drevo3.png").convert_alpha(),
    pygame.image.load("drevo4.png").convert_alpha()
]
class Tree:
    def __init__(self):
        self.image = random.choice(tree_images)
        self.rect = self.image.get_rect()
        
        self.rect.x = screen_width + random.randint(500,1000)
        self.rect.y = screen_height - 230
        self.speed = 5

    def update(self):
        """Move the tree left by its speed."""
        self.rect.x -= self.speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_off_screen(self):
        """Check if the tree has completely moved off the left side."""
        return self.rect.right < 0

menu_texture = pygame.image.load("menu.png")

background_image = pygame.image.load("background.png")
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

texture_train = pygame.image.load("vlak.png")
train_aspect_ratio = texture_train.get_width() / texture_train.get_height()
train_height = int(screen_width / train_aspect_ratio)
texture_train = pygame.transform.scale(texture_train, (int(screen_width * 1.9), int(train_height * 1.9)))

texture_88 = pygame.image.load("20mm.png")
texture_20 = pygame.image.load("20mm.png")

texture_20hull = pygame.image.load("20mmhul.png")
aspectratio_20hull = texture_20hull.get_width() / texture_20hull.get_height()
hull20_height = int(screen_width / aspectratio_20hull)
texture_20hull = pygame.transform.scale(texture_20hull, (int(screen_width * 0.07), int(hull20_height * 0.07)))

texture_88hull = pygame.image.load("88mmhull.png")
aspectratio_88hull = texture_88hull.get_width() / texture_88hull.get_height()
hull88_height = int(screen_width / aspectratio_88hull)
texture_88hull = pygame.transform.scale(texture_88hull, (int(screen_width * 0.2), int(hull88_height * 0.2)))


bullet_texture_88mm = pygame.image.load("20mm.png")
bullet_texture_20mm = pygame.image.load("20mm.png")
bullet_texture_88mm = pygame.transform.scale(bullet_texture_88mm, (25, 25))
bullet_texture_20mm = pygame.transform.scale(bullet_texture_20mm, (12, 12))

fire_sound_20mm = pygame.mixer.Sound("20mmsound.mp3")
fire_sound_20mm.set_volume(0.23)

plane_hit = pygame.mixer.Sound("planexplosion.mp3")
plane_hit.set_volume(0.3)

losing = pygame.mixer.Sound("loosinglife.mp3")
losing.set_volume(0.53)

plane_image = pygame.image.load("p40.png")
plane_width = plane_image.get_width() // 4
plane_height = plane_image.get_height() // 4
plane_image = pygame.transform.scale(plane_image, (plane_width, plane_height))

gun_20mm = pygame.image.load("20mmgunn.png")
gun_88mm    = pygame.image.load("88mmgun.png")
gun_20mm = pygame.transform.scale(
    gun_20mm, (int(gun_20mm.get_width() * 0.15), int(gun_20mm.get_height() * 0.15))
)
gun_88mm = pygame.transform.scale(
    gun_88mm, (int(gun_88mm.get_width() * 0.15), int(gun_88mm.get_height() * 0.15))
)

play_text = font_main.render("PLAY", True, (255, 255, 255))
play_rect = play_text.get_rect(center=(screen_width // 2, screen_height // 2))
button_bg_rect = pygame.Rect(
    play_rect.x - BUTTON_PADDING // 2,
    play_rect.y - BUTTON_PADDING // 2,
    play_rect.width + BUTTON_PADDING,
    play_rect.height + BUTTON_PADDING
)

GUN_88MM_POS = (230, 630)
GUN_20MM_POS = (500, 550)

trees = []
tree_spawn_timer = 0
tree_spawn_delay = 100


class Bullet:
    def __init__(self, angle, x, y, speed=10, width=15, height=5, weapon="20mm"):
        self.angle = angle
        self.x = x
        self.y = y
        self.speed = speed
        self.width = width
        self.height = height
        self.weapon = weapon
        self.travel_distance = 0
        self.fuse_distance = fuse_distance if weapon == "88mm" else 0
        self.hit_planes = []
        self.exploded = False
        self.explosion_effect = None
        bullet_tex = bullet_texture_88mm if weapon == "88mm" else bullet_texture_20mm
        self.texture = pygame.transform.rotate(bullet_tex, -angle + 90)
        self.rect = self.texture.get_rect(center=(x, y))

    def is_off_screen(self):
        padding = 50
        return (
            self.x < -padding
            or self.x > screen_width + padding
            or self.y < -padding
            or self.y > screen_height + padding
        )

    def move(self):
        if not self.exploded:
            rad = math.radians(self.angle)
            if self.weapon == "88mm":
                self.x += self.speed * math.cos(rad)
                self.y -= self.speed * math.sin(rad)
            else:
                self.x -= self.speed * math.cos(rad)
                self.y += self.speed * math.sin(rad)
            self.rect.center = (self.x, self.y)
            self.travel_distance += self.speed
        elif self.explosion_effect:
            self.explosion_effect.update()

    def draw(self, screen):
        if not self.exploded:
            screen.blit(self.texture, self.rect)
        elif self.explosion_effect:
            self.explosion_effect.draw(screen)

    def check_explosion(self, planes):
        global score
        if self.weapon == "88mm" and self.travel_distance >= self.fuse_distance and not self.exploded:
            self.exploded = True
            self.explosion_effect = ExplosionEffect(self.x, self.y, max_radius=100)
            for plane in planes[:]:
                dist = math.hypot(
                    plane.x + plane_width / 2 - self.rect.centerx,
                    plane.y + plane_height / 2 - self.rect.centery,
                )
                if dist <= self.explosion_effect.max_explosion_radius:
                    plane.take_damage(50)
                    if plane.falling and not hasattr(plane, "score_added"):
                        score += 10
                        plane.score_added = True
            return False
        elif self.weapon == "20mm":
            bullet_rect = pygame.Rect(
                self.x - self.width / 2, self.y - self.height / 2, self.width, self.height
            )
            for plane in planes[:]:
                plane_rect = pygame.Rect(plane.x, plane.y, plane_width, plane_height)
                if bullet_rect.colliderect(plane_rect):
                    plane.take_damage(20)
                    if plane.falling and not hasattr(plane, "score_added"):
                        score += 10
                        plane.score_added = True
                    return True

        return self.exploded and (self.explosion_effect and self.explosion_effect.is_finished())


class Plane:
    def __init__(self):
        self.y = random.randint(20, 400)
        self.speed = random.randint(*PLANE_SPEED_RANGE)
        self.max_hp = 100
        self.current_hp = self.max_hp
        self.falling = False
        self.fall_speed = 0
        self.fall_acceleration = 0.1
        self.destroyed_image = pygame.image.load("destroyed.png")
        self.destroyed_image = pygame.transform.scale(self.destroyed_image, (plane_width, plane_height))

        # Random direction
        if random.choice([True, False]):
            self.x = -80
            self.image = plane_image
            self.direction = 1
        else:
            self.x = screen_width + 80
            self.image = pygame.transform.flip(plane_image, True, False)
            self.destroyed_image = pygame.transform.flip(self.destroyed_image, True, False)
            self.direction = -1

    def take_damage(self, damage):
        self.current_hp -= damage
        if self.current_hp <= 0:
            self.falling = True
            self.image = self.destroyed_image
            plane_hit.play()
        return self.current_hp <= 0

    def move(self):
        if self.falling:
            self.fall_speed += self.fall_acceleration
            self.y += self.fall_speed
            self.x += self.speed * self.direction * 0.2
        else:
            self.x += self.speed * self.direction

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

        if not self.falling:
            bar_width = 50
            bar_height = 5
            hp_percentage = max(0, self.current_hp / self.max_hp)
            hp_bar_width = int(bar_width * hp_percentage)

            if hp_percentage > 0.6:
                color = (0, 255, 0)
            elif hp_percentage > 0.3:
                color = (255, 165, 0)
            else:
                color = (255, 0, 0)

            pygame.draw.rect(screen, (100, 100, 100), (self.x, self.y - 10, bar_width, bar_height))
            pygame.draw.rect(screen, color, (self.x, self.y - 10, hp_bar_width, bar_height))

    def is_off_screen(self):
        plane_rect = pygame.Rect(self.x, self.y, plane_width, plane_height)
        off_left = (self.direction < 0 and plane_rect.right < 0)
        off_right = (self.direction > 0 and plane_rect.left > screen_width)
        off_bottom = (plane_rect.top > screen_height)
        
        if off_left or off_right or off_bottom:
            print("Plane went off-screen at", self.x, self.y, "Direction:", self.direction)
        return off_left or off_right or off_bottom
        
menu_texture = pygame.image.load("menu.png").convert()
menu_texture = pygame.transform.scale(menu_texture, (screen_width, screen_height))


def main_menu():
    """Displays the main menu with a custom START button image."""

    menu_bg = pygame.image.load("menu.png").convert()
    menu_bg = pygame.transform.scale(menu_bg, (screen_width, screen_height))

    start_button_img = pygame.image.load("start.png").convert_alpha()
    start_button_img = pygame.transform.scale(start_button_img, (200, 80))
    
    start_button_rect = start_button_img.get_rect(center=(screen_width // 2+200, screen_height // 2+180))

    pygame.mixer.music.load("mainmenu.mp3")
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    return  

        screen.blit(menu_bg, (0, 0))
        screen.blit(start_button_img, start_button_rect)

        pygame.display.flip()
        clock.tick(60)

def run_game():
    """Runs the main game loop after the PLAY button is clicked."""
    global score, fuse_distance
    global angle_20mm, angle_88mm
    global last_88mm_fire_time, last_20mm_fire_time
    global planes, bullets, spawn_timer

    score = 0
    fuse_distance = 300
    angle_20mm = 0
    angle_88mm = 0
    last_88mm_fire_time = 0
    last_20mm_fire_time = 0
    planes = []
    bullets = []
    spawn_timer = 0
    trees = []
    tree_spawn_timer = 0
    tree_spawn_delay = 150
    player_lives = 3



    pygame.mixer.music.load("background.mp3")
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_q]:
            fuse_distance = max(fuse_distance - 5, 10)
        if keys[pygame.K_e]:
            fuse_distance = min(fuse_distance + 5, 1000)

        current_time = pygame.time.get_ticks()
        if keys[pygame.K_SPACE] and current_time - last_88mm_fire_time >= fire_delay_88mm:
            bullet = Bullet(angle_88mm, GUN_88MM_POS[0], GUN_88MM_POS[1], weapon="88mm", width=30, height=10)
            bullets.append(bullet)
            last_88mm_fire_time = current_time

        if keys[pygame.K_RETURN] and current_time - last_20mm_fire_time >= fire_delay_20mm-100:
            bullet = Bullet(angle_20mm, GUN_20MM_POS[0], GUN_20MM_POS[1], weapon="20mm", width=5, height=5)
            bullets.append(bullet)
            last_20mm_fire_time = current_time
            fire_sound_20mm.play()

        if keys[pygame.K_LEFT]:
            angle_20mm = min(angle_20mm + 2, MAX_ANGLE_20MM)
        if keys[pygame.K_RIGHT]:
            angle_20mm = max(angle_20mm - 2, MIN_ANGLE_20MM)

        if keys[pygame.K_d]:
            angle_88mm = max(angle_88mm - 2, MIN_ANGLE_88MM)

        if keys[pygame.K_a]:
            angle_88mm = min(angle_88mm + 2, MAX_ANGLE_88MM)

        spawn_timer += 1
        if spawn_timer >= 150:
            planes.append(Plane())
            spawn_timer = 0

        for bullet in bullets[:]:
            bullet.move()
            if bullet.is_off_screen() or bullet.check_explosion(planes):
                bullets.remove(bullet)

        screen.blit(background_image, (0, 0))
        screen.blit(texture_train, (-460, screen_height - texture_train.get_height() + 243))

        for plane in planes[:]:
            plane.move()
            if plane.is_off_screen():
                if not plane.falling:
                    player_lives -= 1
                    losing.play()
                    if player_lives <= 0:
                        running = False
                planes.remove(plane)

        for plane in planes:
            plane.draw(screen)


        for bullet in bullets:
            bullet.draw(screen)

        rotated_20mm = pygame.transform.rotate(gun_20mm, angle_20mm)
        gun_20mm_rect = rotated_20mm.get_rect(center=GUN_20MM_POS)
        screen.blit(rotated_20mm, gun_20mm_rect.topleft)


        rotated_88mm = pygame.transform.rotate(gun_88mm, angle_88mm)
        gun_88mm_rect = rotated_88mm.get_rect(center=GUN_88MM_POS)
        screen.blit(rotated_88mm, gun_88mm_rect.topleft)
        gun_88mm_rect = rotated_88mm.get_rect(center=GUN_88MM_POS)
        screen.blit(rotated_88mm, gun_88mm_rect.topleft)

        screen.blit(texture_88hull, (120, 590))
        screen.blit(texture_20hull, (475, 525))

        tree_spawn_timer += 1
        if tree_spawn_timer >= tree_spawn_delay:
            trees.append(Tree())
            tree_spawn_timer = 0

        for tree in trees[:]:
            tree.update()
            if tree.is_off_screen():
                trees.remove(tree)
        for tree in trees:
            tree.draw(screen)
        score_text = score_font.render(f"Score: {score}", True, white)
        screen.blit(score_text, (10, 10))

        for i in range(player_lives):
            screen.blit(heart_image, (10 + i * 35, 40))

        fuse_text = fuse_font.render(f"Fuse Distance: {fuse_distance}m", True, white)
        screen.blit(fuse_text, (screen_width - 300, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()

    return
if __name__ == "__main__":
    while True:
        main_menu()  
        run_game() 