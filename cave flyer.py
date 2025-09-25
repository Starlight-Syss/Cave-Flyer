import sys, math, random, os, pygame

WIDTH, HEIGHT = 900, 600
FPS = 60

BG = (12, 14, 20)
PLAYER_COLOR = (90, 200, 255)
ENEMY_COLOR = (255, 90, 120)
ORB_COLOR = (130, 255, 150)
TEXT = (235, 240, 245)

PLAYER_SIZE = 20
PLAYER_SPEED = 4.2

ENEMY_SIZE = 18
ENEMY_SPAWN_EVERY = 60  # frames
ENEMY_SPEED_MIN = 1.2
ENEMY_SPEED_MAX = 2.8
ENEMY_ACCEL = 0.0009

ORB_SIZE = 10
ORB_SPAWN_EVERY = 240
SLOW_FACTOR = 0.35
SLOW_TIME = 120  # frames

HIGHSCORE_FILE = "vector_dodge_highscore.txt"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vector Dodge")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22, bold=True)
big = pygame.font.SysFont("consolas", 48, bold=True)

def clamp(v, lo, hi): return max(lo, min(hi, v))

def load_high_score():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r") as f:
                return int(f.read().strip() or 0)
    except:
        pass
    return 0

def save_high_score(value):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(int(value)))
    except:
        pass

class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - PLAYER_SIZE//2, HEIGHT//2 - PLAYER_SIZE//2, PLAYER_SIZE, PLAYER_SIZE)
        self.alive = True
    def update(self, dt):
        keys = pygame.key.get_pressed()
        vx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        vy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        mag = math.hypot(vx, vy)
        if mag: vx, vy = vx/mag, vy/mag
        self.rect.x += int(vx * PLAYER_SPEED * dt)
        self.rect.y += int(vy * PLAYER_SPEED * dt)
        self.rect.x = clamp(self.rect.x, 0, WIDTH - self.rect.width)
        self.rect.y = clamp(self.rect.y, 0, HEIGHT - self.rect.height)
    def draw(self, s):
        pygame.draw.rect(s, PLAYER_COLOR if self.alive else (200, 70, 90), self.rect, border_radius=5)

class Enemy:
    def __init__(self, player_pos, t):
        side = random.choice(["left","right","top","bottom"])
        if side == "left": self.x, self.y = -ENEMY_SIZE, random.randint(0, HEIGHT)
        if side == "right": self.x, self.y = WIDTH+ENEMY_SIZE, random.randint(0, HEIGHT)
        if side == "top": self.x, self.y = random.randint(0, WIDTH), -ENEMY_SIZE
        if side == "bottom": self.x, self.y = random.randint(0, WIDTH), HEIGHT+ENEMY_SIZE
        self.size = ENEMY_SIZE
        base = random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX) + t * 0.0007
        self.speed = base
        self.vx, self.vy = 0, 0
    def update(self, target, dt, slow=1.0):
        dx, dy = target[0] - self.x, target[1] - self.y
        dist = math.hypot(dx, dy) or 1
        ax, ay = dx/dist, dy/dist
        self.vx += ax * ENEMY_ACCEL * dt
        self.vy += ay * ENEMY_ACCEL * dt
        mag = math.hypot(self.vx, self.vy)
        maxv = self.speed
        if mag > maxv:
            self.vx, self.vy = self.vx/mag*maxv, self.vy/mag*maxv
        self.x += self.vx * dt * slow
        self.y += self.vy * dt * slow
    def rect(self):
        return pygame.Rect(int(self.x - self.size/2), int(self.y - self.size/2), self.size, self.size)
    def draw(self, s):
        pygame.draw.rect(s, ENEMY_COLOR, self.rect(), border_radius=4)

class Orb:
    def __init__(self):
        self.x, self.y = random.randint(40, WIDTH-40), random.randint(40, HEIGHT-40)
        self.size = ORB_SIZE
        self.t = 0
    def update(self, dt): self.t += dt
    def rect(self): return pygame.Rect(int(self.x - self.size/2), int(self.y - self.size/2), self.size, self.size)
    def draw(self, s):
        r = self.rect()
        glow = max(0, int(80 + 40 * math.sin(self.t/10)))
        pygame.draw.rect(s, (glow, 255, glow), r.inflate(10,10), border_radius=10, width=2)
        pygame.draw.rect(s, ORB_COLOR, r, border_radius=6)

def main():
    player = Player()
    enemies = []
    orbs = []
    score = 0.0
    frames = 0
    spawn_timer = 0
    orb_timer = 0
    slow_left = 0

    high_score = load_high_score()
    new_high = False

    running = True
    game_over = False

    while running:
        dt = clock.tick(FPS) / (1000 / 60)  # normalize to 60 FPS units
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    # On restart, if we just set a new high score, it's already saved.
                    player = Player(); enemies.clear(); orbs.clear()
                    score = 0; frames = 0; spawn_timer = 0; orb_timer = 0; slow_left = 0
                    new_high = False
                    game_over = False

        if not game_over:
            frames += 1
            score += 0.1 * (SLOW_FACTOR if slow_left > 0 else 1.0)

            player.update(dt)

            spawn_timer += 1
            if spawn_timer >= ENEMY_SPAWN_EVERY:
                spawn_timer = 0
                enemies.append(Enemy(player.rect.center, frames))

            orb_timer += 1
            if orb_timer >= ORB_SPAWN_EVERY and len(orbs) < 2:
                orb_timer = 0
                orbs.append(Orb())

            if slow_left > 0: slow_left -= 1
            slow = SLOW_FACTOR if slow_left > 0 else 1.0

            for n in enemies:
                n.update(player.rect.center, dt, slow)

            # Collisions: enemies vs player
            prect = player.rect
            if any(prect.colliderect(n.rect()) for n in enemies):
                player.alive = False
                game_over = True
                final = int(score)
                if final > high_score:
                    high_score = final
                    new_high = True
                    save_high_score(high_score)

            # Orbs
            new_orbs = []
            for o in orbs:
                o.update(dt)
                if prect.colliderect(o.rect()):
                    slow_left = SLOW_TIME
                else:
                    new_orbs.append(o)
            orbs = new_orbs

        screen.fill(BG)

        # Vignette grid background
        cell = 30
        for x in range(0, WIDTH, cell):
            c = (22, 26, 34)
            pygame.draw.line(screen, c, (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, cell):
            c = (22, 26, 34)
            pygame.draw.line(screen, c, (0,y), (WIDTH,y))

        for o in orbs: o.draw(screen)
        for n in enemies: n.draw(screen)
        player.draw(screen)

        # HUD
        s = font.render(f"Score: {int(score)}", True, TEXT)
        hs = font.render(f"High: {int(high_score)}", True, (200, 210, 220))
        info = font.render("Move: WASD/Arrows   Orb: slow time", True, (180,190,200))
        screen.blit(s, (14, 10))
        screen.blit(hs, (14, 36))
        screen.blit(info, (14, 62))

        if slow_left > 0:
            pct = int(100 * slow_left / SLOW_TIME)
            tip = font.render(f"Time slowed {pct}%", True, (160, 255, 190))
            screen.blit(tip, (WIDTH - tip.get_width() - 16, 10))

        if game_over:
            msg = big.render("Game Over", True, TEXT)
            sub = font.render("Press R to restart", True, (180,190,200))
            screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))

            if new_high:
                congrats = font.render(f"New High Score: {high_score}!", True, (255, 230, 120))
                screen.blit(congrats, congrats.get_rect(center=(WIDTH//2, HEIGHT//2 + 44)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
