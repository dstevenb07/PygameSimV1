import pygame
from constants import *


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_hud(surface, fighter_a, fighter_b, font):
    # Left bar — fighter_a
    name_a = font.render(fighter_a.name, True, HUD_TEXT_COLOR)
    surface.blit(name_a, (HUD_BAR_MARGIN, HUD_BAR_Y - font.get_height() - HUD_LABEL_GAP))

    pygame.draw.rect(surface, HUD_BAR_BG_COLOR,
                     pygame.Rect(HUD_BAR_MARGIN, HUD_BAR_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT))

    hp_pct_a = fighter_a.hp / BALL_HP
    fill_w_a = int(HUD_BAR_WIDTH * hp_pct_a)
    if hp_pct_a > HUD_HP_YELLOW_THRESHOLD:
        bar_color_a = fighter_a.color
    elif hp_pct_a > HUD_HP_RED_THRESHOLD:
        t = (HUD_HP_YELLOW_THRESHOLD - hp_pct_a) / (HUD_HP_YELLOW_THRESHOLD - HUD_HP_RED_THRESHOLD)
        bar_color_a = _lerp_color(fighter_a.color, HUD_BAR_YELLOW, t)
    else:
        t = (HUD_HP_RED_THRESHOLD - hp_pct_a) / HUD_HP_RED_THRESHOLD
        bar_color_a = _lerp_color(HUD_BAR_YELLOW, HUD_BAR_RED, t)
    if fill_w_a > 0:
        pygame.draw.rect(surface, bar_color_a,
                         pygame.Rect(HUD_BAR_MARGIN, HUD_BAR_Y, fill_w_a, HUD_BAR_HEIGHT))

    # Right bar — fighter_b
    bar_x_b = SCREEN_WIDTH - HUD_BAR_MARGIN - HUD_BAR_WIDTH
    name_b = font.render(fighter_b.name, True, HUD_TEXT_COLOR)
    surface.blit(name_b, (SCREEN_WIDTH - HUD_BAR_MARGIN - name_b.get_width(),
                          HUD_BAR_Y - font.get_height() - HUD_LABEL_GAP))

    pygame.draw.rect(surface, HUD_BAR_BG_COLOR,
                     pygame.Rect(bar_x_b, HUD_BAR_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT))

    hp_pct_b = fighter_b.hp / BALL_HP
    fill_w_b = int(HUD_BAR_WIDTH * hp_pct_b)
    if hp_pct_b > HUD_HP_YELLOW_THRESHOLD:
        bar_color_b = fighter_b.color
    elif hp_pct_b > HUD_HP_RED_THRESHOLD:
        t = (HUD_HP_YELLOW_THRESHOLD - hp_pct_b) / (HUD_HP_YELLOW_THRESHOLD - HUD_HP_RED_THRESHOLD)
        bar_color_b = _lerp_color(fighter_b.color, HUD_BAR_YELLOW, t)
    else:
        t = (HUD_HP_RED_THRESHOLD - hp_pct_b) / HUD_HP_RED_THRESHOLD
        bar_color_b = _lerp_color(HUD_BAR_YELLOW, HUD_BAR_RED, t)
    if fill_w_b > 0:
        pygame.draw.rect(surface, bar_color_b,
                         pygame.Rect(bar_x_b, HUD_BAR_Y, fill_w_b, HUD_BAR_HEIGHT))
