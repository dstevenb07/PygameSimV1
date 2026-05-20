import pygame
from constants import *


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_hud(surface, fighter_a, fighter_b, font):
    # Left bar — fighter_a
    name_a = font.render(fighter_a.name, True, (255, 255, 255))
    surface.blit(name_a, (HUD_BAR_MARGIN, HUD_BAR_Y - font.get_height() - 4))

    pygame.draw.rect(surface, (30, 30, 40),
                     pygame.Rect(HUD_BAR_MARGIN, HUD_BAR_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT))

    hp_pct_a = fighter_a.hp / BALL_HP
    fill_w_a = int(HUD_BAR_WIDTH * hp_pct_a)
    if hp_pct_a > 0.6:
        bar_color_a = fighter_a.color
    elif hp_pct_a > 0.25:
        t = (0.6 - hp_pct_a) / 0.35
        bar_color_a = _lerp_color(fighter_a.color, (220, 180, 0), t)
    else:
        t = (0.25 - hp_pct_a) / 0.25
        bar_color_a = _lerp_color((220, 180, 0), (200, 40, 40), t)
    if fill_w_a > 0:
        pygame.draw.rect(surface, bar_color_a,
                         pygame.Rect(HUD_BAR_MARGIN, HUD_BAR_Y, fill_w_a, HUD_BAR_HEIGHT))

    # Right bar — fighter_b
    bar_x_b = SCREEN_WIDTH - HUD_BAR_MARGIN - HUD_BAR_WIDTH
    name_b = font.render(fighter_b.name, True, (255, 255, 255))
    surface.blit(name_b, (SCREEN_WIDTH - HUD_BAR_MARGIN - name_b.get_width(),
                          HUD_BAR_Y - font.get_height() - 4))

    pygame.draw.rect(surface, (30, 30, 40),
                     pygame.Rect(bar_x_b, HUD_BAR_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT))

    hp_pct_b = fighter_b.hp / BALL_HP
    fill_w_b = int(HUD_BAR_WIDTH * hp_pct_b)
    if hp_pct_b > 0.6:
        bar_color_b = fighter_b.color
    elif hp_pct_b > 0.25:
        t = (0.6 - hp_pct_b) / 0.35
        bar_color_b = _lerp_color(fighter_b.color, (220, 180, 0), t)
    else:
        t = (0.25 - hp_pct_b) / 0.25
        bar_color_b = _lerp_color((220, 180, 0), (200, 40, 40), t)
    if fill_w_b > 0:
        pygame.draw.rect(surface, bar_color_b,
                         pygame.Rect(bar_x_b, HUD_BAR_Y, fill_w_b, HUD_BAR_HEIGHT))
