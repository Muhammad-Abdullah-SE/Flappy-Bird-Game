import pygame as pg
import sys
import random

pg.init()
pg.mixer.init()


class Bird:
    """The player-controlled bird."""

    def __init__(self, scale_factor):
        # Load both wing frames and scale them
        self.img_up = pg.transform.scale_by(
            pg.image.load("Assets/birdup.png").convert_alpha(), scale_factor
        )
        self.img_down = pg.transform.scale_by(
            pg.image.load("Assets/birddown.png").convert_alpha(), scale_factor
        )
        self.current_img = self.img_up
        self.rect = self.current_img.get_rect(center=(100, 300))

        # Physics
        self.gravity = 0.5
        self.flap_power = -8
        self.velocity = 0

        # Wing animation timer
        self.anim_timer = 0

        # Flap sound
        self.flap_sfx = pg.mixer.Sound("Assets/sfx/flap.wav")
        self.flap_sfx.set_volume(0.3)

    def flap(self):
        """Apply an upward impulse."""
        self.velocity = self.flap_power
        self.flap_sfx.play()

    def update(self):
        """Apply gravity and animate wings."""
        self.velocity += self.gravity
        self.rect.y += int(self.velocity)

        # Toggle wing sprite every 8 frames
        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.current_img = (
                self.img_down if self.current_img is self.img_up else self.img_up
            )

    def draw(self, surface):
        """Draw the bird rotated according to its velocity."""
        angle = max(-25, min(15, -self.velocity * 2.5))
        rotated = pg.transform.rotate(self.current_img, angle)
        rotated_rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rotated_rect)

    def reset(self, center_y=300):
        """Reset the bird to starting position."""
        self.rect.center = (100, center_y)
        self.velocity = 0
        self.anim_timer = 0
        self.current_img = self.img_up


class Pipe:
    """A pair of top and bottom pipes."""

    def __init__(self, x, scale_factor, win_height, ground_y):
        self.pipe_up_img = pg.transform.scale_by(
            pg.image.load("Assets/pipeup.png").convert_alpha(), scale_factor
        )
        self.pipe_down_img = pg.transform.scale_by(
            pg.image.load("Assets/pipedown.png").convert_alpha(), scale_factor
        )

        self.gap = 180  # vertical gap between pipes
        self.speed = 3

        # Random gap position (y centre of the gap)
        min_y = 120
        max_y = ground_y - 120 - self.gap
        gap_top = random.randint(min_y, max_y)

        # Bottom pipe (opening faces up)
        self.rect_bottom = self.pipe_up_img.get_rect()
        self.rect_bottom.topleft = (x, gap_top + self.gap)

        # Top pipe (opening faces down)
        self.rect_top = self.pipe_down_img.get_rect()
        self.rect_top.bottomleft = (x, gap_top)

        self.scored = False  # has the player passed this pipe?

    def update(self):
        self.rect_bottom.x -= self.speed
        self.rect_top.x -= self.speed

    def draw(self, surface):
        surface.blit(self.pipe_up_img, self.rect_bottom)
        surface.blit(self.pipe_down_img, self.rect_top)

    def off_screen(self):
        return self.rect_bottom.right < 0


class Game:
    """Main game controller."""

    def __init__(self):
        # Window configuration
        self.width = 600
        self.height = 670
        self.scale_factor = 1.5
        self.FPS = 60

        self.win = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption("Flappy Bird")
        self.clock = pg.time.Clock()

        # ---- Load images ----
        self.bg_img = pg.transform.scale_by(
            pg.image.load("Assets/bg.png").convert(), self.scale_factor
        )
        self.ground1_img = pg.transform.scale_by(
            pg.image.load("Assets/ground.png").convert(), self.scale_factor
        )
        self.ground2_img = pg.transform.scale_by(
            pg.image.load("Assets/ground.png").convert(), self.scale_factor
        )

        # Ground rects (two copies for seamless scrolling)
        self.ground_y = 568
        self.ground1_rect = self.ground1_img.get_rect()
        self.ground2_rect = self.ground2_img.get_rect()
        self.ground1_rect.topleft = (0, self.ground_y)
        self.ground2_rect.topleft = (self.ground1_rect.right, self.ground_y)
        self.ground_speed = 3

        # ---- Font ----
        self.font_large = pg.font.Font("Assets/font.ttf", 48)
        self.font_medium = pg.font.Font("Assets/font.ttf", 28)
        self.font_small = pg.font.Font("Assets/font.ttf", 20)

        # ---- Sound effects ----
        self.score_sfx = pg.mixer.Sound("Assets/sfx/score.wav")
        self.score_sfx.set_volume(0.4)
        self.dead_sfx = pg.mixer.Sound("Assets/sfx/dead.wav")
        self.dead_sfx.set_volume(0.5)

        # ---- Game objects ----
        self.bird = Bird(self.scale_factor)
        self.pipes = []
        self.pipe_timer = 0
        self.pipe_interval = 90  # frames between pipe spawns

        # ---- Game state ----
        self.score = 0
        self.best_score = 0
        self.state = "start"  # "start", "playing", "gameover"

        self.gameLoop()

    # ---- Ground scrolling ----
    def update_ground(self):
        self.ground1_rect.x -= self.ground_speed
        self.ground2_rect.x -= self.ground_speed
        if self.ground1_rect.right <= 0:
            self.ground1_rect.x = self.ground2_rect.right
        if self.ground2_rect.right <= 0:
            self.ground2_rect.x = self.ground1_rect.right

    def draw_ground(self):
        self.win.blit(self.ground1_img, self.ground1_rect)
        self.win.blit(self.ground2_img, self.ground2_rect)

    # ---- Pipes ----
    def spawn_pipe(self):
        self.pipes.append(
            Pipe(self.width + 50, self.scale_factor, self.height, self.ground_y)
        )

    def update_pipes(self):
        self.pipe_timer += 1
        if self.pipe_timer >= self.pipe_interval:
            self.pipe_timer = 0
            self.spawn_pipe()

        for pipe in self.pipes:
            pipe.update()

        # Remove off-screen pipes
        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def draw_pipes(self):
        for pipe in self.pipes:
            pipe.draw(self.win)

    # ---- Collision ----
    def check_collisions(self):
        # Bird mask for pixel-perfect collision
        bird_mask = pg.mask.from_surface(self.bird.current_img)

        for pipe in self.pipes:
            # Check bottom pipe
            pipe_mask_bottom = pg.mask.from_surface(pipe.pipe_up_img)
            offset_b = (
                pipe.rect_bottom.x - self.bird.rect.x,
                pipe.rect_bottom.y - self.bird.rect.y,
            )
            if bird_mask.overlap(pipe_mask_bottom, offset_b):
                return True

            # Check top pipe
            pipe_mask_top = pg.mask.from_surface(pipe.pipe_down_img)
            offset_t = (
                pipe.rect_top.x - self.bird.rect.x,
                pipe.rect_top.y - self.bird.rect.y,
            )
            if bird_mask.overlap(pipe_mask_top, offset_t):
                return True

        # Hit the ground or fly off the top
        if self.bird.rect.bottom >= self.ground_y or self.bird.rect.top <= 0:
            return True

        return False

    # ---- Scoring ----
    def update_score(self):
        for pipe in self.pipes:
            if not pipe.scored and pipe.rect_bottom.right < self.bird.rect.left:
                pipe.scored = True
                self.score += 1
                self.score_sfx.play()

    # ---- UI text helpers ----
    def draw_text_outlined(self, text, font, color, outline_color, center):
        """Draw text with a dark outline for readability."""
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    outline_rect = outline_surf.get_rect(
                        center=(center[0] + dx, center[1] + dy)
                    )
                    self.win.blit(outline_surf, outline_rect)
        main_surf = font.render(text, True, color)
        main_rect = main_surf.get_rect(center=center)
        self.win.blit(main_surf, main_rect)

    # ---- Screens ----
    def draw_start_screen(self):
        self.draw_text_outlined(
            "Flappy Bird",
            self.font_large,
            (255, 255, 255),
            (0, 0, 0),
            (self.width // 2, 180),
        )
        self.draw_text_outlined(
            "Press SPACE or CLICK to Flap",
            self.font_small,
            (255, 255, 230),
            (0, 0, 0),
            (self.width // 2, 280),
        )
        self.draw_text_outlined(
            "Press SPACE to Start",
            self.font_medium,
            (255, 255, 100),
            (0, 0, 0),
            (self.width // 2, 350),
        )

    def draw_score(self):
        self.draw_text_outlined(
            str(self.score),
            self.font_large,
            (255, 255, 255),
            (0, 0, 0),
            (self.width // 2, 50),
        )

    def draw_game_over_screen(self):
        self.draw_text_outlined(
            "Game Over",
            self.font_large,
            (255, 80, 80),
            (0, 0, 0),
            (self.width // 2, 180),
        )
        self.draw_text_outlined(
            f"Score: {self.score}",
            self.font_medium,
            (255, 255, 255),
            (0, 0, 0),
            (self.width // 2, 260),
        )
        self.draw_text_outlined(
            f"Best: {self.best_score}",
            self.font_medium,
            (255, 215, 0),
            (0, 0, 0),
            (self.width // 2, 310),
        )
        self.draw_text_outlined(
            "Press SPACE to Restart",
            self.font_small,
            (255, 255, 230),
            (0, 0, 0),
            (self.width // 2, 400),
        )

    # ---- Reset ----
    def reset_game(self):
        self.bird.reset()
        self.pipes.clear()
        self.pipe_timer = 0
        self.score = 0
        self.ground1_rect.topleft = (0, self.ground_y)
        self.ground2_rect.topleft = (self.ground1_rect.right, self.ground_y)

    # ---- Main loop ----
    def gameLoop(self):
        while True:
            # ---- Event handling ----
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        if self.state == "start":
                            self.state = "playing"
                            self.bird.flap()
                        elif self.state == "playing":
                            self.bird.flap()
                        elif self.state == "gameover":
                            self.reset_game()
                            self.state = "playing"
                            self.bird.flap()

                if event.type == pg.MOUSEBUTTONDOWN:
                    if self.state == "start":
                        self.state = "playing"
                        self.bird.flap()
                    elif self.state == "playing":
                        self.bird.flap()
                    elif self.state == "gameover":
                        self.reset_game()
                        self.state = "playing"
                        self.bird.flap()

            # ---- Update ----
            if self.state == "playing":
                self.bird.update()
                self.update_pipes()
                self.update_score()
                self.update_ground()

                if self.check_collisions():
                    self.dead_sfx.play()
                    if self.score > self.best_score:
                        self.best_score = self.score
                    self.state = "gameover"

            elif self.state == "start":
                # Scroll the ground on the start screen for visual flair
                self.update_ground()
                # Gentle bobbing animation for the bird
                self.bird.anim_timer += 1
                if self.bird.anim_timer >= 8:
                    self.bird.anim_timer = 0
                    self.bird.current_img = (
                        self.bird.img_down
                        if self.bird.current_img is self.bird.img_up
                        else self.bird.img_up
                    )

            # ---- Draw ----
            self.win.blit(self.bg_img, (0, -250))
            self.draw_pipes()
            self.draw_ground()
            self.bird.draw(self.win)

            if self.state == "start":
                self.draw_start_screen()
            elif self.state == "playing":
                self.draw_score()
            elif self.state == "gameover":
                self.draw_score()
                self.draw_game_over_screen()

            pg.display.update()
            self.clock.tick(self.FPS)


game = Game()