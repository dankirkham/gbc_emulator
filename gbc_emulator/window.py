import pygame
import pygame.freetype
from time import time
import os.path
from collections import deque
from statistics import mean
from math import floor, ceil

GAMEBOY_PIXELS_X, GAMEBOY_PIXELS_Y = 160, 144

GAMEBOY_COLORS = {
    'darkest_green': (15, 56, 15),
    'dark_green': (48, 98, 48),
    'light_green': (139, 172, 15),
    'lightest_green': (155, 188, 15),
}

def hexp(s, length=4):
    s = hex(s)
    return s[2:].zfill(length)

def render_title(ctx, title, x, y, width=100):
    title, title_rect = ctx['font'].render(title, ctx['highlight_color'])
    ctx['screen'].blit(title, (x + (width / 2) - (title_rect.width / 2), y))
    return y + title_rect.height + ctx['padding']

def render_fps(ctx, fps, x, y, width=100):
    fps, rect = ctx['font'].render(fps + "fps", ctx['highlight_color'])
    ctx['screen'].blit(fps, (x + width - rect.width, y))

    return y + rect.height

def render_registers(ctx, x, y, width=100):
    registers = [
        {
            "name": "AF",
            "val": (ctx['cpu'].A << 8) | ctx['cpu'].F,
        },
        {
            "name": "BC",
            "val": (ctx['cpu'].B << 8) | ctx['cpu'].C,
        },
        {
            "name": "DE",
            "val": (ctx['cpu'].D << 8) | ctx['cpu'].E,
        },
        {
            "name": "HL",
            "val": (ctx['cpu'].H << 8) | ctx['cpu'].L,
        },
        {
            "name": "SP",
            "val": ctx['cpu'].SP,
        },
        {
            "name": "PC",
            "val": ctx['cpu'].PC,
        },
    ]

    y = render_title(ctx, "Registers", x, y, width)

    # Registers
    for register in registers:
        name, name_rect = ctx['font'].render(register["name"], ctx['font_color'])
        ctx['screen'].blit(name, (x + ctx['padding'], y))

        val, val_rect = ctx['font'].render(hexp(register['val']), ctx['font_color'])
        ctx['screen'].blit(val, (x + width - val_rect.width - ctx['padding'], y))

        y += max(name_rect.height, val_rect.height) + ctx['padding']

    return y

def render_stack(ctx, x, y, width=100, depth=9):
    y = render_title(ctx, "Stack", x, y, width)

    sp = ctx['cpu'].SP

    lower_bound = floor(depth / 2)
    upper_bound = ceil(depth / 2)

    if (sp + upper_bound) > 0x10000:
        center = 0xFFFF - upper_bound + 1
    elif (sp - lower_bound) < 0:
        center = lower_bound
    else:
        center = sp

    for address in range(center - lower_bound, center + upper_bound):
        label, label_rect = ctx['font'].render(hexp(address), ctx['font_color'] if sp != address else ctx['highlight_color'])
        ctx['screen'].blit(label, (x + ctx['padding'], y))

        val, val_rect = ctx['font'].render(hexp(ctx['memory'][address], 2), ctx['font_color'] if sp != address else ctx['highlight_color'])
        ctx['screen'].blit(val, (x + width - val_rect.width - ctx['padding'], y))

        y += max(label_rect.height, val_rect.height) + ctx['padding']

    return y

def render_immediate(ctx, x, y, width=100, depth=9):
    y = render_title(ctx, "Immediate", x, y, width)

    addr = ctx['memory'].last_addr
    # addr = (ctx['cpu'].H << 8) | ctx['cpu'].L

    lower_bound = floor(depth / 2)
    upper_bound = ceil(depth / 2)

    if (addr + upper_bound) > 0x10000:
        center = 0xFFFF - upper_bound + 1
    elif (addr - lower_bound) < 0:
        center = lower_bound
    else:
        center = addr

    for address in range(center - lower_bound, center + upper_bound):
        label, label_rect = ctx['font'].render(hexp(address), ctx['font_color'] if addr != address else ctx['highlight_color'])
        ctx['screen'].blit(label, (x + ctx['padding'], y))

        val, val_rect = ctx['font'].render(hexp(ctx['memory'][address], 2), ctx['font_color'] if addr != address else ctx['highlight_color'])
        ctx['screen'].blit(val, (x + width - val_rect.width - ctx['padding'], y))

        y += max(label_rect.height, val_rect.height) + ctx['padding']

    return y

def do_window(cpu, done, scale=4, info_width=200):
    pygame.init()

    size = SCREEN_WIDTH, SCREEN_HEIGHT = GAMEBOY_PIXELS_X * scale + info_width, GAMEBOY_PIXELS_Y * scale

    pygame.font.init()

    font = pygame.freetype.Font(os.path.dirname(os.path.abspath(__file__)) + '/assets/Inconsolata-Regular.ttf', 16)
    screen = pygame.display.set_mode(size)

    ctx = {
        "font": font,
        "screen": screen,
        "cpu": cpu,
        "memory": cpu.memory.gui_memory,
        "padding": 9,
        "font_color": GAMEBOY_COLORS['light_green'],
        "highlight_color": (255, 255, 255),
        "bg_color": GAMEBOY_COLORS['darkest_green']
    }

    pygame.display.set_caption('Game Boy Emulator')

    last_time = time()
    FRAME_PERIOD = 1 / 59.73
    frame_times = deque()
    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done()

        now = time()
        if now >= (last_time + FRAME_PERIOD):
            # Save frame time
            frame_times.append(now - last_time)
            if (len(frame_times) > 5):
                frame_times.popleft()
            last_time = now

            # Draw a frame
            screen.fill(ctx['bg_color'])

            pygame.draw.rect(screen, GAMEBOY_COLORS['lightest_green'], [0, 0, GAMEBOY_PIXELS_X * scale, GAMEBOY_PIXELS_Y * scale])

            fps = str(floor(1 / mean(frame_times)))
            last_y = render_fps(ctx, fps, SCREEN_WIDTH - info_width, 0, info_width)
            last_y = render_registers(ctx, SCREEN_WIDTH - info_width, last_y, info_width)
            last_y = render_stack(ctx, SCREEN_WIDTH - info_width, last_y, info_width)
            last_y = render_immediate(ctx, SCREEN_WIDTH - info_width, last_y, info_width)

            pygame.display.flip()
