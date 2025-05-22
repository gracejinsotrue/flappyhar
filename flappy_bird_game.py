import math
import os
from random import randint
from collections import deque
import serial  # Add serial module

import pygame
from pygame.locals import *


FPS = 60
ANIMATION_SPEED = 0.18 
WIN_WIDTH = 284 * 2    
WIN_HEIGHT = 512


class Bird(pygame.sprite.Sprite):
   
    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.18
    CLIMB_SPEED = 0.25
    CLIMB_DURATION = 333.3

    def __init__(self, x, y, msec_to_climb, images):
        
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
    
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.CLIMB_DURATION
            self.y -= (Bird.CLIMB_SPEED * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self):
       
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000

    def __init__(self, pipe_end_img, pipe_body_img):
      
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()  
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -                  
             3 * Bird.HEIGHT -             
             3 * PipePair.PIECE_HEIGHT) /  
            PipePair.PIECE_HEIGHT          
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # top pipe
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))
        
        self.top_pieces += 1
        self.bottom_pieces += 1

        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self):
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
    
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        return pygame.sprite.collide_mask(self, bird)


def load_images():
  

    def load_image(img_file_name):
        
        file_name = os.path.join(os.path.dirname(__file__),
                                 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img

    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):

    return fps * milliseconds / 1000.0


def main():

    pygame.init()

    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('FRDM-KL46Z Flappy Harjot')

    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)  # default font
    images = load_images()
    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()

    # serial blah blah
    try:
        # TODO: me when ts will not be com5 universally i should probably fix
        ser = serial.Serial('COM5', 115200, timeout=0.01)
        print("Connected to FRDM-KL46Z")
        kl46z_connected = True
    except Exception as e:
        print(f"Could not connect to FRDM-KL46Z: {e}")
        print("Using keyboard controls only (Space, Up, Return)")
        kl46z_connected = False
        ser = None

    frame_clock = 0  
    score = 0
    done = paused = False

    display_surface.fill((0, 0, 0))
    title_font = pygame.font.SysFont(None, 48, bold=True)
    title = title_font.render('Flappy Bird - KL46Z Edition', True, (255, 255, 255))
    instructions1 = score_font.render('Press SPACE to start', True, (255, 255, 255))
    instructions2 = score_font.render('Use KL46Z SW1 button or SPACE to jump', True, (255, 255, 255))
    status = score_font.render(f'KL46Z Status: {"Connected" if kl46z_connected else "Not Connected"}', True, 
                              (0, 255, 0) if kl46z_connected else (255, 0, 0))
    
    display_surface.blit(title, (WIN_WIDTH/2 - title.get_width()/2, WIN_HEIGHT/3))
    display_surface.blit(instructions1, (WIN_WIDTH/2 - instructions1.get_width()/2, WIN_HEIGHT/2))
    display_surface.blit(instructions2, (WIN_WIDTH/2 - instructions2.get_width()/2, WIN_HEIGHT/2 + 40))
    display_surface.blit(status, (WIN_WIDTH/2 - status.get_width()/2, WIN_HEIGHT/2 + 80))
    pygame.display.flip()
    
   
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                pygame.quit()
                return
            elif e.type == KEYUP and e.key in (K_RETURN, K_SPACE):
                waiting = False
        
        # check for KL46Z button press to start
        if kl46z_connected:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line == "JUMP":
                    waiting = False
            except Exception as e:
                pass
        
        clock.tick(FPS)
    
    # main
    while not done:
        clock.tick(FPS)
        #manually handling 
        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pp = PipePair(images['pipe-end'], images['pipe-body'])
            pipes.append(pp)

        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                    e.key in (K_UP, K_RETURN, K_SPACE)):
                bird.msec_to_climb = Bird.CLIMB_DURATION
        
        # Check for FRDM-KL46Z input
        if kl46z_connected:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line == "JUMP":
                    bird.msec_to_climb = Bird.CLIMB_DURATION
            except Exception as e:
                pass  # ignore serial errors during gameplay

        if paused:
            continue #me when if will crash dont

        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
            done = True

        for x in (0, WIN_WIDTH / 2):
            display_surface.blit(images['background'], (x, 0))

        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        bird.update()
        display_surface.blit(bird.image, bird.rect)

        # update and display score
        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

        pygame.display.flip()
        frame_clock += 1
    
    # least hardcoded grace code
    display_surface.fill((0, 0, 0))
    game_over_font = pygame.font.SysFont(None, 48, bold=True)
    game_over = game_over_font.render('Game Over', True, (255, 0, 0))
    final_score = score_font.render(f'Final Score: {score}', True, (255, 255, 255))
    restart_instructions = score_font.render('Press SPACE to play again', True, (255, 255, 255))
    quit_instructions = score_font.render('Press ESC to quit', True, (255, 255, 255))
    
    display_surface.blit(game_over, (WIN_WIDTH/2 - game_over.get_width()/2, WIN_HEIGHT/3))
    display_surface.blit(final_score, (WIN_WIDTH/2 - final_score.get_width()/2, WIN_HEIGHT/2))
    display_surface.blit(restart_instructions, (WIN_WIDTH/2 - restart_instructions.get_width()/2, WIN_HEIGHT/2 + 40))
    display_surface.blit(quit_instructions, (WIN_WIDTH/2 - quit_instructions.get_width()/2, WIN_HEIGHT/2 + 80))
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                waiting = False
                break
            elif e.type == KEYUP and e.key in (K_RETURN, K_SPACE):
                waiting = False
                main()  # Restart the game
        
        # ts shi dont reconnect rn
        if kl46z_connected:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line == "JUMP":
                    waiting = False
                    main()  #restart
            except Exception as e:
                pass
        
        clock.tick(FPS)
    
    # claen up 
    if ser:
        ser.close()
    
    print('Game over! Score: %i' % score)
    pygame.quit()


if __name__ == '__main__':
    main()