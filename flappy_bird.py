import random
import os
import pygame
from pygame.locals import *
import neat
import time

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))
    )
    for x in range(1, 4)
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))


class Bird:
    """Class representing a Bird"""

    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """Representing the jump action of the Bird"""
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """This function is called on every frame to calculate
        the movement of the bird on that specific frame"""

        # registering the amount of time the bird has been moving
        self.tick_count += 1

        # calculating the distance the bird will move in this frame
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2

        # Limiting d and adding a bit of fine tuning to the movement
        d = min(d, 16)

        # i.e. if we are moving up keep moving a bit longer to a get a nice arc
        if d < 0:
            d -= 2

        # adjusting position of the bird based on displacement d calcculated
        self.y = self.y + d

        # adjusting the tilt of the image based on position of the bird
        if d < 0 and self.y < self.height + 50:
            self.tilt = max(self.tilt, self.MAX_ROTATION)
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """Controls the application of animations based on movement data calculated above"""
        self.img_count += 1

        # simulating the flapping animation by changing images based on animation time
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # for animating the movement of the bird when it suddenly jumps
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # actually rotating the bird based on the tilt
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center
        )
        win.blit(rotated_image, new_rect.topleft)  # blit does draws on the window

    def get_mask(self):
        """Controls collisions"""
        return pygame.mask.from_surface(self.img)


class Pipe:
    """Class representing pipe(s)"""

    GAP = 200
    VEL = 5

    def __init__(self, x):

        # position along the x-axis
        # the height determines the random position of the pipes
        self.x = x
        self.height = 0

        # top is y coordinate of the top pipe
        # bottom is the y coordinate of the bottom pipe
        self.top = 0
        self.bottom = 0

        # Inverted top pipe image and bottom pipe image
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # relevant for AI
        self.passed = False
        self.set_height()

    def set_height(self):
        # Set the random height and calculate top and bottom based on it
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        # move the pipes every frame
        self.x -= self.VEL

    def draw(self, win):
        # draw the pipes on the screen every frame based on fresh coordinates
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win):
        """Checks collision between bird and pipes"""
        # Here we use a concept of mask to check collision
        # since images are drawn as rectangles, it is important we use masks
        # on the images to determine pixel perfect collisions

        # Creating masks for birds and pipes
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Creating offsets which tells the distance between bird and pipes
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # variables checking if collision has occured
        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        if t_point or b_point:
            return True

        return False


def draw_window(win, bird):
    """Draws the the bg image and bird on the window"""
    win.blit(BG_IMG, (0, 0))
    bird.draw(win)
    pygame.display.update()


def main():
    bird = Bird(200, 200)  # initialising the bird
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # creating the window
    clock = pygame.time.Clock()  # initiliasing the clock

    run = True
    while run:
        clock.tick(60)  # setting the frame rate
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        # bird.move()
        draw_window(win, bird)

    pygame.quit()


main()
