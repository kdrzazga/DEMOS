import pygame


def read_speech(path):
    with open(path, encoding="utf-8") as speech_file:
        return tuple(line.rstrip() for line in speech_file if line.strip())


def draw_speech(surface, font, lines, color, left=0, top=0):
    _, line_height = font.size("W")
    for index, line in enumerate(lines):
        surface.blit(font.render(line, False, color), (left, top + index * line_height))


def speech_surface(font, lines, color):
    _, line_height = font.size("W")
    width = max((font.size(line)[0] for line in lines), default=1)
    surface = pygame.Surface((max(width, 1), max(line_height * len(lines), 1)), pygame.SRCALPHA)
    draw_speech(surface, font, lines, color)
    return surface
