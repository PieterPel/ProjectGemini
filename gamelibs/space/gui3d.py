import numpy
import pygame

from gamelibs import sprite, pixelfont, util_draw
from gamelibs.animation import Animation
from gamelibs.space import math3d


class Ship(sprite.GUISprite):
    UP = 1
    DOWN = 2
    LEFT = 4
    RIGHT = 8
    TWIST = 16
    ROTATYNESS = 45

    def __init__(self, level, rect):
        super().__init__(level, None, rect)
        frames = self.level.game.loader.get_spritesheet("ship.png", (24, 32))
        self.anim_dict = {
            "normal": Animation(frames[0:3]),
            "turn": Animation(frames[3:6]),
            "up": Animation(frames[6:9]),
            "down": Animation(frames[9:12]),
        }
        self.flipped_anim_dict = {}
        for key, anim in self.anim_dict.items():
            self.flipped_anim_dict[key] = Animation(anim.frames, anim.speed, True)
        self.surface = pygame.Surface((48, 32), pygame.SRCALPHA).convert_alpha()
        self.direction = 0
        self.anim_left = self.anim_dict["normal"]
        self.anim_right = self.flipped_anim_dict["normal"]

    def up(self):
        self.direction |= self.UP

    def down(self):
        self.direction |= self.DOWN

    def left(self):
        self.direction |= self.LEFT

    def right(self):
        self.direction |= self.RIGHT

    def twist(self):
        self.direction |= self.TWIST

    def update(self, dt):
        for anim in self.anim_dict.values():
            anim.update(dt)
        for anim in self.flipped_anim_dict.values():
            anim.update(dt)

    def draw(self, surface):
        # figure out which animation to use on each side based on direction of travel
        # lots of ifs, it's a right pain
        left_upness = 0
        right_upness = 0
        turn_left = False
        turn_right = False
        rotation = 0
        if self.direction & self.UP and not self.direction & self.DOWN:
            left_upness += 1
            right_upness += 1
        if self.direction & self.DOWN and not self.direction & self.UP:
            left_upness -= 1
            right_upness -= 1
        if self.direction & self.TWIST:
            left_upness += 1
            right_upness -= 1
        if self.direction & self.LEFT and not self.direction & self.RIGHT:
            turn_left = True
            rotation = self.ROTATYNESS
            right_upness += 1
        if self.direction & self.RIGHT and not self.direction & self.LEFT:
            turn_right = True
            rotation = -self.ROTATYNESS
            left_upness += 1
        if left_upness > 0:
            self.anim_left = self.anim_dict["up"]
        if left_upness == 0:
            self.anim_left = self.anim_dict["normal"]
        if left_upness < 0:
            self.anim_left = self.anim_dict["down"]
        if right_upness > 0:
            self.anim_right = self.flipped_anim_dict["up"]
        if right_upness == 0:
            self.anim_right = self.flipped_anim_dict["normal"]
        if right_upness < 0:
            self.anim_right = self.flipped_anim_dict["down"]
        if turn_left:
            self.anim_left = self.anim_dict["turn"]
        if turn_right:
            self.anim_right = self.flipped_anim_dict["turn"]
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(self.anim_left.image, (0, 0))
        self.surface.blit(self.anim_right.image, (24, 0))
        blit_surface = pygame.transform.rotate(self.surface, rotation)
        surface.blit(blit_surface, blit_surface.get_rect(center=self.rect.center))
        self.direction = 0


class Compass(sprite.GUISprite):
    def __init__(self, level, origin):
        super().__init__(level)
        self.origin = origin
        self.positions = (
            numpy.array(((0, 1, 0), (1, 0, 0), (0, 0, 1)), dtype=numpy.float64) * 10
        )
        self.colors = ("red", "green", "blue")
        self.letters = [level.game.loader.font.render(i) for i in ("N", "E", "Q")]

    def draw(self, surface):
        positions_copy = self.positions.copy()
        math3d.rotate_points(positions_copy, -self.level.camera.rotation)
        for offset, color, letter in sorted(
            zip(positions_copy, self.colors, self.letters), key=lambda x: -x[0][2]
        ):
            endpoint = self.origin + offset[:2]
            pygame.draw.line(surface, color, self.origin, endpoint, width=2)
            surface.blit(letter, self.origin + offset[:2] * 1.5 - (3, 4))


class PlanetIndicator(sprite.GUISprite):
    STATE_IDLE = 0
    STATE_PLANET = 1
    STATE_PAUSED = 2
    STATE_ENTER = 3

    def __init__(self, level, rect):
        super().__init__(level)
        self.level = level
        self.rect = rect
        self.log_speed = 30
        self.idle_log_speed = 2
        self.age = 0
        self.font = pixelfont.PixelFont(
            self.level.game.loader.get_spritesheet("font.png", (7, 8))
        )
        self.state = self.STATE_IDLE
        self.last_state = self.STATE_IDLE

    def confirm_quit(self):
        self.state = self.STATE_PAUSED

    def enter(self):
        self.state = self.STATE_ENTER

    def confirm_enter(self):
        self.state = self.STATE_PLANET

    def fail_confirmation(self):
        self.state = self.STATE_IDLE

    def reset(self):
        self.state = self.STATE_IDLE
        self.age = 0
        self.last_state = self.STATE_IDLE

    def update(self, dt):
        super().update(dt)
        self.age += dt
        if self.state != self.last_state:
            self.age = 0
        self.last_state = self.state

    def draw(self, surface):
        if self.state == self.STATE_IDLE:
            text = "." * int((self.age * self.idle_log_speed) % 4)
        elif self.state == self.STATE_PLANET:
            text = f"Auto land on planet {self.level.possible_planet}?\nYes: enter"
            text = text[: min(int(self.age * self.log_speed), len(text))]
        elif self.state == self.STATE_PAUSED:
            text = f"Save and quit?\nYes: enter, No: esc"
            text = text[: min(int(self.age * self.log_speed), len(text))]
        elif self.state == self.STATE_ENTER:
            text = f"Autopilot: FUNCTIONAL\nInitiating landing..."
        self.font.render_to(surface, self.rect, text)


class MiniMap(sprite.GUISprite):
    def __init__(self, level, rect):
        super().__init__(level)
        self.rect = rect

    def update(self, dt):
        super().update(dt)

    def draw(self, surface):
        ...


class GUIRendererHW:
    def __init__(self, level, gui):
        self.level = level
        self.gui = gui

        self.surface = None
        self.gl_surface = None
        self.pipline = None

        self.recompile_shaders()

    def recompile_shaders(self):
        self.surface = pygame.Surface(util_draw.RESOLUTION, pygame.SRCALPHA)
        self.gl_surface = self.level.game.context.image(util_draw.RESOLUTION)

        self.pipeline = self.level.game.context.pipeline(
            vertex_shader=self.level.game.loader.get_vertex_shader("scale"),
            fragment_shader=self.level.game.loader.get_fragment_shader("overlay"),
            framebuffer=[self.level.game.window.get_gl_surface()],
            topology="triangle_strip",
            vertex_count=4,
            layout=[
                {
                    "name": "input_texture",
                    "binding": 0,
                }
            ],
            resources=[
                {
                    "type": "sampler",
                    "binding": 0,
                    "image": self.gl_surface,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                }
            ],
        )

    def render(self):
        self.surface.fill((0, 0, 0, 0))
        for element in self.gui:
            element.draw(self.surface)
        self.gl_surface.write(pygame.image.tobytes(self.surface, "RGBA", True))
        self.pipeline.render()
