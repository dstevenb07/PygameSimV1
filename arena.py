import pygame
from constants import *


class Arena:
    def __init__(self):
        self.obstacles = []

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            WALL_COLOR,
            pygame.Rect(1, 1, SCREEN_WIDTH - 2, SCREEN_HEIGHT - 2),
            1
        )
