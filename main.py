import sys, threading, time, math
import pygame as pg
import pyscroll
from pytmx.util_pygame import load_pygame
import utils, pcolor, dialogs

"""Initialize pygame, create a clock, create the window
with a surface to blit the map onto."""
screen_width = 600
screen_height = 800
paused = False; p_paused = False
pg.init()
fps_clock = pg.time.Clock()
main_surface = pg.display.set_mode((screen_width, screen_height))
main_rect = main_surface.get_rect()
pg.mouse.set_visible(False)

FPS = 60
FPS_dialog = 25
world_time = 0
frame_repeater = 8
time_arg = True; time_thread_count = 0; sleep_arg = False
time_increment = 15; time_delay = 5
clicked = None
menu = False
mouse_size = (32,32)
blockers = []
interactable_objects = {}

default_mouse = utils.load_image(r"mouse\default.png")
click_mouse = utils.load_image(r"mouse\clickable.png")
menu_mouse = utils.load_image(r"mouse\menu.png")

default_mouse = (pg.transform.smoothscale(default_mouse[0], mouse_size), default_mouse[1])
click_mouse = (pg.transform.smoothscale(click_mouse[0], mouse_size), click_mouse[1])
menu_mouse = (pg.transform.smoothscale(menu_mouse[0], mouse_size), menu_mouse[1])

menu_3 = utils.load_image(r"menus\menu_3.png")
menu_4 = utils.load_image(r"menus\menu_4.png")

smallfont = pg.font.Font("data/fonts/prstartk.ttf", 20)
medfont = pg.font.Font("data/fonts/prstartk.ttf", 35)
largefont = pg.font.Font("data/fonts/prstartk.ttf", 50)

tile_renderer = load_pygame("dorm.tmx")
map_data = pyscroll.data.TiledMapData(tile_renderer)
map_layer = pyscroll.BufferedRenderer(map_data, (screen_width,screen_height), clamp_camera=True)

for obj in tile_renderer.get_layer_by_name("Blockers"):
    properties = obj.__dict__
    if properties['name'] == 'blocker':
        x = properties['x']
        y = properties['y']
        width = properties['width']
        height = properties['height']
        new_rect = pg.Rect(x, y, width, height)
        blockers.append(new_rect)
for obj in tile_renderer.get_layer_by_name("Objects"):
    properties = obj.__dict__
    x = properties['x']
    y = properties['y']
    width = properties['width']
    height = properties['height']
    new_rect = pg.Rect(x, y, width, height)
    interactable_objects[properties["name"]] = new_rect

def text_objects(text, color, size):
    if size == "small":
        font = smallfont
    if size == "med":
        font = medfont
    if size == "large":
        font = largefont
    textSurface = font.render(text, True, color)
    return textSurface, textSurface.get_rect()

def add_text(msg, text_color, size="small", x_offset=0,y_offset=0,x_cor=0,y_cor=0,cor="no"):
    textSurf, textRect = text_objects(msg, text_color, size)
    if x_cor == 0 and y_cor == 0 and cor == "no":
        textRect.center = (screen_width/2)+x_offset, (screen_height/2)+y_offset
    else:
        textRect.left = x_cor
        textRect.top = y_cor
    main_surface.blit(textSurf, textRect)
    return textRect

def dialog_box(msg, text_color, size="small", scroll="no"):
    if size == "small":
        font = smallfont
    if size == "med":
        font = medfont
    if size == "large":
        font = largefont
    quit = False
    text_offset = 30
    dialog, dialog_rect = utils.load_image(r"dialog\Dialog Box.png")
    dialog = pg.transform.smoothscale(dialog, (screen_width, dialog_rect[3]*2))
    msg = dialogs.wrapline(msg, font, screen_width - 2*text_offset)
    line_height = 0
    completed_lines = []
    for line in msg:
        for i in range(len(line)+1):
            main_surface.blit(dialog, (0, screen_height - dialog_rect[3] * 2))
            for index, line_2 in enumerate(completed_lines):
                add_text(line_2, text_color, "small", 0, 0, 0 + text_offset,
                         screen_height - dialog_rect[3] * 2 + text_offset + font.get_height()*index, "yes")
            add_text(line[0:i], text_color, "small", 0, 0, 0 + text_offset,
                        screen_height-dialog_rect[3]*2+text_offset + line_height,"yes")
            pg.display.update()
            fps_clock.tick(FPS_dialog)
        completed_lines.append(line)
        line_height += font.get_height()
    while quit == False:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                quit = True

def display_time(time):
    offset = 120
    hour = time /60
    min = time % 60
    add_text(str(hour).zfill(2)+":"+str(min).zfill(2), pcolor.green, "small", 0, 0, screen_width - offset, 20, "yes")

def menu_box(messages, obj_name, color, num = 4):
    global time_arg, clicked
    x_offset = 30
    y_offset = 40
    time_arg = False
    mouse_pos = pg.mouse.get_pos()
    result = None
    position = (interactable_objects[obj_name][2] + map_layer.get_center_offset()[0],
                interactable_objects[obj_name][3] + map_layer.get_center_offset()[1])
    if num == 4:
        menu_rect = main_surface.blit(menu_4[0], position)
    if num == 3:
        menu_rect = main_surface.blit(menu_3[0], position)
    for index, msg in enumerate(messages):
        rect = add_text(msg,color, "small",0,0,position[0]+x_offset,
                        position[1] + (menu_4[1][3] - y_offset) / 4 * index+y_offset,"yes")
        rect.x -= x_offset/2
        rect.y -= y_offset/2
        rect.width += x_offset
        rect.height += y_offset
        if rect.collidepoint(mouse_pos):
            add_text(msg, pcolor.blue, "small", 0, 0, position[0] + x_offset,
                        position[1] + (menu_4[1][3] - y_offset) / 4 * index + y_offset, "yes")
        if clicked != None and rect.collidepoint(clicked):
            result = msg
    return result

def sleep():
    global world_time, sleep_arg
    if sleep_arg == True:
        sleep_increment = 100
        world_time += sleep_increment
    sleep_arg = False

def computer():
    global paused, clicked, menu, time_arg
    paused = True
    result = menu_box(["Hello","this","is","Nevermind"], "computer", pcolor.red, 4)
    if result != None:
        print result
        menu = False
        paused = False
        time_arg = True
        threading.Timer(1, time_update).start()

def study():
    global paused, clicked, menu, time_arg
    paused = True
    result = menu_box(["Hello", "this", "Nevermind"], "book_case", pcolor.red, 3)
    if result != None:
        print result
        menu = False
        paused = False
        time_arg = True
        threading.Timer(1, time_update).start()

def mouse_click_process(obj_name):
    if obj_name == "bed":
        sleep()
    elif obj_name == "computer":
        computer()
    elif obj_name == "book_case":
        study()

class Player(pg.sprite.Sprite):
    def __init__(self, blockers):
        super(Player, self).__init__()
        self.image, self.rect = utils.load_image(r"character\baldric_walk\baldric_walk 2 (2).png",-1)
        #rect only represents the leg of the character
        #self.collision_rect =  pg.Rect(self.rect[0]+self.rect[2]/4, self.rect[1] + self.rect[3] / 2, self.rect[2]/2, self.rect[3] / 2)

        global frame_repeater, screen_width, screen_height
        offset = 64
        self.rect.x += offset
        self.rect.y += offset
        self.collision_rect =  pg.Rect(self.rect[0]+self.rect[2]/4, self.rect[1] + self.rect[3] / 2, 30, 30)
        self.gold = 0
        self.x_vel = 0
        self.y_vel = 0
        self.direction = "right"
        self.direction_vert = "still"
        self.direction_hor = "still"
        self.blockers = blockers
        self.counter = 0
        self.last_direction = ""
        self.moving = False
        self.frame_repeater = 0
        self.speed = 3

    def update_gold(self, amount):
        self.gold += amount

    def animation(self, direction):
        self.frame_repeater += 1
        self.frame_repeater = self.frame_repeater % frame_repeater
        if self.moving == False:
            self.counter = 1
        elif (self.frame_repeater == 0):
            self.counter = self.counter % 9
            self.counter += 1
        if direction == "down":
            self.last_direction = "down"
            self.image, self.temp_rect = utils.load_image(r"character\baldric_walk\baldric_walk 2 ("+str(self.counter)+").png",-1)
        elif direction == "up":
            self.last_direction = "up"
            self.image, self.temp_rect = utils.load_image(r"character\baldric_walk\baldric_walk 0 ("+str(self.counter)+").png",-1)
        elif direction == "left":
            self.last_direction = "left"
            self.image, self.temp_rect = utils.load_image(r"character\baldric_walk\baldric_walk 1 ("+str(self.counter)+").png", -1)
        elif direction == "right":
            self.last_direction = "right"
            self.image, self.temp_rect = utils.load_image(r"character\baldric_walk\baldric_walk 3 ("+str(self.counter)+").png", -1)

    def update(self, keys):
        if keys[pg.K_s]:
            self.y_vel = self.speed
            self.animation("down")
            self.moving = True
        elif keys[pg.K_w]:
            self.y_vel = -self.speed
            self.animation("up")
            self.moving = True
        else:
            self.y_vel = 0
        if keys[pg.K_a]:
            self.x_vel = -self.speed
            self.animation("left")
            self.moving = True
        elif keys[pg.K_d]:
            self.x_vel = self.speed
            self.animation("right")
            self.moving = True
        else:
            self.x_vel = 0
        fps_clock.tick(FPS)

        if not keys[pg.K_w] and not keys[pg.K_s] and not keys[pg.K_a] and not keys[pg.K_d]:
            self.moving = False
            self.animation(self.last_direction)

        self.rect.x += self.x_vel
        self.collision_rect[0] += self.x_vel
        for blocker in self.blockers:
            if self.collision_rect.colliderect(blocker):
                self.move_back("x")

        self.rect.y += self.y_vel
        self.collision_rect[1] += self.y_vel
        for blocker in self.blockers:
            if self.collision_rect.colliderect(blocker):
                self.move_back("y")

        if self.collision_rect.x < 0 or self.collision_rect.x+self.collision_rect[2] > tile_renderer.tilewidth*tile_renderer.width:
            self.move_back("x")

        if self.collision_rect.y < 0 or self.collision_rect.y+self.collision_rect[3] > tile_renderer.tileheight*tile_renderer.height:
            self.move_back("y")

    def move_back(self, direction):
        if direction == "x":
            self.collision_rect[0] -= self.x_vel
            self.rect.x -= self.x_vel
            self.x_vel = 0
        else:
            self.rect.y -= self.y_vel
            self.collision_rect[1] -= self.y_vel
            self.y_vel = 0

class Mouse(pg.sprite.Sprite):
    def __init__(self, interactable_objects):
        super(Mouse, self).__init__()
        self.mouse = utils.load_image(r"mouse\default.png")
        self.mouse_img = pg.transform.smoothscale(self.mouse[0], mouse_size)
        self.interactable_objects = interactable_objects
    def update(self, menu_click=False):
        mouse_world_pos = (pg.mouse.get_pos()[0] + map_layer.view_rect.center[0] - screen_width / 2,
                           pg.mouse.get_pos()[1] + map_layer.view_rect.center[1] - screen_height / 2)
        if menu_click == True:
            self.mouse = menu_mouse
            self.mouse_img = menu_mouse[0]
            return None
        for name, clickable in self.interactable_objects.iteritems():
            if pg.Rect(mouse_world_pos, mouse_size).colliderect(clickable):
                self.mouse = click_mouse
                self.mouse_img = click_mouse[0]
                return name
            else:
                self.mouse = default_mouse
                self.mouse_img = default_mouse[0]
        return None
    def click(self, name):
        mouse_click_process(name)

player = Player(blockers)
mouse = Mouse(interactable_objects)
group = pyscroll.PyscrollGroup(map_layer=map_layer)
group.add(player, layer="Player_layer")

def time_update():
    global time_arg, world_time, time_thread_count
    print time_thread_count
    time_thread_count += 1
    if time_arg == True and time_thread_count <= 2:
    #if time_arg == True:
        world_time += time_increment
        world_time = world_time % 720
        t = threading.Timer(time_delay, time_update)
        t.start()
        time.sleep(time_delay)
    time_thread_count -= 1


def main():
    global paused, time_arg, world_time, p_paused, sleep_arg, menu, clicked
    #dialog_box(dialogs.opening_msg, pcolor.yellow)
    threading.Timer(time_delay, time_update).start()
    while True:
        keys = pg.key.get_pressed()
        if paused == False:
            player.update(keys)
            group.center(player.rect.center)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                time_arg = False
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEMOTION and paused == False:
                obj_name = mouse.update()
            if event.type == pg.MOUSEBUTTONDOWN:
                clicked = pg.mouse.get_pos()
                if obj_name != None and player.collision_rect.colliderect((interactable_objects[obj_name][0]-map_data.tile_size[0],interactable_objects[obj_name][1]-map_data.tile_size[1]),
                                                         (interactable_objects[obj_name][2]+map_data.tile_size[0]*2,interactable_objects[obj_name][3]+map_data.tile_size[1]*2))\
                        and paused == False:
                    menu = True
                    menu_obj = obj_name
                    mouse.update(True)
                    if menu_obj == "bed":
                        sleep_arg = True
            if keys[pg.K_p]:
                paused = not paused
                if paused == True:
                    time_arg = False
                    p_paused = True
                else:
                    time_arg = True
                    p_paused = False
                    threading.Timer(time_delay, time_update).start()
        group.draw(main_surface)
        add_text("$" + str(player.gold), pcolor.green, "small", 0, 0, 0, 20, "yes")
        display_time(world_time)
        if paused == True and p_paused == True:
            add_text("PAUSED", pcolor.green, "large", 0, 0)
        if menu == True:
            mouse.click(menu_obj)
        main_surface.blit(mouse.mouse_img, pg.mouse.get_pos())
        pg.display.update()
        clicked = None

if __name__ == "__main__":
    main()

