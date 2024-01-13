import pygame;
from pygame.locals import *
from pygame import mixer
from pygame.sprite import Group, Group
# Voor inladen van wereld data
import pickle
# Nakijken of gamedata file bestaat
from os import path

# Initialiseer mixer voor geluid
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
# Initialiseer pygame
pygame.init()

clock = pygame.time.Clock()
fps = 60

# Scherm
screen_width = 1000
screen_height = 1000

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Graduaatsproef - Platformer')

# Font bepalen
font_score = pygame.font.Font('font/upheavtt.ttf', 30)
font = pygame.font.Font('font/upheavtt.ttf', 70)

#variabelen
tile_size = 50
game_over = 0
# Kijken of je in main menu bent of niet
main_menu = True
# We beginnen bij level 0
level = 1
# Maximum levels
max_levels = 7
# Bijhouden van score -> coins
score = 0

# Kleuren bepalen
black = (0, 0, 0)
white = (255, 255, 255)
pink = (255, 102, 196)

# Afbeeldingen laden
sun_img = pygame.image.load('images/sun.png')
bg_img = pygame.image.load('images/background.png')
restart_img = pygame.image.load('images/buttons/RESTART.png')
start_img = pygame.image.load('images/buttons/START.png')
exit_img = pygame.image.load('images/buttons/EXIT.png')

# Muziek en geluid laden
pygame.mixer.music.load('sounds/background.mp3')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('sounds/coin.mp3')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('sounds/jump.mp3')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('sounds/gameover.mp3')
game_over_fx.set_volume(0.5)

# Tekst tonen op scherm
# Pygame kent concept van text niet, deze wordt omgezet naar een image
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))

# Methode om level te resetten
def reset_level(level):
    player.reset(100, screen_height - 130)
    slime_group.empty()
    lava_group.empty()
    exit_group.empty()

    # inladen van level data en wereld aanmaken
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)
        world = World(world_data)

    return world


# Button klasse voor restart nadat speler is doodgegaan
class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        # zoek positie cursor
        pos = pygame.mouse.get_pos()

        # kijk mouseover na en clicked conditions
        if self.rect.collidepoint(pos):
            # Als linker button geklikt wordt
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked ==True
        
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False


        # teken button
        screen.blit(self.image, self.rect)

        return action

class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 10
        col_tresh = 20

        # game_over meegeven anders errors
        if game_over == 0:
            # Herken keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_LEFT] == True:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT] == True:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            if key[pygame.K_SPACE] == True and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False

            # animaties
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]
                

            # Voeg gravity toe: anders blijft speler eindeloos springen
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # Kijk voor collision
            self.in_air = True
            for tile in world.tile_list:
                #Kijk voor collision in X-richting
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Check voor collision in Y-richting
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Check of de speler onder grond is -> springen
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # Check of de speler boven de grond is -> vallen
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            # Kijk voor collision met enemies
            # Self is player, slime_group zijn de slimes waarmee je collision checked, False zodat sprite niet gedelete wordt nadat collision gedetecteerd werd
            if pygame.sprite.spritecollide(self, slime_group, False):
                game_over = -1
                game_over_fx.play()

            # Kijk voor collision met lava
            # Self is player, lava-group zijn de lavas waarmee je collision checked, False zodat sprite niet gedelete wordt nadat collision gedetecteerd werd
            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over = -1
                game_over_fx.play()

            # Kijk voor collision met de exit deur
            # Self is player, lava-group zijn de lavas waarmee je collision checked, False zodat sprite niet gedelete wordt nadat collision gedetecteerd werd
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            # Kijk voor collision met platforms
            for platform in platform_group:
                # Collision in x-richting
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # Collision in y-richting
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # Kijk of speler onder platform is
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_tresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # Kijk of speler boven platform is
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_tresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # Van links naar rechts bewegen samen met platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction


            # Update coordinaten speler
            self.rect.x += dx
            self.rect.y += dy

        # Als speler dood is, verander image sprite
        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER :(', font, pink, (screen_width // 2) - 200, screen_height // 2)
            # Ghost float een beetje voor dead-player effect
            if self.rect.y > 200:
                self.rect.y -= 5
            
        # Toon speler in game
        screen.blit(self.image, self.rect)

        return game_over
    
    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 13):
            img_right = pygame.image.load(f'images/character/frog{num}.png')
            img_right = pygame.transform.scale(img_right, (32, 80))
            # Keert image right gewoon om zodat je geen aparte sprites moet laden als de speler naar links loopt ipv rechts
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        # Image voor als player dood gaat
        self.dead_image = pygame.image.load('images/character/ghost.png')
        self.image = self.images_right[self.index]
        # Neemt 'outline' van de image -> gebruikt voor collision
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        # Checked of speler in lucht is om double jump te voorkomen
        self.in_air = True

class World():
    def __init__(self, data):
        
        self.tile_list = []

        # images inladen
        dirt_img = pygame.image.load('images/tiles/dirt.png')
        grass_img = pygame.image.load('images/tiles/grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    # Maak instantie van enemy aan met coordinaten (+22 pixels zodat slimes niet in lucht hangen)
                    slime = Enemy(col_count * tile_size, row_count * tile_size + 22)
                    # Voeg slime toe aan groep
                    slime_group.add(slime)
                # Horizontale platforms
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                # Verticale platforms
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    # // 2 zodat lava naar beneden geplaatst wordt
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                col_count += 1
            row_count += 1
    
    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

# Sprite klasse van pygame zelf voor enemy
class Enemy(pygame.sprite.Sprite): 
    # Constructor
    def __init__(self, x, y):
        # Constructor oproepen uit super-klasse -> functionaliteit overnemen
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('images/enemy/slimeWalk1.png')
        # Maak een rectangle
        self.rect = self.image.get_rect()
        # Steekt enemy op coordinaten die ik meegeef
        self.rect.x = x
        self.rect.y = y
        # Sprites laten bewegen
        self.move_direction = 1
        # Counter om bij te houden hoeveel de enemy al heeft bewogen -> anders loopt deze oneindig door
        self.move_counter = 0
    # Sprites bewegen ipv statisch te blijven staan
    def update(self):
        # Enemy naar rechts bewegen
        self.rect.x += self.move_direction
        self.move_counter += 1

        # Als counter bepaalde value overschrijdt
        if abs(self.move_counter) > 50:
            # Flip
            self.move_direction *= -1
            # Enemy moet ook naar links kunnen gaan
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/tiles/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        # Als counter bepaalde value overschrijdt
        if abs(self.move_counter) > 50:
            # Flip
            self.move_direction *= -1
            # Naar links
            self.move_counter *= -1

# Klasse voor lava
class Lava(pygame.sprite.Sprite):
    # Constructor
    def __init__(self, x, y):
        # Constructor oproepen uit super-klasse -> functionaliteit overnemen
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/tiles/liquidLavaTop.png')
        # Scaled image
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    # Constructor
    def __init__(self, x, y):
        # Constructor oproepen uit super-klasse -> functionaliteit overnemen
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/items/coinGold.png')
        # Scaled image
        self.image = pygame.transform.scale(img, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        # Midpoint omdat coins kleiner zijn dan andere items
        self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
    # Constructor
    def __init__(self, x, y):
        # Constructor oproepen uit super-klasse -> functionaliteit overnemen
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('images/items/exitDoor.png')
        # Scaled image
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y



player = Player(100, screen_height - 130)
# Lijst waar je enemies,... in kan toevoegen
slime_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# inladen van level data en wereld aanmaken
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
world_data = pickle.load(pickle_in)
world = World(world_data)

# maak buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)

# Maak dummy coin om de score te tonen
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

run = True

# Zorgt ervoor dat game window blijft lopen zolang window niet gesloten wordt
while run: 

    clock.tick(fps)

    # Inladen van background en sun image, sun img als laatste anders zie je deze niet -> overlapping
    screen.blit(bg_img, (0,0))
    screen.blit(sun_img
, (100, 100))

    # Buttons om game te starten en eindigen
    if main_menu == True:
        # Run wordt op false gezet zodat de game afsluit
        if exit_button.draw():
            run = False
        # Als speler wilt beginnen wordt main menu gesloten en begint de effectieve game
        if start_button.draw():
            main_menu = False
    else:
        # Tekent wereld
        world.draw()

        # Als game aan het lopen is
        if game_over == 0:
            slime_group.update()
            platform_group.update()
            # Score updaten
            # Kijken of een coin verzameld is
            if pygame.sprite.spritecollide(player, coin_group, True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font_score, black
        , tile_size, 10)

        # Tekent slimes
        slime_group.draw(screen)
        # Tekent platforms
        platform_group.draw(screen)
        # Tekent lava
        lava_group.draw(screen)
        # Tekent coins
        coin_group.draw(screen)
        # Tekent exit
        exit_group.draw(screen)

        # Tekent speler + game_over in variabele zodat je er iets mee kan doen
        game_over = player.update(game_over)

        # Als het game-over is
        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

        # Als speler het level voltooid heeft
        if game_over == 1:
            # Reset spel en gaat naar volgend level
            level += 1
            # Nakijken of je niet naar level gaat dat niet bestaat
            if level <= max_levels:
                # Reset level
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN :D', font, pink, (screen_width // 2) - 140, screen_height // 2)
                # Game complete, herstarten
                if restart_button.draw():
                    level = 1
                    # Reset level
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0
            
    

    # Om spel te stoppen
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    pygame.display.update()

pygame.quit()