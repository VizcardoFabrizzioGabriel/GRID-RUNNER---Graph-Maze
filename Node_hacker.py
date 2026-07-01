import pygame, random, math

pygame.init()

W, H = 900, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("GRID RUNNER - Graph Maze")
clock = pygame.time.Clock()

# Colores cyberpunk
BG = (10, 10, 18)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GREEN = (0, 255, 120)
RED = (255, 60, 60)
YELLOW = (255, 220, 0)
DARK = (25, 25, 40)
GRAY = (60, 60, 80)
WHITE = (220, 220, 240)

font = pygame.font.SysFont("Consolas", 24, bold=True)
small = pygame.font.SysFont("Consolas", 16)


class Node:
    def __init__(self, x, y, node_type='empty'):
        self.x = x
        self.y = y
        self.type = node_type
        self.visited = False
        self.glow = 0.0

    def draw(self, px, py, size):
        cx = px + size // 2
        cy = py + size // 2

        if self.type == 'wall':
            pygame.draw.rect(screen, DARK, (px + 2, py + 2, size - 4, size - 4))
            pygame.draw.rect(screen, GRAY, (px + 2, py + 2, size - 4, size - 4), 1)
            return

        pygame.draw.rect(screen, BG, (px + 1, py + 1, size - 2, size - 2))

        if self.type == 'start':
            color = GREEN
            glow = 25
        elif self.type == 'end':
            color = MAGENTA
            glow = 30
        elif self.type == 'coin':
            color = YELLOW
            glow = 20
        elif self.type == 'trap':
            color = RED
            glow = 15
        elif self.visited:
            color = CYAN
            glow = 10
        else:
            color = GRAY
            glow = 0

        if glow > 0:
            for g in range(glow, 0, -5):
                s = pygame.Surface((g * 2, g * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color[:3], 15), (g, g), g)
                screen.blit(s, (cx - g, cy - g))

        r = size // 3
        if self.type == 'coin':
            pygame.draw.circle(screen, color, (cx, cy), r - 2)
        elif self.type == 'trap':
            pygame.draw.polygon(screen, color, [
                (cx, cy - r + 2), (cx + r - 2, cy + r - 2), (cx - r + 2, cy + r - 2)
            ])
        elif self.type in ['start', 'end']:
            pygame.draw.circle(screen, color, (cx, cy), r)
            pygame.draw.circle(screen, BG, (cx, cy), r - 4)
            t = small.render('S' if self.type == 'start' else 'E', True, color)
            screen.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
        else:
            pygame.draw.circle(screen, color, (cx, cy), 3 if self.visited else 2)

        self.glow += 0.05


class Level:
    def __init__(self, width, height, num_walls, num_coins, num_traps, time_limit):
        self.w = width
        self.h = height
        self.time_limit = time_limit
        self.grid = {}
        self.player = (0, 0)
        self.end = (width - 1, height - 1)
        self.coins_collected = 0
        self.total_coins = num_coins
        self.start_time = None

        for x in range(width):
            for y in range(height):
                self.grid[(x, y)] = Node(x, y, 'empty')

        self.grid[(0, 0)].type = 'start'
        self.grid[(width - 1, height - 1)].type = 'end'

        self.place_walls(num_walls)

        for _ in range(num_coins):
            self.place_random('coin')

        for _ in range(num_traps):
            self.place_random('trap')

    def place_walls(self, num):
        placed = 0
        attempts = 0
        while placed < num and attempts < 1000:
            x = random.randint(1, self.w - 2)
            y = random.randint(0, self.h - 1)
            if self.grid[(x, y)].type == 'empty' and (x, y) != (0, 0) and (x, y) != self.end:
                self.grid[(x, y)].type = 'wall'
                if self.has_path():
                    placed += 1
                else:
                    self.grid[(x, y)].type = 'empty'
            attempts += 1

    def has_path(self):
        from collections import deque
        q = deque([(0, 0)])
        visited = {(0, 0)}
        while q:
            x, y = q.popleft()
            if (x, y) == self.end:
                return True
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in visited:
                    if self.grid[(nx, ny)].type != 'wall':
                        visited.add((nx, ny))
                        q.append((nx, ny))
        return False

    def place_random(self, node_type):
        attempts = 0
        while attempts < 100:
            x = random.randint(0, self.w - 1)
            y = random.randint(0, self.h - 1)
            if self.grid[(x, y)].type == 'empty':
                self.grid[(x, y)].type = node_type
                return
            attempts += 1


class Game:
    def __init__(self):
        self.levels = [
            Level(8, 6, 8, 3, 0, 60),
            Level(10, 8, 15, 5, 2, 90),
            Level(12, 10, 25, 7, 4, 120),
            Level(15, 12, 40, 10, 6, 150),
        ]
        self.current = 0
        self.player_pos = (0, 0)
        self.score = 0
        self.lives = 3
        self.state = 'playing'
        self.msg = ""
        self.msg_timer = 0
        self.move_cooldown = 0
        self.reset_level()

    def reset_level(self):
        self.player_pos = (0, 0)
        self.levels[self.current].player = (0, 0)
        self.levels[self.current].coins_collected = 0
        self.levels[self.current].start_time = pygame.time.get_ticks()
        for node in self.levels[self.current].grid.values():
            node.visited = False
        self.state = 'playing'
        self.msg = ""
        self.msg_timer = 0

    def move(self, dx, dy):
        if self.state != 'playing' or self.move_cooldown > 0:
            return

        level = self.levels[self.current]
        nx = self.player_pos[0] + dx
        ny = self.player_pos[1] + dy

        if nx < 0 or nx >= level.w or ny < 0 or ny >= level.h:
            return

        node = level.grid[(nx, ny)]

        if node.type == 'wall':
            self.msg = "BLOCKED!"
            self.msg_timer = 30
            return

        self.player_pos = (nx, ny)
        self.move_cooldown = 8
        node.visited = True

        if node.type == 'coin':
            node.type = 'empty'
            level.coins_collected += 1
            self.score += 100
            self.msg = f"+100 COIN! ({level.coins_collected}/{level.total_coins})"
            self.msg_timer = 40

        if node.type == 'trap':
            self.lives -= 1
            node.type = 'empty'
            self.msg = "TRAP! -1 LIFE"
            self.msg_timer = 50
            if self.lives <= 0:
                self.state = 'game_over'
                self.msg = "GAME OVER!"
                self.msg_timer = 200

        if node.type == 'end':
            time_bonus = max(0, int(self.time_left() * 10))
            self.score += (level.coins_collected * 100) + time_bonus
            self.state = 'level_complete'
            self.msg = f"LEVEL CLEAR! +{time_bonus} bonus"
            self.msg_timer = 150

    def time_left(self):
        level = self.levels[self.current]
        if level.start_time is None:
            return level.time_limit
        elapsed = (pygame.time.get_ticks() - level.start_time) / 1000
        return max(0, level.time_limit - elapsed)

    def next_level(self):
        self.current += 1
        if self.current >= len(self.levels):
            self.state = 'game_won'
            self.msg = "ALL LEVELS COMPLETE!"
            self.msg_timer = 300
        else:
            self.reset_level()

    def update(self):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1

        if self.state == 'playing' and self.time_left() <= 0:
            self.state = 'game_over'
            self.msg = "TIME OUT!"
            self.msg_timer = 200

        if self.msg_timer > 0:
            self.msg_timer -= 1

    def draw(self):
        screen.fill(BG)

        # FIX: Si current >= len(levels), mostrar pantalla de victoria
        if self.current >= len(self.levels):
            self.draw_victory()
            return

        level = self.levels[self.current]

        cell_size = min((W - 300) // level.w, (H - 100) // level.h)
        offset_x = (W - 300 - level.w * cell_size) // 2
        offset_y = (H - level.h * cell_size) // 2 + 20

        for y in range(level.h):
            for x in range(level.w):
                px = offset_x + x * cell_size
                py = offset_y + y * cell_size
                level.grid[(x, y)].draw(px, py, cell_size)

        px = offset_x + self.player_pos[0] * cell_size + cell_size // 2
        py = offset_y + self.player_pos[1] * cell_size + cell_size // 2

        for g in range(35, 5, -8):
            s = pygame.Surface((g * 2, g * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*GREEN[:3], 20), (g, g), g)
            screen.blit(s, (px - g, py - g))

        pygame.draw.circle(screen, GREEN, (px, py), cell_size // 3)
        pygame.draw.circle(screen, WHITE, (px, py), cell_size // 5)

        # Panel derecho
        panel_x = W - 280
        pygame.draw.rect(screen, DARK, (panel_x, 0, 280, H))
        pygame.draw.line(screen, GRAY, (panel_x, 0), (panel_x, H), 2)

        y = 30
        t = font.render("GRID RUNNER", True, CYAN)
        screen.blit(t, (panel_x + 20, y))
        y += 50

        t = font.render(f"Level {self.current + 1}/{len(self.levels)}", True, WHITE)
        screen.blit(t, (panel_x + 20, y))
        y += 35

        time_left = self.time_left()
        bar_w = 240
        bar_h = 12
        ratio = time_left / level.time_limit

        color = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        pygame.draw.rect(screen, GRAY, (panel_x + 20, y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(screen, color, (panel_x + 20, y, int(bar_w * ratio), bar_h), border_radius=6)

        t = small.render(f"{int(time_left)}s", True, WHITE)
        screen.blit(t, (panel_x + 20 + bar_w // 2 - 15, y - 18))
        y += 40

        stats = [
            (f"Score: {self.score}", CYAN),
            (f"Lives: {self.lives}", GREEN),
            (f"Coins: {level.coins_collected}/{level.total_coins}", YELLOW),
            (f"Grid: {level.w}x{level.h}", GRAY),
        ]

        for text, color in stats:
            t = small.render(text, True, color)
            screen.blit(t, (panel_x + 20, y))
            y += 28

        y += 30
        t = font.render("CONTROLS", True, GRAY)
        screen.blit(t, (panel_x + 20, y))
        y += 30

        controls = [
            "Arrow Keys: Move",
            "R: Restart level",
            "N: Next level",
            "",
            "Goal: Reach E node",
            "Collect coins",
            "Avoid red traps!",
        ]

        for ctrl in controls:
            if ctrl:
                t = small.render(ctrl, True, GRAY)
                screen.blit(t, (panel_x + 20, y))
            y += 22

        self.draw_message()
        self.draw_overlay()

    def draw_victory(self):
        """Pantalla de victoria cuando se completan todos los niveles"""
        screen.fill(BG)
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        t = font.render("SYSTEM HACKED!", True, GREEN)
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 60))

        t = font.render(f"Final Score: {self.score}", True, CYAN)
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2))

        t = small.render("Press R to play again", True, WHITE)
        screen.blit(t, (W // 2 - t.get_width() // 2, H // 2 + 60))

    def draw_message(self):
        if self.msg_timer > 0:
            alpha = min(255, self.msg_timer * 4)
            msg_surf = font.render(self.msg, True,
                                   GREEN if any(w in self.msg for w in ["CLEAR", "COIN", "bonus"])
                                   else (RED if any(w in self.msg for w in ["OVER", "TRAP", "OUT", "BLOCKED"])
                                         else CYAN))

            msg_w = msg_surf.get_width() + 30
            msg_h = 45
            msg_x = (W - 300) // 2 - msg_w // 2
            msg_y = H - 90

            overlay = pygame.Surface((msg_w, msg_h), pygame.SRCALPHA)
            overlay.fill((*DARK[:3], min(200, alpha)))
            screen.blit(overlay, (msg_x, msg_y))

            border_color = GREEN if "CLEAR" in self.msg else (
                RED if any(w in self.msg for w in ["OVER", "TRAP", "OUT"]) else CYAN)
            pygame.draw.rect(screen, border_color, (msg_x, msg_y, msg_w, msg_h), 2, border_radius=8)

            screen.blit(msg_surf, (msg_x + 15, msg_y + 10))

    def draw_overlay(self):
        if self.state in ['game_over', 'game_won']:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            if self.state == 'game_won':
                t = font.render("SYSTEM HACKED!", True, GREEN)
                screen.blit(t, (W // 2 - t.get_width() // 2 - 140, H // 2 - 40))
                t = font.render(f"Final Score: {self.score}", True, CYAN)
                screen.blit(t, (W // 2 - t.get_width() // 2 - 140, H // 2 + 10))
            else:
                t = font.render("GAME OVER", True, RED)
                screen.blit(t, (W // 2 - t.get_width() // 2 - 140, H // 2 - 20))

            t = small.render("Press R to restart", True, WHITE)
            screen.blit(t, (W // 2 - t.get_width() // 2 - 140, H // 2 + 50))


# Main
game = Game()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game.state == 'playing':
                if event.key == pygame.K_UP:
                    game.move(0, -1)
                elif event.key == pygame.K_DOWN:
                    game.move(0, 1)
                elif event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)

            if event.key == pygame.K_r:
                if game.state in ['game_over', 'game_won'] or game.current >= len(game.levels):
                    game = Game()
                else:
                    game.reset_level()

            if event.key in [pygame.K_n, pygame.K_SPACE] and game.state == 'level_complete':
                game.next_level()

    game.update()
    game.draw()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()