import pygame


COLOR = {
    "bg": (16, 18, 25),
    "surface": (22, 25, 34),
    "panel": (31, 35, 47),
    "border": (47, 52, 68),
    "raised": (45, 50, 66),
    "raised_hover": (59, 65, 85),
    "text": (236, 238, 245),
    "muted": (150, 157, 178),
    "faint": (98, 105, 128),
    "accent": (99, 128, 255),
    "accent_hover": (125, 150, 255),
    "on_accent": (255, 255, 255),
    "success": (74, 201, 144),
    "warning": (244, 190, 80),
    "danger": (239, 96, 96),
    "floor": (37, 41, 55),
    "floor_alt": (34, 38, 51),
    "goal": (244, 190, 80),
    "box_on_goal": (74, 201, 144),
    "shadow": (0, 0, 0, 80),
}


FONT_FAMILY = "avenirnext,helveticaneue,segoeui,ubuntu,arial"
FONT_SPEC = {
    "title": (46, True),
    "h1": (26, True),
    "h2": (20, True),
    "body": (18, False),
    "body_bold": (18, True),
    "small": (15, False),
    "small_bold": (15, True),
    "label": (13, True),
}
FONT = {}


TILE = 48
PAD = 16
GAP = 28
RADIUS = {"panel": 14, "button": 10, "segment": 8, "pill": 11}
BTN_H = 42
SEG_H = 34


MOVE_MS = 100
HOP = 3
PULSE_MS = 450


def init():
    for name, (size, bold) in FONT_SPEC.items():
        FONT[name] = pygame.font.SysFont(FONT_FAMILY, size, bold=bold)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def ease_out(t):
    return 1 - (1 - t) ** 3


def text(surf, s, font, color, pos, anchor="topleft"):
    img = FONT[font].render(s, True, COLOR.get(color, color) if isinstance(color, str) else color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def label(surf, s, pos):
    return text(surf, s.upper(), "label", "faint", pos)


def shadow(surf, rect, radius, offset=4, spread=2):
    r = pygame.Rect(rect).inflate(2 * spread, 2 * spread)
    layer = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, COLOR["shadow"], layer.get_rect(), border_radius=radius + spread)
    surf.blit(layer, r.move(0, offset))


def panel(surf, rect, color="panel", radius=RADIUS["panel"], border=True, drop=True):
    if drop:
        shadow(surf, rect, radius)
    pygame.draw.rect(surf, COLOR[color], rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, COLOR["border"], rect, 1, border_radius=radius)


def pill(surf, s, color, pos, anchor="topright"):
    img = FONT["small"].render(s, True, COLOR[color])
    rect = img.get_rect().inflate(18, 8)
    setattr(rect, anchor, pos)
    pygame.draw.rect(surf, mix(COLOR["panel"], COLOR[color], 0.18), rect, border_radius=RADIUS["pill"])
    surf.blit(img, img.get_rect(center=rect.center))
    return rect


def button(surf, rect, s, style="secondary", hover=False, enabled=True, font="body_bold", radius=RADIUS["button"]):
    if not enabled:
        fill, fg, outline = (None if style == "segment" else COLOR["panel"]), COLOR["faint"], None
    elif style in ("primary", "selected"):
        fill, fg, outline = COLOR["accent_hover" if hover else "accent"], COLOR["on_accent"], None
    elif style == "ghost":
        fill, fg, outline = (COLOR["raised"] if hover else None), COLOR["text"], COLOR["border"]
    elif style == "segment":
        fill, fg, outline = (COLOR["raised"] if hover else None), COLOR["text" if hover else "muted"], None
    else:
        fill, fg, outline = COLOR["raised_hover" if hover else "raised"], COLOR["text"], None
    if fill:
        pygame.draw.rect(surf, fill, rect, border_radius=radius)
    if outline:
        pygame.draw.rect(surf, outline, rect, 1, border_radius=radius)
    if s:
        img = FONT[font].render(s, True, fg)
        surf.blit(img, img.get_rect(center=pygame.Rect(rect).center))


def spinner(surf, center, t, r=14, color="accent"):
    box = pygame.Rect(0, 0, 2 * r, 2 * r)
    box.center = center
    start = -t / 160
    pygame.draw.arc(surf, COLOR["raised"], box, 0, 6.2832, 3)
    pygame.draw.arc(surf, COLOR[color], box, start, start + 1.9, 3)


def ring(surf, center, t, color="box_on_goal", r0=0.3, r1=0.75):
    r = round(TILE * (r0 + (r1 - r0) * ease_out(t)))
    layer = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
    pygame.draw.circle(layer, (*COLOR[color], round(200 * (1 - t))), layer.get_rect().center, r, 3)
    surf.blit(layer, layer.get_rect(center=center))
