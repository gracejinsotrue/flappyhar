import math
import os
from random import randint
from collections import deque
import serial 

import pygame
from pygame.locals import *


FPS = 60
ANIMATION_SPEED = 0.18 
WIN_WIDTH = 284 * 2    
WIN_HEIGHT = 512
BACKGROUND_WIDTH = 1136  


class Bird(pygame.sprite.Sprite):
   
    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.15
    CLIMB_SPEED = 0.2
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
    ADD_INTERVAL = 1500  

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
            'bird-wingup': load_image('har_wing_up.png'),
            'bird-wingdown': load_image('har_wing_down.png')}


def frames_to_msec(frames, fps=FPS):
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):

    return fps * milliseconds / 1000.0


def run_game(display_surface, ser, kl46z_connected):
    """Run a single game session"""
    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)
    images = load_images()
    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()
    frame_clock = 0  
    score = 0
    background_x = 0
    done = paused = False

   
   
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                pygame.quit()
                return
            elif e.type == KEYUP and e.key in (K_RETURN, K_SPACE):
                waiting = False
        if kl46z_connected:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line == "JUMP":
                    waiting = False
            except Exception as e:
                pass
        
        clock.tick(FPS)
    
    # main game loop
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
        
        if kl46z_connected:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line == "JUMP":
                    bird.msec_to_climb = Bird.CLIMB_DURATION
            except Exception as e:
                pass  # ignore serial errors during gameplay

        if paused:
            continue #me when if will crash dont
        background_x -= ANIMATION_SPEED * frames_to_msec(1)
        if background_x <= -BACKGROUND_WIDTH:
            background_x = 0

        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
            done = True

        display_surface.blit(images['background'], (background_x, 0))
        # all this code for wide image
        display_surface.blit(images['background'], (background_x + BACKGROUND_WIDTH, 0))

        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        bird.update()
        display_surface.blit(bird.image, bird.rect)
        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

        pygame.display.flip()
        frame_clock += 1
    
    return score


def get_serial_port_input(display_surface):
    #get serial port from game window
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 32, bold=True)
    
    input_text = ""
    cursor_visible = True
    cursor_timer = 0
    
    while True:
        cursor_timer += clock.get_time()
        if cursor_timer >= 500:  
            cursor_visible = not cursor_visible
            cursor_timer = 0
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == KEYDOWN:
                if event.key == K_RETURN:
                    return input_text.strip()
                elif event.key == K_ESCAPE:
                    return ""  
                elif event.key == K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if event.unicode.isprintable():
                        input_text += event.unicode
        
        display_surface.fill((0, 0, 0))
        
        # title
        title = title_font.render('FRDM-KL46Z (bad board) Serial Port Setup', True, (255, 255, 255))
        display_surface.blit(title, (WIN_WIDTH//2 - title.get_width()//2, 50))
        
        #  very reliable
        instructions = [
            "Enter your FRDM-KL46Z serial port:",
            "",
            "Windows examples:",
            "  COM3, COM4, COM5, COM6, etc.",
            "  (Check Device Manager > Ports)",
            "",
            "Linux examples (you know this already):",
            "  /dev/ttyACM0, /dev/ttyACM1, etc.",
            "  (Check: ls /dev/tty* | grep ACM)",
            "",
            "Press ENTER to connect",
         
        ]
        
        y_offset = 100
        for line in instructions:
            text = font.render(line, True, (200, 200, 200))
            display_surface.blit(text, (WIN_WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 25
    
        input_box_y = y_offset + 20
        input_box = pygame.Rect(WIN_WIDTH//2 - 150, input_box_y, 300, 30)
        pygame.draw.rect(display_surface, (50, 50, 50), input_box)
        pygame.draw.rect(display_surface, (100, 100, 100), input_box, 2)

        text_surface = font.render(input_text, True, (255, 255, 255))
        display_surface.blit(text_surface, (input_box.x + 5, input_box.y + 5))
    
        if cursor_visible:
            cursor_x = input_box.x + 5 + text_surface.get_width()
            cursor_y = input_box.y + 5
            pygame.draw.line(display_surface, (255, 255, 255), 
                           (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 1)
        
        pygame.display.flip()
        clock.tick(60)


def main():
    pygame.init()
    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('FRDM-KL46Z Flappy Harjot')
    while True:
        port_input = get_serial_port_input(display_surface)
        
        if not port_input:
            print("Skipping serial connection - using keyboard controls only")
            kl46z_connected = False
            ser = None
            break
        
        port_input = port_input.strip()
        
        # for windows: handle numbers and add COM prefix if needed
        if port_input.isdigit():
            port_input = f"COM{port_input}"
        elif port_input.lower().startswith('com') and not port_input.upper().startswith('COM'):
            port_input = port_input.upper()
        elif not port_input.startswith(('/dev/', 'COM')):
            # append "com" if bro just types in 5
            if port_input.replace('com', '').replace('COM', '').isdigit():
                port_input = f"COM{port_input.replace('com', '').replace('COM', '')}"
        
        try:
            ser = serial.Serial(port_input, 115200, timeout=0.01)
            print(f"Successfully connected to {port_input}!")
            kl46z_connected = True
            break
        except Exception as e:
            print(f"Failed to connect to {port_input}: {e}")
            
            display_surface.fill((0, 0, 0))
            error_font = pygame.font.SysFont(None, 28, bold=True)
            regular_font = pygame.font.SysFont(None, 24)
            
            error_title = error_font.render('Connection Failed', True, (255, 0, 0))
            error_msg = regular_font.render(f'Could not connect to {port_input}', True, (255, 255, 255))
            error_detail = regular_font.render(str(e), True, (200, 200, 200))
            retry_msg = regular_font.render('Press SPACE to try again, ESC to skip', True, (255, 255, 0))
            
            display_surface.blit(error_title, (WIN_WIDTH//2 - error_title.get_width()//2, WIN_HEIGHT//2 - 60))
            display_surface.blit(error_msg, (WIN_WIDTH//2 - error_msg.get_width()//2, WIN_HEIGHT//2 - 20))
            display_surface.blit(error_detail, (WIN_WIDTH//2 - error_detail.get_width()//2, WIN_HEIGHT//2 + 10))
            display_surface.blit(retry_msg, (WIN_WIDTH//2 - retry_msg.get_width()//2, WIN_HEIGHT//2 + 50))
            
            pygame.display.flip()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == KEYDOWN:
                        if event.key == K_SPACE:
                            waiting = False  
                        elif event.key == K_ESCAPE:
                            print("Using keyboard controls only")
                            kl46z_connected = False
                            ser = None
                            waiting = False
                            break
                
                if not kl46z_connected:
                    break
            
            if not kl46z_connected:
                break

    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)

    while True:
        display_surface.fill((0, 0, 0))
        title_font = pygame.font.SysFont(None, 48, bold=True)
        title = title_font.render('Congrats Harjot!', True, (255, 255, 255))
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
                    if ser:
                        ser.close()
                    pygame.quit()
                    return
                elif e.type == KEYUP and e.key in (K_RETURN, K_SPACE):
                    waiting = False
            
           
            if kl46z_connected:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line == "JUMP":
                        waiting = False
                except Exception as e:
                    pass
            
            clock.tick(FPS)
        
  
        score = run_game(display_surface, ser, kl46z_connected)
        
   
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
                    if ser:
                        ser.close()
                    print('Game over! Score: %i' % score)
                    pygame.quit()
                    return
                elif e.type == KEYUP and e.key in (K_RETURN, K_SPACE):
                    waiting = False 
        
            if kl46z_connected:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line == "JUMP":
                        waiting = False  
                except Exception as e:
                    pass
            
            clock.tick(FPS)


if __name__ == '__main__':
    main()
