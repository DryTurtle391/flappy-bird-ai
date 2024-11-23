import random
import os
import pygame
from pygame.locals import *
import neat
import time

pygame.font.init()

GEN = 0
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

STAT_FONT = pygame.font.SysFont("comicsans", 50)


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

    def collide(self, bird):
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


class Base:
    """Class for Base"""

    # Setting the velocity of the Base movement
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        # move both bases with same vel
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # add the other image back just behind the
        # current image of base the moment it is completely
        # out of the window
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, max_fit):
    """Draws the the bg image and bird on the window"""
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    gen_text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(gen_text, (10, 10))

    fitness_text = STAT_FONT.render("Fit: " + str(max_fit), 1, (255, 255, 255))
    win.blit(fitness_text, (10, 80))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []  # Bird(230, 350)  # initialising the bird

    # loop like this cus genomes has objects like (1, g)
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)  # initialising the base
    pipes = [Pipe(700)]  # initialising the pipe(s)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # creating the window
    clock = pygame.time.Clock()  # initiliasing the clock
    score = 0
    run = True
    while run:
        clock.tick(30)  # setting the frame rate
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # handling which pipe to look at if more than one pipe on the screen
        pipe_ind = 0
        if len(birds) > 0:
            if (
                len(pipes) > 0
                and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width()
            ):
                pipe_ind = 1
        else:
            run = False
            break
        # making the birds move rewarding it for every second it stays alive
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False  # var controlling spawning of new pipes
        rem = []  # pipe list to remove
        for pipe in pipes:
            for x, bird in enumerate(birds):

                if pipe.collide(bird):
                    ge[x].fitness -= 1  # punishing genomes which hit a pipe
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                # setting variables for adding a new pipe
                # when the bird has already passed the pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # adding pipe to removal list if it is out of the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        # actually adding a new pipe
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5  # rewarding genomes which pass through a pipe
            pipes.append(Pipe(700))

        # removing passed pipes
        for r in rem:
            pipes.remove(r)

        # handling falling of the bird or going above the screen
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        if len(genomes) > 1 and score > 20:
            break

        base.move()
        draw_window(
            win,
            birds,
            pipes,
            base,
            score,
            GEN,
            round(max(g.fitness for g in ge), 2) if len(ge) > 0 else 0,
        )


def run(config_file):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file,
    )

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)
    print("WINNER: " + str(winner))
    main([(1, winner)], config)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
