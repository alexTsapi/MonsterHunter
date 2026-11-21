"""
MONSTER HUNTER - Κυνήγι Τεράτων
================================
Η ιδέα είναι ενός 6χρονου κυνηγού τεράτων! :)

- 5 κόσμοι: Πόλη, Δάσος, Παραλία, Χιόνια, Στοιχειωμένο Σπίτι
- Σε κάθε κόσμο: βρες τα κρυμμένα τέρατα -> μετά έρχεται ο ΑΡΧΗΓΟΣ
- Νικάς τον αρχηγό -> νέο όπλο + ξεκλειδώνει ο επόμενος κόσμος
- Σκυλάκι-βοηθός που γαβγίζει όταν βρει κρυμμένο τέρας
- Άλμπουμ τεράτων (σαν Pokémon)
- Δώρα: καρδιά, ασπίδα, παπούτσια ταχύτητας, μαγνήτης κυπέλλων
- Σύμμαχοι που παίζουν μόνοι τους
- Αποθηκεύει μόνο του

Χειρισμός ΤΑΜΠΛΕΤ: αριστερός αντίχειρας = περπάτημα, κόκκινο κουμπί = φωτιά (στοχεύει μόνο του)
Χειρισμός PC: WASD/βελάκια, ποντίκι ή SPACE για φωτιά, Q αλλαγή όπλου, P παύση, M ήχος
"""

import array
import base64
import heapq
import io
import json
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------- βασικά
W, H = 1120, 700
FPS = 60
ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.environ.get("ANDROID_PRIVATE", BASE_DIR)
SAVE_FILE = os.path.join(SAVE_DIR, "monster_hunter_save.json")
FONT_FILE = os.path.join(BASE_DIR, "font.ttf")

BLOCK, ROAD, NB = 400, 100, 7
SIDEWALK, ALLEY = 30, 46
WORLD_W = WORLD_H = NB * BLOCK + ROAD           # 2900
MID = NB // 2
HQ = (MID * BLOCK + ROAD + (BLOCK - ROAD) // 2,) * 2   # κέντρο της πλατείας
NAV = 50

MONSTERS_ALIVE = 18
ALLIES = 6                  # πόσοι σύμμαχοι έρχονται όταν τους καλέσεις
HELP_TIME = 30              # δευτερόλεπτα που μένει η ομάδα
HELP_COOLDOWN = 60          # πόσο περιμένεις για να ξανακαλέσεις
ALLY_KILL_BONUS = 1
ALLY_RESPAWN = 7
LIVES = 3
PLAYER_SPEED, ALLY_SPEED, DOG_SPEED = 4.2, 3.4, 4.6
PLAYER_MAX_HP, ALLY_MAX_HP = 100, 80
BULLET_SPEED = 11
REVEAL_RADIUS = 200
AUTO_AIM_RANGE = 520
POWERUPS_ON_MAP = 6
BOSS_REWARD = 25

WHITE = (255, 255, 255)
SKIN = (255, 220, 180)
GOLD = (255, 205, 40)

# ---------------------------------------------------------------- τέρατα
MT = {
    "slime":  dict(name="Γλίτσα",    color=(90, 210, 90),   hp=2, speed=1.7, dmg=16, reward=2, r=18),
    "goblin": dict(name="Γκόμπλιν",  color=(110, 170, 60),  hp=3, speed=2.4, dmg=20, reward=3, r=20),
    "ghost":  dict(name="Φάντασμα",  color=(220, 225, 255), hp=2, speed=3.0, dmg=18, reward=3, r=17, fly=True),
    "troll":  dict(name="Τρολ",      color=(120, 140, 110), hp=7, speed=1.4, dmg=34, reward=6, r=30),
    "spider": dict(name="Αράχνη",    color=(70, 55, 85),    hp=2, speed=3.2, dmg=16, reward=3, r=18),
    "bat":    dict(name="Νυχτερίδα", color=(95, 65, 120),   hp=1, speed=3.6, dmg=12, reward=2, r=15, fly=True),
    "mummy":  dict(name="Μούμια",    color=(225, 215, 180), hp=5, speed=1.5, dmg=26, reward=5, r=20),
    "dragon": dict(name="Δρακάκι",   color=(220, 80, 50),   hp=5, speed=2.2, dmg=24, reward=6, r=24, shoot=3.0),
    # τα τέρατα από τις φωτογραφίες του μικρού (μέτρια δύναμη, σε όλους τους κόσμους)
    "wolf":   dict(name="Μωβ Λύκος",     color=(150, 90, 200),  hp=4, speed=2.6, dmg=20, reward=4, r=22, photo="wolf"),
    "skel":   dict(name="Σκελετοζόμπι",  color=(150, 240, 90),  hp=5, speed=2.1, dmg=20, reward=4, r=22, photo="skel"),
    "yellow": dict(name="Κιτρινόσαυρος", color=(250, 225, 40),  hp=4, speed=2.5, dmg=20, reward=4, r=22,
                   photo="yellow", face=-1),
}
PHOTO_POOL = {"wolf": 4, "skel": 4, "yellow": 4}     # πόσο συχνά βγαίνουν (σε όλους τους κόσμους)
WORLD_GOALS = [30, 35, 40, 45, 50]                     # πόσα τέρατα πριν έρθει ο αρχηγός
BOSSES = {
    "boss_troll":  dict(name="Βασιλιάς Τρολ",     base="troll",  color=(110, 120, 150), hp=60, speed=1.6, dmg=40,
                        r=52, scale=1.9, shoot=2.2, shot_col=(140, 120, 100)),
    "boss_spider": dict(name="Βασίλισσα Αράχνη",  base="spider", color=(110, 40, 120),  hp=70, speed=2.1, dmg=30,
                        r=50, scale=2.6, shoot=2.4, shot_col=(240, 240, 240), summon="spider"),
    "boss_mummy":  dict(name="Φαραώ Μούμια",      base="mummy",  color=(240, 210, 120), hp=85, speed=1.7, dmg=40,
                        r=48, scale=2.3, shoot=2.0, shot_col=(230, 200, 120), summon="mummy"),
    "boss_dragon": dict(name="Παγο-Δράκος",       base="dragon", color=(90, 170, 235),  hp=95, speed=2.0, dmg=40,
                        r=55, scale=2.3, shoot=1.6, shot_col=(170, 230, 255)),
    "boss_ghost":  dict(name="Βασιλιάς Φάντασμα", base="ghost",  color=(200, 180, 255), hp=120, speed=2.2, dmg=40,
                        r=52, scale=2.8, shoot=1.5, shot_col=(200, 120, 255), summon="bat", fly=True),
}
for k, v in MT.items():
    v["key"], v["boss"] = k, False
    v.setdefault("base", k)
for k, v in BOSSES.items():
    v["key"], v["boss"] = k, True
    v["reward"] = BOSS_REWARD
ALBUM_ORDER = list(MT) + list(BOSSES)
ALL_TYPES = {**MT, **BOSSES}

# ---------------------------------------------------------------- όπλα
WEAPONS = [
    dict(name="Πιστόλι",      cd=0.24, angles=[0],             offs=[0],     dmg=1, color=(255, 240, 120)),
    dict(name="Διπλό Όπλο",   cd=0.22, angles=[0, 0],          offs=[-7, 7], dmg=1, color=(255, 190, 90)),
    dict(name="Τριπλό",       cd=0.26, angles=[-0.2, 0, 0.2],  offs=[0, 0, 0], dmg=1, color=(120, 255, 140)),
    dict(name="Όπλο Πάγου",   cd=0.15, angles=[0],             offs=[0],     dmg=1, color=(150, 225, 255), freeze=True),
    dict(name="Λέιζερ",       cd=0.11, angles=[0],             offs=[0],     dmg=2, color=(255, 90, 210), pierce=True),
]

# ---------------------------------------------------------------- κόσμοι
WORLDS = [
    dict(key="city", name="Πόλη", goal=12, boss="boss_troll",
         pool={"slime": 5, "goblin": 4, "ghost": 2, "troll": 1},
         ground=(158, 155, 148), road=(62, 62, 68), park=(72, 140, 72), park_chance=0.2,
         solid="building", side_spots=("bin", "bin", "bush"), road_spot="car", park_spot="bush", tree="round"),
    dict(key="forest", name="Δάσος", goal=14, boss="boss_spider",
         pool={"goblin": 4, "spider": 4, "slime": 3, "bat": 2},
         ground=(72, 128, 62), road=(145, 108, 68), park=(115, 170, 85), park_chance=0.25,
         solid="grove", side_spots=("mushroom", "bush", "bush"), road_spot="log", park_spot="bush", tree="round_dark"),
    dict(key="beach", name="Παραλία", goal=15, boss="boss_mummy",
         pool={"slime": 3, "mummy": 3, "spider": 2, "goblin": 2, "dragon": 1},
         ground=(236, 214, 160), road=(212, 186, 132), park=(240, 222, 170), park_chance=0.3,
         solid="hut", side_spots=("sandcastle", "umbrella"), road_spot="boat", park_spot="umbrella", tree="palm"),
    dict(key="snow", name="Χιόνια", goal=16, boss="boss_dragon",
         pool={"ghost": 3, "troll": 2, "bat": 3, "dragon": 2, "goblin": 2},
         ground=(236, 241, 248), road=(196, 206, 222), park=(225, 235, 245), park_chance=0.25,
         solid="cabin", side_spots=("snowman", "snowpile"), road_spot="sled", park_spot="snowpile", tree="pine"),
    dict(key="haunted", name="Στοιχειωμένο", goal=18, boss="boss_ghost",
         pool={"ghost": 4, "bat": 4, "mummy": 3, "spider": 2, "dragon": 1},
         ground=(64, 60, 74), road=(98, 94, 104), park=(52, 72, 52), park_chance=0.3,
         solid="crypt", side_spots=("pumpkin", "tomb"), road_spot="coffin", park_spot="tomb", tree="dead", dark=True),
]

for _w, _g in zip(WORLDS, WORLD_GOALS):
    _w["pool"].update(PHOTO_POOL)
    _w["goal"] = _g

SHIRTS = [(200, 60, 60), (230, 150, 40), (60, 160, 90), (150, 80, 180), (40, 170, 190),
          (220, 200, 60), (180, 100, 60), (230, 110, 160)]
HELMETS = [(60, 90, 60), (80, 80, 80), (120, 90, 50), (50, 60, 110), (150, 40, 40)]
NAMES = ["Νίκος", "Μαρία", "Κώστας", "Ελένη", "Γιάννης", "Σοφία", "Πέτρος", "Άννα", "Δημήτρης", "Ζωή"]
BUILDING_COLORS = [(190, 95, 75), (205, 175, 125), (165, 175, 190), (150, 110, 90),
                   (215, 205, 175), (120, 140, 175), (180, 120, 140), (140, 160, 130)]
CAR_COLORS = [(200, 40, 40), (40, 90, 200), (230, 230, 230), (30, 30, 30), (240, 190, 30),
              (60, 150, 80), (150, 150, 160), (230, 120, 30)]


_font_cache = {}


def font(size):
    if size not in _font_cache:
        if os.path.exists(FONT_FILE):
            _font_cache[size] = pygame.font.Font(FONT_FILE, size)
        else:
            _font_cache[size] = pygame.font.SysFont("arial,dejavusans,freesans", size, bold=True)
    return _font_cache[size]


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------------------------------------------------------------- σχέδια χαρακτήρων
def limb(surf, color, a, b, w):
    a = (int(a[0]), int(a[1]))
    b = (int(b[0]), int(b[1]))
    pygame.draw.line(surf, color, a, b, w)
    pygame.draw.circle(surf, color, a, w // 2)
    pygame.draw.circle(surf, color, b, w // 2)


_shadow_cache = {}


def shadow(surf, sx, sy, w):
    w = max(4, int(w))
    img = _shadow_cache.get(w)
    if img is None:
        img = pygame.Surface((w, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(img, (0, 0, 0, 75), (0, 0, w, 10))
        _shadow_cache[w] = img
    surf.blit(img, (sx - w // 2, sy - 5))


def draw_hero(surf, sx, sy, aim, walk, shirt=(40, 110, 220), helmet=(60, 90, 60)):
    f = 1 if math.cos(aim) >= 0 else -1
    sw = math.sin(walk) * 6 if walk is not None else 0
    shadow(surf, sx, sy + 22, 30)
    pants, boots = (45, 50, 80), (70, 45, 25)
    limb(surf, pants, (sx - 4, sy + 4), (sx - 4 + sw, sy + 19), 7)
    limb(surf, pants, (sx + 4, sy + 4), (sx + 4 - sw, sy + 19), 7)
    pygame.draw.ellipse(surf, boots, (sx - 4 + sw - 4 + 2 * f, sy + 17, 10, 7))
    pygame.draw.ellipse(surf, boots, (sx + 4 - sw - 4 + 2 * f, sy + 17, 10, 7))
    pygame.draw.rect(surf, (120, 80, 40), (sx - 6 - 9 * f, sy - 13, 12, 16), border_radius=3)
    limb(surf, shirt, (sx - 6 * f, sy - 9), (sx - 9 * f, sy + 2 - sw * 0.5), 6)
    pygame.draw.rect(surf, shirt, (sx - 10, sy - 15, 20, 22), border_radius=6)
    pygame.draw.rect(surf, (90, 60, 30), (sx - 10, sy + 1, 20, 4))
    pygame.draw.rect(surf, (230, 190, 60), (sx - 2, sy + 1, 4, 4))
    hx, hy = sx, sy - 25
    pygame.draw.circle(surf, SKIN, (hx, hy), 10)
    pygame.draw.circle(surf, helmet, (hx, hy - 2), 11, draw_top_left=True, draw_top_right=True)
    pygame.draw.rect(surf, helmet, (hx - 11 if f > 0 else hx - 4, hy - 3, 15, 3))
    pygame.draw.circle(surf, (30, 30, 30), (hx + 4 * f, hy + 1), 2)
    pygame.draw.line(surf, (160, 90, 70), (hx + 2 * f, hy + 6), (hx + 6 * f, hy + 5), 2)
    ca, sa = math.cos(aim), math.sin(aim)
    shx, shy = sx + 3 * f, sy - 8
    hand = (shx + ca * 13, shy + sa * 13)
    tip = (sx + ca * 34, sy - 8 + sa * 34)
    pygame.draw.line(surf, (35, 35, 35), (int(shx + ca * 6), int(shy + sa * 6)), (int(tip[0]), int(tip[1])), 7)
    pygame.draw.line(surf, (110, 110, 120), (int(hand[0]), int(hand[1])), (int(tip[0]), int(tip[1])), 3)
    limb(surf, shirt, (shx, shy), hand, 6)
    pygame.draw.circle(surf, SKIN, (int(hand[0]), int(hand[1])), 4)


def draw_goblin(surf, sx, sy, f, ph, flash, col=None):
    skin = WHITE if flash else (col or (110, 170, 60))
    dark = WHITE if flash else shade(skin, 0.65)
    sw = math.sin(ph * 1.6) * 6
    shadow(surf, sx, sy + 20, 28)
    limb(surf, dark, (sx - 4, sy + 3), (sx - 4 + sw, sy + 18), 6)
    limb(surf, dark, (sx + 4, sy + 3), (sx + 4 - sw, sy + 18), 6)
    limb(surf, skin, (sx - 7 * f, sy - 9), (sx - 11 * f, sy + 2 + sw * 0.5), 5)
    pygame.draw.ellipse(surf, skin, (sx - 9, sy - 15, 18, 20))
    pygame.draw.polygon(surf, (110, 70, 30), [(sx - 9, sy - 1), (sx + 9, sy - 1), (sx + 6, sy + 8), (sx - 6, sy + 8)])
    hx, hy = sx + 2 * f, sy - 23
    pygame.draw.polygon(surf, skin, [(hx - 8, hy - 2), (hx - 22, hy - 9), (hx - 8, hy + 4)])
    pygame.draw.polygon(surf, skin, [(hx + 8, hy - 2), (hx + 22, hy - 9), (hx + 8, hy + 4)])
    pygame.draw.circle(surf, skin, (hx, hy), 11)
    pygame.draw.circle(surf, (255, 230, 0), (hx - 4 + 2 * f, hy - 2), 3)
    pygame.draw.circle(surf, (255, 230, 0), (hx + 4 + 2 * f, hy - 2), 3)
    pygame.draw.circle(surf, (200, 0, 0), (hx - 4 + 3 * f, hy - 2), 1)
    pygame.draw.circle(surf, (200, 0, 0), (hx + 4 + 3 * f, hy - 2), 1)
    pygame.draw.arc(surf, (40, 20, 10), (hx - 6, hy, 12, 8), 3.4, 6.0, 2)
    pygame.draw.polygon(surf, WHITE, [(hx - 3, hy + 5), (hx - 1, hy + 9), (hx + 1, hy + 5)])
    hand = (sx + 13 * f, sy - 3 + sw * 0.4)
    club_end = (sx + 20 * f, sy - 28)
    limb(surf, skin, (sx + 7 * f, sy - 9), hand, 5)
    limb(surf, (120, 75, 30), hand, club_end, 5)
    pygame.draw.circle(surf, (100, 60, 25), (int(club_end[0]), int(club_end[1])), 7)


def draw_troll(surf, sx, sy, f, ph, flash, col=None):
    skin = WHITE if flash else (col or (120, 140, 110))
    dark = WHITE if flash else shade(skin, 0.7)
    belly = WHITE if flash else shade(skin, 1.2)
    sw = math.sin(ph) * 7
    shadow(surf, sx, sy + 30, 54)
    limb(surf, dark, (sx - 11, sy + 6), (sx - 11 + sw, sy + 27), 13)
    limb(surf, dark, (sx + 11, sy + 6), (sx + 11 - sw, sy + 27), 13)
    limb(surf, skin, (sx - 18 * f, sy - 16), (sx - 25 * f, sy + 4 + sw * 0.5), 10)
    pygame.draw.ellipse(surf, skin, (sx - 23, sy - 30, 46, 44))
    pygame.draw.ellipse(surf, belly, (sx - 14, sy - 16, 28, 26))
    pygame.draw.rect(surf, (90, 60, 30), (sx - 20, sy + 4, 40, 9), border_radius=3)
    hx, hy = sx + 5 * f, sy - 37
    pygame.draw.circle(surf, skin, (hx, hy), 14)
    pygame.draw.line(surf, (40, 50, 35), (hx - 9, hy - 6), (hx + 9, hy - 6), 4)
    pygame.draw.circle(surf, (255, 200, 0), (hx - 5 + 2 * f, hy - 2), 3)
    pygame.draw.circle(surf, (255, 200, 0), (hx + 5 + 2 * f, hy - 2), 3)
    pygame.draw.ellipse(surf, dark, (hx - 4 + 3 * f, hy + 1, 8, 6))
    pygame.draw.line(surf, (40, 20, 10), (hx - 7, hy + 8), (hx + 7, hy + 8), 3)
    pygame.draw.polygon(surf, WHITE, [(hx - 6, hy + 8), (hx - 4, hy + 1), (hx - 2, hy + 8)])
    pygame.draw.polygon(surf, WHITE, [(hx + 2, hy + 8), (hx + 4, hy + 1), (hx + 6, hy + 8)])
    hand = (sx + 28 * f, sy - 2 + sw * 0.3)
    club_end = (sx + 36 * f, sy - 46)
    limb(surf, skin, (sx + 18 * f, sy - 16), hand, 10)
    limb(surf, (110, 70, 30), hand, club_end, 8)
    ce = (int(club_end[0]), int(club_end[1]))
    for a in range(0, 360, 60):
        r = math.radians(a)
        pygame.draw.line(surf, (60, 60, 60), ce, (ce[0] + math.cos(r) * 14, ce[1] + math.sin(r) * 14), 3)
    pygame.draw.circle(surf, (95, 60, 25), ce, 10)


def draw_slime(surf, sx, sy, f, ph, flash, col=None):
    c = WHITE if flash else (col or (90, 210, 90))
    sq = math.sin(ph * 1.5) * 0.18
    w, h = int(40 * (1 + sq)), int(32 * (1 - sq))
    shadow(surf, sx, sy + 16, w)
    rect = pygame.Rect(sx - w // 2, sy + 16 - h, w, h)
    pygame.draw.ellipse(surf, c, rect)
    pygame.draw.rect(surf, c, (rect.x, rect.centery, w, h // 2), border_bottom_left_radius=8, border_bottom_right_radius=8)
    pygame.draw.ellipse(surf, (220, 255, 220), (rect.x + 7, rect.y + 5, 10, 6))
    ey = rect.y + h // 2 - 2
    for ex in (sx - 7 + 3 * f, sx + 7 + 3 * f):
        pygame.draw.circle(surf, WHITE, (ex, ey), 5)
        pygame.draw.circle(surf, (20, 20, 20), (ex + 2 * f, ey), 2)
    pygame.draw.arc(surf, (20, 60, 20), (sx - 6 + 3 * f, ey + 3, 12, 8), 3.3, 6.1, 2)


def draw_ghost(surf, sx, sy, f, ph, flash, col=None):
    fl = int(math.sin(ph) * 5)
    shadow(surf, sx, sy + 22, 24)
    g = pygame.Surface((50, 60), pygame.SRCALPHA)
    base = col or (225, 230, 255)
    c = (255, 255, 255, 255) if flash else (*base, 205)
    pygame.draw.circle(g, c, (25, 20), 17)
    pygame.draw.rect(g, c, (8, 20, 34, 24))
    for i in range(4):
        off = 4 if (i + int(ph * 2)) % 2 else 0
        pygame.draw.circle(g, c, (12 + i * 9, 44 + off), 5)
    ex = 25 + 3 * f
    pygame.draw.ellipse(g, (20, 20, 40, 255), (ex - 10, 14, 7, 10))
    pygame.draw.ellipse(g, (20, 20, 40, 255), (ex + 3, 14, 7, 10))
    pygame.draw.ellipse(g, (20, 20, 40, 255), (ex - 4, 28, 8, 10))
    pygame.draw.circle(g, c, (6, 30 + fl // 2), 5)
    pygame.draw.circle(g, c, (44, 30 - fl // 2), 5)
    surf.blit(g, (sx - 25, sy - 36 + fl))


def draw_spider(surf, sx, sy, f, ph, flash, col=None):
    body = WHITE if flash else (col or (70, 55, 85))
    leg = WHITE if flash else shade(body, 0.7)
    shadow(surf, sx, sy + 14, 44)
    for side in (-1, 1):
        for i in range(4):
            a = math.sin(ph * 2.5 + i * 1.4 + (side > 0) * 1.5) * 4
            base = (sx + side * 7, sy - 4 + i * 3)
            knee = (sx + side * (20 + i * 2), sy - 16 + i * 7 + a)
            foot = (sx + side * (28 + i), sy + 4 + i * 5 - a)
            pygame.draw.line(surf, leg, base, knee, 3)
            pygame.draw.line(surf, leg, knee, foot, 3)
    pygame.draw.ellipse(surf, body, (sx - 15 - 4 * f, sy - 10, 30, 24))
    if not flash:
        pygame.draw.polygon(surf, (220, 40, 40), [(sx - 4 * f - 4, sy - 2), (sx - 4 * f + 4, sy - 2),
                                                  (sx - 4 * f, sy + 4)])
        pygame.draw.polygon(surf, (220, 40, 40), [(sx - 4 * f - 4, sy + 9), (sx - 4 * f + 4, sy + 9),
                                                  (sx - 4 * f, sy + 4)])
    hx, hy = sx + 12 * f, sy - 8
    pygame.draw.circle(surf, body, (hx, hy), 10)
    for ex, ey in ((-4, -3), (3, -3), (-2, 2), (5, 2)):
        pygame.draw.circle(surf, (255, 50, 50), (hx + ex * f + 2 * f, hy + ey), 2)
    pygame.draw.line(surf, WHITE, (hx + 3 * f, hy + 7), (hx + 1 * f, hy + 12), 2)
    pygame.draw.line(surf, WHITE, (hx + 8 * f, hy + 6), (hx + 8 * f, hy + 11), 2)


def draw_bat(surf, sx, sy, f, ph, flash, col=None):
    body = WHITE if flash else (col or (95, 65, 120))
    wing = WHITE if flash else shade(body, 0.75)
    bob = math.sin(ph * 2) * 6
    shadow(surf, sx, sy + 20, 20)
    y = sy - 16 + bob
    flap = math.sin(ph * 4) * 10
    for side in (-1, 1):
        pts = [(sx + side * 6, y - 2), (sx + side * 20, y - 12 - flap), (sx + side * 32, y - 4 - flap * 0.5),
               (sx + side * 26, y + 4), (sx + side * 18, y + 1), (sx + side * 11, y + 7)]
        pygame.draw.polygon(surf, wing, pts)
    pygame.draw.ellipse(surf, body, (sx - 8, y - 9, 16, 19))
    pygame.draw.polygon(surf, body, [(sx - 7, y - 6), (sx - 5, y - 15), (sx - 2, y - 7)])
    pygame.draw.polygon(surf, body, [(sx + 7, y - 6), (sx + 5, y - 15), (sx + 2, y - 7)])
    pygame.draw.circle(surf, (255, 230, 60), (int(sx - 3 + 2 * f), int(y - 3)), 2)
    pygame.draw.circle(surf, (255, 230, 60), (int(sx + 3 + 2 * f), int(y - 3)), 2)
    pygame.draw.line(surf, WHITE, (sx - 2 + 2 * f, y + 3), (sx - 2 + 2 * f, y + 6), 1)
    pygame.draw.line(surf, WHITE, (sx + 2 + 2 * f, y + 3), (sx + 2 + 2 * f, y + 6), 1)


def draw_mummy(surf, sx, sy, f, ph, flash, col=None):
    wrap = WHITE if flash else (col or (225, 215, 180))
    line = shade(wrap, 0.7)
    sw = math.sin(ph * 1.2) * 5
    shadow(surf, sx, sy + 20, 28)
    limb(surf, wrap, (sx - 4, sy + 3), (sx - 4 + sw, sy + 18), 7)
    limb(surf, wrap, (sx + 4, sy + 3), (sx + 4 - sw, sy + 18), 7)
    pygame.draw.rect(surf, wrap, (sx - 10, sy - 16, 20, 22), border_radius=6)
    for i in range(4):
        pygame.draw.line(surf, line, (sx - 10, sy - 13 + i * 5), (sx + 10, sy - 10 + i * 5), 2)
    arm = math.sin(ph * 1.2) * 3
    limb(surf, wrap, (sx + 2 * f, sy - 11), (sx + 22 * f, sy - 12 + arm), 6)
    limb(surf, wrap, (sx - 4 * f, sy - 7), (sx + 18 * f, sy - 6 - arm), 6)
    hx, hy = sx + 1 * f, sy - 26
    pygame.draw.circle(surf, wrap, (hx, hy), 10)
    for i in range(3):
        pygame.draw.line(surf, line, (hx - 9, hy - 5 + i * 5), (hx + 9, hy - 3 + i * 5), 2)
    pygame.draw.circle(surf, (120, 255, 120) if not flash else WHITE, (hx + 4 * f, hy - 1), 3)
    pygame.draw.line(surf, (60, 50, 40), (hx - 5 * f - 2, hy - 1), (hx - 2 * f, hy - 1), 2)
    tail = math.sin(ph * 3) * 5
    pygame.draw.line(surf, wrap, (sx - 8 * f, sy - 4), (sx - 20 * f, sy + 2 + tail), 3)


def draw_dragon(surf, sx, sy, f, ph, flash, col=None):
    body = WHITE if flash else (col or (220, 80, 50))
    dark = WHITE if flash else shade(body, 0.65)
    belly = WHITE if flash else (250, 205, 100)
    sw = math.sin(ph * 1.5) * 5
    shadow(surf, sx, sy + 20, 40)
    pygame.draw.polygon(surf, body, [(sx - 10 * f, sy - 2), (sx - 10 * f, sy + 8), (sx - 34 * f, sy - 4 + sw)])
    pygame.draw.polygon(surf, dark, [(sx - 34 * f, sy - 4 + sw), (sx - 42 * f, sy - 10 + sw), (sx - 38 * f, sy + 2 + sw)])
    flap = math.sin(ph * 2.5) * 8
    pygame.draw.polygon(surf, dark, [(sx - 2 * f, sy - 12), (sx - 14 * f, sy - 36 - flap), (sx - 26 * f, sy - 22 - flap),
                                     (sx - 12 * f, sy - 8)])
    limb(surf, dark, (sx - 6, sy + 4), (sx - 6 + sw, sy + 18), 7)
    limb(surf, dark, (sx + 6, sy + 4), (sx + 6 - sw, sy + 18), 7)
    pygame.draw.ellipse(surf, body, (sx - 15, sy - 16, 30, 26))
    pygame.draw.ellipse(surf, belly, (sx - 7 + 3 * f, sy - 10, 14, 18))
    for i in range(3):
        bx = sx - 8 * f + i * 6 * f
        pygame.draw.polygon(surf, dark, [(bx - 3, sy - 14), (bx + 3, sy - 14), (bx, sy - 21)])
    hx, hy = sx + 13 * f, sy - 22
    pygame.draw.circle(surf, body, (hx, hy), 11)
    pygame.draw.ellipse(surf, body, (hx + (2 if f > 0 else -16), hy - 3, 14, 11))
    pygame.draw.circle(surf, (40, 20, 10), (hx + 12 * f, hy + 1), 1)
    pygame.draw.polygon(surf, (250, 240, 200), [(hx - 6, hy - 8), (hx - 3, hy - 18), (hx - 1, hy - 9)])
    pygame.draw.polygon(surf, (250, 240, 200), [(hx + 1, hy - 9), (hx + 4, hy - 18), (hx + 6, hy - 8)])
    pygame.draw.circle(surf, (255, 240, 60), (hx + 3 * f, hy - 3), 4)
    pygame.draw.line(surf, (20, 20, 20), (hx + 3 * f, hy - 6), (hx + 3 * f, hy), 2)


def draw_dog(surf, sx, sy, f, ph, moving, barking):
    fur, dark = (180, 120, 65), (115, 72, 38)
    sw = math.sin(ph * 2) * 4 if moving else 0
    shadow(surf, sx, sy + 13, 32)
    for lx, s in ((-9, sw), (-4, -sw), (6, -sw), (11, sw)):
        limb(surf, dark if lx in (-4, 6) else fur, (sx + lx * f, sy), (sx + lx * f + s, sy + 12), 5)
    wag = math.sin(ph * 7) * 6
    limb(surf, fur, (sx - 13 * f, sy - 4), (sx - 22 * f, sy - 14 + wag), 4)
    pygame.draw.ellipse(surf, fur, (sx - 15, sy - 9, 30, 16))
    pygame.draw.ellipse(surf, (235, 205, 165), (sx - 6, sy - 3, 14, 8))
    pygame.draw.line(surf, (210, 40, 40), (sx + 7 * f, sy - 10), (sx + 10 * f, sy - 2), 3)
    hx, hy = sx + 15 * f, sy - 13
    pygame.draw.circle(surf, fur, (hx, hy), 9)
    pygame.draw.ellipse(surf, (235, 205, 165), (hx + (2 if f > 0 else -12), hy - 1, 10, 8))
    pygame.draw.circle(surf, (20, 20, 20), (hx + 11 * f, hy + 1), 3)
    pygame.draw.ellipse(surf, dark, (hx - 7 * f - 4, hy - 7, 8, 14))
    pygame.draw.circle(surf, (20, 20, 20), (hx + 3 * f, hy - 3), 2)
    if barking:
        pygame.draw.polygon(surf, (120, 20, 20), [(hx + 4 * f, hy + 5), (hx + 11 * f, hy + 4), (hx + 9 * f, hy + 10)])


DRAWERS = {"goblin": draw_goblin, "troll": draw_troll, "slime": draw_slime, "ghost": draw_ghost,
           "spider": draw_spider, "bat": draw_bat, "mummy": draw_mummy, "dragon": draw_dragon}


_photo_src, _photo_cache = {}, {}


def photo_image(key):
    if key not in _photo_src:
        try:
            img = pygame.image.load(io.BytesIO(base64.b64decode(PHOTO_DATA[key])), "monster.png")
            if pygame.display.get_surface():
                img = img.convert_alpha()
        except Exception as e:
            print("Δεν φόρτωσε η φωτογραφία", key, e)
            img = None
        _photo_src[key] = img
    return _photo_src[key]


def draw_photo(surf, sx, sy, t, f, ph, flash, scale=1.0):
    """Τέρας από φωτογραφία: χοροπηδάει, γέρνει λίγο και γυρίζει προς τον στόχο."""
    src = photo_image(t["photo"])
    if src is None:
        draw_slime(surf, sx, sy, f, ph, flash, t["color"])
        return
    h = int(t["r"] * 3.8 * scale)
    hop = abs(math.sin(ph * 1.6))
    q = int(hop * 4 + 0.5)                       # 0..4
    tq = int(round(math.sin(ph * 0.8) * 2))      # -2..2
    flip = f != t.get("face", 1)
    key = (t["photo"], h, q, tq, flip, bool(flash))
    img = _photo_cache.get(key)
    if img is None:
        bkey = (t["photo"], h)
        base = _photo_cache.get(bkey)
        if base is None:
            base = pygame.transform.smoothscale(src, (max(1, round(src.get_width() * h / src.get_height())), h))
            _photo_cache[bkey] = base
        k = q / 4
        w2, h2 = int(base.get_width() * (1.05 - 0.07 * k)), int(base.get_height() * (0.93 + 0.09 * k))
        img = pygame.transform.smoothscale(base, (w2, h2))
        if flip:
            img = pygame.transform.flip(img, True, False)
        if tq:
            img = pygame.transform.rotate(img, tq * 3)
        if flash:
            img = img.copy()
            img.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        _photo_cache[key] = img
    shadow(surf, sx, sy + 20, int(img.get_width() * (0.75 - 0.2 * hop)))
    lift = int(hop * 9 * scale)
    surf.blit(img, (sx - img.get_width() // 2, sy + 20 - img.get_height() - lift))


def draw_crown(surf, x, y, w):
    pts = [(x - w, y), (x - w, y - w * 0.8), (x - w * 0.5, y - w * 0.35), (x, y - w), (x + w * 0.5, y - w * 0.35),
           (x + w, y - w * 0.8), (x + w, y)]
    pygame.draw.polygon(surf, GOLD, pts)
    pygame.draw.polygon(surf, (180, 120, 10), pts, 2)
    pygame.draw.circle(surf, (230, 40, 60), (int(x), int(y - w * 0.3)), max(2, int(w * 0.18)))


def draw_monster_type(surf, sx, sy, t, f, ph, flash=False, scale=None):
    """Σχεδιάζει οποιοδήποτε τέρας (και αρχηγό με στέμμα) με κέντρο τα πόδια στο (sx, sy)."""
    scale = scale if scale is not None else t.get("scale", 1.0)
    if t.get("photo"):
        draw_photo(surf, sx, sy, t, f, ph, flash, scale)
        return
    fn = DRAWERS[t["base"]]
    col = t["color"] if t["boss"] else None
    head_top = {"troll": 51, "ghost": 36, "spider": 18, "mummy": 36, "dragon": 36, "goblin": 34,
                "slime": 20, "bat": 30}.get(t["base"], 40)
    top = sy - head_top * scale
    if abs(scale - 1.0) < 0.01:
        fn(surf, sx, sy, f, ph, flash, col)
    else:
        tmp = pygame.Surface((130, 130), pygame.SRCALPHA)
        fn(tmp, 65, 95, f, ph, flash, col)
        sw, sh = int(130 * scale), int(130 * scale)
        img = pygame.transform.scale(tmp, (sw, sh))
        surf.blit(img, (sx - sw // 2, sy - int(95 * scale)))
    if t["boss"]:
        bob = math.sin(ph) * 5 * scale if t["base"] in ("ghost", "bat") else 0
        draw_crown(surf, sx + (12 * f * scale if t["base"] in ("spider", "dragon") else 0), top + 4 * scale + bob, 9 * scale)


# ---------------------------------------------------------------- φωτογραφίες τεράτων (από τα παιχνίδια του μικρού)
PHOTO_DATA = {
    "wolf": (
        "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"
        "Zqqt+2c103z2ia++7TLJi++W4HB1DSHKQHDoN4zjgJIKrSsg0q/PiMEyX8ypmwlKt2hdY0dfUHJaMayXrM+W2NHjvScnidI1ISXq"
        "aVFPSiHSTiZ4n/jYAx/bapu+xRlF6MRsNmO1Oi2+goDznr29c5w/d4Ebd65xsrnDTM/w3jEMHSEUcd8UEz4MDMOKHB0xFnnu2rSE"
        "4DnJx8iZQleGJBNKZ+qqKqaQMpJVJsjI82d3iJ63a5Dc/SxPPPs4VaWwbiB4SyahjaKZ1EgJtu+Ky4WUbM6WbNYrRjsyjiPDpi/o"
        "vpxZnx5DzlR1RSLRtHOm0xlDX+TMl6uTkpnqihDgI+97+HXJKvI7wbS+97H3cvPGcxwdHRTmXkiMY2A+3yVlUDqTQsQ7z3qzwnlH"
        "ykWLVQiKyVKIGKM5Wd1mtCPeB5Qx7J6/SD2dcu9D78WZkcGuqYxBiIgUhSlIDbcPzt6+meTrrnG0ROXwdiBEi9RlDTadTljM55AT"
        "yTtO7tzh4PYNTCMwk4qmbVBK0XUb+mFVJtTOouoaVdcEEju751BKcHR6i+XqhGG0KGPISvLeC49QVeKtm6NkIge3rvPs019BCEHf"
        "F8eKnZ1d9s5fplsfk5In+IQTDj+skUKRyAghaactMQekTAxDh8wULVTnqNuWsd8w9h3Lo9tMTIudXqaJBkRAqSLw9+Xnn35b8XO/"
        "WQckELg4sLt3GXJmNtlHbmXHqsqgtKRfHzN2S5IoeBala6K37Ozt8uXrv8/RyW0WZp+kGurFgnYyoV+PVFXN1av3c3Z6QCbhR0tq"
        "WoxWpJD48IOP8Htf+ep31AF9+3dZZI6ObuNCIGWJ80Xn9ZH3Pcpk1nLr1jM45yFJrLPYrVzF4Dt29vaYTBrcsMaHAecHvLPEEAgx"
        "MDqLtcW1o++XkEoh1w0rXHIEGUjCs1rZd0Q2eeHjPf7UF5HC0NS7XLjyAM1kUQj5EuaLWXH5GPuiPt2PxdGsbZnv7HPhwnlW/piU"
        "YtHV73p0VdM0M5z3gGAynRGsY7M6Yb1eFayOhCv7l9H6O6tV5Lf/HyouXLqAsx5S4tL+Hu9/6BEe+eBj3LrxPP2mw7mETKKI9GlN"
        "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"
    ),
    "skel": (
        "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"
    ),
    "yellow": (
        "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"
    ),
}


# ---------------------------------------------------------------- ήχοι (φτιάχνονται με κώδικα)
def _sq(f, t):
    return 1.0 if (t * f) % 1 < 0.5 else -1.0


def _tri(f, t):
    return 4 * abs((t * f) % 1 - 0.5) - 1


def _noise():
    return random.uniform(-1, 1)


class Sfx:
    def __init__(self, on=True):
        self.ok, self.on = False, on
        self.snd, self.last = {}, {}
        self.music_ch = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.sr, _, self.ch = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(24)
            self.build()
            self.ok = True
            self.music_ch = self.snd["music"].play(loops=-1)
            if not self.on:
                self.music_ch.pause()
        except Exception as e:
            print("Χωρίς ήχο:", e)

    def make(self, dur, fn, vol):
        n, sr, ch = int(self.sr * dur), self.sr, self.ch
        a = array.array("h")
        for i in range(n):
            v = fn(i / sr, i / n)
            s = int((1 if v > 1 else -1 if v < -1 else v) * vol * 32767)
            if ch == 1:
                a.append(s)
            else:
                a.extend([s] * ch)
        return pygame.mixer.Sound(buffer=a.tobytes())

    def build(self):
        m = self.make
        self.snd["shoot"] = m(0.12, lambda t, p: (_noise() * 0.6 + _sq(200 - 120 * p, t) * 0.4) * math.exp(-p * 5), 0.26)
        self.snd["laser"] = m(0.10, lambda t, p: _sq(1400 - 900 * p, t) * (1 - p), 0.14)
        self.snd["ally_shoot"] = m(0.10, lambda t, p: (_noise() * 0.6 + _sq(240 - 120 * p, t) * 0.3) * math.exp(-p * 6), 0.08)
        self.snd["hit"] = m(0.07, lambda t, p: _sq(900 - 500 * p, t) * (1 - p), 0.18)
        self.snd["poof"] = m(0.35, lambda t, p: (_tri(500 + 900 * p, t) * 0.6 + _noise() * 0.3) * (1 - p), 0.28)
        self.snd["growl"] = m(0.55, lambda t, p: (2 * ((t * (55 + 12 * math.sin(t * 30))) % 1) - 1)
                              * (0.5 + 0.5 * math.sin(t * 40)) * min(1, p * 8) * (1 - p), 0.36)
        self.snd["boss"] = m(1.3, lambda t, p: ((2 * ((t * (40 + 20 * math.sin(t * 9))) % 1) - 1) * 0.7 + _noise() * 0.3)
                             * min(1, p * 5) * (1 - p), 0.45)
        self.snd["coin"] = m(0.09, lambda t, p: _sq(1320 if p < 0.4 else 1760, t) * (1 - p), 0.12)
        notes = [784, 988, 1175, 1568]
        self.snd["powerup"] = m(0.36, lambda t, p: _tri(notes[min(3, int(p * 4))] / 2, t) * (1 - (p * 4) % 1 * 0.6), 0.3)
        album = [523, 659, 784, 1047, 784, 1047]
        self.snd["album"] = m(0.6, lambda t, p: math.sin(6.283 * album[min(5, int(p * 6))] * t) * (1 - (p * 6) % 1 * 0.5), 0.3)
        fan = [523, 523, 523, 659, 784, 0, 659, 784, 1047, 1047]
        self.snd["fanfare"] = m(1.6, lambda t, p: _sq(fan[min(9, int(p * 10))], t) * 0.5 * (1 - (p * 10) % 1 * 0.5)
                                if fan[min(9, int(p * 10))] else 0, 0.3)
        self.snd["team"] = m(0.14, lambda t, p: math.sin(6.283 * (660 if p < 0.5 else 880) * t) * (1 - (p * 2) % 1), 0.13)
        self.snd["hurt"] = m(0.12, lambda t, p: _sq(140, t) * (1 - p), 0.22)
        self.snd["player_die"] = m(0.7, lambda t, p: _tri(500 * (1 - p) + 120, t) * (1 - p), 0.32)
        self.snd["ally_die"] = m(0.25, lambda t, p: _tri(400 * (1 - p) + 120, t) * (1 - p), 0.14)
        self.snd["flee"] = m(0.25, lambda t, p: _tri(500 + 700 * p, t) * (1 - p), 0.16)
        self.snd["bark"] = m(0.32, lambda t, p: ((_sq(330 - 160 * ((p * 2) % 1), t) * 0.5 + _noise() * 0.5)
                                                 * (1 - (p * 2) % 1) if (p * 2) % 1 < 0.6 else 0), 0.3)
        self.snd["fire"] = m(0.3, lambda t, p: _noise() * (1 - p) * min(1, p * 10), 0.18)
        sad = [523, 440, 392, 330]
        self.snd["retry"] = m(1.0, lambda t, p: _tri(sad[min(3, int(p * 4))], t) * (1 - (p * 4) % 1 * 0.6), 0.28)

        bass = [110, 110, 131, 110, 147, 147, 165, 98, 110, 110, 131, 165, 147, 131, 98, 98]
        mel = [440, 0, 523, 587, 659, 0, 587, 523, 440, 0, 392, 440, 523, 0, 440, 0,
               440, 0, 523, 587, 659, 784, 659, 587, 523, 0, 440, 392, 440, 0, 0, 0]

        def music(t, p):
            beat = int(t / 0.5)
            tb = t - beat * 0.5
            v = _sq(bass[beat % 16], t) * 0.20 * math.exp(-tb * 2.5)
            v += math.sin(6.283 * (50 + 80 * math.exp(-tb * 30)) * tb) * math.exp(-tb * 12) * 0.45
            th = tb - 0.25
            if th >= 0:
                v += _noise() * math.exp(-th * 80) * 0.10
            e = int(t / 0.25)
            te = t - e * 0.25
            if mel[e % 32]:
                v += _tri(mel[e % 32], t) * 0.13 * math.exp(-te * 4)
            return v

        self.snd["music"] = m(8.0, music, 0.5)
        self.snd["music"].set_volume(0.3)

    def play(self, name, gap=0.04):
        if not (self.ok and self.on):
            return
        now = pygame.time.get_ticks() / 1000
        if now - self.last.get(name, -9) < gap:
            return
        self.last[name] = now
        self.snd[name].play()

    def set_on(self, on):
        self.on = on
        if self.music_ch:
            self.music_ch.unpause() if on else self.music_ch.pause()


# ---------------------------------------------------------------- κόσμος
class Solid:
    def __init__(self, rect):
        self.rect = rect
        self.color = random.choice(BUILDING_COLORS)


class Spot:
    """Κρυψώνα για τέρατα."""

    def __init__(self, x, y, kind, horiz=False):
        self.x, self.y, self.kind, self.horiz = x, y, kind, horiz
        self.color = random.choice(CAR_COLORS)
        self.occupant = None

    def eyes_pos(self):
        if self.kind == "car":
            return (self.x - 5, self.y - 14) if not self.horiz else (self.x + 9, self.y)
        return self.x, self.y - 4


class World:
    def __init__(self, idx):
        self.idx = idx
        self.th = WORLDS[idx]
        self.solids, self.parks, self.spots, self.trees = [], [], [], []
        self.grid = {}
        for bx in range(NB):
            for by in range(NB):
                blk = pygame.Rect(bx * BLOCK + ROAD, by * BLOCK + ROAD, BLOCK - ROAD, BLOCK - ROAD)
                if (bx, by) == (MID, MID):
                    self.parks.append(blk)
                    self.plaza = blk
                elif random.random() < self.th["park_chance"]:
                    self.make_park(blk)
                else:
                    self.make_solids(blk, bx, by)
        self.make_road_spots()
        self.spots = [s for s in self.spots if math.hypot(s.x - HQ[0], s.y - HQ[1]) > 260]
        self.build_nav()
        self.render()

    # ---------- κατασκευή
    def make_park(self, blk):
        self.parks.append(blk)
        for _ in range(random.randint(3, 5)):
            self.spots.append(Spot(*self.park_point(blk), self.th["park_spot"]))
        for _ in range(random.randint(3, 5)):
            x, y = self.park_point(blk)
            self.trees.append((x, y, random.randint(28, 40)))

    @staticmethod
    def park_point(blk):
        while True:
            x = random.randint(blk.x + 35, blk.right - 35)
            y = random.randint(blk.y + 35, blk.bottom - 35)
            if abs(x - blk.centerx) > 38 and abs(y - blk.centery) > 38:
                return x, y

    def make_solids(self, blk, bx, by):
        inner = blk.inflate(-2 * SIDEWALK, -2 * SIDEWALK)
        mode = random.choice([1, 2, 2, 4, 4])
        R = pygame.Rect
        side = self.th["side_spots"]
        if mode == 1:
            rects = [inner]
        elif mode == 2:
            if random.random() < 0.5:
                w = (inner.w - ALLEY) // 2
                rects = [R(inner.x, inner.y, w, inner.h), R(inner.x + w + ALLEY, inner.y, inner.w - w - ALLEY, inner.h)]
                self.spots.append(Spot(inner.x + w + ALLEY // 2, inner.centery + random.randint(-60, 60), random.choice(side)))
            else:
                h = (inner.h - ALLEY) // 2
                rects = [R(inner.x, inner.y, inner.w, h), R(inner.x, inner.y + h + ALLEY, inner.w, inner.h - h - ALLEY)]
                self.spots.append(Spot(inner.centerx + random.randint(-60, 60), inner.y + h + ALLEY // 2, random.choice(side)))
        else:
            w, h = (inner.w - ALLEY) // 2, (inner.h - ALLEY) // 2
            rects = [R(inner.x, inner.y, w, h), R(inner.x + w + ALLEY, inner.y, inner.w - w - ALLEY, h),
                     R(inner.x, inner.y + h + ALLEY, w, inner.h - h - ALLEY),
                     R(inner.x + w + ALLEY, inner.y + h + ALLEY, inner.w - w - ALLEY, inner.h - h - ALLEY)]
            self.spots.append(Spot(inner.centerx, inner.centery, random.choice(side)))
        for r in rects:
            self.solids.append(Solid(r))
            self.grid.setdefault((bx, by), []).append(r)
        for _ in range(random.randint(1, 2)):
            s = random.choice("nsew")
            if s == "n":
                x, y = random.randint(blk.x + 25, blk.right - 25), blk.y + 15
            elif s == "s":
                x, y = random.randint(blk.x + 25, blk.right - 25), blk.bottom - 15
            elif s == "w":
                x, y = blk.x + 15, random.randint(blk.y + 25, blk.bottom - 25)
            else:
                x, y = blk.right - 15, random.randint(blk.y + 25, blk.bottom - 25)
            self.spots.append(Spot(x, y, random.choice(side)))

    def make_road_spots(self):
        kind = self.th["road_spot"]
        for i in range(NB + 1):
            for j in range(NB):
                lo, hi = j * BLOCK + ROAD + 45, (j + 1) * BLOCK - 45
                if random.random() < 0.45:
                    self.spots.append(Spot(i * BLOCK + random.choice((22, ROAD - 22)), random.randint(lo, hi), kind, False))
                if random.random() < 0.45:
                    self.spots.append(Spot(random.randint(lo, hi), i * BLOCK + random.choice((22, ROAD - 22)), kind, True))

    # ---------- συγκρούσεις
    def nearby(self, x, y):
        bx, by = int(x // BLOCK), int(y // BLOCK)
        for gx in (bx - 1, bx, bx + 1):
            for gy in (by - 1, by, by + 1):
                yield from self.grid.get((gx, gy), ())

    def blocked(self, x, y, r):
        if x < r or y < r or x > WORLD_W - r or y > WORLD_H - r:
            return True
        for rc in self.nearby(x, y):
            if rc.left - r < x < rc.right + r and rc.top - r < y < rc.bottom + r:
                return True
        return False

    def los(self, x1, y1, x2, y2, r=0):
        b0, b1 = int(min(x1, x2) // BLOCK) - 1, int(max(x1, x2) // BLOCK) + 1
        c0, c1 = int(min(y1, y2) // BLOCK) - 1, int(max(y1, y2) // BLOCK) + 1
        for gx in range(b0, b1 + 1):
            for gy in range(c0, c1 + 1):
                for rc in self.grid.get((gx, gy), ()):
                    if rc.inflate(2 * r, 2 * r).clipline(x1, y1, x2, y2):
                        return False
        return True

    def build_nav(self):
        self.gw = WORLD_W // NAV + 1
        self.bad = set()
        for b in self.solids:
            r = b.rect.inflate(24, 24)
            for cx in range(r.left // NAV, r.right // NAV + 1):
                for cy in range(r.top // NAV, r.bottom // NAV + 1):
                    if r.collidepoint(cx * NAV + NAV / 2, cy * NAV + NAV / 2):
                        self.bad.add((cx, cy))

    DIRS = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.41), (1, -1, 1.41), (-1, 1, 1.41), (-1, -1, 1.41)]

    def find_path(self, sx, sy, tx, ty):
        s, g = (int(sx // NAV), int(sy // NAV)), (int(tx // NAV), int(ty // NAV))
        if s == g:
            return [(tx, ty)]
        h = lambda c: math.hypot(c[0] - g[0], c[1] - g[1])
        openq, cost, prev = [(h(s), 0, s)], {s: 0}, {s: None}
        n_iter = 0
        while openq and n_iter < 3000:
            n_iter += 1
            _, gc, c = heapq.heappop(openq)
            if c == g:
                break
            if gc > cost[c]:
                continue
            for dx, dy, k in self.DIRS:
                n = (c[0] + dx, c[1] + dy)
                if not (0 <= n[0] < self.gw and 0 <= n[1] < self.gw):
                    continue
                if n in self.bad and n != g:
                    continue
                if dx and dy and ((c[0] + dx, c[1]) in self.bad or (c[0], c[1] + dy) in self.bad):
                    continue
                ng = gc + k
                if ng < cost.get(n, 1e9):
                    cost[n], prev[n] = ng, c
                    heapq.heappush(openq, (ng + h(n), ng, n))
        if g not in prev:
            return [(tx, ty)]
        path, c = [], g
        while c != s:
            path.append((c[0] * NAV + NAV / 2, c[1] * NAV + NAV / 2))
            c = prev[c]
        path.reverse()
        path[-1] = (tx, ty)
        return path

    def random_street_point(self):
        i = random.randint(0, NB)
        along = random.randint(60, WORLD_W - 60)
        across = i * BLOCK + ROAD // 2
        return (across, along) if random.random() < 0.5 else (along, across)

    # ---------- σχέδιο (μία φορά)
    def render(self):
        th = self.th
        bg = pygame.Surface((WORLD_W, WORLD_H))
        bg.fill(th["road"])
        key = th["key"]
        rnd = random.Random(self.idx * 99)
        # υφή δρόμων
        for _ in range(2500):
            x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
            pygame.draw.circle(bg, shade(th["road"], rnd.choice((0.9, 1.08))), (x, y), rnd.randint(1, 3))
        if key == "city":
            for i in range(NB + 1):
                c = i * BLOCK + ROAD // 2
                for t in range(0, WORLD_W, 50):
                    if (t % BLOCK) >= ROAD and ((t + 25) % BLOCK) >= ROAD:
                        pygame.draw.line(bg, (220, 220, 200), (c, t), (c, t + 25), 3)
                        pygame.draw.line(bg, (220, 220, 200), (t, c), (t + 25, c), 3)
            for i in range(NB + 1):
                for j in range(NB + 1):
                    X, Y = i * BLOCK, j * BLOCK
                    for k in range(X + 12, X + ROAD - 8, 14):
                        pygame.draw.rect(bg, (230, 230, 230), (k, Y - 24, 7, 18))
                        pygame.draw.rect(bg, (230, 230, 230), (k, Y + ROAD + 6, 7, 18))
                    for k in range(Y + 12, Y + ROAD - 8, 14):
                        pygame.draw.rect(bg, (230, 230, 230), (X - 24, k, 18, 7))
                        pygame.draw.rect(bg, (230, 230, 230), (X + ROAD + 6, k, 18, 7))
        elif key == "haunted":
            for x in range(0, WORLD_W, 26):
                for y in range(0, WORLD_H, 20):
                    if (x % BLOCK < ROAD) or (y % BLOCK < ROAD):
                        pygame.draw.rect(bg, shade(th["road"], 0.8), (x + (y // 20 % 2) * 13, y, 26, 20), 1)
        # τετράγωνα
        for bx in range(NB):
            for by in range(NB):
                blk = pygame.Rect(bx * BLOCK + ROAD, by * BLOCK + ROAD, BLOCK - ROAD, BLOCK - ROAD)
                pygame.draw.rect(bg, th["ground"], blk)
                pygame.draw.rect(bg, shade(th["ground"], 0.8), blk, 3)
                for _ in range(25):
                    x, y = rnd.randint(blk.x, blk.right), rnd.randint(blk.y, blk.bottom)
                    pygame.draw.circle(bg, shade(th["ground"], rnd.choice((0.92, 1.06))), (x, y), rnd.randint(2, 4))
        for p in self.parks:
            self.draw_park(bg, p, rnd)
        for b in self.solids:
            pygame.draw.rect(bg, shade(th["ground"], 0.78), b.rect.move(8, 8))
        for b in self.solids:
            SOLID_DRAW[th["solid"]](bg, b, rnd)
        for x, y, r in self.trees:
            if th["tree"] not in ("dead",):
                pygame.draw.circle(bg, (90, 60, 30), (x, y), 8)
        for s in self.spots:
            draw_spot(bg, s)
        self.bg = bg.convert() if pygame.display.get_surface() else bg

        size = 150
        k = size / WORLD_W
        mm = pygame.Surface((size, size))
        mm.fill(shade(th["road"], 0.9))
        for bx in range(NB):
            for by in range(NB):
                pygame.draw.rect(mm, shade(th["ground"], 0.85), (int((bx * BLOCK + ROAD) * k), int((by * BLOCK + ROAD) * k),
                                                              int((BLOCK - ROAD) * k) + 1, int((BLOCK - ROAD) * k) + 1))
        for p in self.parks:
            pygame.draw.rect(mm, shade(th["park"], 0.85), (int(p.x * k), int(p.y * k), int(p.w * k) + 1, int(p.h * k) + 1))
        for b in self.solids:
            r = b.rect
            pygame.draw.rect(mm, (45, 45, 50), (int(r.x * k), int(r.y * k), int(r.w * k) + 1, int(r.h * k) + 1))
        self.minimap = mm

    def draw_park(self, bg, p, rnd):
        th, key = self.th, self.th["key"]
        g = p.inflate(-20, -20)
        pygame.draw.rect(bg, th["park"], g, border_radius=10)
        path = shade(th["park"], 1.15) if key in ("beach", "snow") else (205, 185, 140)
        if key == "haunted":
            path = (90, 85, 80)
        pygame.draw.rect(bg, path, (g.x, g.centery - 12, g.w, 24))
        pygame.draw.rect(bg, path, (g.centerx - 12, g.y, 24, g.h))
        pygame.draw.circle(bg, path, g.center, 36)
        c = g.center
        if key == "city":
            pygame.draw.circle(bg, (120, 170, 220), c, 22)
            pygame.draw.circle(bg, (180, 210, 240), c, 10)
        elif key == "forest":
            pygame.draw.circle(bg, (90, 150, 200), c, 24)
            for _ in range(30):
                x, y = rnd.randint(g.x + 5, g.right - 5), rnd.randint(g.y + 5, g.bottom - 5)
                pygame.draw.circle(bg, rnd.choice([(250, 220, 60), (240, 120, 160), (255, 255, 255)]), (x, y), 3)
        elif key == "beach":
            pygame.draw.circle(bg, (60, 170, 210), c, 30)
            pygame.draw.circle(bg, (120, 210, 235), c, 20)
            for _ in range(6):
                x, y = rnd.randint(g.x + 10, g.right - 40), rnd.randint(g.y + 10, g.bottom - 20)
                pygame.draw.rect(bg, rnd.choice([(230, 70, 70), (70, 130, 230), (250, 200, 50)]), (x, y, 30, 14), border_radius=3)
        elif key == "snow":
            pygame.draw.circle(bg, (170, 215, 240), c, 30)
            pygame.draw.line(bg, WHITE, (c[0] - 15, c[1] - 8), (c[0] + 10, c[1] + 6), 2)
        elif key == "haunted":
            pygame.draw.rect(bg, (110, 105, 110), (c[0] - 12, c[1] - 20, 24, 34), border_top_left_radius=12,
                             border_top_right_radius=12)
            pygame.draw.line(bg, (60, 60, 60), (c[0], c[1] - 14), (c[0], c[1]), 3)
            pygame.draw.line(bg, (60, 60, 60), (c[0] - 6, c[1] - 9), (c[0] + 6, c[1] - 9), 3)
        if p is not getattr(self, "plaza", None) or True:
            for _ in range(30):
                x, y = rnd.randint(g.x + 5, g.right - 5), rnd.randint(g.y + 5, g.bottom - 5)
                pygame.draw.line(bg, shade(th["park"], 0.85), (x, y), (x + 3, y - 6), 2)


# ---------------------------------------------------------------- σχέδια για εμπόδια
def _face(r, h=42):
    face_h = min(h, r.h // 3)
    return pygame.Rect(r.x, r.y, r.w, r.h - face_h), pygame.Rect(r.x, r.bottom - face_h, r.w, face_h)


def solid_building(bg, b, rnd):
    r, base = b.rect, b.color
    roof, face = _face(r)
    pygame.draw.rect(bg, base, roof)
    pygame.draw.rect(bg, shade(base, 1.18), roof, 5)
    for _ in range(rnd.randint(1, 3)):
        w, h = rnd.randint(16, 30), rnd.randint(12, 22)
        x = rnd.randint(roof.x + 10, max(roof.x + 11, roof.right - w - 10))
        y = rnd.randint(roof.y + 10, max(roof.y + 11, roof.bottom - h - 10))
        pygame.draw.rect(bg, (150, 150, 155), (x, y, w, h))
        pygame.draw.rect(bg, (90, 90, 95), (x, y, w, h), 2)
    pygame.draw.rect(bg, shade(base, 0.6), face)
    for wx in range(r.x + 10, r.right - 18, 22):
        col = (250, 230, 140) if rnd.random() < 0.3 else (170, 205, 235)
        pygame.draw.rect(bg, col, (wx, face.y + 8, 12, 12))
        pygame.draw.rect(bg, (40, 40, 40), (wx, face.y + 8, 12, 12), 1)
    pygame.draw.rect(bg, (100, 65, 35), (r.centerx - 8, r.bottom - 20, 16, 20))
    pygame.draw.rect(bg, (30, 30, 30), r, 2)


def solid_grove(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (30, 80, 35), r, border_radius=18)
    for x in range(r.x + 18, r.right - 10, 34):
        for y in range(r.y + 18, r.bottom - 10, 34):
            cx, cy = x + rnd.randint(-6, 6), y + rnd.randint(-6, 6)
            rr = rnd.randint(20, 27)
            pygame.draw.circle(bg, rnd.choice([(35, 95, 40), (45, 110, 45), (30, 85, 38)]), (cx, cy), rr)
            pygame.draw.circle(bg, (60, 130, 55), (cx - 6, cy - 7), rr // 3)
    pygame.draw.rect(bg, (20, 55, 25), r, 3, border_radius=18)


def solid_hut(bg, b, rnd):
    r = b.rect
    roof, face = _face(r, 36)
    pygame.draw.rect(bg, (220, 185, 90), roof)
    for y in range(roof.y + 4, roof.bottom, 9):
        pygame.draw.line(bg, (185, 150, 60), (roof.x, y), (roof.right, y + 3), 3)
    pygame.draw.rect(bg, (160, 110, 60), face)
    for x in range(face.x, face.right, 12):
        pygame.draw.line(bg, (125, 85, 45), (x, face.y), (x, face.bottom), 2)
    for wx in range(r.x + 16, r.right - 30, 46):
        pygame.draw.rect(bg, (100, 190, 230), (wx, face.y + 8, 16, 12))
    pygame.draw.rect(bg, (90, 60, 30), (r.centerx - 9, r.bottom - 22, 18, 22))
    pygame.draw.rect(bg, (90, 60, 25), r, 2)


def solid_cabin(bg, b, rnd):
    r = b.rect
    roof, face = _face(r, 40)
    pygame.draw.rect(bg, (245, 248, 255), roof, border_radius=6)
    pygame.draw.rect(bg, (205, 220, 240), roof, 6, border_radius=6)
    pygame.draw.rect(bg, (120, 80, 50), face)
    for y in range(face.y + 4, face.bottom, 8):
        pygame.draw.line(bg, (90, 60, 35), (face.x, y), (face.right, y), 2)
    for x in range(face.x + 4, face.right - 4, 10):
        pygame.draw.polygon(bg, (210, 235, 255), [(x, face.y), (x + 6, face.y), (x + 3, face.y + rnd.randint(6, 12))])
    for wx in range(r.x + 16, r.right - 30, 40):
        pygame.draw.rect(bg, (255, 220, 120), (wx, face.y + 14, 14, 12))
    pygame.draw.rect(bg, (70, 45, 25), (r.centerx - 9, r.bottom - 22, 18, 22))
    pygame.draw.rect(bg, (70, 60, 60), r, 2)


def solid_crypt(bg, b, rnd):
    r = b.rect
    roof, face = _face(r, 42)
    pygame.draw.rect(bg, (78, 72, 92), roof)
    for _ in range(4):
        x, y = rnd.randint(roof.x + 5, roof.right - 5), rnd.randint(roof.y + 5, roof.bottom - 5)
        pygame.draw.line(bg, (50, 45, 60), (x, y), (x + rnd.randint(-25, 25), y + rnd.randint(-25, 25)), 2)
    pygame.draw.rect(bg, (100, 95, 115), roof, 5)
    pygame.draw.rect(bg, (45, 40, 55), face)
    for wx in range(r.x + 12, r.right - 22, 30):
        pygame.draw.rect(bg, (190, 120, 255) if rnd.random() < 0.5 else (60, 40, 90), (wx, face.y + 10, 12, 18),
                         border_top_left_radius=6, border_top_right_radius=6)
    pygame.draw.rect(bg, (30, 20, 30), (r.centerx - 10, r.bottom - 26, 20, 26), border_top_left_radius=10,
                     border_top_right_radius=10)
    pygame.draw.line(bg, (200, 200, 210), (r.x, r.y), (r.x + 22, r.y + 22), 1)
    pygame.draw.line(bg, (200, 200, 210), (r.x + 22, r.y), (r.x, r.y + 22), 1)
    pygame.draw.rect(bg, (25, 20, 30), r, 2)


SOLID_DRAW = {"building": solid_building, "grove": solid_grove, "hut": solid_hut, "cabin": solid_cabin,
              "crypt": solid_crypt}


# ---------------------------------------------------------------- σχέδια για κρυψώνες
def _rot_blit(bg, img, x, y, horiz):
    if horiz:
        img = pygame.transform.rotate(img, 90)
    bg.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))


def draw_spot(bg, s):
    x, y, k = s.x, s.y, s.kind
    if k == "bush":
        for dx, dy in ((-12, 4), (12, 4), (0, -8)):
            pygame.draw.circle(bg, (40, 130, 50), (x + dx, y + dy), 20)
        pygame.draw.circle(bg, (55, 155, 60), (x, y), 15)
    elif k == "bin":
        pygame.draw.rect(bg, (40, 90, 55), (x - 11, y - 12, 22, 24), border_radius=4)
        pygame.draw.rect(bg, (60, 120, 75), (x - 11, y - 12, 22, 8), border_radius=4)
        pygame.draw.rect(bg, (20, 50, 30), (x - 11, y - 12, 22, 24), 2, border_radius=4)
    elif k == "mushroom":
        pygame.draw.rect(bg, (240, 230, 210), (x - 6, y - 4, 12, 18), border_radius=4)
        pygame.draw.ellipse(bg, (220, 50, 50), (x - 22, y - 20, 44, 26))
        for dx, dy in ((-10, -12), (6, -14), (0, -6), (13, -8)):
            pygame.draw.circle(bg, WHITE, (x + dx, y + dy), 3)
    elif k == "sandcastle":
        c = (215, 180, 110)
        pygame.draw.rect(bg, c, (x - 20, y - 8, 40, 20))
        for dx in (-20, 6):
            pygame.draw.rect(bg, c, (x + dx, y - 22, 14, 16))
            for i in range(3):
                pygame.draw.rect(bg, c, (x + dx + i * 5, y - 26, 4, 4))
        pygame.draw.line(bg, (90, 60, 30), (x + 13, y - 26), (x + 13, y - 38), 2)
        pygame.draw.polygon(bg, (230, 50, 50), [(x + 13, y - 38), (x + 22, y - 35), (x + 13, y - 32)])
    elif k == "umbrella":
        pygame.draw.line(bg, (90, 60, 30), (x, y), (x, y + 14), 3)
        cols = [(230, 60, 60), WHITE]
        for i in range(8):
            a1, a2 = i * math.pi / 4, (i + 1) * math.pi / 4
            pygame.draw.polygon(bg, cols[i % 2], [(x, y), (x + math.cos(a1) * 26, y + math.sin(a1) * 26),
                                                  (x + math.cos(a2) * 26, y + math.sin(a2) * 26)])
        pygame.draw.circle(bg, (90, 60, 30), (x, y), 3)
    elif k == "snowman":
        pygame.draw.circle(bg, WHITE, (x, y + 4), 15)
        pygame.draw.circle(bg, WHITE, (x, y - 16), 10)
        pygame.draw.circle(bg, (180, 195, 215), (x, y + 4), 15, 2)
        pygame.draw.circle(bg, (20, 20, 20), (x - 3, y - 18), 2)
        pygame.draw.circle(bg, (20, 20, 20), (x + 3, y - 18), 2)
        pygame.draw.polygon(bg, (240, 130, 30), [(x, y - 15), (x + 10, y - 13), (x, y - 12)])
        pygame.draw.rect(bg, (30, 30, 30), (x - 8, y - 32, 16, 8))
        pygame.draw.line(bg, (210, 50, 50), (x - 9, y - 8), (x + 9, y - 8), 4)
    elif k == "snowpile":
        for dx, dy, r in ((-12, 4, 16), (12, 4, 15), (0, -8, 17)):
            pygame.draw.circle(bg, (200, 215, 235), (x + dx, y + dy + 2), r)
            pygame.draw.circle(bg, WHITE, (x + dx, y + dy), r)
    elif k == "pumpkin":
        for dx in (-9, 9, 0):
            pygame.draw.ellipse(bg, (240, 130, 20), (x - 12 + dx, y - 14, 24, 28))
        pygame.draw.ellipse(bg, (200, 100, 10), (x - 12, y - 14, 24, 28), 2)
        pygame.draw.rect(bg, (60, 100, 30), (x - 3, y - 20, 6, 8))
        pygame.draw.polygon(bg, (60, 30, 0), [(x - 10, y + 2), (x + 10, y + 2), (x, y + 9)])
    elif k == "tomb":
        pygame.draw.rect(bg, (120, 120, 130), (x - 14, y - 20, 28, 34), border_top_left_radius=14, border_top_right_radius=14)
        pygame.draw.rect(bg, (80, 80, 90), (x - 14, y - 20, 28, 34), 2, border_top_left_radius=14, border_top_right_radius=14)
        pygame.draw.line(bg, (70, 70, 80), (x - 7, y - 6), (x + 7, y - 6), 2)
        pygame.draw.line(bg, (70, 70, 80), (x - 7, y), (x + 5, y), 2)
        pygame.draw.ellipse(bg, (60, 50, 40), (x - 18, y + 10, 36, 10))
    elif k == "car":
        w, h = (60, 32) if s.horiz else (32, 60)
        body = pygame.Rect(0, 0, w, h)
        body.center = (x, y)
        wheels = ((body.left + 10, body.top), (body.right - 10, body.top), (body.left + 10, body.bottom),
                  (body.right - 10, body.bottom)) if s.horiz else \
            ((body.left, body.top + 10), (body.right, body.top + 10), (body.left, body.bottom - 10),
             (body.right, body.bottom - 10))
        for cx, cy in wheels:
            pygame.draw.rect(bg, (20, 20, 20), (cx - 6, cy - 4, 12, 8) if s.horiz else (cx - 4, cy - 6, 8, 12))
        pygame.draw.rect(bg, s.color, body, border_radius=9)
        lighter = tuple(min(255, c + 40) for c in s.color)
        glass = (60, 80, 120)
        if s.horiz:
            pygame.draw.rect(bg, lighter, (x - 14, y - 12, 28, 24), border_radius=4)
            pygame.draw.rect(bg, glass, (x + 14, y - 12, 9, 24), border_radius=3)
            pygame.draw.rect(bg, glass, (x - 22, y - 11, 7, 22), border_radius=3)
        else:
            pygame.draw.rect(bg, lighter, (x - 12, y - 10, 24, 26), border_radius=4)
            pygame.draw.rect(bg, glass, (x - 12, y - 21, 24, 10), border_radius=3)
            pygame.draw.rect(bg, glass, (x - 11, y + 16, 22, 7), border_radius=3)
        pygame.draw.rect(bg, (25, 25, 25), body, 2, border_radius=9)
    else:
        img = pygame.Surface((44, 70), pygame.SRCALPHA)
        if k == "log":
            pygame.draw.rect(img, (125, 85, 45), (8, 4, 28, 62), border_radius=10)
            for yy in range(12, 60, 10):
                pygame.draw.line(img, (95, 60, 30), (10, yy), (34, yy + 2), 2)
            pygame.draw.ellipse(img, (210, 170, 110), (8, 2, 28, 14))
            pygame.draw.ellipse(img, (150, 110, 60), (14, 5, 16, 8), 2)
        elif k == "boat":
            pygame.draw.polygon(img, (200, 70, 50), [(22, 2), (38, 22), (38, 64), (6, 64), (6, 22)])
            pygame.draw.polygon(img, (240, 240, 240), [(22, 8), (33, 24), (33, 58), (11, 58), (11, 24)])
            pygame.draw.line(img, (140, 90, 40), (11, 36), (33, 36), 4)
            pygame.draw.line(img, (140, 90, 40), (11, 48), (33, 48), 4)
        elif k == "sled":
            pygame.draw.line(img, (80, 80, 90), (8, 4), (8, 66), 3)
            pygame.draw.line(img, (80, 80, 90), (36, 4), (36, 66), 3)
            pygame.draw.rect(img, (200, 50, 50), (10, 12, 24, 48), border_radius=4)
            for yy in range(18, 56, 10):
                pygame.draw.line(img, (150, 30, 30), (10, yy), (34, yy), 2)
        elif k == "coffin":
            pts = [(14, 2), (30, 2), (40, 18), (32, 68), (12, 68), (4, 18)]
            pygame.draw.polygon(img, (90, 55, 40), pts)
            pygame.draw.polygon(img, (50, 30, 20), pts, 3)
            pygame.draw.line(img, (210, 190, 150), (22, 18), (22, 44), 3)
            pygame.draw.line(img, (210, 190, 150), (14, 26), (30, 26), 3)
        _rot_blit(bg, img, x, y, s.horiz)


def draw_tree(surf, kind, sx, sy, r):
    if kind == "round":
        pygame.draw.circle(surf, (30, 95, 40), (sx, sy - 8), r)
        pygame.draw.circle(surf, (45, 120, 50), (sx - 9, sy - 16), r // 2)
    elif kind == "round_dark":
        pygame.draw.circle(surf, (25, 80, 32), (sx, sy - 8), r + 4)
        pygame.draw.circle(surf, (40, 105, 45), (sx - 9, sy - 16), r // 2)
    elif kind == "palm":
        pygame.draw.line(surf, (140, 100, 55), (sx, sy), (sx + 6, sy - 40), 6)
        for a in range(0, 360, 60):
            ra = math.radians(a)
            ex, ey = sx + 6 + math.cos(ra) * (r + 6), sy - 40 + math.sin(ra) * (r * 0.6)
            pygame.draw.line(surf, (40, 140, 60), (sx + 6, sy - 40), (ex, ey), 8)
        pygame.draw.circle(surf, (110, 70, 30), (sx + 6, sy - 38), 5)
    elif kind == "pine":
        for i, w in enumerate((r, r * 0.75, r * 0.5)):
            yb = sy - i * 18
            pygame.draw.polygon(surf, (30, 90, 55), [(sx - w, yb), (sx + w, yb), (sx, yb - 30)])
            pygame.draw.polygon(surf, WHITE, [(sx - w * 0.35, yb - 20), (sx + w * 0.35, yb - 20), (sx, yb - 30)])
    elif kind == "dead":
        c = (60, 45, 40)
        pygame.draw.line(surf, c, (sx, sy + 8), (sx, sy - 40), 6)
        for dx, dy, ex, ey in ((0, -20, -22, -42), (0, -28, 20, -50), (0, -36, -8, -60), (-12, -32, -26, -36)):
            pygame.draw.line(surf, c, (sx + dx, sy + dy), (sx + ex, sy + ey), 3)


# ---------------------------------------------------------------- κινούμενα
class Mover:
    path = None
    path_t = 0.0
    fly = False

    def steer(self, world, tx, ty, speed, dt):
        if math.hypot(tx - self.x, ty - self.y) < 3:
            return False
        if self.fly or world.los(self.x, self.y, tx, ty, self.r * 0.8):
            self.path = None
            dest = (tx, ty)
        else:
            self.path_t -= dt
            if self.path is None or self.path_t <= 0:
                self.path = world.find_path(self.x, self.y, tx, ty)
                self.path_t = 0.5 + random.random() * 0.4
            while len(self.path) > 1 and math.hypot(self.path[0][0] - self.x, self.path[0][1] - self.y) < 22:
                self.path.pop(0)
            dest = self.path[0] if self.path else (tx, ty)
        dx, dy = dest[0] - self.x, dest[1] - self.y
        l = math.hypot(dx, dy)
        if l < 0.5:
            return False
        step = min(speed, l)
        nx, ny = self.x + dx / l * step, self.y + dy / l * step
        if self.fly:
            self.x = min(max(nx, 20), WORLD_W - 20)
            self.y = min(max(ny, 20), WORLD_H - 20)
        elif not world.blocked(nx, ny, self.r):
            self.x, self.y = nx, ny
        elif not world.blocked(nx, self.y, self.r):
            self.x = nx
        elif not world.blocked(self.x, ny, self.r):
            self.y = ny
        else:
            self.path_t = 0
        self.dir = math.atan2(dy, dx)
        return True


class Human(Mover):
    def __init__(self, x, y, is_player=False, role="escort"):
        self.x, self.y, self.r = x, y, 16
        self.is_player = is_player
        self.maxhp = PLAYER_MAX_HP if is_player else ALLY_MAX_HP
        self.hp = self.maxhp
        self.dir, self.cool, self.walk = 0.0, 0.0, 0.0
        self.moving = False
        self.invuln = 1.5
        self.alive, self.respawn = True, 0.0
        self.shirt = (40, 110, 220) if is_player else random.choice(SHIRTS)
        self.helmet = (60, 90, 60) if is_player else random.choice(HELMETS)
        self.name = "Εσύ" if is_player else random.choice(NAMES)
        self.role = role
        self.slot = random.random() * 6.283
        self.goal, self.goal_t = None, 0.0
        self.shield_t = self.speed_t = self.magnet_t = 0.0

    def protected(self):
        return self.invuln > 0 or self.shield_t > 0

    def gun_tip(self):
        return self.x + math.cos(self.dir) * 34, self.y - 8 + math.sin(self.dir) * 34

    def draw(self, surf, cam, t):
        sx, sy = int(self.x - cam[0]), int(self.y - cam[1])
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        if self.speed_t > 0 and self.moving:
            for i in range(3):
                pygame.draw.circle(surf, (255, 255, 160), (sx - int(math.cos(self.dir) * (14 + i * 9)),
                                                           sy + 18 - int(math.sin(self.dir) * (14 + i * 9))), 4 - i)
        draw_hero(surf, sx, sy, self.dir, self.walk if self.moving else None, self.shirt, self.helmet)
        if self.shield_t > 0:
            pygame.draw.circle(surf, (120, 200, 255), (sx, sy - 6), 34, 3)
            pygame.draw.circle(surf, (200, 240, 255), (sx, sy - 6), 30 + int(math.sin(t * 8) * 2), 1)
        if self.is_player:
            bob = int(math.sin(t * 5) * 3)
            pts = [(sx - 9, sy - 54 + bob), (sx + 9, sy - 54 + bob), (sx, sy - 43 + bob)]
            pygame.draw.polygon(surf, (255, 220, 40), pts)
            pygame.draw.polygon(surf, (0, 0, 0), pts, 1)
        elif self.hp < self.maxhp:
            pygame.draw.rect(surf, (60, 0, 0), (sx - 15, sy - 46, 30, 4))
            pygame.draw.rect(surf, (80, 220, 90), (sx - 15, sy - 46, int(30 * self.hp / self.maxhp), 4))


class Dog(Mover):
    def __init__(self, x, y):
        self.x, self.y, self.r = x, y, 12
        self.dir, self.walk = 0.0, 0.0
        self.moving, self.barking = False, 0.0
        self.target = None        # κρυψώνα με τέρας που βρήκε
        self.bark_t = 0.0

    def draw(self, surf, cam, t):
        sx, sy = int(self.x - cam[0]), int(self.y - cam[1])
        f = 1 if math.cos(self.dir) >= 0 else -1
        draw_dog(surf, sx, sy, f, self.walk, self.moving, self.barking > 0)


class Monster(Mover):
    def __init__(self, spot, mtype, x=None, y=None):
        self.t = mtype
        self.boss = mtype["boss"]
        self.fly = mtype.get("fly", False)
        self.spot = spot
        if spot:
            self.x, self.y = spot.x, spot.y
            spot.occupant = self
            self.state = "hidden"
        else:
            self.x, self.y = x, y
            self.state = "chase"
        self.hp, self.r = mtype["hp"], mtype["r"]
        self.flash, self.lost, self.slow_t = 0.0, 0.0, 0.0
        self.wobble = random.random() * 6.28
        self.dir, self.face = 0.0, 1
        self.fled = self.boss
        self.shoot_t = random.uniform(1, 2.5)
        self.summon_t = 6.0

    def hit_center(self):
        return self.x, self.y - self.r * 0.5

    def draw(self, surf, cam, t):
        sx, sy = int(self.x - cam[0]), int(self.y - cam[1])
        draw_monster_type(surf, sx, sy, self.t, self.face, self.wobble, self.flash > 0)
        if self.slow_t > 0:
            pygame.draw.circle(surf, (150, 225, 255), (sx, sy - int(self.r * 0.5)), self.r + 6, 2)
            for i in range(3):
                a = t * 3 + i * 2.1
                pygame.draw.circle(surf, WHITE, (sx + int(math.cos(a) * self.r), sy - int(self.r * 0.5) + int(math.sin(a) * self.r)), 2)
        if self.hp < self.t["hp"] and not self.boss:
            w = self.r * 2
            top = sy - int(self.r * 2.6) - 10
            pygame.draw.rect(surf, (60, 0, 0), (sx - self.r, top, w, 5))
            pygame.draw.rect(surf, (230, 40, 40), (sx - self.r, top, int(w * self.hp / self.t["hp"]), 5))


class Bullet:
    def __init__(self, x, y, angle, owner, weapon):
        self.x, self.y, self.owner = x, y, owner
        self.vx = math.cos(angle) * BULLET_SPEED
        self.vy = math.sin(angle) * BULLET_SPEED
        self.life = 1.0
        self.dmg = weapon["dmg"]
        self.pierce = weapon.get("pierce", False)
        self.freeze = weapon.get("freeze", False)
        self.color = weapon["color"] if owner == "player" else (255, 170, 80)
        self.hit = set()

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        return self.life > 0 and 0 < self.x < WORLD_W and 0 < self.y < WORLD_H

    def draw(self, surf, cam):
        x, y = int(self.x - cam[0]), int(self.y - cam[1])
        if self.pierce:
            pygame.draw.line(surf, self.color, (x, y), (int(x - self.vx * 2), int(y - self.vy * 2)), 5)
            pygame.draw.line(surf, WHITE, (x, y), (int(x - self.vx * 2), int(y - self.vy * 2)), 2)
        else:
            pygame.draw.circle(surf, self.color, (x, y), 5 if self.owner == "player" else 4)
            if self.freeze:
                pygame.draw.circle(surf, WHITE, (x, y), 2)


class Shot:
    """Βολή τέρατος (φωτιά, πέτρα, ιστός, πάγος...)."""

    def __init__(self, x, y, angle, speed, dmg, color, ghost=False):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.dmg, self.color, self.ghost = dmg, color, ghost
        self.life = 3.0

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        return self.life > 0

    def draw(self, surf, cam, t):
        x, y = int(self.x - cam[0]), int(self.y - cam[1])
        pygame.draw.circle(surf, shade(self.color, 0.7), (x, y), 10)
        pygame.draw.circle(surf, self.color, (x, y), 7 + int(math.sin(t * 20) * 1))
        pygame.draw.circle(surf, WHITE, (x - 2, y - 2), 3)


class Coin:
    """Κύπελλο που πέφτει από τέρας και το μαζεύεις."""

    def __init__(self, x, y, delay=0.0):
        a, s = random.random() * 6.283, random.uniform(2, 5)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s
        self.t = 0.0
        self.delay = delay

    def draw(self, surf, cam, t):
        x, y = int(self.x - cam[0]), int(self.y - cam[1] + math.sin(t * 6 + self.x) * 3)
        draw_trophy(surf, x, y, 0.8)


POWER_KINDS = ["heart", "shield", "shoes", "magnet", "team"]
POWER_NAMES = {"heart": "Καρδιά!", "shield": "Ασπίδα!", "shoes": "Παπούτσια ταχύτητας!", "magnet": "Μαγνήτης!", "team": "Ήρθε η ομάδα!"}


def draw_power_icon(surf, kind, x, y, s=1.0):
    if kind == "heart":
        pygame.draw.circle(surf, (230, 40, 70), (int(x - 6 * s), int(y - 3 * s)), int(7 * s))
        pygame.draw.circle(surf, (230, 40, 70), (int(x + 6 * s), int(y - 3 * s)), int(7 * s))
        pygame.draw.polygon(surf, (230, 40, 70), [(x - 13 * s, y - 1 * s), (x + 13 * s, y - 1 * s), (x, y + 13 * s)])
        pygame.draw.circle(surf, (255, 180, 190), (int(x - 7 * s), int(y - 5 * s)), max(1, int(2 * s)))
    elif kind == "shield":
        pts = [(x - 12 * s, y - 12 * s), (x + 12 * s, y - 12 * s), (x + 12 * s, y), (x, y + 14 * s), (x - 12 * s, y)]
        pygame.draw.polygon(surf, (70, 140, 230), pts)
        pygame.draw.polygon(surf, (220, 235, 255), pts, max(1, int(2 * s)))
        pygame.draw.line(surf, (220, 235, 255), (x, y - 10 * s), (x, y + 10 * s), max(1, int(2 * s)))
    elif kind == "shoes":
        pygame.draw.rect(surf, (230, 60, 60), (x - 12 * s, y - 2 * s, 24 * s, 10 * s), border_radius=int(4 * s))
        pygame.draw.rect(surf, (230, 60, 60), (x - 12 * s, y - 12 * s, 10 * s, 12 * s), border_radius=int(3 * s))
        pygame.draw.rect(surf, WHITE, (x - 12 * s, y + 5 * s, 24 * s, 4 * s))
        pygame.draw.polygon(surf, (255, 230, 80), [(x - 14 * s, y - 10 * s), (x - 22 * s, y - 14 * s), (x - 20 * s, y - 6 * s)])
    elif kind == "team":
        draw_team_icon(surf, x, y, s)
    elif kind == "magnet":
        pygame.draw.arc(surf, (220, 50, 50), (x - 12 * s, y - 12 * s, 24 * s, 24 * s), 3.14, 6.28, max(2, int(7 * s)))
        pygame.draw.rect(surf, (220, 50, 50), (x - 12 * s, y - 1 * s, 7 * s, 8 * s))
        pygame.draw.rect(surf, (220, 50, 50), (x + 5 * s, y - 1 * s, 7 * s, 8 * s))
        pygame.draw.rect(surf, (230, 230, 230), (x - 12 * s, y + 7 * s, 7 * s, 5 * s))
        pygame.draw.rect(surf, (230, 230, 230), (x + 5 * s, y + 7 * s, 7 * s, 5 * s))


def draw_team_icon(surf, x, y, s=1.0):
    for dx, col in ((-8, (230, 120, 40)), (8, (60, 160, 90)), (0, (40, 110, 220))):
        yy = y + (2 if dx else -2) * s
        pygame.draw.rect(surf, col, (x + dx * s - 6 * s, yy, 12 * s, 12 * s), border_radius=int(4 * s))
        pygame.draw.circle(surf, SKIN, (int(x + dx * s), int(yy - 5 * s)), max(2, int(5 * s)))


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = x, y, kind

    def draw(self, surf, cam, t):
        x, y = int(self.x - cam[0]), int(self.y - cam[1] + math.sin(t * 4 + self.x) * 4)
        pygame.draw.circle(surf, (255, 255, 255), (x, y), 22)
        pygame.draw.circle(surf, (255, 220, 80), (x, y), 22, 3)
        draw_power_icon(surf, self.kind, x, y)


class Particle:
    def __init__(self, x, y, color, star=False, speed=5):
        a, s = random.random() * 6.28, random.uniform(1, speed)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s
        self.life = random.uniform(0.4, 0.9)
        self.color, self.star = color, star

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.life -= dt
        return self.life > 0

    def draw(self, surf, cam):
        x, y = int(self.x - cam[0]), int(self.y - cam[1])
        s = max(1, int(self.life * 8))
        if self.star:
            pygame.draw.polygon(surf, self.color, [(x, y - s), (x + s // 3, y), (x, y + s), (x - s // 3, y)])
            pygame.draw.polygon(surf, self.color, [(x - s, y), (x, y + s // 3), (x + s, y), (x, y - s // 3)])
        else:
            pygame.draw.circle(surf, self.color, (x, y), s)


class FloatText:
    def __init__(self, x, y, text, color, size=24):
        self.x, self.y, self.text, self.color, self.size = x, y, text, color, size
        self.life = 1.3

    def update(self, dt):
        self.y -= 0.8
        self.life -= dt
        return self.life > 0


def draw_trophy(surf, x, y, size=1.0):
    s = size
    dark = (200, 140, 20)
    pygame.draw.rect(surf, GOLD, (x - 9 * s, y - 12 * s, 18 * s, 14 * s), border_radius=int(4 * s))
    pygame.draw.circle(surf, GOLD, (int(x - 10 * s), int(y - 7 * s)), int(5 * s), max(1, int(2 * s)))
    pygame.draw.circle(surf, GOLD, (int(x + 10 * s), int(y - 7 * s)), int(5 * s), max(1, int(2 * s)))
    pygame.draw.rect(surf, dark, (x - 2 * s, y + 2 * s, 4 * s, 6 * s))
    pygame.draw.rect(surf, GOLD, (x - 7 * s, y + 8 * s, 14 * s, 4 * s))
    pygame.draw.circle(surf, (255, 250, 200), (int(x - 4 * s), int(y - 8 * s)), max(1, int(2 * s)))


def draw_heart(surf, x, y, s, full=True):
    c = (230, 40, 70) if full else (90, 70, 80)
    pygame.draw.circle(surf, c, (int(x - 5 * s), int(y - 2 * s)), int(6 * s))
    pygame.draw.circle(surf, c, (int(x + 5 * s), int(y - 2 * s)), int(6 * s))
    pygame.draw.polygon(surf, c, [(x - 11 * s, y), (x + 11 * s, y), (x, y + 11 * s)])


def draw_lock(surf, x, y, s=1.0):
    pygame.draw.arc(surf, (230, 230, 230), (x - 12 * s, y - 26 * s, 24 * s, 28 * s), 0, 3.14, max(2, int(5 * s)))
    pygame.draw.rect(surf, (230, 190, 60), (x - 16 * s, y - 12 * s, 32 * s, 26 * s), border_radius=int(5 * s))
    pygame.draw.circle(surf, (90, 60, 20), (int(x), int(y)), int(4 * s))


class Button:
    def __init__(self, rect, text, color, action, size=28):
        self.rect = pygame.Rect(rect)
        self.text, self.color, self.action, self.size = text, color, action, size

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (0, 0, 0), r.move(0, 5), border_radius=16)
        pygame.draw.rect(surf, self.color, r, border_radius=16)
        pygame.draw.rect(surf, shade(self.color, 1.3), r.inflate(-8, -8), 2, border_radius=13)
        if self.text:
            img = font(self.size).render(self.text, True, WHITE)
            surf.blit(img, (r.centerx - img.get_width() // 2, r.centery - img.get_height() // 2))


# ---------------------------------------------------------------- παιχνίδι
DEFAULT_SAVE = dict(trophies=5, best=5, unlocked=1, cleared=[], weapons=1, weapon=0, album={}, sound=True)


class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 1024)
        pygame.init()
        flags = pygame.SCALED | (pygame.FULLSCREEN if ANDROID else 0)
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except Exception:
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Monster Hunter - Κυνήγι Τεράτων")
        self.clock = pygame.time.Clock()
        self.load()
        self.loading_screen("Φόρτωση...")
        self.sfx = Sfx(self.save["sound"])
        self.state = "menu"
        self.hot = []
        self.t = 0.0
        self.touch_seen = ANDROID
        self.joy_id = self.joy_origin = self.joy_pos = None
        self.fire_ids = set()
        self.mouse_fire = False
        self.album_back = "menu"
        self.album_cache = None
        self.banner = None
        self.ui_particles = []
        self.world = None
        self.dark_mask = None
        self.save_t = 0.0
        self.clear_info = None

    # ------------------------------------------------------------ αποθήκευση
    def load(self):
        self.save = json.loads(json.dumps(DEFAULT_SAVE))
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            for k in DEFAULT_SAVE:
                if k in data:
                    self.save[k] = data[k]
        except Exception:
            pass

    def save_game(self):
        try:
            tmp = SAVE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.save, f, ensure_ascii=False)
            os.replace(tmp, SAVE_FILE)
        except Exception as e:
            print("Δεν αποθηκεύτηκε:", e)

    @property
    def trophies(self):
        return self.save["trophies"]

    def add_trophies(self, n):
        self.save["trophies"] = max(0, self.save["trophies"] + n)
        self.save["best"] = max(self.save["best"], self.save["trophies"])

    # ------------------------------------------------------------ κόσμος
    def loading_screen(self, text):
        self.screen.fill((30, 40, 80))
        img = font(40).render(text, True, WHITE)
        self.screen.blit(img, (W // 2 - img.get_width() // 2, H // 2 - 30))
        pygame.display.flip()
        pygame.event.pump()

    def start_world(self, idx):
        th = WORLDS[idx]
        self.loading_screen(f"Πάμε στον κόσμο: {th['name']}!")
        random.seed()
        self.widx = idx
        self.world = World(idx)
        self.player = Human(*HQ, is_player=True)
        self.dog = Dog(HQ[0] + 40, HQ[1] + 25)
        self.allies = []
        self.humans = [self.player]
        self.help_t = self.help_cd = 0.0
        self.monsters, self.bullets, self.shots = [], [], []
        self.coins, self.powerups, self.particles, self.texts = [], [], [], []
        self.lives = LIVES
        self.progress = 0
        self.boss, self.boss_spawned, self.boss_dead_t = None, False, 0.0
        self.dead_timer = self.shake = self.time = 0.0
        self.power_t = 3.0
        for _ in range(MONSTERS_ALIVE):
            self.spawn_monster()
        for _ in range(POWERUPS_ON_MAP):
            self.spawn_powerup()
        self.joy_id = self.joy_pos = None
        self.fire_ids.clear()
        self.mouse_fire = False
        self.state = "play"
        self.set_banner(f"{th['name']}: βρες {th['goal']} τέρατα!", 3.5)

    # ------------------------------------------------------------ ομάδα (έρχεται μόνο όταν την καλέσεις)
    def call_team(self, dur=HELP_TIME, from_button=False):
        if self.state != "play" or self.dead_timer > 0:
            return
        if from_button:
            if self.help_cd > 0:
                return
            self.help_cd = HELP_COOLDOWN
        p = self.player
        if not self.allies:
            for i in range(ALLIES):
                a = Human(p.x, p.y, role="escort")
                a.slot = i * 6.283 / ALLIES
                a.invuln = 0
                for _ in range(25):
                    ang, r = random.random() * 6.283, random.uniform(60, 150)
                    x, y = p.x + math.cos(ang) * r, p.y + math.sin(ang) * r
                    if not self.world.blocked(x, y, a.r):
                        a.x, a.y = x, y
                        break
                self.allies.append(a)
                self.poof(a.x, a.y - 10, (150, 220, 255), 10)
            self.humans = [p] + self.allies
        self.help_t = max(self.help_t, 0) + dur
        self.set_banner(f"Ήρθε η ομάδα για {int(self.help_t)} δευτερόλεπτα!", 2.5, (150, 230, 255))
        self.sfx.play("powerup")

    def dismiss_team(self):
        for a in self.allies:
            if a.alive:
                self.poof(a.x, a.y - 10, (150, 220, 255), 8)
                if self.on_screen(a.x, a.y):
                    self.add_text(a.x, a.y - 50, "Γεια!", WHITE, 18)
        self.allies = []
        self.humans = [self.player]
        self.help_t = 0

    def set_banner(self, text, dur=3.0, color=(255, 230, 80)):
        self.banner = [text, dur, color]

    def alive_humans(self):
        return [h for h in self.humans if h.alive and not (h.is_player and self.dead_timer > 0)]

    def free_spots(self):
        return [s for s in self.world.spots if s.occupant is None]

    def spawn_monster(self):
        spots = [s for s in self.free_spots()
                 if math.hypot(s.x - self.player.x, s.y - self.player.y) > 600
                 and all(math.hypot(s.x - h.x, s.y - h.y) > 300 for h in self.humans if h.alive)]
        if not spots:
            return
        pool = WORLDS[self.widx]["pool"]
        key = random.choices(list(pool), weights=list(pool.values()))[0]
        self.monsters.append(Monster(random.choice(spots), MT[key]))

    def spawn_powerup(self):
        for _ in range(10):
            x, y = self.world.random_street_point()
            if math.hypot(x - HQ[0], y - HQ[1]) > 200:
                self.powerups.append(PowerUp(x, y, random.choice(POWER_KINDS)))
                return

    def spawn_boss(self):
        key = WORLDS[self.widx]["boss"]
        far = [s for s in self.world.spots if math.hypot(s.x - self.player.x, s.y - self.player.y) > 750]
        s = random.choice(far) if far else random.choice(self.world.spots)
        x, y = s.x, s.y
        if self.world.blocked(x, y, BOSSES[key]["r"]):
            x, y = self.world.random_street_point()
        self.boss = Monster(None, BOSSES[key], x, y)
        self.monsters.append(self.boss)
        self.boss_spawned = True
        self.set_banner(f"Ο ΑΡΧΗΓΟΣ ΗΡΘΕ: {BOSSES[key]['name']}!", 4.0, (255, 90, 90))
        # δώρα για τη μάχη: ομάδα + καρδιά δίπλα στον παίκτη
        p = self.player
        for kind, dx in (("team", -70), ("heart", 70)):
            x, y = p.x + dx, p.y + 40
            if self.world.blocked(x, y, 20):
                x, y = p.x, p.y
            self.powerups.append(PowerUp(x, y, kind))
        self.sfx.play("boss")
        self.shake = 8

    def pick_hideout(self, m, flee):
        humans = self.alive_humans()
        near_h = lambda s: min((math.hypot(s.x - h.x, s.y - h.y) for h in humans), default=9999)
        cands = [s for s in self.free_spots() if near_h(s) > 220]
        if not cands:
            return None
        cands.sort(key=lambda s: math.hypot(s.x - m.x, s.y - m.y))
        if flee:
            cands = [s for s in cands if math.hypot(s.x - m.x, s.y - m.y) > 150][:8] or cands[:8]
            return max(cands, key=near_h)
        return cands[0]

    def on_screen(self, x, y, margin=80):
        return abs(x - self.player.x) < W / 2 + margin and abs(y - self.player.y) < H / 2 + margin

    def add_text(self, x, y, text, color, size=24):
        self.texts.append(FloatText(x, y, text, color, size))

    def poof(self, x, y, color, n=26):
        for _ in range(n):
            self.particles.append(Particle(x, y, random.choice([color, WHITE, (255, 230, 90), (255, 150, 200)]),
                                           star=random.random() < 0.6, speed=6))

    # ------------------------------------------------------------ όπλα / στόχευση
    def weapon(self):
        return WEAPONS[min(self.save["weapon"], self.save["weapons"] - 1)]

    def cycle_weapon(self):
        n = self.save["weapons"]
        self.save["weapon"] = (self.save["weapon"] + 1) % n
        if self.state == "play":
            p = self.player
            self.add_text(p.x, p.y - 60, self.weapon()["name"], self.weapon()["color"], 22)
        self.sfx.play("coin")

    def auto_target(self, h, rng=AUTO_AIM_RANGE):
        best, bd = None, rng
        for m in self.monsters:
            if m.state == "hidden":
                continue
            cx, cy = m.hit_center()
            d = math.hypot(cx - h.x, cy - h.y)
            if d < bd and self.world.los(h.x, h.y - 8, cx, cy, 2):
                best, bd = m, d
        return best

    def player_fire(self):
        p = self.player
        wpn = self.weapon()
        p.cool = wpn["cd"]
        tx, ty = p.gun_tip()
        for a, o in zip(wpn["angles"], wpn["offs"]):
            ox, oy = -math.sin(p.dir) * o, math.cos(p.dir) * o
            self.bullets.append(Bullet(tx + ox, ty + oy, p.dir + a + random.uniform(-0.03, 0.03), "player", wpn))
        self.sfx.play("laser" if wpn.get("pierce") else "shoot")

    # ------------------------------------------------------------ λογική
    def update(self, dt):
        self.time += dt
        self.shake = max(0, self.shake - dt * 20)
        if self.banner:
            self.banner[1] -= dt
            if self.banner[1] <= 0:
                self.banner = None
        self.help_cd = max(0, self.help_cd - dt)
        if self.allies:
            self.help_t -= dt
            if self.help_t <= 0:
                self.dismiss_team()
        self.update_player(dt)
        self.update_dog(dt)
        for a in self.allies:
            self.update_ally(a, dt)
        for m in self.monsters[:]:
            self.update_monster(m, dt)
        self.update_bullets(dt)
        self.update_shots(dt)
        self.update_items(dt)
        self.particles = [o for o in self.particles if o.update(dt)]
        self.texts = [t for t in self.texts if t.update(dt)]
        if not self.boss_spawned and self.progress >= WORLDS[self.widx]["goal"]:
            self.spawn_boss()
        if self.boss_dead_t > 0:
            self.boss_dead_t -= dt
            if self.boss_dead_t <= 0:
                self.world_cleared()
        self.save_t += dt
        if self.save_t > 8:
            self.save_t = 0
            self.save_game()

    def move_input(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dy:
            l = math.hypot(dx, dy)
            return dx / l, dy / l
        if self.joy_id is not None and self.joy_pos:
            jx, jy = self.joy_pos[0] - self.joy_origin[0], self.joy_pos[1] - self.joy_origin[1]
            l = math.hypot(jx, jy)
            if l > 10:
                k = min(1.0, l / 70) / l
                return jx * k, jy * k
        return 0, 0

    def update_player(self, dt):
        p = self.player
        for attr in ("shield_t", "speed_t", "magnet_t"):
            setattr(p, attr, max(0, getattr(p, attr) - dt))
        if self.dead_timer > 0:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                p.x, p.y = HQ
                p.hp, p.invuln = PLAYER_MAX_HP, 2.5
                self.dog.x, self.dog.y = HQ[0] + 40, HQ[1] + 25
            return
        mx, my = self.move_input()
        p.moving = bool(mx or my)
        sp = PLAYER_SPEED * (1.6 if p.speed_t > 0 else 1)
        if p.moving:
            p.walk += dt * 12 * (1.4 if p.speed_t > 0 else 1)
            nx, ny = p.x + mx * sp, p.y + my * sp
            if not self.world.blocked(nx, p.y, p.r):
                p.x = nx
            if not self.world.blocked(p.x, ny, p.r):
                p.y = ny
            p.dir = math.atan2(my, mx)
        p.cool = max(0, p.cool - dt)
        p.invuln = max(0, p.invuln - dt)
        keys = pygame.key.get_pressed()
        wants_fire = keys[pygame.K_SPACE] or bool(self.fire_ids) or self.mouse_fire
        if self.mouse_fire:
            cam = self.camera(False)
            mx2, my2 = pygame.mouse.get_pos()
            p.dir = math.atan2(my2 + cam[1] - (p.y - 8), mx2 + cam[0] - p.x)
        elif wants_fire:
            tgt = self.auto_target(p)
            if tgt:
                cx, cy = tgt.hit_center()
                p.dir = math.atan2(cy - (p.y - 8), cx - p.x)
        if wants_fire and p.cool <= 0:
            self.player_fire()
        if not any(m.state == "chase" and dist(m, p) < 300 for m in self.monsters):
            p.hp = min(PLAYER_MAX_HP, p.hp + 6 * dt)

    def update_dog(self, dt):
        d, p, world = self.dog, self.player, self.world
        d.barking = max(0, d.barking - dt)
        d.moving = False
        if dist(d, p) > 900:
            d.x, d.y, d.path = p.x + 30, p.y + 20, None
        if d.target and (d.target.occupant is None or d.target.occupant.state != "hidden"
                         or math.hypot(d.target.x - p.x, d.target.y - p.y) > 520):
            d.target = None
        if d.target is None and self.dead_timer <= 0:
            best, bd = None, 400
            for m in self.monsters:
                if m.state == "hidden" and m.spot:
                    dd = math.hypot(m.x - p.x, m.y - p.y)
                    if dd < bd:
                        best, bd = m.spot, dd
            if best:
                d.target, d.bark_t = best, 0.2
        if d.target:
            s = d.target
            l = math.hypot(s.x - p.x, s.y - p.y) or 1
            tx, ty = s.x - (s.x - p.x) / l * 38, s.y - (s.y - p.y) / l * 38
            if math.hypot(tx - d.x, ty - d.y) > 14:
                d.moving = d.steer(world, tx, ty, DOG_SPEED, dt)
            else:
                d.dir = math.atan2(s.y - d.y, s.x - d.x)
                d.bark_t -= dt
                if d.bark_t <= 0:
                    d.barking, d.bark_t = 0.35, 1.3
                    self.add_text(d.x, d.y - 40, "ΓΑΒ! ΓΑΒ!", (255, 255, 255), 22)
                    self.sfx.play("bark")
        else:
            back = p.dir + math.pi
            tx, ty = p.x + math.cos(back) * 40, p.y + math.sin(back) * 30 + 10
            if world.blocked(tx, ty, d.r):
                tx, ty = p.x, p.y
            dd = math.hypot(tx - d.x, ty - d.y)
            if dd > 30:
                d.moving = d.steer(world, tx, ty, DOG_SPEED * (1.3 if dd > 200 else 1), dt)
        if d.moving:
            d.walk += dt * 14

    def update_ally(self, a, dt):
        world = self.world
        if not a.alive:
            a.respawn -= dt
            if a.respawn <= 0:
                a.alive, a.hp, a.invuln = True, a.maxhp, 2.0
                a.x, a.y = self.player.x, self.player.y
                a.path = None
            return
        a.cool = max(0, a.cool - dt)
        a.invuln = max(0, a.invuln - dt)
        a.moving = False
        target, bd = None, 480
        for m in self.monsters:
            if m.state != "hidden":
                d = dist(a, m)
                if d < bd:
                    target, bd = m, d
        if target:
            want = 220 + (target.r if target.boss else 0)
            if bd > want:
                a.moving = a.steer(world, target.x, target.y, ALLY_SPEED, dt)
            elif bd < 110 + (target.r if target.boss else 0):
                a.moving = a.steer(world, a.x - (target.x - a.x), a.y - (target.y - a.y), ALLY_SPEED, dt)
            cx, cy = target.hit_center()
            a.dir = math.atan2(cy - (a.y - 8), cx - a.x)
            if a.cool <= 0 and world.los(a.x, a.y - 8, cx, cy, 2):
                a.cool = 0.4 + random.random() * 0.3
                tx, ty = a.gun_tip()
                self.bullets.append(Bullet(tx, ty, a.dir + random.uniform(-0.09, 0.09), "ally", WEAPONS[0]))
                if self.on_screen(a.x, a.y):
                    self.sfx.play("ally_shoot", gap=0.08)
        elif a.role == "escort" and self.dead_timer <= 0:
            p = self.player
            tx, ty = p.x + math.cos(a.slot) * 110, p.y + math.sin(a.slot) * 110
            if world.blocked(tx, ty, a.r):
                tx, ty = p.x, p.y
            d = math.hypot(tx - a.x, ty - a.y)
            if d > 35:
                a.moving = a.steer(world, tx, ty, ALLY_SPEED * (1.3 if d > 250 else 1), dt)
        else:
            a.goal_t -= dt
            if a.goal is None or a.goal_t <= 0 or math.hypot(a.goal[0] - a.x, a.goal[1] - a.y) < 30:
                a.goal, a.goal_t = world.random_street_point(), 14
            a.moving = a.steer(world, a.goal[0], a.goal[1], ALLY_SPEED * 0.8, dt)
        if a.moving:
            a.walk += dt * 12
        if not any(m.state == "chase" and dist(m, a) < 300 for m in self.monsters):
            a.hp = min(a.maxhp, a.hp + 4 * dt)

    def update_monster(self, m, dt):
        world = self.world
        m.wobble += dt * 6
        m.flash = max(0, m.flash - dt)
        m.slow_t = max(0, m.slow_t - dt)
        humans = self.alive_humans()
        if m.state == "hidden":
            for h in humans:
                if dist(m, h) < REVEAL_RADIUS:
                    m.state, m.lost = "chase", 0
                    m.spot.occupant, m.spot = None, None
                    if self.on_screen(m.x, m.y, 200):
                        self.sfx.play("growl", gap=0.3)
                        self.add_text(m.x, m.y - 50, "!", (255, 60, 60), 34)
                    break
            return
        speed = m.t["speed"] * (0.4 if m.slow_t > 0 else 1)
        if m.state == "chase":
            if not m.fled and m.t["hp"] >= 2 and m.hp <= m.t["hp"] / 2:
                spot = self.pick_hideout(m, flee=True)
                if spot:
                    m.state, m.spot, m.fled = "flee", spot, True
                    spot.occupant = m
                    m.path = None
                    if self.on_screen(m.x, m.y):
                        self.sfx.play("flee")
                        self.add_text(m.x, m.y - 55, "Τρέχει να κρυφτεί!", WHITE, 20)
                    return
            target = min(humans, key=lambda h: dist(m, h), default=None)
            if m.boss and target is None:
                target = self.player
            d = dist(m, target) if target else 9999
            if d > 650 and not m.boss:
                m.lost += dt
                if m.lost > 3:
                    spot = self.pick_hideout(m, flee=False)
                    if spot:
                        m.state, m.spot = "return", spot
                        spot.occupant = m
                        m.path = None
                return
            m.lost = 0
            if d > m.r + target.r - 4:
                m.steer(world, target.x, target.y, speed, dt)
            m.face = 1 if target.x >= m.x else -1
            # βολές
            if m.t.get("shoot") and d < 560:
                m.shoot_t -= dt
                if m.shoot_t <= 0:
                    cx, cy = m.hit_center()
                    if m.fly or world.los(cx, cy, target.x, target.y - 8, 4):
                        m.shoot_t = m.t["shoot"] + random.uniform(0, 0.8)
                        ang = math.atan2(target.y - 8 - cy, target.x - cx)
                        if m.boss:
                            for da in (-0.25, 0, 0.25):
                                self.shots.append(Shot(cx, cy, ang + da, 5.2, 16, m.t["shot_col"], ghost=m.fly))
                        else:
                            self.shots.append(Shot(cx, cy, ang, 5.5, 12, (255, 140, 40)))
                        if self.on_screen(m.x, m.y):
                            self.sfx.play("fire")
            if m.boss and m.t.get("summon"):
                m.summon_t -= dt
                if m.summon_t <= 0 and len(self.monsters) < 28:
                    m.summon_t = 7.0
                    for k in (-1, 1):
                        x, y = m.x + k * 60, m.y + 30
                        if not world.blocked(x, y, 20) or MT[m.t["summon"]].get("fly"):
                            self.monsters.append(Monster(None, MT[m.t["summon"]], x, y))
                            self.poof(x, y, (200, 200, 255), 10)
            for h in humans:
                if not h.protected() and dist(m, h) < m.r + h.r + 2:
                    h.hp -= m.t["dmg"] * dt
                    if h.is_player:
                        self.shake = 4
                        self.sfx.play("hurt", gap=0.35)
                    if h.hp <= 0:
                        self.human_died(h, m)
        else:
            sp = speed * (1.45 if m.state == "flee" else 1.0)
            m.steer(world, m.spot.x, m.spot.y, sp, dt)
            m.face = 1 if math.cos(m.dir) >= 0 else -1
            if math.hypot(m.spot.x - m.x, m.spot.y - m.y) < 12:
                if m.state == "flee":
                    m.hp = m.t["hp"]
                m.state, m.path = "hidden", None
                m.x, m.y = m.spot.x, m.spot.y

    def update_bullets(self, dt):
        world = self.world
        alive = []
        for b in self.bullets:
            if not b.update(dt) or world.blocked(b.x, b.y, 0):
                continue
            used = False
            for m in self.monsters:
                if m.state == "hidden" or id(m) in b.hit:
                    continue
                cx, cy = m.hit_center()
                if math.hypot(cx - b.x, cy - b.y) < m.r + 6:
                    b.hit.add(id(m))
                    m.hp -= b.dmg
                    m.flash = 0.1
                    if b.freeze:
                        m.slow_t = 2.0
                    if self.on_screen(m.x, m.y):
                        self.sfx.play("hit")
                    if m.hp <= 0:
                        self.kill_monster(m, b.owner)
                    if not b.pierce:
                        used = True
                        break
            if not used:
                alive.append(b)
        self.bullets = alive

    def update_shots(self, dt):
        alive = []
        for s in self.shots:
            if not s.update(dt) or (not s.ghost and self.world.blocked(s.x, s.y, 0)):
                continue
            hit = False
            for h in self.alive_humans():
                if math.hypot(h.x - s.x, h.y - 8 - s.y) < h.r + 8:
                    hit = True
                    if not h.protected():
                        h.hp -= s.dmg
                        if h.is_player:
                            self.shake = 5
                            self.sfx.play("hurt", gap=0.2)
                        if h.hp <= 0:
                            self.human_died(h, self.boss or None)
                    break
            if not hit:
                alive.append(s)
        self.shots = alive

    def update_items(self, dt):
        p = self.player
        alive_p = self.dead_timer <= 0
        rad = 520 if p.magnet_t > 0 else 110
        keep = []
        for c in self.coins:
            c.t += dt
            c.x += c.vx
            c.y += c.vy
            c.vx *= 0.9
            c.vy *= 0.9
            d = math.hypot(p.x - c.x, p.y - 8 - c.y)
            if alive_p and c.t > c.delay and (d < rad or c.delay > 0):
                sp = 9 + c.t * 3
                c.x += (p.x - c.x) / (d or 1) * min(sp, d)
                c.y += (p.y - 8 - c.y) / (d or 1) * min(sp, d)
            if alive_p and d < 30:
                self.add_trophies(1)
                self.sfx.play("coin", gap=0.03)
                for _ in range(4):
                    self.particles.append(Particle(p.x, p.y - 20, GOLD, star=True, speed=3))
                continue
            keep.append(c)
        self.coins = keep
        keep = []
        for u in self.powerups:
            if alive_p and math.hypot(p.x - u.x, p.y - u.y) < 36:
                self.apply_power(u.kind)
                continue
            keep.append(u)
        self.powerups = keep
        self.power_t -= dt
        if self.power_t <= 0:
            self.power_t = 8.0
            if len(self.powerups) < POWERUPS_ON_MAP:
                self.spawn_powerup()

    def apply_power(self, kind):
        p = self.player
        if kind == "heart":
            p.hp = PLAYER_MAX_HP
            if self.lives < LIVES:
                self.lives += 1
        elif kind == "shield":
            p.shield_t = 8.0
        elif kind == "shoes":
            p.speed_t = 8.0
        elif kind == "magnet":
            p.magnet_t = 12.0
        elif kind == "team":
            self.call_team(HELP_TIME)
        self.add_text(p.x, p.y - 60, POWER_NAMES[kind], (120, 255, 200), 26)
        self.sfx.play("powerup")
        for _ in range(16):
            self.particles.append(Particle(p.x, p.y - 10, (120, 255, 200), star=True))

    def discover(self, key):
        alb = self.save["album"]
        first = key not in alb
        alb[key] = alb.get(key, 0) + 1
        if first:
            self.album_cache = None
            self.set_banner(f"ΝΕΟ ΤΕΡΑΣ ΣΤΟ ΑΛΜΠΟΥΜ: {ALL_TYPES[key]['name']}!", 3.0, (150, 230, 255))
            self.sfx.play("album")

    def kill_monster(self, m, owner):
        if m not in self.monsters:
            return
        self.monsters.remove(m)
        if m.spot:
            m.spot.occupant = None
        self.discover(m.t["key"])
        cx, cy = m.hit_center()
        if m.boss:
            self.poof(cx, cy, m.t["color"], 90)
            self.shake = 12
            self.sfx.play("poof")
            self.sfx.play("fanfare")
            for i in range(BOSS_REWARD):
                self.coins.append(Coin(cx, cy, delay=0.8 + i * 0.03))
            self.boss = None
            self.boss_dead_t = 4.0
            self.set_banner("ΜΠΡΑΒΟ! ΝΙΚΗΣΕΣ ΤΟΝ ΑΡΧΗΓΟ!", 4.0, (255, 230, 80))
            for mm in self.monsters[:]:   # τα υπόλοιπα τέρατα τρέχουν να κρυφτούν
                if mm.state == "chase":
                    spot = self.pick_hideout(mm, False)
                    if spot:
                        mm.state, mm.spot = "return", spot
                        spot.occupant = mm
            return
        self.progress += 1
        self.poof(cx, cy, m.t["color"])
        if owner == "player":
            for _ in range(m.t["reward"]):
                self.coins.append(Coin(cx, cy))
            self.sfx.play("poof")
        else:
            self.add_trophies(ALLY_KILL_BONUS)
            if self.on_screen(m.x, m.y):
                self.add_text(m.x, m.y - 40, f"+{ALLY_KILL_BONUS} ομάδα", (255, 200, 120), 18)
                self.sfx.play("poof")
            self.sfx.play("team")
        if random.random() < 0.22:
            self.powerups.append(PowerUp(m.x, m.y, random.choice(POWER_KINDS)))
        if not self.boss_spawned or len(self.monsters) < MONSTERS_ALIVE // 2:
            self.spawn_monster()

    def human_died(self, h, killer):
        if not h.alive or (h.is_player and self.dead_timer > 0):
            return
        self.poof(h.x, h.y - 10, (200, 200, 200), 30)
        if killer and not killer.boss and killer in self.monsters:
            spot = self.pick_hideout(killer, flee=False)
            if spot:
                killer.state, killer.spot = "return", spot
                spot.occupant = killer
        if h.is_player:
            self.lives -= 1
            self.add_trophies(-1)
            self.shake = 10
            self.add_text(h.x, h.y - 50, "-1 κύπελλο", (255, 120, 120), 28)
            self.sfx.play("player_die")
            self.fire_ids.clear()
            if self.lives <= 0:
                self.save["trophies"] = (self.save["trophies"] + 1) // 2
                self.state = "retry"
                self.sfx.play("retry")
                self.save_game()
            else:
                self.dead_timer = 2.0
                h.hp = 1
        else:
            h.alive, h.respawn = False, ALLY_RESPAWN
            if self.on_screen(h.x, h.y):
                self.add_text(h.x, h.y - 50, f"{h.name}: Γυρίζω αμέσως!", (255, 200, 200), 18)
                self.sfx.play("ally_die")

    def world_cleared(self):
        idx = self.widx
        s = self.save
        key = WORLDS[idx]["key"]
        if key not in s["cleared"]:
            s["cleared"].append(key)
        new_weapon = None
        if s["weapons"] < len(WEAPONS) and idx + 2 > s["weapons"]:
            s["weapons"] = min(len(WEAPONS), idx + 2)
            s["weapon"] = s["weapons"] - 1
            new_weapon = WEAPONS[s["weapon"]]
        next_world = None
        if idx + 1 < len(WORLDS):
            if s["unlocked"] < idx + 2:
                s["unlocked"] = idx + 2
            next_world = WORLDS[idx + 1]
        self.clear_info = dict(boss=BOSSES[WORLDS[idx]["boss"]], weapon=new_weapon, next=next_world,
                               final=idx == len(WORLDS) - 1)
        self.state = "clear"
        self.banner = None
        self.ui_particles = []
        self.sfx.play("fanfare")
        self.save_game()

    def camera(self, shake=True):
        p = self.player
        cx = min(max(p.x - W / 2, 0), WORLD_W - W)
        cy = min(max(p.y - H / 2, 0), WORLD_H - H)
        if shake and self.shake > 0:
            cx += random.uniform(-self.shake, self.shake)
            cy += random.uniform(-self.shake, self.shake)
        return cx, cy

    # ------------------------------------------------------------ σχέδιο: παιχνίδι
    def text(self, txt, size, color, x, y, center=True, shadow_px=3):
        img = font(size).render(txt, True, color)
        if center:
            x -= img.get_width() // 2
        if shadow_px:
            self.screen.blit(font(size).render(txt, True, (0, 0, 0)), (x + shadow_px, y + shadow_px))
        self.screen.blit(img, (x, y))
        return img.get_width()

    def button(self, rect, txt, color, action, size=28):
        b = Button(rect, txt, color, action, size)
        b.draw(self.screen)
        self.hot.append((b.rect, action))
        return b

    def draw_play(self):
        s = self.screen
        t = self.t
        cam = self.camera()
        s.fill((0, 0, 0))
        s.blit(self.world.bg, (0, 0), pygame.Rect(int(cam[0]), int(cam[1]), W, H))
        vis = lambda x, y, m=80: -m < x - cam[0] < W + m and -m < y - cam[1] < H + m

        # το σκυλάκι δείχνει κρυψώνα
        d = self.dog
        if d.target:
            sx, sy = int(d.target.x - cam[0]), int(d.target.y - cam[1])
            rr = 30 + int(math.sin(t * 8) * 5)
            pygame.draw.circle(s, (255, 230, 60), (sx, sy), rr, 4)
            bob = int(math.sin(t * 6) * 5)
            pygame.draw.polygon(s, (255, 230, 60), [(sx - 12, sy - 58 + bob), (sx + 12, sy - 58 + bob), (sx, sy - 42 + bob)])
        for m in self.monsters:
            if m.state == "hidden" and vis(m.x, m.y) and int(m.wobble) % 3 != 0 and \
                    (dist(m, self.player) < 380 or (d.target is m.spot)):
                ex, ey = m.spot.eyes_pos()
                ex, ey = int(ex - cam[0]), int(ey - cam[1])
                for k in (-5, 5):
                    pygame.draw.circle(s, (255, 255, 0), (ex + k, ey), 3)
                    pygame.draw.circle(s, (200, 0, 0), (ex + k, ey), 1)
        for c in self.coins:
            if vis(c.x, c.y):
                c.draw(s, cam, t)
        for u in self.powerups:
            if vis(u.x, u.y):
                u.draw(s, cam, t)
        actors = [m for m in self.monsters if m.state != "hidden" and vis(m.x, m.y, 200)]
        actors += [a for a in self.allies if a.alive and vis(a.x, a.y)]
        if self.dead_timer <= 0:
            actors.append(self.player)
        actors.append(self.dog)
        for a in sorted(actors, key=lambda a: a.y):
            a.draw(s, cam, t)
        for b in self.bullets:
            b.draw(s, cam)
        for sh in self.shots:
            sh.draw(s, cam, t)
        tk = self.world.th["tree"]
        for x, y, r in self.world.trees:
            if vis(x, y):
                draw_tree(s, tk, int(x - cam[0]), int(y - cam[1]), r)
        for pa in self.particles:
            pa.draw(s, cam)
        if self.world.th.get("dark"):
            if self.dark_mask is None:
                self.dark_mask = pygame.Surface((W * 2, H * 2), pygame.SRCALPHA)
                self.dark_mask.fill((15, 0, 30, 170))
                for r in range(380, 0, -8):
                    a = int(170 * min(1, (r / 380) ** 2))
                    pygame.draw.circle(self.dark_mask, (15, 0, 30, a), (W, H), r)
            px, py = self.player.x - cam[0], self.player.y - cam[1]
            s.blit(self.dark_mask, (int(px - W), int(py - H)))
        for tx in self.texts:
            img = font(tx.size).render(tx.text, True, tx.color)
            img.set_alpha(int(255 * min(1, tx.life)))
            s.blit(img, (tx.x - cam[0] - img.get_width() / 2, tx.y - cam[1]))
        self.draw_hud(cam)
        if self.dead_timer > 0:
            self.text("Ωχ! Ξαναπάμε!", 50, (255, 120, 120), W // 2, H // 2 - 40)

    def draw_hud(self, cam):
        s = self.screen
        p = self.player
        panel = pygame.Surface((300, 118), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        s.blit(panel, (10, 10))
        draw_trophy(s, 40, 44, 1.6)
        self.text(str(self.trophies), 40, GOLD, 68, 18, center=False, shadow_px=2)
        for i in range(LIVES):
            draw_heart(s, 205 + i * 32, 36, 1.2, i < self.lives)
        hp = max(0, p.hp) / PLAYER_MAX_HP
        pygame.draw.rect(s, (60, 0, 0), (22, 76, 276, 16), border_radius=6)
        col = (60, 210, 80) if hp > 0.5 else (240, 190, 40) if hp > 0.25 else (230, 50, 50)
        pygame.draw.rect(s, col, (22, 76, int(276 * hp), 16), border_radius=6)
        x = 26
        for attr, kind in (("shield_t", "shield"), ("speed_t", "shoes"), ("magnet_t", "magnet")):
            v = getattr(p, attr)
            if v > 0:
                draw_power_icon(s, kind, x + 10, 108, 0.7)
                self.text(str(int(v) + 1), 16, WHITE, x + 24, 100, center=False, shadow_px=1)
                x += 52

        # πρόοδος / αρχηγός
        th = WORLDS[self.widx]
        if self.boss:
            b = self.boss
            self.text(b.t["name"], 24, (255, 120, 120), W // 2, 12)
            pygame.draw.rect(s, (50, 0, 0), (W // 2 - 200, 44, 400, 20), border_radius=8)
            pygame.draw.rect(s, (230, 50, 60), (W // 2 - 200, 44, int(400 * max(0, b.hp) / b.t["hp"]), 20),
                             border_radius=8)
            pygame.draw.rect(s, WHITE, (W // 2 - 200, 44, 400, 20), 2, border_radius=8)
        elif not self.boss_spawned:
            goal = th["goal"]
            self.text(f"{th['name']}   Τέρατα: {min(self.progress, goal)} / {goal}", 22, WHITE, W // 2, 12)
            pygame.draw.rect(s, (30, 30, 50), (W // 2 - 160, 42, 320, 14), border_radius=6)
            pygame.draw.rect(s, (120, 200, 255), (W // 2 - 160, 42, int(320 * min(1, self.progress / goal)), 14),
                             border_radius=6)
        # μικρός χάρτης
        mm = self.world.minimap.copy()
        k = mm.get_width() / WORLD_W
        for m in self.monsters:
            if m.state != "hidden":
                pygame.draw.circle(mm, (255, 60, 60), (int(m.x * k), int(m.y * k)), 6 if m.boss else 3)
        for a in self.allies:
            if a.alive:
                pygame.draw.circle(mm, (90, 255, 90), (int(a.x * k), int(a.y * k)), 2)
        for u in self.powerups:
            pygame.draw.circle(mm, (255, 255, 255), (int(u.x * k), int(u.y * k)), 2)
        pygame.draw.circle(mm, WHITE, (int(p.x * k), int(p.y * k)), 5)
        pygame.draw.circle(mm, (60, 140, 255), (int(p.x * k), int(p.y * k)), 4)
        pygame.draw.rect(mm, WHITE, mm.get_rect(), 2)
        mx = W - mm.get_width() - 10
        s.blit(mm, (mx, 10))
        # παύση
        pr = pygame.Rect(mx - 66, 10, 56, 56)
        pygame.draw.rect(s, (0, 0, 0), pr.move(0, 3), border_radius=12)
        pygame.draw.rect(s, (70, 80, 120), pr, border_radius=12)
        pygame.draw.rect(s, WHITE, (pr.x + 17, pr.y + 15, 8, 26))
        pygame.draw.rect(s, WHITE, (pr.x + 31, pr.y + 15, 8, 26))
        self.hot.append((pr, self.pause))
        # βέλος προς τον αρχηγό
        if self.boss and not self.on_screen(self.boss.x, self.boss.y, -40):
            ang = math.atan2(self.boss.y - p.y, self.boss.x - p.x)
            cx, cy = W / 2 + math.cos(ang) * (W / 2 - 90), H / 2 + math.sin(ang) * (H / 2 - 90)
            pts = [(cx + math.cos(ang) * 30, cy + math.sin(ang) * 30),
                   (cx + math.cos(ang + 2.5) * 22, cy + math.sin(ang + 2.5) * 22),
                   (cx + math.cos(ang - 2.5) * 22, cy + math.sin(ang - 2.5) * 22)]
            pygame.draw.polygon(s, (255, 60, 60), pts)
            pygame.draw.polygon(s, WHITE, pts, 3)
            draw_crown(s, cx - math.cos(ang) * 10, cy - math.sin(ang) * 10 + 8, 12)
        # όπλο
        wpn = self.weapon()
        wc = (W - 245, H - 80)
        pygame.draw.circle(s, (0, 0, 0), (wc[0], wc[1] + 4), 46)
        pygame.draw.circle(s, (60, 70, 110), wc, 46)
        pygame.draw.circle(s, wpn["color"], wc, 46, 4)
        pygame.draw.rect(s, (40, 40, 40), (wc[0] - 22, wc[1] - 14, 40, 12), border_radius=3)
        pygame.draw.rect(s, (40, 40, 40), (wc[0] - 20, wc[1] - 6, 10, 16), border_radius=3)
        pygame.draw.circle(s, wpn["color"], (wc[0] + 22, wc[1] - 8), 6)
        self.text(wpn["name"], 15, WHITE, wc[0], wc[1] + 14, shadow_px=1)
        if self.save["weapons"] > 1:
            self.hot.append((pygame.Rect(wc[0] - 46, wc[1] - 46, 92, 92), self.cycle_weapon))
        # κουμπί ΒΟΗΘΕΙΑ (φωνάζει την ομάδα)
        hc = (W - 110, H - 262) if self.touch_seen else (W - 365, H - 80)
        ready = self.help_cd <= 0
        active = bool(self.allies)
        col = (60, 160, 230) if ready else (100, 100, 115)
        pygame.draw.circle(s, (0, 0, 0), (hc[0], hc[1] + 4), 46)
        pygame.draw.circle(s, col, hc, 46)
        pygame.draw.circle(s, (200, 235, 255) if ready else (160, 160, 170), hc, 46, 4)
        draw_team_icon(s, hc[0], hc[1] - 12, 1.3)
        if active:
            lbl = f"ΟΜΑΔΑ {int(self.help_t) + 1}"
        elif ready:
            lbl = "ΒΟΗΘΕΙΑ"
        else:
            lbl = f"{int(self.help_cd) + 1}"
        self.text(lbl, 15, WHITE, hc[0], hc[1] + 14, shadow_px=1)
        self.hot.append((pygame.Rect(hc[0] - 46, hc[1] - 46, 92, 92), lambda: self.call_team(HELP_TIME, True)))
        # χειριστήρια αφής
        if self.touch_seen:
            fc = (W - 110, H - 120)
            pressed = bool(self.fire_ids)
            pygame.draw.circle(s, (0, 0, 0), (fc[0], fc[1] + 5), 72)
            pygame.draw.circle(s, (240, 70, 70) if not pressed else (255, 130, 130), fc, 72)
            pygame.draw.circle(s, (255, 180, 180), fc, 72, 4)
            self.text("ΦΩΤΙΑ", 26, WHITE, fc[0], fc[1] - 16, shadow_px=2)
            if self.joy_id is not None and self.joy_pos:
                o, jp = self.joy_origin, self.joy_pos
                dx, dy = jp[0] - o[0], jp[1] - o[1]
                l = math.hypot(dx, dy)
                if l > 70:
                    dx, dy = dx / l * 70, dy / l * 70
                base, knob = o, (o[0] + dx, o[1] + dy)
            else:
                base = knob = (150, H - 150)
            js = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(js, (255, 255, 255, 60), (100, 100), 90)
            pygame.draw.circle(js, (255, 255, 255, 140), (100, 100), 90, 4)
            s.blit(js, (base[0] - 100, base[1] - 100))
            pygame.draw.circle(s, (230, 230, 240), (int(knob[0]), int(knob[1])), 38)
            pygame.draw.circle(s, (150, 150, 170), (int(knob[0]), int(knob[1])), 38, 4)
        else:
            self.text("WASD: κίνηση · ποντίκι/SPACE: φωτιά · Q: όπλο · H: βοήθεια · P: παύση", 18, WHITE, W // 2, H - 30, shadow_px=2)
        if self.banner:
            txt, dur, col = self.banner
            img = font(34).render(txt, True, col)
            bw = img.get_width() + 40
            bgp = pygame.Surface((bw, 60), pygame.SRCALPHA)
            bgp.fill((0, 0, 0, 160))
            s.blit(bgp, (W // 2 - bw // 2, 80))
            self.text(txt, 34, col, W // 2, 88)

    # ------------------------------------------------------------ οθόνες
    def draw_menu(self):
        s, t = self.screen, self.t
        s.fill((34, 46, 92))
        for i in range(12):
            y = (i * 70 + t * 20) % (H + 70) - 70
            pygame.draw.circle(s, (44, 58, 110), (int(80 + i * 97) % W, int(y)), 40)
        deco = [("slime", 120, 230), ("ghost", 1000, 220), ("dragon", 110, 640), ("bat", 1010, 640)]
        for k, x, y in deco:
            draw_monster_type(s, x, y + int(math.sin(t * 2 + x) * 6), MT[k], 1 if x < W / 2 else -1, t * 4, scale=1.5)
        self.text("MONSTER HUNTER", 72, GOLD, W // 2, 30, shadow_px=5)
        self.text("Κυνήγι Τεράτων", 32, WHITE, W // 2, 118)
        draw_trophy(s, W - 150, 42, 1.6)
        self.text(str(self.trophies), 40, GOLD, W - 125, 18, center=False)
        cw, ch, gap = 186, 220, 16
        x0 = (W - (cw * 5 + gap * 4)) // 2
        for i, th in enumerate(WORLDS):
            r = pygame.Rect(x0 + i * (cw + gap), 190, cw, ch)
            unlocked = i < self.save["unlocked"]
            pygame.draw.rect(s, (0, 0, 0), r.move(0, 6), border_radius=18)
            pygame.draw.rect(s, th["ground"], r, border_radius=18)
            pygame.draw.rect(s, th["road"], (r.x, r.y + 140, r.w, 80), border_bottom_left_radius=18,
                             border_bottom_right_radius=18)
            boss = BOSSES[th["boss"]]
            draw_monster_type(s, r.centerx, r.y + 118 + int(math.sin(t * 2 + i) * 4), boss, 1, t * 3,
                              flash=False, scale=1.15)
            pygame.draw.rect(s, WHITE, r, 3, border_radius=18)
            self.text(th["name"], 24, WHITE, r.centerx, r.y + 160)
            if not unlocked:
                ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                ov.fill((10, 10, 20, 190))
                s.blit(ov, r.topleft)
                draw_lock(s, r.centerx, r.centery, 1.6)
            else:
                if th["key"] in self.save["cleared"]:
                    cx, cy = r.right - 26, r.y + 26
                    pts = [(cx + math.cos(a) * (16 if j % 2 == 0 else 7), cy + math.sin(a) * (16 if j % 2 == 0 else 7))
                           for j, a in enumerate([-math.pi / 2 + j * math.pi / 5 for j in range(10)])]
                    pygame.draw.polygon(s, GOLD, pts)
                    pygame.draw.polygon(s, (150, 100, 10), pts, 2)
                self.hot.append((r, lambda i=i: self.start_world(i)))
        self.text("Διάλεξε κόσμο!", 30, WHITE, W // 2, 430)
        n_alb = len([k for k in ALBUM_ORDER if k in self.save["album"]])
        self.button((W // 2 - 330, 500, 300, 80), f"Άλμπουμ  {n_alb}/{len(ALBUM_ORDER)}", (150, 80, 190),
                    lambda: self.open_album("menu"), 30)
        self.button((W // 2 + 30, 500, 300, 80), "Ήχος: " + ("ON" if self.sfx.on else "OFF"),
                    (70, 140, 90) if self.sfx.on else (110, 110, 110), self.toggle_sound, 30)
        self.text(f"Όπλα: {self.save['weapons']}/{len(WEAPONS)}   ·   Ρεκόρ κυπέλλων: {self.save['best']}", 20,
                  (200, 210, 240), W // 2, 610, shadow_px=1)

    def open_album(self, back):
        self.album_back = back
        self.state = "album"

    def build_album_cache(self):
        cache = {}
        for key in ALBUM_ORDER:
            t = ALL_TYPES[key]
            boss = t["boss"]
            size = (180, 130) if boss else (125, 92)
            img = pygame.Surface(size, pygame.SRCALPHA)
            sc = 1.45 if boss else (0.95 if t.get("photo") else 1.1)
            draw_monster_type(img, size[0] // 2, size[1] - 22, t, 1, 0.0, scale=sc)
            sil = img.copy()
            sil.fill((25, 25, 40), special_flags=pygame.BLEND_RGB_MIN)
            cache[key] = (img, sil)
        self.album_cache = cache

    def draw_album(self):
        s = self.screen
        s.fill((48, 34, 80))
        if self.album_cache is None:
            self.build_album_cache()
        alb = self.save["album"]
        n = len([k for k in ALBUM_ORDER if k in alb])
        self.text(f"Άλμπουμ Τεράτων   {n} / {len(ALBUM_ORDER)}", 36, GOLD, W // 2, 10)
        mons, bosses = list(MT), list(BOSSES)
        per_row = (len(mons) + 1) // 2
        cw, ch, gap = 150, 138, 10
        for row, items in enumerate((mons[:per_row], mons[per_row:])):
            x0 = (W - (cw * len(items) + gap * (len(items) - 1))) // 2
            for i, key in enumerate(items):
                self.album_card(pygame.Rect(x0 + i * (cw + gap), 62 + row * (ch + 8), cw, ch), key, alb)
        cw, ch, gap = 190, 190, 14
        x0 = (W - (cw * 5 + gap * 4)) // 2
        for i, key in enumerate(bosses):
            self.album_card(pygame.Rect(x0 + i * (cw + gap), 358, cw, ch), key, alb)
        self.button((W // 2 - 120, 568, 240, 70), "Πίσω", (80, 90, 140), self.album_close, 32)

    def album_card(self, r, key, alb):
        s = self.screen
        t = ALL_TYPES[key]
        found = key in alb
        pygame.draw.rect(s, (0, 0, 0), r.move(0, 5), border_radius=14)
        pygame.draw.rect(s, (250, 240, 210) if found else (90, 80, 110), r, border_radius=14)
        pygame.draw.rect(s, GOLD if t["boss"] and found else WHITE, r, 3, border_radius=14)
        img, sil = self.album_cache[key]
        s.blit(img if found else sil, (r.centerx - img.get_width() // 2, r.y + 4))
        if found:
            self.text(t["name"], 16, (60, 40, 30), r.centerx, r.bottom - 44, shadow_px=0)
            self.text(f"x{alb[key]}", 15, (140, 90, 20), r.centerx, r.bottom - 22, shadow_px=0)
        else:
            self.text("???", 22, (200, 200, 230), r.centerx, r.bottom - 42, shadow_px=0)

    def album_close(self):
        self.state = self.album_back

    def draw_overlay(self, alpha=170):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        self.screen.blit(ov, (0, 0))

    def draw_pause(self):
        self.draw_play()
        self.hot = []
        self.draw_overlay()
        self.text("ΠΑΥΣΗ", 64, WHITE, W // 2, 110)
        self.button((W // 2 - 170, 230, 340, 80), "Συνέχεια", (60, 160, 90), self.resume, 34)
        self.button((W // 2 - 170, 330, 340, 80), "Άλμπουμ", (150, 80, 190), lambda: self.open_album("pause"), 34)
        self.button((W // 2 - 170, 430, 340, 80), "Μενού", (90, 90, 140), self.to_menu, 34)
        self.button((W // 2 - 170, 530, 340, 70), "Ήχος: " + ("ON" if self.sfx.on else "OFF"),
                    (70, 140, 90) if self.sfx.on else (110, 110, 110), self.toggle_sound, 28)

    def draw_clear(self, dt):
        self.draw_play()
        self.hot = []
        self.draw_overlay(150)
        info = self.clear_info
        if random.random() < 0.6:
            self.ui_particles.append([random.uniform(0, W), -10, random.uniform(-1, 1), random.uniform(2, 4),
                                      random.choice([GOLD, (255, 120, 160), (120, 220, 255), (140, 255, 140)])])
        for pp in self.ui_particles:
            pp[0] += pp[2]
            pp[1] += pp[3]
            pygame.draw.rect(self.screen, pp[4], (int(pp[0]), int(pp[1]), 8, 12))
        self.ui_particles = [pp for pp in self.ui_particles if pp[1] < H + 20]
        if info["final"]:
            self.text("ΕΙΣΑΙ Ο ΚΑΛΥΤΕΡΟΣ", 60, GOLD, W // 2, 50, shadow_px=5)
            self.text("ΚΥΝΗΓΟΣ ΤΕΡΑΤΩΝ!", 60, GOLD, W // 2, 120, shadow_px=5)
        else:
            self.text("ΜΠΡΑΒΟ!", 80, GOLD, W // 2, 50, shadow_px=5)
        self.text(f"Νίκησες: {info['boss']['name']}!", 34, WHITE, W // 2, 200)
        draw_monster_type(self.screen, W // 2, 380, info["boss"], 1, self.t * 3, scale=1.4)
        y = 410
        if info["weapon"]:
            self.text(f"Νέο όπλο: {info['weapon']['name']}!", 32, info["weapon"]["color"], W // 2, y)
            y += 46
        if info["next"]:
            self.text(f"Άνοιξε ο κόσμος: {info['next']['name']}!", 30, (150, 230, 255), W // 2, y)
            self.button((W // 2 - 320, 570, 300, 80), "Επόμενος κόσμος", (60, 160, 90),
                        lambda: self.start_world(self.widx + 1), 28)
            self.button((W // 2 + 20, 570, 300, 80), "Μενού", (90, 90, 140), self.to_menu, 30)
        else:
            self.button((W // 2 - 150, 570, 300, 80), "Μενού", (90, 90, 140), self.to_menu, 30)

    def draw_retry(self):
        self.draw_play()
        self.hot = []
        self.draw_overlay(170)
        self.text("Ξαναπροσπάθησε!", 66, (255, 200, 90), W // 2, 120, shadow_px=5)
        self.text("Τα τέρατα κέρδισαν αυτή τη φορά...", 30, WHITE, W // 2, 220)
        draw_trophy(self.screen, W // 2 - 270, 322, 2.4)
        self.text(f"Κράτησες {self.trophies} κύπελλα!", 36, GOLD, W // 2 + 40, 300)
        self.button((W // 2 - 320, 450, 300, 90), "Ξανά!", (60, 160, 90), lambda: self.start_world(self.widx), 38)
        self.button((W // 2 + 20, 450, 300, 90), "Μενού", (90, 90, 140), self.to_menu, 34)

    # ------------------------------------------------------------ ενέργειες
    def pause(self):
        if self.state == "play":
            self.state = "pause"
            self.fire_ids.clear()
            self.joy_id = None
            self.mouse_fire = False
            self.save_game()

    def resume(self):
        self.state = "play"

    def to_menu(self):
        self.save_game()
        self.state = "menu"
        self.world = None
        self.dark_mask = None

    def toggle_sound(self):
        self.sfx.set_on(not self.sfx.on)
        self.save["sound"] = self.sfx.on
        self.save_game()

    def quit(self):
        self.save_game()
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------ είσοδος
    def finger_pos(self, e):
        try:
            ww, wh = pygame.display.get_window_size()
            sc = min(ww / W, wh / H)
            ox, oy = (ww - W * sc) / 2, (wh - H * sc) / 2
            return (e.x * ww - ox) / sc, (e.y * wh - oy) / sc
        except Exception:
            return e.x * W, e.y * H

    def on_press(self, pos, finger):
        for rect, action in reversed(self.hot):
            if rect.collidepoint(pos):
                action()
                return
        if self.state == "play":
            if finger is None:
                self.mouse_fire = True
            elif pos[0] < W * 0.5 and self.joy_id is None:
                self.joy_id, self.joy_origin, self.joy_pos = finger, pos, pos
            else:
                self.fire_ids.add(finger)

    def on_back(self):
        st = self.state
        if st == "play":
            self.pause()
        elif st == "pause":
            self.resume()
        elif st == "album":
            self.album_close()
        elif st in ("clear", "retry"):
            self.to_menu()
        else:
            self.quit()

    def handle_events(self):
        bg_events = {getattr(pygame, n) for n in ("APP_WILLENTERBACKGROUND", "APP_DIDENTERBACKGROUND")
                     if hasattr(pygame, n)}
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            elif e.type in bg_events:
                self.pause()
                self.save_game()
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, getattr(pygame, "K_AC_BACK", -1)):
                    self.on_back()
                elif e.key == pygame.K_p:
                    self.resume() if self.state == "pause" else self.pause()
                elif e.key == pygame.K_m:
                    self.toggle_sound()
                elif e.key == pygame.K_q and self.state == "play":
                    self.cycle_weapon()
                elif e.key == pygame.K_h and self.state == "play":
                    self.call_team(HELP_TIME, True)
                elif e.key == pygame.K_RETURN and self.state == "menu":
                    self.start_world(self.save["unlocked"] - 1)
            elif e.type == pygame.FINGERDOWN:
                self.touch_seen = True
                self.on_press(self.finger_pos(e), e.finger_id)
            elif e.type == pygame.FINGERMOTION:
                if e.finger_id == self.joy_id:
                    self.joy_pos = self.finger_pos(e)
            elif e.type == pygame.FINGERUP:
                if e.finger_id == self.joy_id:
                    self.joy_id = self.joy_pos = None
                self.fire_ids.discard(e.finger_id)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.touch_seen or getattr(e, "touch", False):
                    continue
                self.on_press(e.pos, None)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.mouse_fire = False

    # ------------------------------------------------------------ βρόχος
    def frame(self, dt):
        self.t += dt
        self.handle_events()
        self.hot = []
        st = self.state
        if st == "play":
            self.update(dt)
            if self.state == "play":
                self.draw_play()
        st = self.state
        if st == "menu":
            self.draw_menu()
        elif st == "album":
            self.draw_album()
        elif st == "pause":
            self.draw_pause()
        elif st == "clear":
            self.draw_clear(dt)
        elif st == "retry":
            self.draw_retry()
        pygame.display.flip()

    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.frame(dt)


def main():
    Game().run()


if __name__ == "__main__":
    main()
