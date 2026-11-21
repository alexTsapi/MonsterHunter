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
    "wolf":   dict(name="Μωβ Λύκος",     color=(150, 90, 200),  hp=4, speed=2.6, dmg=20, reward=4, r=22, photo="wolf",
                   voice="howl"),
    "skel":   dict(name="Σκελετοζόμπι",  color=(150, 240, 90),  hp=5, speed=2.1, dmg=20, reward=4, r=22, photo="skel",
                   voice="rattle"),
    "yellow": dict(name="Κιτρινόσαυρος", color=(250, 225, 40),  hp=4, speed=2.5, dmg=20, reward=4, r=22,
                   photo="yellow", face=-1, voice="chirp"),
    "pinkdino":    dict(name="Ροζόσαυρος",     color=(240, 80, 200), hp=4, speed=2.4, dmg=18, reward=4, r=22,
                        photo="pinkdino", face=-1, voice="chirp"),
    "bluedragon":  dict(name="Μπλε Δράκος",    color=(60, 160, 240), hp=4, speed=2.3, dmg=18, reward=4, r=22,
                        photo="bluedragon", face=-1, voice="screech", fly=True),
    "golddragon":  dict(name="Χρυσός Δράκος",  color=(240, 160, 50), hp=4, speed=2.3, dmg=18, reward=4, r=22,
                        photo="golddragon", face=1, voice="screech", fly=True),
    "reddragon":   dict(name="Κόκκινος Δράκος", color=(240, 50, 50), hp=4, speed=2.3, dmg=18, reward=4, r=22,
                        photo="reddragon", face=1, voice="screech", fly=True),
    "spikydino":   dict(name="Αγκαθόσαυρος",   color=(120, 80, 220), hp=5, speed=2.1, dmg=20, reward=4, r=22,
                        photo="spikydino", face=-1, voice="roar"),
    "purplerex":   dict(name="Μωβ Τ-Ρεξ",      color=(130, 90, 230), hp=5, speed=2.2, dmg=20, reward=4, r=22,
                        photo="purplerex", face=-1, voice="roar"),
    "franky":      dict(name="Φράνκι",         color=(60, 150, 70),  hp=5, speed=2.0, dmg=20, reward=4, r=22,
                        photo="franky", face=1, voice="groan"),
    "bluefrill":   dict(name="Μπλε Φρίλο", color=(60, 200, 230), hp=4, speed=2.5, dmg=18, reward=4, r=22,
                        photo="bluefrill", face=-1, voice="chirp"),
    "yellowfrill": dict(name="Κίτρινο Φρίλο", color=(250, 230, 50), hp=4, speed=2.5, dmg=18, reward=4, r=22,
                        photo="yellowfrill", face=-1, voice="chirp"),
    "orangespino": dict(name="Πορτοκαλί Σπίνο", color=(250, 150, 40), hp=5, speed=2.2, dmg=20, reward=4, r=22,
                        photo="orangespino", face=1, voice="roar"),
    "greenspino":  dict(name="Πράσινος Σπίνο",  color=(150, 230, 60), hp=5, speed=2.2, dmg=20, reward=4, r=22,
                        photo="greenspino", face=1, voice="roar"),
    # ο ΓΙΓΑΝΤΑΣ Γορίλας: πολύ μεγάλος, αργός, αντέχει πολύ, δίνει πολλά κύπελλα
    "gorilla":     dict(name="Γορίλας Γίγας", color=(220, 150, 70), hp=14, speed=1.6, dmg=30, reward=10, r=40,
                        photo="gorilla", face=1, voice="gorilla", h=215),
}
PHOTO_POOL = {k: (1.5 if k == "gorilla" else 3) for k, v in MT.items() if v.get("photo")}  # σε όλους τους κόσμους
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
    h = int(t.get("h", t["r"] * 3.8) * scale)
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
    lift = int(hop * 9 * scale) + (int((10 + math.sin(ph) * 4) * scale) if t.get("fly") else 0)
    surf.blit(img, (sx - img.get_width() // 2, sy + 20 - img.get_height() - lift))


HERO_T = dict(photo="hero", r=16, h=80, face=1, key="hero_photo")
HELPER_T = dict(photo="helper", r=12, h=62, face=1, key="helper_photo")


def draw_hero_photo(surf, sx, sy, aim, walk):
    """Ο ήρωας του μικρού (κόκκινος με κέρατα) με όπλο που στοχεύει."""
    f = 1 if math.cos(aim) >= 0 else -1
    ph = walk if walk is not None else 0.0
    ca, sa = math.cos(aim), math.sin(aim)
    behind = sa < -0.5          # όταν στοχεύει προς τα πάνω, το όπλο είναι πίσω του
    gun = lambda: _draw_gun(surf, sx, sy, ca, sa)
    if behind:
        gun()
    draw_photo(surf, sx, sy, HERO_T, f, ph, False)
    if not behind:
        gun()


def _draw_gun(surf, sx, sy, ca, sa):
    """Μπλε-ασημί όπλο-blaster στα χέρια του ήρωα."""
    def pt(d, side=0.0):
        return (int(sx + ca * d - sa * side), int(sy - 12 + sa * d + ca * side))
    body = [pt(4, -7), pt(30, -7), pt(30, 7), pt(4, 7)]
    pygame.draw.polygon(surf, (20, 30, 60), [pt(2, -9), pt(32, -9), pt(32, 9), pt(2, 9)])
    pygame.draw.polygon(surf, (60, 130, 230), body)
    pygame.draw.line(surf, (170, 210, 255), pt(6, -4), pt(28, -4), 2)
    pygame.draw.line(surf, (20, 30, 60), pt(30, 0), pt(44, 0), 9)
    pygame.draw.line(surf, (200, 205, 215), pt(30, 0), pt(44, 0), 5)
    pygame.draw.circle(surf, (255, 170, 40), pt(44, 0), 5)
    pygame.draw.circle(surf, (255, 240, 150), pt(44, 0), 2)
    pygame.draw.line(surf, (20, 30, 60), pt(12, 0), pt(10, 12 if ca >= 0 else -12), 7)


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
    ),
    "skel": (
        "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"
    ),
    "yellow": (
        "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"
        "YII="
    ),
    "pinkdino": (
        "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"
        "pXxkS0JjWNIyJ6GyBpSloqJCD728jjCR5kLMzrN9Pvm8F/ptaWXhuwxkTFG+phRpcKhJZhQ6cX6ypcU7hy0MyiuOtys2sWcyNThv"
        "CCHR9gM36oKKxGBet53cz9m06iUfh6nnd939W3xcrQgTy/Nuw8oPUlwWBgrFkALP9kteaFcMasSXkVFHei/tzZAiPo5EGxlcw9hu"
        "ie1A8pF07msyevm7HyGOKBVQJtI//RxsNqR+YH18StSgbRCPxOzcmzoRa07nrWSfoBCSENYSlUVTUGCZYJlRk7BMqaiBEZ+FtwMe"
        "d2HZ0GcjHoOSofe5EINrxS9+tZIUa3QSKE0vSIJz4Oi5Rwcpw1KiDPJCRimHrIBbFajCMgyedhhRSlEqQ/KafgjsFRP2yymuDfxm"
        "rvNLwI4eBMdn4fS42J4Glfgjm3/CfxP+KfM3zDl4ww5nqmFMI6qA436LjZpRiWX4ahhZupaTYcutzYpV7DnuVgyqY7COk7MV665l"
        "KKPoxYdETFlF1wdUAh8S7nSFanuGu0eovsUWBr9aowykFGUeEnPaMjiUycw9LSeRCh6rRCjiwlU1qwsqYJJ5jzr7hQjdzOe0aqTF"
        "5WBpOUsNz25u49Z3hW5usle6DWLg2W1AR1L0pL6naZaEppPAUbmblbJo3XYkNYP46GbLND948brRhnlVU2pLbSwTKq7vX+aLbjzM"
        "JFl+7fQ6k5RetwHyuTjn+HSPP3o+AwHFMo38/dUvcGm+4OHtnL4ZaLsBbCJF4c23racfO1CR3d0ZZ01DWWq2w0DSmpgCySi2Y49K"
        "kbqqSD4KbDuHo1KaFANjcCxTSztsUT4wLyrGcST5gJ1NYAyEsxYVE8rkwWSK0sodR7RWFzKoPnmsEms3pWDIjkc1moGezYUFtRDK"
        "Qi7cA4GOnnVWBFutV+x5gwkybEzBETctOjrSOODjiBtE5LkoLcml3KSKKGvk9RFJIc/nPXSjpx8CpbJ0zjHGSFkUzKwYjBa6wEaN"
        "SonBO96+u8dPjkckpe6fU70uZh/qjTc+n3/HHp+yO111Bb+1/zweD/vsxgJjEhOrcGt34QCyqKd4n5gYy8F0hvMBN4pbVUyRCstU"
        "VSxsRVnUoLO1TdfT+xEfPavYZMVGxZsm15kt5sSY0GMiVRZWI3o6gxvCG0m3llKjGMnvQwjoqAhxoLAVUSX6cUtPj1cJlTx3OeIX"
        "uJWVocTIs6I+rzQuiGYFhpbEZX2Fy3tXmNYzDIp2s+Vwe4pVsKemDARUgKvFAlPXxD6gi4QqDTHKcDTGJN3epNi0A9aI0dAqDFSF"
        "YTEts1PbSMKDCRy6Nae+YbXbcXpD89+efCj3214/eKt/F4Pj0x/hKXI5lfyBR7+W6VOe5D2LMTGOPU0aqSiYqpL9csJiWtOMgWH0"
        "Mg80JXUw7NqKGITzVMTE1rVZLNRxypYq+xa2JKZFxaOTA6yqiC5RFyXqyg689VGZR3zkkNiOuLHDGkVSCuPivYGcgmFoqcuK1o+0"
        "vgUGfpYPc0pPlXWHQVOrKruHWFRWhbRJMaqEA66Ya7xt/hh7quJ4c8rKb5lSMs0i0IWt2J/sg4MUxc1WF1aEo0eHd2JbFmIiJLEl"
        "cwpsqdnfmaCUwjvH4D1D7GnCQCgjx2XDemfk41XLnzr7SKZPvz4C5N/l4Pi0QWJU4tuqN/Luo2vsDBYTkbw9OLwKDEQWdsJOMWG3"
        "qMFHtIZSGUpv8V246E0aEkMas7O6zAIcHrFrEUnMWk95k3qEy/v7qKsH8EVvgLMVPH+W7altJmtJpygNDrqeFOXUysRg1q4hBs+K"
        "Q/41H0NjczAUzBD92XNbT5+5GAJDN/xEecjNQjNRNdbA02zYDQU7yfLtwxv5Mn+DpA1zXWOTwRQFsTT0TU+IjkIptDFCstSawhqa"
        "4CnqgqIyxBQZzy2jVcSngTEOnBU9L6g1d6uR/7f6GM/G8UFwvP4DJWFD4mC0POYnvMnP+XX+IXZCKSbMCSo7IRQRlZSIhWjNji7Z"
        "tuJqpJLI5mgVmCnLMrYMOGHXZfG7U7Z4PLtc4sve/NUU734bvOUq/NwzcHdzIaqWVgPKZxu1rid5h+sGYgb7lloTfOBk2LDkLu/h"
        "oxRoTpXnqWLkA7VjJFImzZ1K1txgFDbKKCMY84telm9YXeXPuq/lVPXYaBlSYM9M8d5TFBpbiP2btkLsSkG6ZBgtg0EfsEbRjwMh"
        "i2iuhpbejLS250h3HJeOP50+wO2sdPZaB4h9EA+fRv8KhTeKw0nkkIafpeGvx9sUUb72hJ/ym/yTvHEzR5P+/+2da6ymV1XHf3vv"
        "5/bezv2cmTNDZZgWWuiEGgM2Ni1yUaIoiWBC9UM/GWJCIAJi1A9qCFqFxBjjhSiEWwIhKlCDQQMKGsqtBVILvdAydIbOdM6cOZf3"
        "9lz3zQ/7mWkLQxjbufOuZJLJ5HyYc85e7157rfX//RljGSQdnAlr2whB4Rq8d0TeUfkKjW0/rcM+V9UiMiMhKPwEsX8VDh0IQ8XS"
        "BBcnoYJCZbEXtBjbIwBsbTEGZCTAW7QPm7GpiNAoMq/4m/ldTnbj9ts6+0Ray3P7sfzH/Clua+7ii8XrEVIwNE1oDEQSJSUiSRCn"
        "19sFiCxCGUddVmdA3da2ju4q/IgjESG9w2pJJiPmYsub1Yt4p/5fGimf+oElZq3cy6v1+8O/ECnRkURHgkezkr/qP8hb177Kh/qP"
        "0IkzMhcx1CUnfM4umlgEM5bdtoNkoKVB+jOU8UxENL5hdekA0f69+OEUvvZ9aNrdKknQmy/12tZuIKR4D2kcIYXAWYsQAiEFpbDM"
        "ecl753Y42U1+3LkS5/DnTGwkmhv7H+cD7j4WrERlGUmnj8wGgdOV9QKGSCi8BWElkYlRGpQRKBmB8HSzBO99sB3wnqrWFFojUJSF"
        "442dg5dFV3eWHOeeKGdNGKMk9wxGvGnpS7x37ltEacaC6KOt5agfY/HkrXN6RkxOg8ZRYNDCs0uFjmKuv+GleK0RWwX+yA7u0eNB"
        "OzJouVra4p3FlRVeCqSUOO9ptA4rK94zqRty3/CA2OZ4N/l/fy/nMidqIsGdyw/znvReUtFBRzJo0q0A1cE3AlSG0Aq0J0piUBFx"
        "1CGTMa5xaONIopgkDhzjxaTLWtxhtFlQjHOWypSDKr3k84/Zm+M8P+aF87xQz/HrxUFWm4SxL+j6UK1lrb9d3PLpg5GP59W3/BqD"
        "9evxAoT1cGqIVyAiETZg6yq8PaYmQNgwlJNpEPd5j5cWbWt2fEHPK1679F/sphek6+OfYgHGp/PXcl3nemRiUCVB3NWJoCzaBcXW"
        "GSxNQkOhqbA+LDEGwqFju8gpI4NVlomtOOWGbCZBdPZn5n6qJ+W0YnZzXMHTdwAvBQ+mE961cB9/t/QgK/E8VkgQwVNboShwbDKl"
        "EY6XH3oVg5t+Br9nHlHZIK8VhCFbWQcduWlXN6Zl8MRxDucEUSTJsohYJORoIu95b/btC5UYP8hf4q74MHFvAUMG3UEASBgbsEBz"
        "GSwvYFVMszkMehEhkSJGOoVywXc3S1Pm4oxURPTSjMTH7Et7uHHJ7frSrpfMkuMCJQlC8J04523zX8Z6hfOCMQ1aepwQzKser775"
        "NSzfcgt+cYCwJhysvApCo7rBbY3wJ0ewWQQtiFSI2uIaQ5rERP0UJxQ+ClYQOxR8dGHjonV6Br3gcyilgueswHP3BGjEgX3wU/sh"
        "SkI7eb7fruNLRBIhVAxWUlUWaz3WeLwX1LVjoPr0bcJi0uP52TIdOXtzXLVJUkbwB3u+waeWj9HPOmy5ipGfcPNNL2f5RTfj9qwh"
        "Tk3CJq9wQZnX70JeIVfmEEtzAdRQm0BRzMKUW7Udsdpqtk1B4yzv7N//JKX9wpSQZz69I+f5zewW7HxC1J0LenSnYDAXNCkiAh8h"
        "9q4hVlbCv2WndfsSESt6vZRYgRCeiISeDHOjjlB0I8l0VPDL/fVLdnvMkuNiJImUfCnZ5QODwzxnZZGX3fwa9t/8SlxtkafGQWQ0"
        "KuHF++DA6pPIf0RYh1ftQuKkBCEQWYxTAoyl8Yahrqmk4YFedaFujacdyoM24+G532e5ewDpPKKTha/Ymob2cxIHnYs7LeRqpbRC"
        "BpCFCG8payxCKuI4xntPpGKUjIlVQiITCm25sZhj6elr7X4257jKQgr4pRtu41VrrwR6+NEQaYDv7gYEUK7DY3YuC8jQWgQN92kC"
        "o/P42iAWMtAEL3gMtQucqs/FR/FSXvCmw21ihQ/2f5tKdUkHKWJSwPpKcKYqSqiLoFXZbUVUpgXonXbSpVUSyhiwRE0ARcQquHtF"
        "KqHQJVp41noLNFXNHYPn8dfl4Yv+Jp8lx0UIJQRf/dV3syj3o9cXiba3EY9v475zEim74UbopTCsYHk+sHZr25rHtEaVxiJiFYRG"
        "1qKtIW8qTGRxjeUTnaMXtjsF3MoKHxy8haG1zO9fR+QeMmCtD8s9GGfweA2TSbgtpq0BTywDTLtqcT8+QOqUDNNzJyDKYnr7Mo4f"
        "3qQRhm6asmAcE+VJStjjFSeFu6iDwVlZdRHavJ/5xT9k0c5TJRVx3KJyjIPG4nemoaQa5aHc2JwE2WmjzyjvXKkxlcWdFh91BLX3"
        "WC+omgYVCY5kzQW9MV6m9vKh1XcwEYqFG65FLA6CyKkbBR25FDCehNshS8ONYV24+aZ5kARHHt/UwS2yqdBNTeMMeEdpPSeHBbmr"
        "iToqOPkqi3OAhjfEz2tX5Gc3x1UT+7vzXLvnEBPRMBh7uP+xQCs5PkRWHqqg6RBOhY5OWcLmdrhN8gKKhqqsA1BBeCo3ZG1hQKwE"
        "U+FZkjF/mXwDJ8UFSQrpPbdnL+Jdy28kjxSD69dDYj92ChZj2LsQKJFP7MLGbiilmtPe5a0lmw7NBnFacQk47/GJIhaKwtSMxtNg"
        "k65gczSljBoKoQMIX3jSWvDcKOGoN7PkuFrizp/7DWzi6Q41bJWwVeCP7CKMDHvtjUMsdIM34A3r8L2TAb5QBhhcMc0Z+ilTNHtl"
        "j0hJtnenZJECGo6ZEf+0+MRTi4DzliUH6fDZvW+B5ABVV9LbtwoTA8e2YX0RXrAcGFzeh45a09Lrx2WLN6pCM0G25BYRPNC9tQgV"
        "zFVLE2RY3Y7CxR5jPUIGiLez0CSO3aYgQZCq2ZvjqimplBD87OJN6MObZFa2bKtJmFtEAeDmvEXGMtTt+xbg4WOBcaUtptQ4FwSv"
        "ESDimExKCt8wqnKsb/iiOt76Kp7fW+MV6TrvW3s7lY9hTpItLwWIRNnAngHcsBTeEscnQV8yGodbz54GMGgwZcsm9kFlGAXyorUu"
        "AEyFo3aWqa3JqbHGMKFGdiC18PikoqkgbsBngkd9dTavwFlyXIlxcHGVOJc0G9tg4wCGnjYIGYeDJgXypn34ukGsLMMjm3Bk6wzW"
        "xxuLEOC8Y9/aKukgptwqiCPB2BlSIbg72zxfD/EzibGPlPetv43tpS5Li3sQDXBiJxh6Lg9gqRMaBuPiyXdSYwNaKJEt49dAHOHL"
        "HKECrd4YgxcOJQRGB+JK4wyNcOS2YWJyhr5mVJV004hMKCam5DPZCb4X1/iLmBiz5LjA8cq1F8LODknjYClBb+9g8xqlBbFwwdzm"
        "2kXEbhUclZom1O9RBLXDGUvhNQZLum8OU0xxwuClQwtHJRseTqfno5J6crjn4Qsv+CMme9dZ2ruMKCycOBVujH4vdJwmBPj07ihY"
        "OhQV7T56oJjggk+7dggh8M6AEhgXulRaeowE6wPCNHeaKSU6NvTjjGlpqazlY/Iw35trKSyXwP1plhwXMF46/zxsE0zuq7IiO9EQ"
        "F2lIgvUBvHgR9s8HCvtwGhb1ygo3yanzAiUFE1MyocGOc4zWFKZu9dk523LEVD3rrubTlgnf/9w7cHsOkB1YQUgJhzeDmehgobVl"
        "qENpsz0KDYNKg6me5FxJwrJh24XytqF0BmM81nuctWhpKJWltJqhzxERZFJBFvPf+hifjU6wrVw7t7nQ5qqz5LgkUXmNcg5XVmSH"
        "a74SfZeP7H+I6+I9vH31dbj1DsrpsDayNYJG44dTXFFQmBJNTU0NOIrxlFFd081SjuxsUPiK+9TOU98b4tkqH/9+9Ve4de3l6L4i"
        "TiI4thNKvCwOqyuFDfzcvAoLkk3ZDvREsGbTOjhZeYuzDucDvXeznCAyRZpJStNgsYyrgnGkqajpr6Z8sn6Mf2s2cFK2vQV52fmQ"
        "z+I8xlu//jE++pLfYnEAv5PdxUPNFhSQ71WI5Q66lwRggjdQ5fhpjZ3UFLYmp2RCzoiS+WhA6R2NtQyHu2yLgqmruFttnadSyvO+"
        "Q3dwW/fnqXoR2eoSnMzh8Z1gDZ3GwSq6aTtOk9ZvxLWmP7pl7lbVmQm4cIbC1ORU+NhTypLv5mOyVFF7jU8ttTT8o3iUb0/DWsxZ"
        "GgtihgO9SsM4z+33vP+Hftsffsmb0CNHenwcPp0LDVioaipTU7uaKQVblBRYOtIxEQahYOwKJl7TkZInEv1M57hPuzH+5eAdHEpu"
        "pVrqka0swLEhPLoJBxehQ/AjLNr5hWvpJ3kB0pzxDwmOvXVAEpmgL/HW4KRjJEu+r3cpY83ebhcvHV8xG3yc41SXuHSaJQeXUov+"
        "9LhxaT9iDE1ZEO9WQbxkHfnmCKkdHs12i11r8AwxxK6kyT1KCiopiKxnJ2vIY/GsE+NdK6/iUHoj1foc2cpqmFtsjOCaRdg3Fxxo"
        "fWtJXdfh4W1NuCHyql0NqUE6XG0CWkdacqeplKZMCjbLXUTXkySCL6kNPmy+j5XysiidZslxGfiEnD6UQrc+F6d2aE4WKGOw2mK8"
        "xxjDkDE7omLqa4aU9ESGVJLaNYytZmimWGH5T3HG/OUZH6rfW38Fr1U/TbU8R9qdg+0x3H88WCzsH4TJ9rgKJVOZBweqNAnlVFWE"
        "pKnrcMbbzhTSUdCwwYSOgi1XcvfgFF+PtjlORW7F2dbqxcyCYBaYloV72iu8rhq8h0lVIpygwpDTkOOpgb6KMN5Ru4YnzIRGOLpJ"
        "wj290TMpqc7cGs/Plni9PIRfXiJbXQ9l0sY4gBzWegGCXbcCLG2CuY2UrftVgFJjTfi787i6AWEY64LtpmAQSz7rH+Pd3QexSv6o"
        "HBDM/DlmcTpUGmFNibY1aQdM3nB0uEvXC47LHR7Ye4rMKcRGi9mxhsI5hq4gRhHLlH/oP/SUA/fMKqv3rL6OXn+RdO2nwnthcxKO"
        "6jWLYZlw2K7LW8Kb6LRfYZOHQZ9oXaK8wVYNRTWliTzGaGSqeXP2Fb6dFT8qgcWV8LuaJcdFjm4nQxnN7nhIrRWy0GQI3r//fv7Z"
        "HgUvuT5NeIM4yAhLQ0Xha+JIcW/nFJ/PtjDRs2PK3tjZxzVyFd/vhdHazjgsDO5fBNt6pxd1uBVqE0ooq8E3rQ21biEKBm0rnDZ0"
        "VERhK/50cA//nm48teS7ohJilhyXML658RhH1p9gfTBP1Vi+lRznHaPPs+3cmVr8aFlglzSdYQdtHSqW3L26y91+5wc/iZ/Rgbvz"
        "utsZdAewsACRgJM7sDof7Ae0hs1puDGqMrRty7KdeOtQmE1zKhFwnolRWKd5t7yXT/ePsxu7K658mqF5uHz0HQLPdekiR+oRmrMe"
        "JvrOsUfHTJwlTyBX56U08ZlUfPO2P0fHiq4aIHYqODGCa9eDic+4CBZo1sNkGtZGqhJXTDBNydQZlvoZTVkzFRWfVof5C38f+uwb"
        "s+JK/oXNbo5L0N71CB6th2c7P2e+Ziol09Seayfs3P8TXpCICG3b4WNdB/POug5qvd08rLHY1inWNNA0bJ/axkSWjlc8wog7o3v5"
        "mjrV4kTFVZUUs+S4vOYf4lxmJOfj0Fnv2D62SZZJRI/w1sjSkByu3TysqrBhaz2MJkxGu+y4nGvcIn/S/zKfSo+c7U1x1STFLDku"
        "n/nHRT1kDZaRGTFfLaCHJ4kaiVghSPCmNUwb7LTAeY3sSobVCFE5VlSH3+19gc9lG1ftTcFMQz7LzX+NvoNWgkYYtNe4vACtsbqg"
        "slMKUbJZDLG7U5b7A/524T5uXfkkn+ts8GNhdrPkmMWVHHcd/yY2U+yWFSYSTEYTyu0xykCmBU4LMpXxCfsIL3Uf4COdR9DyJ+O2"
        "mHWrmHXMXpCu8sfdX0BUDtOPWdg3z/9sPcBXTz1KXTc85LcppLvq3xWz5JjF+SAGip+0H9TsQT6LWVLMkmMWP+mHffYgn8UszlP8"
        "H3tSjvG0owwOAAAAAElFTkSuQmCC"
    ),
    "bluedragon": (
        "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"
    ),
    "golddragon": (
        "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"
        "+D8AHVwXPwcAG0gAAAAASUVORK5CYII="
    ),
    "spikydino": (
        "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"
        "QmCC"
    ),
    "purplerex": (
        "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"
        "YII="
    ),
    "franky": (
        "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"
    ),
    "bluefrill": (
        "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"
    ),
    "orangespino": (
        "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"
        "YII="
    ),
    "reddragon": (
        "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"
        "RK5CYII="
    ),
    "yellowfrill": (
        "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"
    ),
    "greenspino": (
        "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"
    ),
    "gorilla": (
        "iVBORw0KGgoAAAANSUhEUgAAASIAAADuCAYAAACd4wrNAAEAAElEQVR42uz9d7St6XXWif7e9/3yt9LOZ59Up7JKpRwsybZsOQvj"
        "tsAGDNcYm9QEYzBwb18u4NE23bdv01ya5jaD0EBHTGyaZEAYbGzhqJJklVSliiefvc/OK335e8P9490qy7ZsbFOSLHk9Y5yxz9ln"
        "7bXX+sKz5nzmnM8UD+++nhVWWGGFzyXk6hCssMIKn2sEq0OwwmcI7hf5vlgdmhVWEdEKn0sS+uT/udUhWmFFRCt8ViCE48/+F7+f"
        "1732QcJIrQhphRURrfDZj4a+6zc/yce////NW0ZH/Nlvfpxrlwa/0uhpBVYa0Qor/KpJSErBH/mOb+AZscei67io7vAbf8cmHz+9"
        "yn//w3f4xF6J0e5Tf26lHf16jp5X5fsVPhOa0H/1e97J104OcNUpm1e2IIRSOeJpwc0Xj/ixcpf/9v0HGLMSsVdYpWYrvMoktDaM"
        "eP93PclXVv+enBmbX/Yk7k2X4O3XSB+6RE9I2Vom9z/MN755Y5WirbAiohVeXRL6ne9+gKf+m3fy4PiI9Qd3UFmIPThGVBZkjCtK"
        "5NkpEkcix3z1eoUQK/5ZYaURrfAqEJBS8Dd+xyO8520xzfQWSgoCLRGRgrbFfuxlZGBBhqByaJaQxOSm4/UXh3xsr1hpRauIaIUV"
        "fkUE9HNIKE8DfvjPfDHveecaTWUIzk7RJ0eIJAYpwYJMFHpacPzh28wPamaFJTaOftbzXW/ZIghXl+GKiFZY4VcpSH/tux7k6b/1"
        "TVzaAdP0JOUUUy7BGGxXYZsSUgtDR3N2Qjebc+NwThaNuDzeJEkFaXXE//Mb37zSilap2Qor/PIJSAj4osfW+SPf8Djveus25f5t"
        "EkBJBZM1lOwobt0hvLCBfMuj8MAOSMNAt9hyj+NDS91rRplkMs742K19LpCSRIKmW3HQKiJaYYX/SBq2NY754J//Wr7/Dz7Auy6d"
        "UX3kJ8huPY+SLbz5cWhrlrfukiQpKh0hLz4E25dAaEw5p6wtx4uGXmuev7PHfG7YTHL6wxf5jjcPV1HRKiJaYYVfPAqKI8Vv/8rH"
        "+J5vfhATljQvnRIWC7K1HFwP4xwnHGJnjeHBkOZ4hrl3SvADH8BNJDxxCTXZYHr/BY5PFdqW3Dpr+PI356SxZHqiec+Fkv81FjTt"
        "ioNYNTSusCKgT/mUUvB3/l9fw9tevwbFPs3xMWFZoE7PYGsTdA/OgLDokxkiDlBRSLt3HykjRJ4SYHBBjFgb0tw+5emPH/Hc/px7"
        "C8tgEHNpc0gShlwcKf6X+RXe/+zZalJ/RUQrrEjI49ErY77/T72T9XafZdOSrG0SKgGxgv17UCzBWmgbWCxgkuOKEloNScL89j5F"
        "b9m+dhWlQYYKtKI+LbkzrVk0hntnNePxCAQ0i4aNJ57gj//YguPTamUdsiKiFX69k9D/9n//Kr7kYYuZn0JVoHJg8zI4C4d7cO8O"
        "TMb+j9XQNdC2/odP5ti2xRpDXWmssSgBMk7oasdosEbvAo7nFXXrEGFEFEcczhoWVUN87Un+xA/e5mzerMhoRUQr/HokofEg5m/8"
        "sa/lbY8Ylvs3GHYNVA0Mcx/5YLDLU6S2sL0FsxLyCISFogBjQVtYlrA+xmrL4uYe4ShDGEHXQNdBNl5HW8Fs3tI5iZKSOElZ9JJS"
        "G/p8jX9xNuAf/YfnV2TEqmq2wq8jEhqkIR/+K9/B2yan9EfHDGc19ALCBBYVnJzBdI4oKriwAUUFkYJFAdMFru5hOIIoxgmFq3vk"
        "omJyeYd8ZxPRdwihyUcZRnf0rabtGtJYkoSC49mMW0d7bO9OWAsdf+Axxe/4qjeuLENWRLTCr6t07L/+rTSLF2lOFoS6gaCGiYIL"
        "CTw4gS9+HL7oNYitDWh6mAzhwQuwkYEztIsl0+depi8qiEJEGOBwuL6HtkcCTvckeQimI1aWLJKYviFQFuVaUjr2XnqBrTzk7M4t"
        "vu1Kw+/+xi9akRGr8v0Kvw7wX/2ed/DGSyXNrCXZSeENl+DKO70I/cwnYGsCD16GGBhIT0KqBxuA0lCVJK9/HcH1ffrrB8g4Qg1i"
        "eGCb7uMvE21tEI5yOClol0ukACUkqXIQB/R9i7Q9W3HA5nrG3s1PgNYsbpzxXV/yNTzz4iWeen5vdaK+gKHWhzuro/DrOBp687Wc"
        "P/fVIWVgyL7sDSC1J51hDs88DVsbsLUGeQj5BDaHcPHLYHMAsYWrO/DQFlzZQLY1YdEh0xh2txBrI4JFieg1YnMNlcdE0hIPMghD"
        "2sKnf0kYkkaCvmvQxiINJNISqoBbN2/wvkdHNOuX+cSdk0++7O8Fvm91GlcR0QpfACS0MQr4R/+PR1m2BcMLGezP4HgBzQswm8Px"
        "HC4qmJegOggkGAHJEnLp07Y8g6rwX1/3MCxaX8J/cAfuHUEagoihbRFxBF2Pa3q62lB3DThLHEuqqiAQBula1oYjjpdLnKuIesHs"
        "9kt869ZlfmwccX/erSb1WVXNVvgCISKlBP/+L309w2aP7N2vR+3dgY/cgt7ipEN0ln5ZEOQpDEPE8r5vYAxSXN8hNobw6Gvg2gX4"
        "xM9AD7zlSbi9D3fvw2jsFciPv+ArabUDJXCBQ88aVLqOrVruHZ5hrWW2bKi7lo1JhrUgghQnJGEQUpmQsmrY2L3EN/zLJc6JVRVt"
        "RUQrfCFEQ3/xu7+K971W0E8LwkT5knvb+obFKMIcnCBDEFmGPT5DXsnANOAUVC3USyhr/4zDIYScE1UAcQTrExinuKc+gjua0fY9"
        "ySDHGklTVBR9RECOETCdzgiDiLPFkvVJTtN1FE1PEqWsDYc0QcDZwrKmFD+dP8r3/Zvbq5I+q6rZCp/nePzKhPe9OWf58m1CFEzn"
        "oBVEI1ya0d7aQ4yHiDiBtQz5wLYnm+EIsgBC7S+d3Q0YD32j48mp7yVaLrHzGcynuI88i21rDBYVSIQIUElKoiRxqJGiRtqeLInR"
        "2vDA7hZJIEmCAGkttm/pupauasmkprGS965LBmmwqqKxEqtX+DyPhv7+73uCtF6SEODKCnk+ZsEoQRiDevASMg1BAXUFpoVUQChh"
        "mEEWgpL+Y2xtDMaA7qDrMcuC9vSEUDqQEhkPkFkAyxp56QJsjpCjlMQp0kGG05ZeG6y1xFFArzVl3WIBIRVSKJRSOCwHy4rOKL7x"
        "t38z/+cHnvnU9/a9rMTrFRGt8HmB7wV45NKA7/qj76WdjBEvXkdKkIMMnAMpMEmM3BhDFsMkgJGC3TV44kGIQogCsD3sTGBtCIs5"
        "JBE4Qz+d0pYlURTjeou6cAFdLKHRqAcuI17/OFze9tO0jYBeYzuLMZYoktRNy2xZ44BYKZx2KKGomgZtLQJB1VbE5ZT06sN87ObR"
        "p76/FRGxqpqt8HkSDf217/5azHRBtjyDQY4Y57jZEr1YIAcj7t2fcuGRHcIgwF3Ica99lGAU4VKF2NmCl67DzjpUS09Aa0Ofks1P"
        "aJcFwgUYG9BNK3J1iNEdYWcRV2LY3vY60uF1WFaYpkUoQdv1SCVxeHdZpSR9b2ibDiEFVdWyvT6m7XrqtsLeeY5vegheeGSDD758"
        "uqqirYhohc8nPLyT8eBuQrlckJ4VyPEQUxacfvRpytMlrQmZPPkoL/7gB+mWDTK17DyQs3Fpjfj1D+OKAvH4JTiqIIohcHB6Bi/c"
        "oL99QCgiZBAi04hASU7u3kdKRRIHdB94mvTF+2QP7mLunTI7njMc5nRNS9P2GBzOWIxxaK3pjWEySPyUSRjQa0MeBaggpLNw/8az"
        "fMfFyzx9W9D2K5loRUQrfN7gT33Doz4KWS5w9RJ0R/vc8xxff4m+10RRSv1cx2K2xBrINdT3G4737xN/7BMEzjC4ukVoLVzcxmYp"
        "7uVb6NNT5qcFKkkgjhhGAYvpnGx7ExnA/Rdvs/XFbyecndG/cIu7d6eoOCEKFF3VIoC26wkDxSCLaTqNBZre0OEYZzFtrzFAEiQ0"
        "TcO8h0ftgoujMTdP+9XJXRHRCp8PaZmUjjdfiJh95IOs7WwiQ4m5d4/54T100xMKqOcNdEf0laHWjid/67dgbr3A/PkX6ehAa+zJ"
        "kjAJEC/s07U9o0HA2aLHAbavyYOA4mRK1xlGXU/fOMbjCaGB8M1vov/AT4MzCGM5XdakUcxkJOlmGqMNWRxicRhhaauGzgjqs4bZ"
        "wjDYkIzWFCKQbMaSRmt+w8Mj/urp6eosr4hohc8HbIxShmsRZyc15XPPkacJxf0jdNURSegbEK2lcx2phkuPXsXNOs6ePyGSKVkU"
        "I9qSvtGUVY+SgBIkCQwUqAjc7kXyy1fQVc24rTFdRywl+c4GdrnEXb+NbTq21kfcP6m4f2wRtORSI4TjbN5y4nw0JiX0JXTCa+PW"
        "gK4sOmtQSUoQB+i25gG1XMlDKyJa4fMF73ntNqo8Y/jgJZL7x/R39rDLEtd2GCMwDtLUESchZZSwtbnNvR/6IU6rkmEaYWSHLXv6"
        "Q8gvw9qGoG4d9w868hjS9Qnj97wbjqYEQQgM/abX2RxChewKXFUSRAEnRwXT05J27ugtLBykw4CHdtc4mS9Ylo6itNSlnxwRAlTo"
        "9fHRumRjnDAtGrQxbI8dcaRoO7s6ySsiWuHXOs7KClRKf+suidYsTs4oZkvGecp0tgQNl5/YINneZVFqLI6dNz9JOp1jmyV3b+/x"
        "0Lu+kvWLQ2b/9J9xcuZwQLY9IlsL6LSjeuoTqECg0ghhHSqIkIOxd3CUoBdzrGvJM8n2ZkrXNtRziwpABoajRcEgTanalqq2jIe+"
        "XckYH/MkIZyeLVGZwDiBFBFSSJzTqxO8IqIVPh/wwPoQkhG2vUt17y5US5qmRmjFOA+YPPEYw/d9HeQTNkKFXbTIhx9k/EM/xg+/"
        "/0eYvPs3Er3zHZjXv5WrX/Gl1P/7P0ANJeHAEEWWptHEi4rytORwviCOIwZJTr45RqxnuCxDzpbIJGW8MyE5qljfgPsnNdoaLj64"
        "y9l0jp7PQBdc3vZRUN9BHINDcDZ19NZxeLhguD2mN5pYqdXJXRHRCp8v+NNfcwnm9xk//hAmNDT1y4wGMelgg9Fv+FLkF73FOzJO"
        "LuOiGBZL3MUdznoIdi8z2LzEP/lHP8xPfvf/yF/9n/4k/WOPM377IxAWdM89RwpweEDW90SDDVzbU1c11qQokSE2hqhhCkICgsRE"
        "RIWGLOfe/TPC3YuM8yGHp2eMJyG5EPTOYQeSKA7psBjVs3eiUVrQtY5snILTWLsq36+IaAV+ra2C/rS4sustPoRDjQekgxF5NiR+"
        "zePw+kdwaxniqIadDcSzL+JO5rAzxsmGtTTjv/vv/w7r2xO+7du+CLX3CTavrDP/iZ+ieOF53PEBeZqSbIxBOeIwQgwGGDvFWIO6"
        "dgne8AS8cB373G3KW4fMZjVZkjFvNAGGGz/9UcJA0hiLCiJIE5Tu0b0myFLSJCQeasJhzaLsiJKQOFAk2YAgmKONWV0JKyJa4dcC"
        "AYVKILA4BEIIrANtHIEChKbfWCM8vg9JhhoOCb/+y3y1KYsR1RL7M8/gpjV905JcfACmZ+y+60nu7H2AP/xtX8o7/8BvBuHgIx+i"
        "+MC/orl+ncUZJBkczlqSszlhHrK5u01Q9QRK0Fct0bN34ayjvn6T+Uv3WFSak3mDVYIsCQmSGGtD4iQnHA9ZVIZwPMHonq6qaZEM"
        "kpxS11zZHTErKvLJkHv7c8hWIvWKiFb4NUFCaSz5zi+/wh/8mqsQGJiW4DQsW374NOat73oIuvvIRQNvehxeukOUKtjdhuEAlIK+"
        "Q4wUXH+G4+fvctIEPPLmh8jXU97xje8Apeie+SjqmeeRQUc5PaBWQASzAiIBxjp00LNclvRNj4oEQirKF69jP/48ddszX/ZYAUms"
        "OK0NYWTRvWZjMqTTEGQ51y6tY6xCBYrLseT0+IT7x1NCKTAhhEGEcLAxzjlqC8zPRkNutfVjRUQrfJZJSEn4M7/1jfyuxzTogurs"
        "Ls4pKBbYokJFPV8ZW+z1Gbz9MdTBKWhgmOCe+wTc3US8+0tgbw9u30eMMkSccMU2tE89zWKRM3zXO3CnNa6HaBDirm2gl3PWdsaI"
        "RLDzxDbtaUHw+seJrl7AfuQ5xLLi8M49UjJmiwptLJMkwGiDEzBMQwZJhpkXSCXR1qGkRGqYnZyxWMwxFvIkY2ttwsm0JA4jrDEs"
        "yp4sDajqjqLsCdZzrFv8YhmqW5ESq+n7FfiMTdGD40f+8m/j3ZuHzJ6/icpzkq4mXJ4iljPSWNFqg+1i5HCMHAXettUJb15262VE"
        "PvL3Z934r8sa8gTXt2xcWGf0xW+GF24h7t5DtDU0HeLSJdTb3oAMQvK1DcLBgGQyIlobowYj1NaYAMvQOaJAEiqBlY7R2pA8i3HC"
        "olTArO5wAuIoZjJeA6EIFGRxiO40prdY59DWIqWk6TRaW6xxbK2PMcBsUSMHOXfUBgPV8q1v2+B1V0bcPyvorMBYVlYhKyJa4TMZ"
        "DX37ex7iG17rOP6pD5MHmjiWuGqJXi44m89xXUMw3CB93ePIQMAggkvbsLcPWxuI9Ynf0jEcecfFsoH1CfZkSn/nkI6AQDmE7qDv"
        "vXPjMMMeHOJuXkcWU8SiwGkDSYxQwJ07CCdBSgQgtyaESjEYDYhGQ9pWI5zDOEkUxDTasLu1TZREtF2LEFC1PdY51kYD6l4jpa+a"
        "SSGw1qJ7Q6Aky7ZDO8385JSv2Y34jRdrHnZHvC2t+D1vzPhd79hh30S8fFh9ajC0IiNWVrErvEpElCeSp//ae1k+9ZMMdQuxxNUd"
        "rmkwXU3TNtRly/br3wpvej0sprAWeSvY0cB7CoUR7GzAjSNvE6t916A7nsKyQqyPYRzD3T2oa7i0CyLEzY9xTQeTAeLwGEEP1kGa"
        "gNYgY5hNcQKMVTjTIlpNkE/oi5J+sWTR9KRRyllVk+UjIiUpqhLnBNbA2aJCCIkTARZJlsQIAU3fEyrFvKxBCaQUZIMhxgkIQmIZ"
        "kOYhURBgFYxTw/Pxo/zOv/lxnF1pR6ysYld4NfE1r9uh+ejTfvuqs5iioC8LRKiQYUCS52SjEa5dwOmBHwaz1s9KvHQDtrahBff+"
        "D8G9Uyga6HrswRmu6RCTAVQV9Bo21+E1j4EBFjPEIEUj6Q5Ome8f4JLUr59OU9icwCjCaoMtatrjKcJZ1GgAu1uEVy6QrU2IkgQV"
        "BkRpjJOgux5jHFKAVI7djQlrw5xBlhCEAb0xnM5rpAxwQmCFYGM4ZHOyQRKlWCFZi2O2hgl5JAmkZZSETHXEI/0dfuBPfPHqomEl"
        "Vq/wKuMPfNXDBHsfJhykIC2ma6j7xg+eWk1tBIONTRiM4dplP9G6fwpf8U44ugfP34BpBYME6taHWmWNk9IblLWdDxnKBoYJhAom"
        "KbgGkpjosQnMp4QPbSLSka/SzU9g3kHk/Yia+ZKybaB05KMNr08FAtZHTFRIt6jp+4o4zgiR9NYgpUBrex7pJKwlKSeLGqMNSZrQ"
        "tJpQKjaHIUYoqkYTpRBK4W1CjGF9I2feNPSFIQ8Cyk6xG1znyatjnr0zX5morYhohVcLTWdww4y+KkhjRzQaElQhThtEEJOPM+T6"
        "Fm5zExoDH7sB73wtxAGsb0DdgVKIwyVIhT6dItIYvayJ8xSc8eRjja/Nn8xhmOIGQ0TXwHIOTzyMkg7+w0dg2WOaErEoqJuOuq1R"
        "VpDlMW3v0HdPiI4KhFKESYhxFo1jGMek0jEta5I4Ik8iTqYLatPhrGXR9GRpjg0dCEnf15RtxyAfkCQJpmqJlaLHkMSK9dEQAaRR"
        "SG80nTNYB/PpnL/4vjfw3v/xg6uLZ0VEK7ya+XQYJDgauuWCaG2MHCXnvtMSNjchmyDiGLoKLozAady9u4hnXsLNDXWnyfIEogCV"
        "RNBrot0Nb+XaWbi2C0bDvX1IQ5zuOX7642w8eAXlDBycYBcVdm8GiyVaNxR1QxQG0INCkFjB7TvHhOGAbDBgMMhYLJY4rUmD0Os+"
        "XccwSyjrjrbtGKQhRQ8GiySmbg2NMwyTlCBN6aQizlPCKCRVUJY125OcpuuJowBjDEpLECES7yHSONiu7vLmh7f4mevHqwtoRUQr"
        "vBqYli3sjmmOD4kDiatahAohjXFCIcYbEITAuUJ7dRuExd2+jxARdDOSNPcbOOYLRJL4BshYQtf5q6LxE/PsbsGlHcR6xtbVDcQL"
        "e0yfvYV8/i5pFNGdLRB9Te8Mrtc4J3G95qxquXvQMystQsxJm4Zhus3JyYKmbcnTGIHACUEcxWRxiLOSvnc4C0Y6sjggFjGpVGgr"
        "CCNLFob0QiAlrE2GLIqaWdHStB1baw5tLEXZEoUKBIShYlH3zI+OecvGgJ+5vrp+VkS0wquCURxDCDKMCKXBWRBJACKALPV9QkL7"
        "CKl2MAhhax2pgXqKuLSDeOgqvHwbNyshihEbGaDhwgRkgLMOcXyC25wgZnP0rduIgyPM/inzswWJCui6JYKeqlzQNhapAuquQgUC"
        "oy1NZ+lasNYwCDs+8cIdlHBoJyiLliBU5HlGIC0NPYFSIAVl0yBCxdKUZJElChPmywbnAKUYjUfU2rB/PGV7MmJZ1CRRwmxRMcxC"
        "JsOMsm1otcZpKKoGEQrWg2R18ayIaIVXC089e4Mn44Q4SRBW+22soU9FRJrgDk4RkwwiCU88AErAM9dBRL5p8dIurqjRdw4IhMTN"
        "54jLa7A9hLaD3iCGAcwE4voN6v0z7r58QJJGRIFikqVEQlKUC9q+4mzWESuYz3vCwMtLnYGuh7byv/7oRKOlH1XLM4eKFEkUkMQh"
        "eRpz5+iU7fGAXlvKtiUXKa1p6JsGZyWDQYZFUTct5VIw2lwnT2OkdpRSUNQtSD9XZ6xFCEfZtIRhwDhPsH3Dlzx6kb/4Uy9iV+Np"
        "KyJa4T8df+/pE37vkxs0UqJ1iigcycUBxBGuanw000VwcQeiDD7yMVjUsJX5Mrt12Ot3aBcdwSiGPPZCtpCePe4fMbu3T3BWkOYx"
        "+y/epZ03zE40G+MEmyRUraYuGopWc7Z0rA99NmgcJKHAaG9k5jJB21lmhV8WKwWUS3BRj8XRm4C60xxNC2azhigBKSTSGLI0Ybps"
        "2J6MadqG1kCsYrq2ZjqbMRgOmM1K1vOUIFCUXc/hdIHpNXkW0LQNcTxEIxkPUv72R++tSGhFRCu8Wrh1qnnxvmYiG/aWcLiwDG8d"
        "8MTbH2ByeRd3b8+X3bcn0NU+yrmwBacLmHg2kG1LOsoQIbRHJySDEPtcyeL+Ea5vuH1zj1xG2LqhKEoSJRk7hyobqqJiurQk4Xk2"
        "GAkWlSMKBbubMUZbDs46toaCYeInSC5vR/TWsqwNUegYXdygLivu3JszmQQII5HScHhoCSQw7oikYJSENJ1BRgoVWFpTAwGiEZzV"
        "huEg42i2IFAB4yShtpZpX9IsK+IwJFQBRkBjDb1etc2tiGiFVwMCcCD4rg/U/PPf9Th7L97nYDnlqcN9di5vszZIEO98A8TA08/D"
        "ZAxBhH3hNmI8QDgL+0e4ztAfHzJvGuaH99maHWMMnMxritMzJBaUZjGrUQKCGKoalq1hYwiD1BfoFg1MBj4VM9bhnKWxjuFYooVE"
        "yIDRhiYfhuxsTNg7nbKYt+xeXueFFzVRUNP0Bt2BCgTj2PdRVo2jPl5QG8n2esxEjsjTgB4IA0XTt1gDgRyQ5TnSWtJYIVxEZ0L2"
        "TxbkaYzDEMoQgKePm9UVtCKiFV5NXD+q+UP/8h7f8nBO0VQMHfRlBW6EGKewOYCTBc3Hb2IWNVkUQdT6DuvNdURdMN+/zbLRLIuS"
        "0/tTLjz6AIEwtKcVk0xxVvk8xknBdOpIlGKSWc5OLYOhIsRyYeSopWN7ax3nAnCKEMd2ErF+4QLNssAJQW014zTjaNkwWY84vXef"
        "QWBZf2BAbwx379cczRybQ0jjT87mCmToOJ3V6L5lmMZYKxmkMa2TWOlouob1q5eY3tnnhXv32ZqMyPKMcduidc+y7smHCafNgGeO"
        "Fqs+xhURrfDqRkXw/P0FV9/3LkbDnNM7N5lMRpwdnbExW0IWQJ4Tba/T2AV9ANFmjj5ZELxxF2FL1q5dwr14k1bEbLzhNZhqyfJw"
        "ShJL6t5Qa6hLEPjxiy7UbE8U6VseIA8M0XiEjQW7gyFi74Sq6VFBgkBStQ1dDy7OWRQ140FOU1U8eHUb6+Dm/hGTXKCEoGhqrl6M"
        "6NctoTAUtWOxBFs70hysFhSlpalrpBBUVUOUpQxHKW1VcffZF+mcJY1DP72PZTQaovuO1oSMZMTfetGsSGhFRCt8JvB1734bJ43i"
        "gde8lXd993fD7Y9T/Zu/e16ycnAywx2e0S4aDs7mPJQ+jOxa+MQLsDEi+qI3sXZxi+BDLxI1Lfsv3OLkUCNzCJzAAflE8tDlhHwS"
        "E167QP66JxE7O9g7e7g7++hlS3M0wy6W3Lx3yiCOWVsbcTZb8uzLd8iyDKs79oVgmGeMJgN6J0iimDAUSARracy9oxNU5KhqRzaU"
        "pJljOnUUSwgDx7yCJPCk2KWGLOiY4AgDx2SYc1bUICU9gq63tFVLkii2JylVusGPXH/5U4loxUgrIlrh1cL9+/f50PKMwbvezEbj"
        "MKcLL/Tun8K8orl1TFQBPUynBfXBGenuhq+crU0gS4nDhPhtb6T72Is8cC0jub7PQDucMrhmwfab3wTrI3j0Gly5inv2OhzNcU7R"
        "3D2hmy2wfUfR9fTG4JShamfsndVEAdTzJcb6xsLDxZyLpqftegIVsTEeIJXACnj44jbLRcFC1BihcRiGQ8HWWkiWZJR1QdNoWi0Y"
        "TzLy0RBUSByGdH1HFCnSOEGEIYuyI89HJJMLfOePHvHxg5dX3LMiohU+YzrRwYK/8D3fxgsfeZrrP/gveTKfQ6ywswpzUnDvmRsM"
        "RxP6qmUyzJnPFoTrQ4ImgLMZHJ74MQ7REV1Zhwc32Yo1kTWoq7sYleIuXkYkA3jda6n/8T9n8S9+jMmlHcqDA5qqxgJaG5ZFTRpK"
        "5kVPUTiEhbLyO8nqDvzQBnTDlrOlputahNEYIRkME4SDQZKgkVhnOJ0tqDpD1/eEQUsUKEhhdzhiZ3Odg6JFBgEISyAFXW9o+o48"
        "joijgCsPPcY3/sMb3D7pfz4JrRiJlTHaCrx6Lo2XL6xxUZSc3rjOF73hIu3+86g8QW2uIccZqTaIULG+OUbonqIoUc6QOAFFhZUB"
        "PHgF8WVfCZcGfiOrVQTf/nuR4wEqHiPSgP7Hn8Z97Dru2efQbUG1qHC2JZSKsmzAQdVa6s4ShgEGwXCgcMYTUqRg0cK13ZjOWKZL"
        "QxxA0fYs2o6665guK3prGQ5SnLf/Z5jGSCyzZYt2EAQxSRxzVlbUxhAGAUpJEqmYLkum8xk37hxxOm9RKuYjU9ibdysSWhHRCnwG"
        "XRr/8/c8xIs/+QF28oQnBj2qmBE6iQgVIktwp3PyyxdxZYnsWlzb47SjnxdEKqA7nFIXNXEmII6wL91GvfUNiOv36H/ow8x++nn6"
        "WwfMP/ES3Us3EJ2jLWuasmEyzJgtS6QMWB/lhFFAkoVoDCJQBIFESUeSSIaDmNEwwEpJEEq01iAgSQTifJNroARN12Oto+974jQh"
        "iyPGoxFVZ9gY52RZxnTZ0BvL5mTIIM9omo6ybJhWDVuba2ytr4GMWCznLMIhHz9sVyS0Ss1W+Ext7ticpPymd1/iH3y44dqFDJVH"
        "6KXCNjXMBFjN8mTKZGuCGsS4E42zBmklYRwhjGF6eoo7uk96eB+xPsEcHxN86AWavRPu3drj5OiUzVFKNh7RWgh6TWssddtycmZZ"
        "Vh15FtI4QxAJAitpGkGjHS2C3gqSQDFrNY125GlA3bUEscBoxzAJ6BBMix5nvIH+dFESRQGjPCNPU5wIuHZ5B4VD9wY3dNS9RhtL"
        "ICXWaIwD6Rxtq1kfDHjoUspsvsQdri6aFRGt8BnbX7Y9ifmJ/9830R+8wLf/lneRBBHUDUHqbTDsbEGsJOPJAHd0Qm8MZVXRdQ1d"
        "V1OWIFyLa0rquqJTluXzL+OkIrkXUlqLNZqtzTFOQt21YB3TrqZpeoSCed3SaUtgBYNQEQUJB6czoiSmazUEgiTMsMaRKMPWIObw"
        "tCAIFYNBxHxR0/UWFwSEoa/Q9drQdRDHkrrrSOOYLAy5Py9AOwIBQaAIA0HVNQRNgFIC6xzjPAXlOJ3NCDqNc45783Z19ayIaIVX"
        "m4DGmeK/fN9VvvGNQ5pnPkDsILx4AQ5mlNMpbVGwtjWiMxo7X6CGOfpsjookXVvRlQukUrRdj3AtmQq4P13SVi15FLKcLTHOYoTG"
        "Goii4NxKQ2Kspmh7itoyTBRZFlF0vlfo4GxJliRIFSKURMseJQPCWGEdtLXBCEGUBESBotcWFYWEStD0mt44klAhAoHpDLNZi7Cw"
        "mNesj0Y457C2Z1b2hEFAqzussLRti9ESCIiTCKkF2kLbVlwaTfjQXsWnuCGvVguxMs9f4T+BgIap5E990+N8yzsSaM5oKkcSJOCs"
        "twDJc/pb++jTBUpJetuRboyRSYI9OWN2csbh8SlZGGGdf/qirEiTBGcdzhrKoqdvO1COjfUMbQxd7xcXaqNpe0cQCMrGYM/L8Tif"
        "TqWposMwyBOKqkc7SxjFRLFkmCXMixrrFIGSTBeF14fiGKk76rZl3giEgDhQWGuxFprGEQWQRAGbgwRtHU2nqdqWQEra3hIomJeO"
        "nY0hcZIwHgxptMUqQdsIPiYv8f2fKNib95+Oe1ZktCKiFX45++ujUPB7v+Iyf/Lrx9AuKQmJnCXE+KZFC+QZ9M7buw4z3K1j7PEU"
        "NfJ+1OXZnKJY0vYGYwVN29H2mlhI2lYTRwFFXdG3Gt3CaBCQDQKUCDiaNdSNRSqHNo5WC4xxhAGsjwJ6YwlCQRArtLLEcUxVdYRK"
        "op0kyyPAEihFb/yd37Q9gZJ02mC7nq7X9Eia1lA2UFSwvSZwCE7nlgvrEtdbnIMokHQalBAMMkFRG8aDiHmtGY+HrOdDjBBoJ+lc"
        "xNr2Bkky4sWF5R++VPOBl2Zouyrlr1KzFX5J4vkkpISvf9sW/8N3vh72btJ0HcoE5O35nXrpAmxmftPGyak3QktiiATigRHubEp9"
        "cEKkIJKWQICQiqrXWGMIpSAJAgIkvTZg/K4wIy19pzk50XQOjIV5cW72KEFrxyjzy0DmpabTMMgFTWu5cCGj6Q15GqO1AWsw1voV"
        "Qc5hrUFbwzDLqNoe5xwIi3XQaEfTed+iQPpoKIn9QeotLFuY5IJOQ1FbukYSCJA4uqrnbGG5sO0wzhCKABRYKTibl/SLhhzJdz45"
        "4g+97SF+29+9gXPi55+HFSF9gRKR+1XOUP26JJ8wEARK8N43XeFdFwzf9CWbkAvKwz2iMCbB+R31dQMbE2gNXLoIH3sGFH55YtvC"
        "5hZcuAAf+hhCJLi+J1SQxX6zqsKPbiglqWovQEeBJEZQthbpIFCSpreIQFBVjqqBTHrn2Dj0dkUO/zVLoDeQZwG6hfUspWxatDFY"
        "HEXVkqcJXd8zzCJCFVN3BnAEgaLroO0dZePIYmg6GGUwXULROYaZoNeOJBY0ncO0DgG02uKQZLGkKiyqh498dM5kUvCmxy/SaIN2"
        "PXGeYQUgIqbzBf18yp/+4hF/8+mCo8L9/HOzIqMvACJyv/yHiV/Oc4gvZAKSEi5tDPiqJy/w1U+MeedjY1iewPQQqhnt9SluvE4+"
        "TnBF4Ucs6hai0B+ZtoAPfhg6v94H4aAtYe8OXHwNwYMT9IfvU1hLTMCsbGnaniTyDYH3T2YIY0ikRAtHUVo/V5YLegtW4G/yxiCl"
        "99NXAsLQZ4PLEtYGnjjSQFBVGmehbTrqTjMYRDS9JQwlTdchhMRYS6cNWjt6bYnCECslSgn6TtNabwxQdP73xQL61rGsIE8hVdD2"
        "ECjYWoNFZVmUsChge+z3QwrnUIFlOi1xMiUdjGhrjQq9VtV0mstiwf/23h3+j1uWv/uhk18P19+vCyJyv1hssz7JeeyBC1xZi/iy"
        "RyaczE8xxYLt8ToyCKlawz/64HU+vt/SdPYXe17xhURCQsDXvPEif/Vbn4RyCsUxiAOWL9+EpiC0DgzEqUFMT0BNEIMMNy8Q2njj"
        "n9OpD0WshrUhyBAWp1AtIbFw4z58+VuRN38As9ewJPV750eG/aMZTdMjpcN0FiMsTeM9heIQRO84LRx1A3ljmC49CSjpV5zNS08W"
        "W5+ypTqKLWksKEqNlA4HlHVPZ7wJfhgpLAZXWNbHA5JY+tdRa7Ik4qiu6FtPPF3ryW2c+01G1dK/zc56l1ul/L+XHQxi0BbWh1C0"
        "PoWLFRTFEt03DPII3VVcGI85LlriYIhwgiKIuXFywm+/tsUw2uTfvbTg+nH78y+1Vcr2eUJEv4CAgkBw+eImb3/jYzz5+CWubY85"
        "3DvkUiIRes7B/gnrtiaaFUjdoosp33ERgkcHXF8qfvRkyFM35ljrvlAuiJ/zRt715GX+9z/8FsTx8/QHH6HrHJGSSGfJRYsRDuUs"
        "QgmEs/RFi+kN4bhFKuk3dBzPvEl+oPy2DbzZPLMpmAr6zN+12ztE3/IexF/+p7Q1NCcdTdMxW5YM4hDtoNU+3ap7KGroNDjpI59P"
        "6kBt759+kHqC0Hgb7MOp31qN8NumTxcO6yCOfZe0cxYUaGOIlaLRBhlJJJKqaXHO0feGrrbUhSOL/O+rfdGOuoKmP7+ulA/4uta/"
        "5kBBKEEq6FsQIaSB79K+MJHMi4LAgjId8+kpi7ZlY2Mb5xzOwUaegBQcns1468Dw3vesc6tw3Jz2/PWnpnRG/FLX+YqY+LVTNfs5"
        "J2cwiPmaL34tNol579ueJAslD13eRDvHYllw/blnqU/2ybIQfXZIfzZlY5hiyjnNvKA3JZGtiURCv/Mo/+J+xk9cn1I3+vNZR3Kf"
        "GgX94W96B3/8S4ec3nwG2XWM8wAhHPTnRvXCoasapSS61/R1SxBGuMGAYJghwxC3WEIA8uIGDnD3j5DveCtEAn7yR3EnJ7C1iXj4"
        "Gjz+OMyO0R/9GO1Pv8SN/Y6itiRK0RnLrNTo821BgYJ5C30PceSJxDrvktgb7zIbCKg1xInfONQ7CM+JaDSB2cy/VxWCDCAPfRbZ"
        "dJDFgvEwYtr2jAcJi7o59622zJbeJjtSgPXEJ/DZ5nTpj2Ik/MG09vyr80Q0SkBraC1kEVzckKyvK24c9WyMQ+JBim4cp71jsnWR"
        "MBuTxinSCbRzIGHZaaq2QRpNGij6dMI/udnzr56d/VKX2oqMfg0Q0c8hod2LE77hvW/n9ZfWyeKMyxd3yfOENI6YzkvWxhnPPvM0"
        "N196kbe94TWEtuHggx+gOtgHa2iWC0IFRvlzK7Vma32bPbHG378OH7q9+NQKx+eL6P3KMdrdyPhn3/ONjOs73N+7wcYoheWSWPTI"
        "MACrcW0PdYvpWjrb07YNYZKRjzawgURd2sYcTVFpBK+5iL11B1v2GK2JH3sMbAv7L8PZCbbtkNeuekH7bAFrA9zBMfs/8gnOTjv6"
        "TtL2hs7A4jzqsAauXEw4m3XMFtZ3BVjIz7dRV40/oMaCUP59JaF/l8sGBjnoDt/PpGAwOCe4wKd0kQIrBB2Oojo31LdgJWSxj3LK"
        "6lz89tV+rAXtvFYUCbDKE2MQ+MgtjTwZWQtRev76elgfA0pw7YEJIo5wnWVet7Q2JM4nbK5vU2iQgWSQRDStYV4XKAnOhczrGaa3"
        "2MmD/M2Pznl0DAfLlqf2zYqMfg0R0Ss3WBhKfsv73s03fOVbmQxDdjY2cdpS1C27m2ugHVXTUdUNwnaEARzevEHZtJx99N8z/9iH"
        "mayPaNoK5xwK70nTRZI0GRAbvyNLjS/wN14Meer62afdviCl+Pmp3Of6YnnlxVxYT/m3f/StzOcHpMoRS0OYStRGDmenMFv6vTuN"
        "Bq1ZHB1xspyCcWyubZJv7yAvbNJOC5IwgEkOscVtDhBpDE0Lx3NfJWtquPU87N+Fyw/6kKLtvajSWmg7pp+4xcvPnqGtj9JmlS+L"
        "YwEnEcKiFN4ZUfiIp6o8AajQv7G68+SUBD4zTBP/46Hz6ZMMfNQUBj51EngR2VhPIgi/LEQDaS6oa0fbeycShCcuZ6Cu/b+b1qeJ"
        "rfF6UBR6nepNj0a01nB6ZljfEJzNHInyEd2DV1O2ticYoTC9oawrFmVHOlinlTkuSBkMYpxzVFXDsqrIooB8OKCxltPZnDwb8sDO"
        "JT74Mx/BxBm3git8/8+cYKxckdHnWCN65QYLQslf+Ut/gs1UEQWK9cGIqmoRwCCLOTyZE8UKKQVZntDbiG45o+46Dp77IC//xAeZ"
        "pJqh6zDg9Q8pQDuEsbRljZQRB+WSja7hj19b487FIX/hoz3H55YOm7ngO9+1xebmGh/b7+hkzN/78Rfo+s9pSfaVX741DvmB73wD"
        "N248z/ogIRqlhNIiAgADm+croOclru+RShAPEuIuRGuDU96TR0qJsT12PETSwrUriEeu+rt1Ooc4hXwAAZjZEhXlXrmdVz7nMRoI"
        "cK1h7aFd3jDO2LtxxNlJRx77w34yA2vPq2aJ14B6C7b3HQFtB4Hx0pPB6+TOQHSu6zjro5T4nDhE4Emn6TwBSeGrhEXjedda/7PL"
        "wuEM5w2Kr6xTIwl9lNZqvyvSWK8FZQPfyxQqqDrBxkSxmBuK0oGFyQR2NgOGwwjnoOtayqpmNq+Z1YZNNScbST+WUsQIHG3dQWeo"
        "tCBQEAhJhsaWp3zs2VPGWUy+PuSJtZjf8p4v45v/hx+jN6uS/+cqInKf+tfv+Z5v540PX2YSRQgBt49OGSQJcRiwPs5pqp6X9+6T"
        "JgmvuXoZt5zx4//2h7l4cczyxk/wzL/+CeL1kN21IUmY+HkmoGhqAinQraWYFlglyDbHlBritmDjsbfwE9UFHhn1PO6O6HpJowtc"
        "p1EqZfORN/BXnzrhX3/4+ucqMnIA2+OQf/n7HqOYzRmPUlQE+cUBXbkkGCbIQQCzBeCwt49wTQO6w3QdURBytliQZiPSKxdhNPSC"
        "Cw6ubfmwY1H7nMbh6+nL880U967D9VuQjb32NBnhlhXdwRlhPkBIiZAOXZSc3T3j9LRiVji6cwKYl1CV/sbPIqCH48brMEnqNaJO"
        "e2IxxjceauujmMD3JnoBWZzrPqHXcxK/QIP+k6SE/332nFSk8qSje//8gc+u0AaSxG8OGSQwGvhq2bKEPPfpWSRgNBSsjRUuMAxH"
        "CamKWFYNvbM4a6k6g7aS3Y0NVBRzVjfY3oETqCBkkKfUrSZMQuZFTewMkZT0BhZVi4lTwsk6hCO2H36Yb/1bH0GbVXf257Rq9ru/"
        "/T/jXY9fo6or5l0LNmC+rBlmIUkUUrctZTHj+KWXuDBM+NizH2f/5vNU968j9ycsDm4RJwKBo+5aBmnGOMuZlzUCCRKEbFBRyMbu"
        "NrPlAlU0lE6yuP4Cb73QsqMmFJ1CCktESNU0LJojuv4pvvXiBk29w7//xOHnTB76O7/nbfTlbZxwWNcw3JzAWkzkalC930AYeTVX"
        "PrCDef4WtuoIsgRnHAMVEO3uYjYnyM0xYhhDV/go5/KOr7NXPTx4Fc7O/LoLnI+ORgNvKWYVBBKBIEhT3LJCpOd1eCvIhjEiCBBx"
        "SVNr0iBm1znm857jmWO69FFPEvqyuTzf0Cp6P1nySc0IB1Kfp02BJw/rzjWc85Ss7fzP9+dZYBicV+OUj7o+Gbg5IDwXo6PIE1ZV"
        "+zVGtQBhvB70xK6/742FK9shceSF50Xt+5iM0nRWo7VDSEWEYDhI/ZLbag7akIYRRgfIUGKxvqLW9/TlgigK6VWAlIJBKrGhI5A9"
        "tS24/cLH+Zv/tyf4/X/3uU8lo1Vk9Fkgoleiofd+7Vv5be99O11bM1tWZLHimRs3yZKYJJwwnc+ZNZrXrkfc/5kf4xMnxzxxcQtd"
        "L6EvWNw/Q+qSJFUQBfTGsX92Rt11OCMJnEa3PXcOCrZf8yRPvufdPPP0x8nimCQIuX7nFtfv3OXetOKx3Q3yOOZ4viRTmkAawr7k"
        "5PYhv3MywTx+iQ+8cPTZvFAcQKQEu4mmS9ZYixXhOABb4PaXiK0RfiFYBoczLyYvK2SosElIPV2Qr41QGxu411xD3rmLuLgGj12D"
        "ooDnXoa6gPVNGAkfhixKfycL4VlDSlzRIIa5V5mVRKWxv8XjGPoOqw1BFDOMoDUtCL8PzBoII0syNGQzx+nsXCdqYD7z1TJhzkVi"
        "CepcQ7J4Iupar/9EgdeV6tZHTZ/sxu7wGlJx/ri+988fCM/N1vmTJIVP65z1UVCSe+1HCLi0FdB0lqa3bE4Ei0qT9L7toDWOUEEa"
        "RYRBgEBQNhoRSZQULMsaYy1hqFCBRJseoy0SSxKEdL0mDgRSaiQWqyEKQyrX01cFTnUMk4z53kv8xd/8EH/yn9xYkdFniYheIaHN"
        "zRF/+g99C7PZCXVvGOc5oyTkdQ9f4MrmBN0ZsmHK7kbKh370h+jnSx6/vEsiWqJYkGhLMZ8ThoowjogjSXnuZzM1mjRMyUdrRIFk"
        "Nxwy2b3KWWHZfvBxZCDZGk3YfeARTDHnhdu3WTQdUgqqeklMj1TQ9QURmunpEX9wK+PDNwVl5z6rB3MtD0mVo9eCMA1hK4cehJ+z"
        "8B2ATQv37vseIOctUekN8XhAXzfIOENg4DVXvXJ8464nrcEQKgP9AjIFS+3v1ij26q6xEMfIdADHZ74rUAgfKggJzmI6Q3ThAswW"
        "OAVRWbMWRGjdMSsahsOMzaEiyRt2dwOmpw2zpSMS0DeeMILQ/1lUPrUKzqMYKfxLcOfRTRR4cdued5LHwXnZX/h0r+t8iida//KS"
        "xJOcUF5jEs4/vj7XmoY53D8zVI0jjf3lmUaO2vm0UUoIIpjNG+JUkaYRTkofvTmLRJBEIb0x9F0PwiGwYA1KpWSRom8dVd2SRoo4"
        "CjG2IXSCQEIoBEpBWVWEsz3+j9/9Zr71b/8M1q3IiM+gVewrd/D6es7f/xvfy/HRAYEMzyenG8qmRApF02uapiGSXqA+vvkyp3v3"
        "mKwlmK4kDCSB0khnsMYRhwGJCtDakoYhSkjCQCJjxfpki7XtCwy2dnDSsX86JQ4VXVOzKB3bO9scLVseeOASW5cukg4TlseH6K5F"
        "ChC2Z5iktMtjhpN1PnrySqnt+z4bIvXf/91vIZrfQmiNbCpUFsHWJkyn2IMTxGQNTmc+RADoNWa+pFwURIOEzliCJEU+8Qjsrvso"
        "Zrk8z28UTBfQVOctxg6Oznw34vGpL2UR+O8FCoaZ/x2f7DKUsDycIpME11Q4Y6jqliBUDPPED4oKAULQGEOepBRVSxYJosCTj0r8"
        "ywikJw2tfZldnTc2CgHuPLJxjvPhUy8y971/fNP58bg0gjSEJPLVNyl8SubO9aGmg/EAstxnsmHgD0OW+r875yUy3cF87rPOTxKU"
        "cY7WOKRSKCkpm56zecvWOMVZ6I0FAcZoHHA8K4kDRRhK4kAhJTRti7aWySCn7XuU8t5MSoWEcUbfL9mYjPjovepTr4XvW1HKqxcR"
        "/WwznoQ/9Sd/J8f37zBvGgZpgpKCeVkwTiPWhykHZ3MubkzYyFLmZUUYpzz+8EUubg+5/lLDUBmsEZRNR+gErtdM2xYlBXWnEUIw"
        "GaXMpnNmJ6fUGjZ2r+BG21x58CFOTufEUjIYrDOvOy5u7pKOE6I4ZnftIpHRvPyTP0qYxlRFQyEaUqV5SN8Bdj9rH1KhcjweHlL0"
        "PaHpEZ2DfY09PMS2S4KLW1CU5yUpL4DYoylCCvJRims7XGeQ62v+cQPO69jAxtiHINb6cr3RvgnIOdCtH/WoSk84eXreWRjC7ACS"
        "DLbXoagYP3ABtyjpOk1V1wzziCRJ6TvDxlpEVXdobQiVQmtHMgxxGgYjmM46+oXnQDRkiZ+qN8anb4Hy2eHJ0hMHnD9W+jMQh16k"
        "HmSQx/7/m/5nz07X+3+ryBPdxsg7nDT2Z382/WRrwHkjprV+1CRJff9SFAQ0nUYKcS6qG+I4IktDQFA0HV1vSJIQFSpmix59/lnV"
        "mdavYnKCXlucEEgh6LSmqCtCDVtpjnSW3jbU84p3b63xzIMpT92sv9CiIvfZ7tn7JTWi3/T176Cdz9D5BuvDjJNpSZaEzBYV63lK"
        "ICRRGFK0mqKZUy0b3viGJ/jpo1vcPTphbRgz3buDLeY4DB2QqpBBHGLO7UizKMQajcThJKzHAjs9RjYlh8Uph0dTKhPy7t/4G+mt"
        "plcGqpaq7Jgt7lHduEEkNX0HQShYtjWxSAiV+qyeubdfG+HymMBGKFsRhAJ9coSzlhYN1RLZW2wQM7hyAeIQOcxx8znO4a0+pEKM"
        "UlxdYO/2qMcuwf6BvyzkeZgRBzDZ9NdKU/mJfGO9WJ2k/rH7J57sxmv+/zrtBRo0QgpUnJDiUNIhpBe7rbFo4wdT0zik1w2DxOdK"
        "YRAgY0GSG4QxGO3YO3CMch+5BLFvKEwVTIaeVFrtdzwGwflV7SB1Pmqx7nyK3/nop/eLQPwInfMzY00HJvCZp7FeJ4rPI6NO+5Qt"
        "VF7AjmOIoxAnAmrdEwvBKEuQgcCdV/bWhyFl26GN4Wzek+cRQRCyMR4SBpKibnHaUncNUgJWeC3JduRpSBpFuL6jbDqSHLayAfuL"
        "Gd/ySMaHbno3gF8n5PMZGcEKfrEX89ijO1zbGvDYzhptaxHKsTZI2ZueMS2WOLfGjftHLJcVkyyhqhu6tuX2i0tu759y7+MfYXcQ"
        "sBH0xBiiWBHLkDBQlOfzRoM0QQpYFBVV1WPx/TTCtRzuzQnEfU4X8PATj1PPT5nWKZPRiEAp5ouS8uQ+/eyEQCi/JrnuaFpIBUSj"
        "/LN6Fv/wl1xBCUeY5QRK4roaJySd7qiagnKmwThGScogUDAIwfkVP9pa4jjEtJq+0wSTHcyPP426etXnRKcLL5I8sukFkfrEN/w8"
        "8TCcLeHw1Ask86XPb+LzHMdJaBtA4YoaYcwrV40KFVII2rZD9xqlQqxz5GlM3+tXnBx9r5Dj8vYG5gLMTpf0pmc4iZhNK+4fa8YD"
        "Lzo35x3SaQxdCa736VOvfbUtUp5AhPACtzufT8vOC3pO+NmxKPRaUpRBmEIkBEI4lBSESuCcxQYQB4IgdmRxjDOCrtdIKQml91lK"
        "wwgVSNquxyGQQpImEbI3RKEvmCyrmjAIyJOYjh4TBBRVTRz644GBMAoBTdcviayjbwS1MqxlQ6bFjG96MuYfP2u+oMhnmEh+w9sf"
        "JBM9fVlQNTVBnHB7KXn69oy2M68qIX3aiEgIx1e98zVkWUBvDQenC7IyYFYu0UaTC3j+hZssq5q7+6dsDLwe8cCldeZFye7uVdKu"
        "oDzbw3bQd4Z8EDJOMz/0aC3DLEUgCENFloRU5ZxBJIgTgXMBm2NLWfTsjGFjIrlx8yZXHnwYozV1b6iqJUGaEowm2FnPsq5Q1rCW"
        "CALX0UTDXyXJ/yqasYRjqzmmLDPycYhrDbpsUTjyC1vk6WX66YymLEmUxLYNXbXAaT+IWVcto2GOjSK663cItUGiWfzjH2D00CWv"
        "/KYpVC36+g3knUPkax6Eo5l3LtucwMkZLOYwX/j0b5DCdImdF7TGgHGESNS5HWtZdqRpjHASh3rlEnLOeU1ESpS0WOdo+paDqSEf"
        "JEybmiSMee1j2zz18XtsbGrSHJwVrK/DbOmYzcAFnmsVXivC/ax05ZyfJQuU14qE9FFOEkOce91I4LnVdzt4EgmUYNlorPbRkJAO"
        "6RR95zw5OYcS0BmD1oJ2aSjrnrVRSiQlndZY6xiPcoRS2FYjzwWtpusJlcThCGOFc5bwfDavN5ZWG5y1jNOM2rTYwmJCDSLmK65N"
        "+L+ePcH92sjK3C8jlfq0j1HS8XWv2+S7373JuFtwVh4SxxFoQ1VbrGjQKqf+8tfxo/cVf/9Hn2FRdK9KE/GnJaLHH9khkJJxMuRs"
        "XnC0mFLuFUQKpLTMypJAxbR1S1NU1MKhgpC796dcnqSs767xhjc8xkApJmHHh//1P2R59x4yFygpmYwGNI1fEyyUxFpYW09oq56z"
        "s4Y0VSSxn1xoK8e9G9cZXHmcOArpuopy0bE2GRAFCYd3esJQMCssyjmsgTx1/O0XaiD5rJz5SDp2047qsCRL1hBRSDDOEZGCy7ug"
        "BGGiCOsB9uiMqqjo+4627lHOIS3MT+fgJPnGht8NFsao/DzVksortWdz5KxAvP4RqDq4f+Lv2vtH0PW4ewc465BpAs7hmhYxGpCG"
        "AW5R0pctQRhgmo6m68mSGBVGNH1N3fbnqYhDG0uaxPS99yNSCtq2oawqhBDkseLGnUOO5w0P7ERIaTkrNErC7k7EaGA4PDLUjddx"
        "wsBLVtOl/5onviwfnM+iVY2PnLLcdxpYr5ljnC8M1q0ljSXGeE3KWJ+pxqEiCUPqXtNqjTYgnWA4iqict9M11jIrWyLVIQUkcegF"
        "dadQ0qKk8N5I1qKdxUlHpAKwDikESgqEsehO0ztHExpCJSm6mv2DU9xwk7dcfhgl3SdtaD8XOpH71T4uCgSvuzTgd79tky+/IrD1"
        "lGV9j6PSkIUpqQqpjQ/EZ0VLb1v0/WMei0f89W97E3/9A7f4D584wrn/NDL6tEQUBIJAKQ5nC9ZMijKGSEAaKJZ1Q6IU2mjqumFn"
        "Y8BrHthFAAcnBbUL+fJ3vYVmPuPWnUNufvxFnnnukN3MUdQtvTZoLDvbG9Br2raj6wxBGGJicLZlUfaUDdQldI2g7HrCcJ/w0dci"
        "hKBrSs6mGrHY5+juHmAIpP+k7SyEKqAi/OxdAEKSXXkAc++2J4zLO4hBDmUByxqkgV7jioqu1xhjSYOIWbUEbZBI+k4QE8GjawQb"
        "a7imI58MfLnJxX7u4eK2H2qdzaCZweYYpMCVFfUzL5KOxl4KSkJQypens4T2dEaIJBoPcFWDUpLRICeMQqyxRKFCBL7CdP9sThwF"
        "ZHFI1/c0bY9AEAUBceAdHHGGRdMyHgJYFpVllAVIKbH4ebP1da+5R5FPs45nsL7muxq73s+Q1R1kGcjzqf8k9f1JXe9JKlDiFaeT"
        "T7YIBAriUIAF4SR1b6k7wyCJAEijkCBSNHVDksTE1tJZh7GWLI2RUtL1Paa39NaQhgFJHKJUQNf3SOFTP38fKJrWIBVoqYmDiFAp"
        "b3OrDc5Y1uKYtlpyeRJy68x8ziOgMBA8tpPzvtfv8Ng44v0vHPIjNxYcLPQviOJ/85ND/puv3iaQGmzDWWOQ6Zi17ZyhdbggIlEJ"
        "SVmhkwXBtqQnYntrjf3DOWfTE/6L3/AIv/c9T/DH/85Pcfaz65t+xWT0aYmorloevXqB+2dzRCjZ2J6QRptkQvh9U1GEMZo8jWna"
        "jjyNmS9LvuLxR1ksSv7n7//n9PNDouqU+fWnWcMxrwXLqiNQglY71tckl9bH3Nq7j7WG8Dw0PCgcGwNBUTlM78PvthWc7Z9ycnTM"
        "1UeusQwksQo52LuJMAahvOjQCVChYFk6ZBj5ua7PiuGZgGyM3BgjthN/t0znmMNT5DBF6BbqBut8o81ofQ1d+mHLZd0gVMDm2hoy"
        "ENCWmFsHqK2Rz2PEedVsfQJl7RXbssKVFSIIoOkRQqC0QyQBi8Nj8mGGShJMMqC+eR5eS4vtO5qyQoYR2WhIPV9w/eCErfUJyjqs"
        "6TGm53DWcWnTDxR3xtL2mmEaY63FWIsUkjwKsMZyPNcY67uQo/P1QEVt2N1IOY5aWmPJ0ojtDNJIUNY9beNtaW3jC3xKwGAk2RxJ"
        "hLVUjU9ZlRBoB0VnQTlGsSQJJE3nzfy3shBtLT2QRCFpFNJpQ9F0fkzDWrIkJNCGMIi88b+UdNZgbY81lmXvo8PNyRglQYaKiJAA"
        "KIxBIMmTmCiMmC9bNseKWVEhFexu5DRCUNcFj27E3DqrPqck9OSVnP/uq9e4lsyx1XVs0/K210n+3BsHvP/ukI92Q6JBzpia3/Fa"
        "RaZP6NZCmoUhSsasP/ggjDdxSJIkxZandI1j+PaHGaoQ5zTHL91kOjth54GMwazisCjYjmK+9xsf5S/8uzvcvb/4VZHRpyWiJInZ"
        "Xt9gPMip2p5GWDbHCc2yJAoCNiZD5vMlTii21wecLpZsb29ze/8eL/z4j9GfHSCpGCjL5MI6riupigbrxHnrvOLu7XvcvyNJUsUg"
        "ieibjgeuXUaEpyzP5hSFj83jEPLEsShhlOcoG+CMIzZLZNcQpZ5v6gbSoUBrWMgRz5/2n7rT6jN28seZ4vu+/jH60yOiUOHa3kci"
        "wwFqZ8OLynUIcYgyHSpW0CtsUTBcWydMYtA9lW5J17ZQvQFRQxHA8LwktKx8G/PeAW44RGyvI7rGhxzjIWhLtLOG63pE0yDSCJRA"
        "KEVbtyglEVFItShIQkk0zLl+fY/5subS9oAoCrGNpmpaiqYnCATaGsqmxRhHICVV2xIqv9Cw6XuaTuOsQwi4uKlYVj0L48gSSRQI"
        "GicYTYasj4fMy5pLw5ym07THUyZjBc6y5ZzXqjqHE46zhcE4x8WNCJyi7hyhFMjY0BiDjAKfkgnNMJQEoWAx71BSEihJ3fcIB4Ms"
        "odGa00VFnoSEKiAMJHcO5lzZHpKlIW3VksYBTdszSCKkEGhniVRIqJSPvpqWKIvJ4hglJUXZ0p9/ABdlTacNw7Gia1oeWRvyb6k+"
        "Z55X3/SmHf7Y2wyJqujSlGwypDk5pe8st/YOeTKwfOl4QJJGhLvblCLAPPQ64q1LJMEA2h6b7dIb0HHE/t491kXCcDjgxv4ZH/vR"
        "H2dDdAwF7J2dMhnkTOctSR5hti8SFzP+zFdc5c//6D1u7s1+xWQUfLr398YnH6PuNTIISKVkEkpsrwlVRJ4GLMvOl0UDwbwqyUZD"
        "LgxT/vX/+UMMTMlkIKnnmtNiwTDQRAiEFEgrMNYhBYRSYazldNbSJY5knDK+eInHk4gP3JrRasF67uc3rYX1iSSgw2IZDyRPfeDf"
        "cymSRPGQql5gBBjtx8H/56PJZ4WEvvVLHub7vvISVPu4NPAEEApPPvK8a69uIApwRYGbLXG6BS0IwxiEZTK+ANqwf2uf4RNPEAkB"
        "syNc1WKfvYV6/Op5J18Ik5EPIaw499nocF0FB2eIyQQGKcPxwPcZtRo5yth45CK6aHFN69uPowhdNeAs2+sp2hhoWnY21uh1y7Lp"
        "eOTyBr22CCTWQKctZdNgnO+zCZVEKUtnHNoYqgZfZQo0fe8IlMQqhZCKzgrSPEOECmEt1y5tY/qOpmlIAsn2KOd0vuR02dIYeOhi"
        "5rukZUA+UIDAnbcAdMZQ1R3GwPZajkPS9pqy6VFK+M5u50gDgRCKPA4o6pZhmuIcDLKQounQGKRQSOHnVrR1WAuCgCj0Tbqfqid1"
        "vSaJQ9aGKVIIsiSm1z1xGGKcYaE1X/rwFn/tg2efkzaiv/CbnuBrthbcW87IL4wZbk1wXUu+NWa+f8zWKMcKwaJsKdOUsYqIpSTc"
        "3obLj8EDD3H69CcQ+1PWv+KL6Z56lsAGvDydMf/Qhzm58RLBcEj+5MO4O/tsip6dzTVe+8gmH3/mWTYjSK9e4Mc+9Am+54sf4I/9"
        "q5Jl2f+KyCj4tIZeayMshslwQFmV3Lh/yMZ4QBZFtMagnWUwyogjhbCaLB/w4z/xk4TlgixWNMUCpRvWUoVwGlpvaYH0YqI1YJ0g"
        "zWI0FV3fYReWezfu8tKLx0xnQODoHQwTmFaQCMdP/eAPsbk1hFAx1C1hOvCfgjJiUXZMS9jditnv4s9E09XPIaHv+JKr/Nkv32BZ"
        "HpE9dhkle7h/CKdz2sWcSPrZBtf1iED6jrzAC6699iSfrA1x2nu0Xn70QWw8xCxOcPsnqEHudaW9I8T6CMIEc3MP9fqHvVjySVf5"
        "PMIGM5TAD3iNJ3D/GGqLLWbMp3PWti9wcjL1afX6CFd37IyHOGk5ms7IAkfVtYRRyKX1MUooiq5DyZCzeYm1ju31Ca3pcQ6M1UyG"
        "EUNrGeUGaSVF1YByxGFIliYQhURxSlE1rI1S6rZGWcHOxpjpfEEUJJxMl4jeG+lPhoIo7gkCSVG1SGkYZQkqkKR5itaaQAuyOCQJ"
        "Rjjd+X4fFVPeb+m1Jg4DhHJIZ0gDhckSOu0F96bXXNjImS0rikozGaUsqwaHY1G2KBGhpKQ2PcumIYsCosj3ollrmRcVoVJY6zDG"
        "4qQCq3zlTjr6vkEK96kjH5+VaOgdD6/xYHvInVnHxcvrjB67AkGAKxb0t5ckgYJBRFG3iMggjubEX/0OqB3TE0c7SBhNBpy+eMZk"
        "9wL/6q9/P8994CdpFiWmbfnmP/F7+PJv/33EF3Y5+zd/j2d+9IchVLx0eszWhYu0h4cc5BlXHn6YRx6+xPHePb7zHbv8tz985z9N"
        "rB4MQpxrKRYFwjha3WCNIQkCUqXoez8fdbqoeOTyJoulJsewf90PZc5nNaZfMglBnI9VG+eIlP90M84ilCSQIXXTkagYqbzlwjPP"
        "3KSY+WrvdAFba4I0gEXt0NZxIdNQTTkpYLIWkmUBpmw5nenzoSZoekEQSD9l+eo1Xf2cMPh3vu0Sf/ardymTiOFkjf7WDRanJwwx"
        "2EZjXE8v/DR4nCdEgwzXtjRVi+ktSgnSQYopG07O5mhtyJME8ZP/gTjPSAYDCBUyChFBeN4PVKPWMrh+Gy6sedJZmyCyAerxB+HW"
        "AcwL9O1DJCDzHNlbhoMRxDFpGlPWLdPjM7LAr4YGR5bENI0h7TRRoNDW0PY9aRLRNobxICWQCm0tztnzNCig6y1JHBKqkPmi9e4L"
        "WqOkRGtDZx0yiFgbZowmAxyGII5xeUagOyLdsyUERd0iz8vj4zQhDhOGGzkniyVKSvIkIY5Cpm1PGkUoJbHG0GqQwvvIXt0eUnYW"
        "Yw15qLDGUdYdWgiSKCBUAdpY4jBkUfakaUIcBxgXIgk5XZQsygrnfFNsrzVrg4wggKpukdJfOhbo+95/qDqHlIJWW4RU5En6WZ87"
        "C6Xjz3/JJfaO7hB2AkKJeGgXjs+Qo224e0S37Kh158dZjEA8+Wbq5FGiy1ssPvBBfvAf/n/QPezd2CeKAsrFGa955ApX33GNR9/+"
        "RWxdfRhzNuXuD72fs6fez3BrSNdawrYkrKYMI9AHN3h5OmN7+zKPv+ut3H72eZ64NOK5vV++XvQLiCgOJYNEEgaCvmupqoam6lks"
        "KmamZ5jGCCEozhZcbxsccP/6TWYH96nvn3FhJJlNa5xzTPGWOmtrMboTxEHwSqgrz4cOrYXWWFCCQQKZdNzb89UUB7x8z+GEn3iY"
        "SsgGgmQA1hkWxRxnHCGWOPTPU3Yd3/LEgP/l49XPd3X81RLSKySkFHzwv/xGxt0RjXLktqa+8Tynp/soAoaXLhNdyIiOzyiLJXIQ"
        "E2Y+OnC9b2jU1niD+eMp1liKWcGiWLKxtsblx6+iO01XNUQbI5AKVxrqg3uoLCLeGePKnuJD14lHCdHBke8bcg60xY1S5MkU4WL6"
        "k1OEEARJjm1aqqImQnAyK9iaDEmUn7i3ViIEKASBVHRSkoQhQSApa0schQhnqcqWJPMeVIuy9g2AncEZWBtmaKMJWuEXNgrQ1ncs"
        "bqwNCSdDhBDotiPMB6xZy+LoCKEkD1/dpWt9KTwSIWEYYbRFhQobCLJRhtbGN2EqgZKwKDu6WhMGnxxOtQyl84OwcUTXapZNhUWh"
        "RIRzjiwKEdaRxSEOx7wovfGcM4SBw9LRW4MiIUv8czaV8b5FSpJEgRfrpcQYQ9f2xGGEchAg6aaHPLgRcfO0/6yR0be8ZsKzn3iG"
        "eJRibc3GiWCsBK7vEbMatT7hzoeeIZMa6zRbX/YtNFdfy/KlU3Zf81Ye+OZtfv9b30x/dMTNjzyNrUp0YNgYb7L21jdQ3t3j+f/1"
        "zzNUPV1bkA9ynIwpXUFvQ/rGERpHaGtmx9e5fXCKEa9j64Et/ty1dX7rX/qRTz0Ev+Tx+FRjNAfwte+6yBOXd9jZ2QYcujfszxZs"
        "r41IAm8UrIRAWk2SBNw/PmUtEuy/+AInL72Aaud0nUNPHVvrAhE7dtcVWZaSRAGBUmht6Y2mb71H6KJo/G51JYikYHpq6Gpfjapa"
        "RxL5V1e2cGXXW4cOU+ELSA0I4yhKmBbw6IMRKhuSXXgEN77G9/y7F5g35lP7HH6laZvjfIL8R//cb2JTnmGqAtHO6I8PSC9tgO5Q"
        "y9qPkEcSN5tRLAuQgiSNCdOEellRLSt0r2m7jmGaEASKs8WSrjf01vCat76Wal7StC1JEJBPBpiq5fRoST7KSULhGw6LkjYM2Hj0"
        "iiehqvXVNN1T7R+idMByuWB9ew36lr2DE5IooKt76rZjazzEWEeaJ0jnKMoahyAKJXES0tYtQkh603G6WOKsRGvBME9ozmczhBQY"
        "bQmlRBtD22kGWcKi8h3lUZYyHA4YDDPSLCZMUpbzgjSKcabB2ZZkOPAEVRWcTQuquicMlPc5Ep4A4iigbDq0towHCdaBM5a2qpFS"
        "oFTIbFljnSWNQ5Ioou96FnVPLxVxFNFpTa/1+Wycw2ivbaECOt2fD7/6nqFhlp0Pc/sIDCBNvHhdVA3aOpwxNJ0lzRKcCtgcrPHS"
        "8YLhxYf5o/92QdF+Rm2L3SfL73/7q7eZndwhygKkNFy+MOSJ3/YVCCl46h/8G3a2H2DcnDDtNMO3v5eNJ74UV8xY3LpFlA04q1qO"
        "5yXze3d5/fu+ku6jP85LP/UfUEFIZg2Z7HARDOKUVDlUEtGrgMB2VNOS05MG5xzFsiE2krk2iCCmiTKuvu5xfvgg4C//i+d+Wcfi"
        "F0REj18ZkUnHcj5H65aqqkgCxfK4YmYtEkfd9VxcG9M1gkg3zBct2Xid13/x27n51EeY3ThhdyRpC0tmYCYNtS5ZGySMshjnLMM0"
        "RmYJTd3ijCKOfKt+3RvWxpbGOZaV71WdzX2fySj3Ewsy9Mv0zqY+Q0HAMIZLWzDMY+Ztx97NZ5jEN/n/vmGHweNv4o/9s2c4nOtf"
        "6azMK/T1J77yYXaqPSrdohYH4Cp6o0nLHlssEQGIrsLOG1ACGSjatsMJQRAHSCVwziCFZWM89LvdF3PmVUUcJvTGMrt7RBidV3RG"
        "Ct32BEjyJMIZDXFO33Zk4wFUPe3tY2SaIHWPjQNE2aBUwN7eCaMsYHlyxqIqGWQpdadZlDXDKGRRlDjn0KYnVIq66xnnGWEA/SvN"
        "jhFRoJgMM9reons/NlG3niyMNqRRQNP3KCGI4oC27+k7S9n2rCURQSCp244oCnFaM1obUh1NOSuWrA9T75AWBzS9JYpisiRlsSwY"
        "DzOUUhxPC5quJwh8930WRRRNy7ys2BznSClYzCo8d3kjOHCewOKASAhmxYIgVCSBRBuHlYLGWiKlaLVBaz/uIeV5ZKj8wKwysDZK"
        "WZY1ddMhlfB9Urqn6QxKKiKlOC0qhFNcGKcc7V/nr37dY/zh90/5uQ3Hr350NIgEspli8V3zURiRhQH6xXuEb3sdW3nKjeef5Y1f"
        "881ce9+3++78/SNEX6Ol4vZTTzG/+QyLo7uY1nJU32I5OyBRkCeGvtes7WySjzJi6VBPXMAKjZiVuPUx2Qt7JMEJJ4czXBIxnTUY"
        "3eH6hvr4kHvVkrdvb/NHvvY1/JUffP4/eiw+1QbkewEujWFxuqRre9AtdVHTNB1l6cVGqy2zecn941MGacR8OifA0XYaG4aMtydc"
        "2h0RbaasXxwjbI9se6JUcFZ6n74gVFzd3WSSp5RlQ9N0uHP9qCh7ytphtG9iW9RgunOvmnOLiKo9d/Lzlj7IwDNqngnSLEAqRaQE"
        "CMtsWZIXZ3z5RfjK1w54cQrL1vz87SDfe/7n59s4fC/A7iTkL33dRe7d3cPMT6iKKVmk/HhGURKEFqEsKgroGz/BLpVEKokzFmkt"
        "xlgGceyXsvb9+aJDaPrem8srn7YKJXHOEYWKtu5QFn7gx17i+f0lm1s5d+7c4+7dKeM0oa4ajvaOUVJxdHTKYlYQh4rre0dkSUga"
        "SeZlQ39+s8WJ761aVi1pEvgd9UAaR2RZgu41ndb+MrHeHaHTBikkxliEFCRxQN8bH8kYv7s+DEKcEAgETdMTBr76tLWzQZLEJElE"
        "NEiRec7p3gHCaJqy4WS6QDmYLypviiYFVatJBilG+2NmnfN9UlJS9x3a9Od9PJK1tdErbatN19H2hiSKqLueOFB0ne8ViqU8H/Hw"
        "ek6SREjlidWBH/btNfqTo/g46rbDOkPb9XTGT/TPi5pACeIoJFD+/QZS0uoOgUIFEctiyn/2povcmBuOCvOZsAj5XoB3XMl4vTyk"
        "alsGWUKSJMSRIpMWliUbV3a49uRVbjxzg9GTb0ehvC/8YERUFNz56E9SnN3koQcuMVrP2MoNk60Ja3nG5pULbD98kTSQJOtj5O4a"
        "bG8jdi8hhhuIjU1U38DxKbpu6buequtAayKlcEJimo56seCBoOLSYw/xoZuzX/JY/AIiesu1AYv5nPEgOrfr7FEY2rphZ23I/tGU"
        "2bxgkMRYo4lk4MvreYLCcVJZti5cIc432XroGtY1dNWSRx+8QJoGCKlYtjUWSENF3/U4LEJKqkZTl9b71vSQR55o2u68a/rcX9na"
        "8w7d8++XtV9yMcyg1haH9Yb+TtN3DbbX6K4nquZ8xbbh6163zuXNhHulo2zMzz/J3/fzo6G//LU7RIv7HB7uUS9PUM4wny2ZVwXh"
        "uW5hjKFvNXXT0WtNksR0fc9glBOqAKst0gmkU5zNCtpOg3MUTYs2lqrpGGTek8g5i+79FLx0lllRc3g2R3YFwyTheFqwuz3x83pK"
        "sihKyronDyN0b+hsy/b6GpEQ5Gl07h0dEMcho1FGkkSEcchwmJOlMcLiK0HOb19R0nt3ZLEvTzddj9YOpcQrKa42lqJuzonKfz9S"
        "6pXf11Q9XdMz3hgRjXNEEFAez2gWM6qqpK0bhPVis3SaO/dPMb1mOEgZpglRkuCMZrmsCJ3wcoAEKSVN07OWJtSln5S31vmSu1Rk"
        "cUjd9pRNd06SijgMMMbhpMA46K1/r02j/RjL+ShJICVV12OtI4kiBlnCdFlRNf0r7pGLsgMsSRxQ1g1Ga7JYeTO4KCJC0HZLvvqB"
        "Mcc93J6ZT3dt/ScXTX7La3OuNLeZljWua9BNTVm2HB2fsrM2IHzjE4hAMdYlBCPCR96IMA3OOFSQs64anvvxH6J3mo2NDS5cushg"
        "NGRw6SLRlV0CHGo0hMkYujmcFjBd0nz0RfSzL2L3D3HGj/WY3lAVPbrvcdZ7hWvjZ3vKuuYBtWDnkYf4mduLX/RY/ILU7KW9U167"
        "OyJWAVXfoWKYHpc8c+M2B9MZQgRsjEYkach6mmGFJE4DojRiMsx5dJySqIhUGE7PpohLD7GZWBZnJ+RZyLXLm9y8f8zZosQ2PVV5"
        "bmpmQLfOG2gZb6J1UviRKif99+T5mppPWpEK4UcB8sxbSHQ99MoSOkMaK4z1ox+Nbv0CPadY1iXMb/LmjQFf8iWX+Mcva95/fUGr"
        "P33ouDNSPORmnEyXdO2cuq+JgyFl09IbA1bTd14IRUpUqMjjlKroiaKQ5azAGUdRNmjtN59a55BS0nY+MrPOsawaXpOnHJ4tGKYZ"
        "Qkiq1pAmAV/8lgd4+HhCLBUqCLl5tOB0Xr6SVhjj2BmNWd/ZRGHYXht5NwStaXTLME+QQoEQCBEShoYwkFjrvPVIdB59WEeeel9W"
        "rQ1C+F4sKQRrw5TO9OgewkShbXsuHge02g/JJnGAtpZGt3SNwQVLbu8d89qtMS4N0XXlLWlFgJG+6maNZu9kSds7TG5ZljVxFDBc"
        "D+l1z2QYo1uDxDFKYuq2Z5LGrxDhMM0wDoZp5t9v1/vqn7GESmLxx9rgF1la568L8Hqb77KQKCxhoGiNQSmJsZajaeHTOevoeo21"
        "/jHCCYzpMc6wPsqZLmrSSEFQIqxiqFNm02P+89df5MP7LWX3qlTTXiGhLFG8a1NycFSThxIM3N2fszEZ8sijFzDOIOolTkqii2vM"
        "Du8Q951/hkZDlHPv8IDFfssgq1iezfhEXfH4299IogTdnXvYYkk0yZHHJ5Aolvu3qO/fJ7FQqZDOagYiJLCCrVHOnZtH1F0LLmSy"
        "luOWNUpaOgeH+ye8cdcxTIcsa8t/zKHxewHmy4YHNiI0FmEglYqirNhaH3B0dMbR6ZxrFzcplhW72+usTQaMhikGwzDK6GczfuAH"
        "/ikff+ojdMcH1Md3OXz5DstphRA9R9MFkywlUyHFrKQqe8pKU9bewbHr/QYJfb6xwTea+dOntSefTzr2peeOF2vDc1dAIQgiQRLH"
        "hKGiajqiQOKcZVk1BHHAZJTjhAPT0y4K3jrp+KYnL/KRuWBWdj/nWAB833u20Pdf5nh+QlsXpIGgLGvQFqMNSgqqyldK0jAglJKT"
        "s5LTeUEaKuqypW5b6rb3EYaxhFLRCUfVdvTWIvAmXGEQkESKvrP01rKsG/Ik4+7hjDzLUHGMU5I4kBydzknCgJPZknGekicZSZ5y"
        "enxMsZxT1AUH01Oy2HcGCylJ04Rq2RBGEiX9sLEQsChqmrb3HdhAlsQ4fNq1qGp6bRmkCcuqxhjHMEspm9aX3POEoul9IUL+/9n7"
        "r1hd0yy/D/s96U1f2OHESl1dHaeHnMAhJcoQo2UIkmXDkGHZli4EGzDgC18YvrB9S8J3NnxhCzKgC8GWQFuQZIFQMmglS9QQ5IxE"
        "TuyZ6Z7qruruqpN3+MIbn+SL9XxnV6cJ7O5hD9UbOKhT+5yz97ff733Xs9Z//YMW3CVCTpG2q7n34JK2cqTDSLuqSEtgGRaMlfep"
        "KWNO7RS10xijUCljUfhxkS1ijNSVJcZI8AmtFUuIxJwK8VI6MqNlrEUp1l3NEgKLT68V9ktKZGVRSpFSYlki3kdAxj+tFcrI+Pni"
        "ekADF5uWGIUHdyJFDkskeE+lDbVz3BxH2sqSU6SyGR8WNJHeT/yL/8h7/PXfviVm/YOMaPmTCvm//r/8R/nWL/9NTJWwRnA84TMZ"
        "Hr19SVo8Z3/h5+HeFhUScYhUl58l9QG9amAcCdcfMX34G3zpH/k5pqsrvvHBh4Qc8DevePLVrzH3PcPTp0zXzxhefoxyFfXjx3Q/"
        "8yVWmzUXP/MFzM2R423P9X5EXWwIU+TRe1/g03/yS7x8/oLjTY/SmqgchCOPPvt5fuVb/fe8Dt/VEVWV42p34J5xNCbhMFRWcRgX"
        "FJnH9y/50hc/x0XT0rSOl1dXPPnaN7l6+hFPTOL6+Td5aAY6Bfr5S0wtlqCVtSx9YPSJDkttNefrhufXe5SS8UoDcZYi5L1c/Yx0"
        "PUaJ7fMUZHu21tDoO5GkMxKDM6bMcRiL7acmK1hCYLOqRAs192SfUJVGKc/TF0f89S1/9ee/yP/2l2qe3wn3ePOi5p3xCS/2Nyzz"
        "wvnKokOiH33hLSlMhqw1u93Ech7ZdI1gEynz5MWOura0dYUxMC6BxhmGxTMsgcn74qmc0doyzoHzTYdXnpwzyxz54KMXMlpVNWny"
        "xBCxWB6eb/Eh0jUV1wfJMRuejoz9LZfnFVWsyDTcv9wwLZH+cGC1LGhn8SGQjSGpRH+QzumNx/e5eXWDtZolnOQxEprZ1TU3+yM5"
        "gXNikXG+7kgJGlexbgK3x5HQZNraYVKSiKAl0u8nXuVrHr/9kGkRu5PjzS1Wiyh3WiL3th1Krzj2I5UzdK6iNoZJQ3Yi65gWz7at"
        "wWZmL+Og04ZMKV5AyomuqTkMk6jpY6RrhB09+ij+QkbGXm0MXVe9/nmHOZDnQLeyHIaRBxctlRUEyhpLTCI/+ejlyKrVXJ53ZBT7"
        "cWFVOdpGM86e2Xu0slSI1vnlt36T//lPn/Gv/OYfGrjO3+tT/+d/5l2e/Vf/MeSeTSdRSFe7PW3nWFDMy4RZFsb3n9P+pT/D/MEH"
        "xI8/YH//C5z93H+H/PIJLDMXmwu6lWNVWfZZYQbFi9/8XfbO8nI/YULkUz/3Nu996QvUf+rPU3/hMyxf/lX8i485fv1j4m98lelm"
        "4Pn1kWg7Pv2X/3Hi+HdQNrH51Od499WOZ/abJKU4XN2QJrgX92WU/u7r8F2F6GaABxfnMmZYw/U08eow8uk3Lqlrx3F/5Otf/TqN"
        "aVjR8+QbH5B9T2UN3VnD6qKmcxVpPrBSGqMzldV4bxhmz/lK8+zF8XVypzMiULdarJddqT7GijWE0fDgTLof68Rg6+NXYje63Ygo"
        "/ZTDPowZGmhrS4wJ4zQxlmC/EJj9HmMUla3Jo2KOM8ZY8pj5xm/+Hf53732ev+m+wL/7X73PtjP8H//ifY5feZ9OZ6rKYDMcjoGU"
        "S3dmMrc3k4yOGpy15KwkU0spDsNEEyuWkGlqS1s5rvYHpsXTNjXWaLRSDNMCSpNRWGOxVtbLbSVjnA+B51fX3L/YkkKECCGE4scD"
        "KQW8Hxm8x5nEq9uBpnbUVY3KmXmZ5XtpyNlL55lgdzxiUqJxjv3tDmOEpjAHj9UW5xw+ZF5NA11bg9Eoo9jNnkprLrZr5vLwVdaA"
        "hmGa6Psg200TSdPCy3HifLuhahy3w4S1ms264/nVDfe2W3zMtM7y4GIjouvZ4/sRheJwHIpbQEeImRADOYvGDaWwWuG9FwmRVkIv"
        "AKY5YI0uftMVTVUzzCMxZ1qnGUIi5UQ/LxReJNuNZV4yKHlfZh8IIZJSkoJVvnfKmWn2xGLaf75pyDmiVIkUITJMe8iafa748w8a"
        "/jVTMUXzA1h5ZP4Xf+GLPDh+hecvv8WDe2uiilw+6HhsV7y4OuJng+9Hptoy/L1fpX10hvvil6jffMzN3/z3OVRbNn/yz8KrHcvz"
        "F4wfX/P+9S/yvM8MS6AzNQo43iZ+7i/+NH/if/YvYC/uM/z2b/HqX/6XsE8/wnuPbyuMqjEZLpuGl4vnN//9/y/rtmUeXvD8m9/g"
        "M//Ef5v8S79CuH7BYVl4uvP8qT/186y//CvsT1l8v9doBoq6TjxqBMi9f/+Sn/rsO/zJL3yKh+uG3/6vf4Nv/trv8PFvv0/cf4NW"
        "L2xbzbaBOB5ZDj2z98QYBTdBTjBrFc4qKmewJqGU6Mhu9mCyaDpP27E5yEbMR3h0CZerAlZH6X5WjThdtJUI3VUWsuGqlfugdoaU"
        "YfYJZxWHKXFzzEwhsV4LYJl1AJ1wGipryCly8+o57+Yd/5M/9S7/3Oc65m/+FnO/4+Xtwq4vfjVZbEznstXLGVwlBjo+JhKiVs+I"
        "QpwM87JQWcv14cihH1/f5DElFh+JMb/GZDZdLWxjrViWiM6Zw3FC60zwCzf7A5mEjwIMyngSJS3Waa5u91D8fNZtxVJW8Zuu4ziM"
        "5fVaMlAD87wwRc8wzcScqSthTa/ahhQTs/dYU1G7isM40Y8zISsihgcXZ4QgpnQoqJ3FL5K+6gw8vc74PDH7mUpbtquOcZiYxwFj"
        "FMdhoh8XGmexWqE0Rf8FVzcHNm1NBjZtI5q2eWEJsrHzUTZeKSV2/YQxitpWTD7Q1qLC75qKmDJXu562rlA5MWfpzo+TJJfIiJpx"
        "VhHiHSAeo1iH1LVFK8G/hjmiVaZrFG0jpM+6thiViSkQvLDTjVFMc6CuDOvKUJvM/ctLfvlp+n5Lkb/yXQ+mymiV+ROPat67dPxv"
        "/uwjflp9zMuPv8rZpsVYxdlZyxsPz3nnjXtcrBp+9+svuL0daSoFPtFkRf3OQ3h4n+b6W4Rf+TVefvVDvvFv/TW++h//DeZnIx99"
        "nPBD4mwFuzESG80/+uc+zxf+7C+gHt3n+B/9h9iv/wbb84bmU29Qrzacvf2Qzbql9gG0YQkZZyJLilhjePL+V3j6ZODBp97CuIr1"
        "+UPu/ew/wuf//F/ixmt+/bc++K7xzH4H0SgDvDwkPreN1Npw2A24Gr76jSMfffWrLNOez396zXmt+eazA/YQsCFABcc+sLIw3EoS"
        "slllfITLM4fCME9ROqe2Imd52K73IjhMuWSplwjicZFuyAfJFhwWoUKgpfhUVqJnlJK/4z2YVpUAv8BxlBtGISmk2+KHPExRsrwq"
        "TcqQVMKqSNdYfIyo6RnXX33J86Q5r2T7M0zivVyMDhm8vLbFS1fn50xSsLKZcfK0dSWr8Jhoqvr1ynnfD9w/7whBtjYxJrqmYt9P"
        "zD5iFs+HT6/wXh4iozXHcRKOS8EYQowYDYejrP+3bU2OkegX8Y+pKhpbYSNMg2zkKqW5OYyEshkL44K2imc3B4Zp5o17W3yK9KN0"
        "TsPkqazjanfk2c3A2/fPWXxgGT11ZXn+cuDtNyrW644YJ3ipmJeA0RFnDW2V6Cd5X8chcb+puD32bI8rclygjPrWGipnyVkU/lqB"
        "sgadEuumZj+I2t1Zea9WdcW4LGVJoUW6kQNtK0kwVWHuH44TpjJcjxNWKc7POurGsb86oF0jWFGO1E5kRyWykWGKXJ5X7MeFxhmc"
        "kXy0yhmhQFjFxbojpYxGoy2EFBimWFJIDHVtmcWhDRUjJkVup8xfuLzhX7UtYzDfpwPKNDrxxcvMf++9is+tMxURo2c0Cj9+jWne"
        "c7GpxeWBCCETQ8CnjLaan/78Jb/65ee8fD5j08D5V75Kc7FG/8IXUHFN1X+V8Zf+GuHqGW6BAaFyzaN09Js3FZ/69BvYquXVB1/j"
        "/vE5zYMW97mfhssNKmWqcZGHwSmaD58S/t432UbFy0PAzxPDtHDWNcwvvsL705E/80/9MxyaFR//9jf45odf4wtn1fecTr8zTuiv"
        "ABzGwM88tvS7A02ecWnm8OoKO/U8ulRUOVFphZ9njvvEcEyMU8JneVhzLuF5pXBsulr4JMYKr6bokdadwqrSNXj5laIUF1Uy040u"
        "ovHy9S7PpFDVxU5Ua9heaDYbSz8mVo1m9onKikwlJJjmLCkTRoy9usaK100Q3dyyyI2fUxI+UwQdPfMcWUrRMcXOdJjuKASp2J/O"
        "XkZJbTNZKbLKaKNQBRAOKZCTAKTGSLzNy5uJuqqYlsiuX8ilu9qP02twXmu5EEZrqtI1pByZfUCdYpi03MRaG/qxGPBnqLSS7K7y"
        "daZZdGAg8os5LFRO0zVN8RiSmJ2cwYfA9WHEaU3vI5tNS11ZvA/UzlFXlrquWLUVt/sD0zjTz4mmMhzLWDZO5V5Qwu8CmIJn8Qtj"
        "EG3Z4jNt02KtIauMtQbnHDlJxxyLwHScPXXlCDGyampJ6tCKmDM+JLQyXKxWVM6xH2dJpVWK3nuWKO75MUk8bEK91s0tIaK0wlkx"
        "WGtrjasUw5QwBglkNBZjFTFFFp8gC+GxclYIkDrTTwvDnFjVmnER7lHrNHGJzHMiLoF5PPKFd+/xt56o73gIM293C//7L838i28d"
        "+MfPrlnNV4z9QXyylwmjI50DR2D2HkVk3TkSgUf3L1g9uqRuGx5sO25f7rnaeboOKpV49cFH3P7a19BXR5Z+5Pb6yHE/05hM8hLn"
        "7RVcvlvR3ut49/Pv8OCde2w/+ybq4RazqeDxQ3h8Xx7qmwN89i0pJi/3LFcHhqknqoT3C94HYla0lUUtC/ubK37x//M3ePtP/ym6"
        "zZp/+9/7W3z91fh7dkTf9rFyisUPzMfM1S7SmEy/27NygePtwrf2iXWJfjlll6sgWlNbMs0rB65VWFfx3uOHHHYDT1/eYCu4uGi5"
        "2vXYSlEF8R3yo4xZuQgMH1zeOV7YJKC3NVKIYokqbsXzi4uNZX8M7IaEM3KThkUyzisHTaXRORNJTHMmIzegAoYlUI0zlRES3zxl"
        "XMlolxhsKXiLh+MkRbIuP/vixZkDBYvPAqBrAYSNMfTzTIwRMlSVZtd7+mGhNob+6EFD8ImqtoyTFz5PpAgrhem7hEztDPthQmsR"
        "ZW5XFc46xmmClOmDhE52lcLqLLymJMVnfxyprCWmJCOzUlTW0TYOpRTjvNDWjrQ74oMnpowPmdlENutauoG2pqorXt4OPD5fE3Nm"
        "8gs3x5H9LF3L7APbTcOsMs9vRion5NOPnge2ZwF3HNisah7e29DHBaUVh2GGdYU1Fk9CL57dYaSqHFobZj/RVhXzEnDOYqyIWLPK"
        "9P3E2brDGsO+H1mCjKkqZRYvsICPiWUM3FuvSc7gQ2YJkaHIi3LKXPeB2klR2R8E+1nIzEtmdjOfemMrtrpqkuWHD3RNRVaRGBOb"
        "zlH7JAU1R9ZNzTR7lgkCEBW0VnH/ydf4/OZdfvdQA5n31gv/00fXvGt3TENkX6/oQ+TB+YomehobGZaZPI9kHCkHKgfWaqoKLrZr"
        "usrKjZozbFo+/alLvvX8Y8Zx4ekLwQSn5SW3qzVZR8LuyO420u8zOShiyPz0n9hw76feZvPoHvc+8wgen8tD9t4jefCUheudrLHf"
        "fQzfekZ+9or5g+dcH48yVWhFXVlSUiw+shsmnAmoj7/GW6pn/7d/kd96uuPevc99T5b1d3ZEf1W6osQX73nGV9fgZw63t6R5QEXP"
        "iycL2WdcwXh82VgpCr7jhRy2BOka2kqRs0IzE+LCi0OPdUoiZVJid8z0g0QWhyAPd8hwdiYJDrqIz6sSqhezbM4iJb6rfE904vYo"
        "5umXZzLWxJS5PohWrSpG7DlLV5RSJqeEc5qQoKstda1er3o1sGoFT1JaTvclyO99UfpnJEJZFxDdaikcSolTYYiR4AMaiw+JcY4M"
        "k7B0jYJD72kqRe0M13vPPItmrp8STSXpGW3jiCkTfKCW4C2maeZwXARE1ZJqaE0u9qaQSZCTbI4Ke3hcFnwBW1dNizbQTzPT4vEh"
        "0I/SIV3vZ4Ypsmod2RoWX3LOYsQ5i48icThfdxz6gaubHp8Sq0okEI/uXWIN3PaTcLMkTLUkcyh0VuyOswQcBunAjIHjOBcxtGwj"
        "p1mK90lx39Z14e8kKmtpK8uuH4VHlRJLCMScMEqM/Mfgsc4RfGBV15xvOumWyKQM3meRqqTMEjKVu4s3cmXkjwF8kGubc0ZpjcrS"
        "udXOEGOQqCNXSXILMM0LoFFa0U+JaS6b3jHxu9+I/LM/35Cs459/dMNfaj5m3B3JNtOtG+paUxtFDglnCn8pLNRW4TQYq9Face+s"
        "5mLjWDcVMQRCP2EAdbbBEHn64TN81PikmPYj/bVnvB15+tGIWSLDDvpBcNjLC4g2ozYr1tsOHQPurYew3ZCXiIoKbo/kj56Rphm9"
        "BOLf+xq87NnfHLjZHaic3KOJLO4LMZdJIEnartUsxz3nOnDZtfznz8InBel/9fslvf4VrTNfOl9Ixx4TeuISiVNgWhJkiRX26a4I"
        "xSydS4zCgj75gamC9RyHwBImdpNkyZyvKnJK9FMQAmNhTC9BTpB7D2CzLYF7Gda1YvQwlk1bVpQTDNpasV1pvJdoYbEjFWmC0UJ0"
        "bGohr51AMF0e3hBAG/E/rmvNMHtCysyTFMepcMAOvXRl61YeqqRhUqV7KyNb5aRYhpTxXk7KXBCI2hoWH8gJNIp5kTdNK8gl+2Hx"
        "gqdNBQtry8+XQianTAwerWAcZyojOqcpBlIKpOTFSxrhH8nPkSAlQvk1LwKOW2NZtzWjn1kKJX/2oYQcZoJP+JL7fttPdI1wfXbH"
        "ke26oR89VW0Yh5mXL3tySrRO45fM5dkZc0yM81HImKWDDVGuVVhg1ydQEWMiPiqU0sUzSCQjPit0GeG7WuQaRiucNVSVlQNs8Ux+"
        "keTV0tENs3hKayXF01qDdYaubCfH2UuRQuxqUxZwPacEKondL7JQseUwycg04kOkqR2PLrfUlSvaNPEmausK56QIURjbOWvGSTMs"
        "kcmXuO0ZhgPs9z2Pl1ek/kDSmboxNC6htRQ3haKtDE5nvPfcO+tY16JyUEbhnGbVWZpaOFNN7dA6oZVCeYU7c7x5brh6tuf5q4km"
        "l6LgYdkrjgdpFLQX8Xi9BkzG1BU3hwmsZMKpqx23v/I+vOhx1wf2X/4687deoV7esn9xw/7FLfvdjqwyS85crFoB/nOSMFVtOAwL"
        "++NINkLEXaJhqwJ/b2zZT+n3L0Q5Kz53qTk8e8JmXRNn4c0MvTxwIfM60gUZveVzJbEhcxpV7vL/cpLkm+3aCHM1KoYpyAM/FiA4"
        "wr0LWK2ExaLLhkqXOOGukXivE3aUXwf1KcY5yepxEtC7beD2ULqyWl6Tl24cY+SGbCqJF15C4jhHbC0nT/ZZ9GzlRowloXRM8nuM"
        "FMNTkunJRdJHAdanueS/G4Uxhv0gJD/ZxJTXX7Zc05IZpozS4nW276XwrVdSPA9HT9aRtnESPJCkRbs5iklZW2sOQ+D2GDBGYQ1Y"
        "bUSgmRM5BnJGlOc5s2pqnNG82o1MsxTHnKUY55SJxf61HwONsbTOYrOmcobbYWEZPWqJ3O48rhKXzpAydddwdrFFBc/Tlz0pSTii"
        "0XJQncwryTAHJSMtgtNoo1FGM/liGpcTOUVyzviUcE3F7TiSFWA0Wmv8Ikb3ravxXkiitbOkKPITZ42M9VoRgnSGVWWJOUtRMoaQ"
        "Iz5kQhI3RvIJulaE01iuoKsrLjZrcpZCY2ymH0faRsz0UcJhQsmmNCTNs+tZsi0XObSHsmXVKUOtMFbw0W3jWHcWpWRziobVumHV"
        "1mzbugSFZtH7IZu8s1Utwl7nmBfPfhxJy4LKAdU0NA/u0fmBq2c9L68VfpbCo4M8j8Mg70tTSWqK6kBrh6st19d7OPa4JTDc9Lx4"
        "eoWbJ558/ZtMxyOvvvUtputrDvsdh30PVtNUDq2gHzzHacFoi9WGwzARk6Kxjv44cpwnhrSgHr7LV56Nv38hAsXzMfOe2qFyxC+J"
        "oQcHTJOccORyykUJyzO23HTIiJULmHtiRE+LtLqLT1yPgRevAuMM4yBdlHVSaC7PBIANSf4+CjadYtXJ11RZCsQpJ0spWILEzDh7"
        "l8TsxBYZ54RrsiyiFTKleDaVpqo0oTygdSV2ImmR8Y4SrDrNUoSSlvErl5vTlFSJ1kqBc07+PwosRVWuh/eZccmcrQVImoM86CFI"
        "J5WRn//ETbrawxjhbCWBgnOAm0GhlTCIh0m6vcoq6kpO0ZASXSOzuVaQkLZeK01YygMdC58rRkJMvLwZBcvTmto6+nEpvZlmnAUM"
        "zmSmacGWf/fqZiQtiZwVIWZy8Qi6t+nYrGr6eeK463FWCitagOpVp3hyLfeKyQI/LB5iyKgMTePYHwU7yymjjGbddVRVRYACzsO4"
        "eMZJur0YFRlDIBPI1LXjME8sEVxliBr248L5qsFHsXpVRbiqjIEsMo55SaDEb8gHKcTeZ+aQX4/ym5UjpMDHr/bCpjeglaj8j4Mw"
        "5+W9mejHyO4QCTGzH+R+iIV6Mixw/0IOshBBG03TCeHVWnDGsFk3VLXDKsVZUzNMM+MicppEYtU0tI0tUELNHCL7w5EYgry2OWIj"
        "2JzJcWJ3EKyqP0gBylnCMGsD7QZWlwrbVsJH8x4/zvT9yO72lvH2BR9+5Zv4JPQQP8+sLh/zxuffRauJ9eUW6zTjODMvgavdCGhy"
        "ElXD7D0pyXUOIdJUksT7+HNf4m/+7u23FaLvC1bfjprx/iVV/xKdM62GxsIhyQO3BHngKOC0Oe3/k+AmMcODrdxw/QKTbBtZjuIN"
        "r1L55l7axjbBG+eGs5Xl+c0sc3yQ4lI5OBylk1BOgvhCgLnYMKPKer0QIbWWzmgO8GB11wn5KK/T6lPeeiSmjEGhc6ZxlpAjS8zC"
        "iykxN8eT9YgtWVxavvdSqAbW3HVteZabbFlO0TlZ0k59whjpiMrWmH7OrAqtYJ6EXa6kw+d2VFQVDEvmOGUuOjGsi1lJp6VlC7cf"
        "EqtG/L+3XUUsncQcElWtCUHG5rYWnGeZhN3ddYppTuTkOY5BVO+1jAbOSqfoQ2SYMuM8EJOcpl0thT1mxXlXg0kcRk/WmavbCQes"
        "WvF99l664Xtbx2feTAxzYO4hlXjqOYGOGUtkmQPTmHEqM1jL3GUO48g4zpxtKq52R5raFZKi2NgarbFaYZzm5XHg+c3A2aqiSQbn"
        "RMoRcy5bXMswLUw+sl4ZQlCM5UTNCY5jADLHYxJqiBbooa5g8Z5GVzw470hls6iU2ONKARP+0W0faKuamAQWyCmx6yWAhQxnnbhJ"
        "4KBtFduuQluLdrVwnrwnp0xKiapyRBWoas3FZsNhGCCXbWLOWGehqdicr3HKcHW1J4TMze6Grj+y6la8++YFn3p0xq999QXvfy1x"
        "uAGH4jBkjJX7tWotAcX1bpSu1Wle3B45O9PM14m3f/bTbL70eT793/8fo7f3ITloLatv/l34+m8w/uZv8OLJC7714kjTtFhteXZ9"
        "ZA6JZcro7BnmTNU69ksgmYrfef/Z70lo/A7AWvGtseLzm5Gb5566ALIqSVcRUnn4S0GxpownJXI4JvjcO5bjqNiPGVMesKTk7+iS"
        "/hnK16uMANtdLeLL06hTCL3Ulfx57WQmG6cyZpVC1FRwK15krFspPraIZYeJIqWQ1+msKmbrAko7IyPSpnOCCY2JKZzsOIu41pYO"
        "r+BhUkgEA2sb+V61hHXgI1yspZs6XZ/JZ5YlvwZnQxlt+7EUykJh8KVL8hmiz/ST4EXKwKEPTEFMsboSOGitlc4QjdYCvvoYqSpD"
        "TpmVc6QsI93iBS/bD4F+FKtTreE4ikK8tkjXFDJLSNz2Elipit7PB2gqw+0x0nWWs41lCYFxCXROitc0J0KUrm/VKLYry7pp2HSO"
        "tjb4mBi9rEZ9cU7QWsbCYZRxvHWG/TBKHn2COQTONuJDHkJAKVXeT6EdKODmsKDJdI1h1dQYo+gaxzxLumsGXtweqStdvndmmIIY"
        "r43y88pYm6mcbFNf3Z5G/0ztLKumYr1yZCRqyRhFiAFnLNYagvesm4YnrzzjlDnbmNe0j1TgihihrhXrlUFrQ1s5KqvRTmGNpq1q"
        "nDU0zjCFQEJwMJ9k26mNwVhDZQ3zMFKVUApSJoZIGDyvdkfC4lmvWtpNy+N3Lrl3FjB6ls5oBNvBxVuOpm2YJtE8aqPQRka44z6j"
        "nOFn//n/IW/+5X+S8dYwVxvM9Uj49V9E/9YvwThgVOT2+oDWFSEo9v3EVHypVqs1l+99ms3ZllA3fLQb+ZM//7P82+8v7Mb8+45m"
        "r/lEGU0yift5zzxr1i6zqu7U8YuXjkCXefM0+nQOqgZ++gsNx11if5BTJMeyXaukM5kK2G0t1I3mvTccwxRYN8L/8VG+ZlM2GnWl"
        "JD2UAgzHchOX8aZxd5urrla0jXCC2lq95iU1tdwRwgHRMqplKUo5ywMy+ExEWtimFJZYNmVNJeNhLJ1h19x1iF0jAGeQEI3X18WX"
        "sdEYcZGMSV5nTKUIpbJtLJQBH+F6grNa2OKUIiDWKdJ1ek/hATkhas6iKK8qIw9pTNzsIpSfa17k+81e3reQKJ8TFnQuGF+MMMwC"
        "WIfS8WnKgaFOxmMKY8RYDaBrLbMPGJOwRjFMMlbGDOu25eH5Oft+pHaWrrPUVWaaEzpKdzktUrhK7BuoVDyUNFMI1K6iK7Yqi5cL"
        "m5PYf6QsXliLD7xxb40zhphlRb/pWmJKpXOcmX3EGUtM0M8Jqw3WVExLoG0cr3ayLYkx83In2sa6jPvTEkBlluC52Q8FG03FJVLi"
        "jCpr6ceFcU6EkKidQlu43ct7P0bpqptO45xm8RGjFF1doU2mMppt25QQy0xUYpMcUkIryxLlIHtwviaTGSbPMCzY8hBowOnSLZOx"
        "jUO3juZyw2ZVcbY1fOantnSbxELk0aMV1/sBH8Stgpxfb7wuz1r+3L/wl1i/9xbLL/0dPvyP/h3yB3+L1e7XsDxHv/UQda9FRcX8"
        "8pZx9oQoNsKzTzTOErPhZ//pf5a3f+ZnuLzccnW9J2D4D76W5Hn6AxSiv3oqRtdLzWc3B8JRgM2pbMzCIg+ktVJYYpQ3bt3ABAwR"
        "Nl0mk7je5ddr8NPaeypeQqsa9geJ8FpXkamYnsUS367K6OPc3ed9kF9VAZKNLumfQNcqtMr4kigqLfKpa5KTdPTSrRyGzHEQsLZy"
        "MM6ZyWe2W7m5Fp9fYz4RKToncqNz0qWdcCE+Qb6MuWBERrqm07/LBaz1Xn6fJCRWcK3Sse1HeNXDyxnGEVwtQKe09lpAfCNM46wy"
        "PokKPQN1bQWAFlSXHCLWScxOWORnXrx8rWmW11fbshhQMk5Ok4yPp7FqGOV1aSWdpLXQtHKjO6cxWqgIIZ06Ic28ZA79qbAm1p0j"
        "oNmcrVit1zy4XFPXGWWEyJm83FdLlmVEXRnCApuqpnWO/byUTDxHU1clfNHJ+BjhOHkq5+iquiwEMm1VA4qxjDv7cUFjQVnGRfxy"
        "lpDEfsRnhilK96cVWWnmKFvMpRyGl9uKOQTmCNYZauOwWtM0hroSVnhMic1qhTWi3QoxcyyZmIdBiu6qAVdrtqtaNr7rlvO2IanI"
        "unFYJYdITJlpDiyzRB9lpbHGMBdy27wkzu5fEHJmf3tgnBeudwMqKXxYqDtD3Qg/yxTeS/fpN9j++Z9BPXvG17/Zs+oqQvC0jWYa"
        "Ise9EGGzgrffPUOFjH31jPq9DQ9/9j22P/sZzC98EbW+gPVagKYX16jjTI6JKSw8e9VTuwZnLeMwcfSwuTzjb/2tv0c9Hfmdac2v"
        "PM/fZZL2/QrRt2nPbnLDm2onCRlGYn5cidcSawK5qU8yCOvgU2/INmCz0Uxz5NVRbvilnLyzP3F64O0HFmMSpftGKbGFDVEe1MoI"
        "DyikApSfTmgNtnqt5mUuhmpzWbs7I+v2nKVbqZyiqjTW3BW6XU9hWEv3c6LqO6cYZylozsqvrrw+Y2XjFoKcWKtGMS+yoXGlvT2J"
        "eTftHa/q1I2okkF76kCmRcbHeYFXB/kzlYXKYApLva6kpZ+9YvYldGAGbSRHrGuF9EfBeFLO6CwbueMsVIUgNs1MpRidQOOqjNWx"
        "2IIMo7yW4vfPppVrPXnYNKYU0SxbR6VZtRXGZMYpyUiytmSVCFFR27IwqBzD7Ek5U1mLdTKeLyFgHByHYnSXpCKHIJHT0ywM7GkM"
        "HCcPShGjiINnH9DGkMlcbFf0sxcdXIZh9q9NzXKWzZkPSTyWlLDHrXWMc+Y4Ro5zKWqjcIeWclhNC6waTW2lU5xDRuksBmNlxV9Z"
        "S+UqFh9QynKzX14D/mM5cHeDeIxt1gZXOSprWK8qzlYVyXuyyqxbMbZzxojW0Eca53D2lKKSqayjnxecMczDhMmZq91BxL0qk4Jn"
        "dbbhwaffpFl30r37iNm2qMcPySlw8+X3CT5wc/B4n7Aq42dFf4R1DT4pmtbx9ntv0f3ln0P99KfgbE3eblAhCfP4xQ083XH83adM"
        "Y2ScAs+vD6gsigVZaCyM19fcvLiivx243LT8x08VT3v9Xf7V9veQ+77Wnt34Fb/ZvMHPq2csg0Lp/BoYtuU0jVFO/7aGR5eKR5di"
        "tL7MkZ/5fEeKEy+vE0YL3mEM2Az3N4p3H8H1HiIK52CeM4VyRO3K154oDOlyqoe7LulEdDxtr8yJfV2KYiojoY+ZlTNQZZLKNE7z"
        "KGdSAae1EVpCjJmuqbh/rrk++NeqoHGRdbkwj4U8J9su4QStG7EjzUnIll0txSlnMFlOWG3LlqxgRGO52UVaU7oriXzHZThM4sm/"
        "HyDnhA+K2sCjc/mZlglUTlgdyUmA5Gny2OLIuD9KcOFhkM7MLWVMKMWmruDVTr7fiQsmHBteq9KdlQOj6wxtbVBWHr5hXliSANrW"
        "KNrWoHTi8mLNG48sOURIYi0TlOL5fuLZ9Z7725bLbcfZtqOyYhBn9Mirl7JKH2fZTl7tvbDsT52kgtFn3ry/YhhnzrYdbW14erUT"
        "AmuWzdW+DyiVqayhrR3jHAV/K9iVj5nKtfiQePJqIQFj2WJWyPJEl47WaVhi5vk+0NSKVa2JPjOZSAQeNCtSNkxz4rYPVE6zFPb6"
        "s+tUnADg4gzOzzW1q7FWs24qHl2ucTqzi30hV4LWBlOCA7xzxBQZ51jwUE1lNBnL4gO3h4GuLrKpDFVjuXi44vyn3oM334Cba/KT"
        "p+VEV3C9Jx2OrDcrfuFntkxJ8Z/+lx8xF9xomME18N67Hc1qxTgHNocevjZC16DGidwvxA+ecZwSt197yovbXpYvKXJ/u+FGDRx6"
        "0d9dD5GHFw1uGNBLINHw+J234MUfDKz+Hl0RDKmld4bOH0nlRK20YBZRuHMsQX4QNFzvF1LMPD5bs2prnAochsjZSm7+fpCT31WK"
        "+yvQCHenH+HZrYw4Dy7KQ1rW4adR7AT0ngBk5+TvnTqz2snpeuIagYwVJ+sI57TowTit2GUzlhVs12J9cRw9MSQZ2ZZS1E6jVxKg"
        "V2n5Ws7qQiMQpvPJcMyXU3U3yNcO8W57t26KoLeYv+0OMp6MWVEmSfl+iJxl0wrLPmS4f14kNUDIMhopZVm1DXVVEUIu74fcgK9u"
        "M994Xn7WVNa4Ub6/LiD7NMo1HL18r7NVkbiUznKzNrQrh3KSdLrpWsbgyUrRGMt52xJIaGfIWtPUjrNVB1pkM8pAP0z44Mk5MS+e"
        "VVXRVTUhZda1ZrvSZBVZCv42Lidb2jK6RthP4utqtaGfEzfHhdVWEimO/czXPp6YF9lQnm9aamdYQuRqH0RgixJ7YGM4jIEpJV70"
        "8PwIbz6sefSw5uvXnrm8h11baCLlXjJW09YO6zSTl7W2RTPPgYBiCdIVX+88T67gci0433ajSSjWbUVdyYEbY8JZTdcKO9xZhzZK"
        "aAVRXCEXLzKdTMY5izUaU1JorTW82vc0Trh5Gli/+ZD653+KfOxFmjRN6KoCbUj9yHJzEGeG7Zqzdx6S+z3f+GAhJnj4wHL5sMK2"
        "LVjNtHjWQfHyq9/Cf+MVN7/9lKe/+gEvv/mSb37lWxyOsxAWI6hsmBZFRjq5aZG4pcMwQc4kDM2q4nf8GV9//t3maL9fIfqrnyxG"
        "fWp5arZ8bjWQp8CiFDHcFaJQWlCL3Oi1VVwdPN960XO9i5x1MgaQpIj1EV720JC5WMvNd5zF+vXB+Z3QtVgoi8HVJGOWLfquXBTE"
        "ZOmYtLrTv5kiuHS1eIXUVdGiFFFtLsetswptMtvOyRy+RJYlF0EprFr9WogaT+NUkJ/Pao0tp/q6E+/inDPalKKZpVgei+eS0oXl"
        "6uXkbyp4fnM3Gk0ZZkpHVKQtofCinL1zrMxlPLVOMSygbc2r/cziExnNfggsXnG2qTn0kZc3GWfvCtxpZD1RLlIp2E0tuN3ZRotm"
        "Dbh3bjnfdpiqpF0Y4V9t1x1OK6JPdLXBOSOYWiFG1nXFR69u0VbTWIsJGXUyLHMV27plGgNdZXFWODQXZzWoyDInrJYuuyod2TDL"
        "yDrOiTl6xrBwGBYysDsGiMKB+sxbm9fujbfHmZCkO+qqio9ejPQx8/IYGELmeoD9JEXv+pj48FnkxU2mru+6QZchTKdCpKSjMobz"
        "VUuKME6eYQrEDPMSOU6RQx95dCEYXEwwp8y6q3h4vkWbVCx5xTUyJSHItbUjFXZ8Vkj3k4WTZY14bDWVjGq5EE+V1uL2EIVgd//d"
        "N7APL+HVDvXOY/JuhzKaOE2kQ884TcImJ+O0YWUDHz09spvgs5/uoHIEpRmmheNh4njTk4dAfzPw5S9/g+vrA+NxYpoDGsPNdc80"
        "RVTSvLrtGRcxhjPaMA6yyatqQ1TiZfV3bxxP9/EPXYi+qxihLE/0GVs10Y0zs1LodCe5MGXey0kIa7t9Ji53BL8lyAP2zsOKn/u8"
        "4lP3ROk8TQUHaUrEe8F32lrWNrO4R9DWApjOQf6OUndK+FiAxdmX12MhZjmhULJhOSm6fZQAGl1sRlPZgsxzAC0PbcpCqgyxMJM/"
        "gVHJzyNdkQLqSlM7S0iByiliEtU8SbRu0yxfS+c7zVrKcNsXEqSHG2Pp334TFT1uCVI0kA6zrQTDSuU1jIuMkrteOpfZe0afuDkG"
        "Xu49/ZQ4zInjFPFBybq+YF1kIddp5EA4jlJkLy81n36zRhnQ1nJ5saKpFG3r2E8zPom7wDBOYkVR5CS1tSgteE9Wiuv9hDO6sH/F"
        "NSAsAecMtbZoZFOUEHOys3XH5AOzj6Ijqw1do2WNroX2kArzPofS2RUHBGs1x35BAVOMPLxsaauK4EsxdIbn1wvTnBgWz2EUacPZ"
        "meY4Zl4d4MmhLD1yYb8Xwq7V8r69XkiUwyGUxYu4BMjGdfSBnDX97Lm+DWwb0QVqZ0hBkVzm3v0VxlVEBD/aNDXnm5ZpClRZ0ShD"
        "8OIQYJRm1TWMIeBDonXCltdKsesn6krsRjQKlSPTsqC05sHZCh0C6p1HcuAaBeOEdhZCIEyLMPb7EYNifbbiXqc5LBPJGJR2eB/p"
        "h5murvAhcrM7UivNYZjYT54YMzplpskzjpGcYFU5hmlBGeFr7Y4zh8mzbg1Lyhy8Z7Vu+NW940Wv/uDq++8TipYBlmj4VfsuX2q+"
        "xnuM9ItmNwj+c9bJ396PZWNUyejko4Cd205wm8ePGlzruR4CVSN+KIu+6xoEyBYtktWZyoqHcj9lsRcpK+1TcQtl7X3W3fGOlngC"
        "ZMUgTev0GseqjPA2wpyoKst09HLyNoZxia/Z47FgQKfN20mUW6Y8seIwYtMxL4EYDNopmkoTQ2YY5WR3RkbRY/E2WhbpqoQMqhic"
        "5dcuP0v2DtYb/oz6XfIxMqZME4ps5MRjKqPKx1dSWDbNnZ/36Tpoysi1JCpVOrEAixE8xJaNXm3hc59v+fRb9zEVvHpxRbupmaZA"
        "AC4vV+zHkaigLhq9xjkUgmOcr1umyTMvHusM/exJWR7QXFquaQ5Ya4hkXG1xKqMrQz/OOGN4cbsT5m4Ir+0/sIp33zrncQy83A/c"
        "HgLffOIJEiCLnyDNkMdEV4l1zVuPO6x1XO97zroWHz3jEoX/1CpeDsUjyQOHxKLg4xt4MYhJXFOwS+NAV3LY2Rqmwug3lZAwmTKT"
        "SkxTpGvEbF8b89q07d6ZJcdM9EI6Xa0U17MiTZHgAjFnXE5oo9n3I9O8cFgik480dYVzFme0RLJXYgHbNTVWa26OAx+9vEWrC+ra"
        "0Q8j5IgxMvalnGQ11zZy6l0fpPVeYrFOkUPLp4X90GMax+NfeI8v+YX3vz7KBtfA/e2am6NgCuPkubnq8TGhnOJ6TMQlcbESXV6M"
        "iScvDrwaM906UTmhZ9ROEzKEEEtMucd+H5PcP0hH9D27I6UUr9wFT3XF26qnXhI+FZfEcmK0lTx4p81BUxWAu1YkHZiXQFcrjqPY"
        "gGzWmou1Ef6FymxqK6rrQl6z5UaJRcQXy4r+NGYZU7ZUZc1/eh0oOdVOG6W2cWKXGpJgSwYap6mNQStTKAPiGOg/gU8odafEzxms"
        "VXifOM6BpBXVa/RcGNXHQSxHQiwAbBEFLyeW+SxOAKPXfPT4s1ylqpR9jY8j96aJYBQmwlJGt6YqMpMyXp2tpCgex7J1UvJ1NeXf"
        "hAJoF9qE97KBBFmVf+HTDe+8dYnWjuk4sz/0rx+os3Uj8gpEIOqUQaMwVrP4QF072sphcsZkWLUNGVHHi8OkjEfn606SfVPGVVba"
        "dy39aE6ZOXjxj3LiL70Ez/ObiVe7he265mzbseoq3nxYE5Pn6jYzzrIxHX1ZjVtQOjAv0irNITJMCzFGxiUzFjysbeXXYYSvfAxP"
        "ezmNFTBncb04jay2EHfneAcRTJNQIYzNHE5yqSgLFjHkz1RGfvZVIziWsxqtxEmhdZabQ8+6cSyLZ5wW1k3NdrWi7RpU4QHNXqxV"
        "Vo0kllgrrppGw6qpih5OUlx8kcCsmprNxQb99iO4uoFvPCHf7lBFHKnmRQTD00zOUhC1UjRvXHK43vHy4x4w+CT0g3EKTGMkZcU0"
        "Rppa8/B8zavbmVj0lceSyDz6zNURKp1xtmjjUmZdW4bFE7UmaMeXlzOuev6+RrPfY1RTeN3yLbPmwuzZVIlhUZKuUTRYpzRkre9E"
        "sqawYVWZcyurSFGRk2bbGYZJrCs0SFsfMynLOjgnPpGtJf9NWR7seCLh6bL6NlJQjC4WtdrgrMYowYFSYUlnBWddVexHBcRypiDF"
        "Srqhyt0VNFMK3xI+8f1TxvtEigkfE7shMs8SFHkqXCmJQFZaZsFjjhFGZfiv9f3X8T0Ak6nYzjeYLNfyxKfKiMyF0jXWjTwsORZe"
        "U+FNaeSa4O/cAZQSUPqtB4q339CsVrBZV1zdjMToudrvaRtH11RlfRzISRI0msrRNhVNSSIBxeIF0F/GCaUNwyxi2Mpq2q6hqWq0"
        "Era3s5rr3UAI4iU9zAJ0b+umsJQ1/bgUQl3ier9wf1OxrjsmH9kfR4bF8+aDjsrBN54HjrN0hHMZ28YJ+iEx+cTuGHEWbnshc25W"
        "QuW/6WUT+XwHX7sqGQgFkys0N7l+SQp+U9+B5T5BZ6ThyOX6jyP0vViFaDJOSTxU00pRjRYu7rXUtaV2gr3cX69oakvOiW3bYo3g"
        "a5UVJ0gfZasRk9hqZKWYvBcVvtI4axiXGWsN266ha5yIeq1lve7QlYX9HoYBpbWsALNEZVttJPtu9rRNJYm+j+/jK8vTrzzjOGVU"
        "TBzHQEyK4xC42DS8/WjDk5uRFBPLmLh6LvfSPMnBNy9QZaEWLR6Cz3St4ugD2VqUSjx45zP8m1/5NnfG14VI/31mLH1bgxV1y3/d"
        "fIFwtqKrM3uvSIWEd7mWcSYXMLlxsnq/vc28uIGbfWbfC34zzJGnVwuVEwb17FNp72VLFaPknp3GosregbiNFe7R+RrqWr7XqtGs"
        "W/EWDsXjOITIOC9YY2hry6bVaDK7YWaIkeMyEzLMxQ+6qTXrTtM2SryyKwHLnb1jKgu/6WS1kTkOIkHRRR6SsnSFIUrbG4J0LzeL"
        "wqP4lfWnUOrbjdWTbpnWjTC7lSIUeoI2EiS5amCzKXIRhLIfjIx7uoDqVXGYs6awqCO8+QDeeuB4fNFQGXhxPZDTwvNXB5yWzeK+"
        "n2kqS9vKjVpbKx2ROWWjSYdVVxVtLbYYIMTCw7iwH5bihDCjFMJwziejMnGYTDGyaRoZz6wpFIw7j/O3H1QoLb7brdY0ShN8Ypgi"
        "bQurteJb13DvrOj+PGxaeY9OXubjJFo+beB8LW6Zu17Y7b/zQkZlXfAGj5j6+dM9naU4DZOstsdRto0ic5HvmaJ0l02530CAbOMM"
        "yimyg1Vt2FY1j883TIuIb6vavZaNHIbxNT3ElzWl1oraWfGtMuUVZnE5uD2O3PYTPoqQ9DgtsnFzluMgtpjp2SuW2x7OtrL5qR20"
        "DcpatBHbFYXo7VAWdgMPHm+5d1lwvzGJuLnYEh/Hhfef7cgxs/SJY5FSkSB68ZofjjLapiDNWGNgHDKuqTAoVqsV/9Jvpe8bYPL3"
        "0xF9spp9YlTTfCNuedweaGMgKo3WggKncjr7Yjo/FmuPqpzQOskPsCzy5o59ZtOIVUQ/RsZZ2qCTJcjpFDtxXkK6Y1+7WrKpYlCi"
        "UK4cMYg9rdZinSASBV28o+Fi0zF7CTs0uqjaayfzdjFSW3wiJS16NFWKZypxR+XBVwaWJbPvpVCEJPynxOuJjaUUk1hpDkPm1foR"
        "H+bz7yzykjFnGt6JO9JSVOqVWGvMi/y+qe78i05M7bocLUlB76ULq508KJ96DO8+dqDFPhctsg2rFNvOsQRJ3T0OgXWree/h/df5"
        "9qu2JofEabfetbVIE1DkKLwiHyKr1hBS4JtPBgErV45xCRz6hfO1RC3t9xPzknEmEVNk8J4HZ2tJZ01ZtGt1LfYmJWdqWALOOYw2"
        "dHXFFEY2rRxE4kmlOFvdjeiNU6wazWEUbOeUXNJH+OgabmcZyWruCtIpvtqcunYl96Ox5T0sK/1tJ913LITPJck/mry4MSadUSqT"
        "tbRSp81XXVm6uuL+2brkoCWMsSTkHnMlfFMp9boIhRBLmvEsDPridX4iPXaNYwmZ4yTj7qYt2kOV0a6Wh6LSpN2B6dBz7Af8Emm0"
        "rCKTyoRxorl/ic+a93/zGqxiKJYhJklAwbqCwx6OhwyFWneywQlRIBmrhbDcNSJniU6zqjK7YPh/3b7Fk776vs2M5Qf/eE18RBl+"
        "0X+Wd9pX/Oz8Eu9hUYqWjEuyqQm9ENPeuyfYhdF3p8u6k+hoX7ZUJwZ2TLAUj+pxEaKgqwpj2UsROs3wPmZqp+kaATCVUlirJdMq"
        "Jw6Df73NkaC+zGFcaCtHiKIdsuWGsEbo7vs+cBwpc774EPvCZZpL8ghKiqyKBcf5RNHx4S6FJOSSWjJlrk3Fr6RL4Td9j4+kOz7o"
        "zvnMdMUcRGg5lO3iVMzkfJAuq8SsCZBb+EoPzuG8lSI/LPJ6pyWypERTlaRXMvcvGpTRXLotn358wRQmhimQonhsK6X48OkVq6bm"
        "0/cvmFJgmD3T4jFoNIphXhgXTyy+3wroWs3zmz3rtuWtBxfM84TTmseXGw6D2OLu+wVjFB+9vOU4erFymRNXceHteyv2cyAaqNqa"
        "HLNE/CTN+bpCa8+6rV5rpYY5ggqcr2tSynz48UJVKVatZlgy2glWd+ilAJlP3MDuE78vNuCvfUxPukBnBbR+diU8MFeSh7Mq94GR"
        "9zj5TOUyW2NO4kdSFoM7ryLHcRYHxuL2aLWWzPgCTkkQgSqhjtIl1rVls+6Y+gmrNb545Ih3uXRRlbP4lOi2LWnfszx5gWpqovcc"
        "bg+lE5Xoptl7UkzEBeaQ2V6NPFq1XL5peXkbWHqZXHIxt/voubiymjLp+XgHjRTjUNliOgnOuJ4M2yoyXz7mX/mdC9LvU2p+GIXo"
        "24qRUpqP8kM+Nlt+vnnOp/KReMjczIrWZpQTgyxlRH1tyjanW8nDdNtLa714OWH66Y58ty5VN2W5obS6036dRK0J2ZJVTlrZKSS6"
        "yhDLyYLSeJ9kC5cSKWaUUZLlZcxr7+XFB4lJKbKNygkGMBUDtlVTPJaKsyQF2NalO9v38kadb+5U3LEIE69nkYH8Vvv2d45k6juv"
        "58f6EQ/dHmKQNJEWXKEr5CjFOBTagi5F3RQ3gq6W/0YjY1zdKDF57wR3enzvnDcfnnHvsuP21TXRS+G5f3aJn2eevzwwxci8LBzH"
        "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"
    ),
    "hero": (
        "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"
    ),
    "helper": (
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
        # φωνές για τα τέρατα του μικρού
        self.snd["v_roar"] = m(0.8, lambda t, p: ((2 * ((t * (95 - 35 * p + 6 * math.sin(t * 35))) % 1) - 1) * 0.7
                                                  + _noise() * 0.35) * min(1, p * 6) * (1 - p) ** 0.7, 0.42)
        self.snd["v_chirp"] = m(0.36, lambda t, p: math.sin(6.283 * t * (700 + 900 * ((p * 3) % 1)))
                                * (1 - (p * 3) % 1), 0.22)
        self.snd["v_screech"] = m(0.6, lambda t, p: ((2 * ((t * (1300 - 600 * p)) % 1) - 1) * 0.5 + _noise() * 0.4)
                                  * min(1, p * 8) * (1 - p), 0.22)
        self.snd["v_groan"] = m(0.9, lambda t, p: _tri(105 + 25 * math.sin(t * 6), t) * min(1, p * 5) * (1 - p), 0.38)
        self.snd["v_howl"] = m(1.0, lambda t, p: math.sin(6.283 * t * (300 + 300 * math.sin(p * 3.14)))
                               * min(1, p * 4) * (1 - p) ** 0.5, 0.3)
        self.snd["v_rattle"] = m(0.5, lambda t, p: (_noise() if (t * 30) % 1 < 0.25 else 0) * (1 - p), 0.3)
        self.snd["v_gorilla"] = m(1.3, lambda t, p: (math.sin(6.283 * 70 * ((t % 0.18))) * math.exp(-(t % 0.18) * 25)
                                                     if t < 0.75 else
                                                     ((2 * ((t * (75 + 10 * math.sin(t * 30))) % 1) - 1) * 0.6
                                                      + _noise() * 0.3) * (1.3 - t) / 0.55), 0.55)
        self.snd["helper"] = m(0.42, lambda t, p: math.sin(6.283 * t * (520 if p < 0.45 else 780)) *
                               (1 - ((p / 0.45) % 1) * 0.6) if (p < 0.4 or p > 0.5) else 0, 0.28)
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
        if self.is_player:
            return self.x + math.cos(self.dir) * 44, self.y - 12 + math.sin(self.dir) * 44
        return self.x + math.cos(self.dir) * 34, self.y - 8 + math.sin(self.dir) * 34

    def draw(self, surf, cam, t):
        sx, sy = int(self.x - cam[0]), int(self.y - cam[1])
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            return
        if self.speed_t > 0 and self.moving:
            for i in range(3):
                pygame.draw.circle(surf, (255, 255, 160), (sx - int(math.cos(self.dir) * (14 + i * 9)),
                                                           sy + 18 - int(math.sin(self.dir) * (14 + i * 9))), 4 - i)
        if self.is_player:
            draw_hero_photo(surf, sx, sy, self.dir, self.walk if self.moving else None)
        else:
            draw_hero(surf, sx, sy, self.dir, self.walk if self.moving else None, self.shirt, self.helmet)
        if self.shield_t > 0:
            pygame.draw.circle(surf, (120, 200, 255), (sx, sy - 6), 34, 3)
            pygame.draw.circle(surf, (200, 240, 255), (sx, sy - 6), 30 + int(math.sin(t * 8) * 2), 1)
        if self.is_player:
            bob = int(math.sin(t * 5) * 3)
            pts = [(sx - 9, sy - 76 + bob), (sx + 9, sy - 76 + bob), (sx, sy - 65 + bob)]
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
        ph = self.walk if self.moving else t * 2
        draw_photo(surf, sx, sy, HELPER_T, f, ph, False)
        if self.barking > 0:
            pygame.draw.circle(surf, WHITE, (sx + 26 * f, sy - 62), 9)
            pygame.draw.polygon(surf, WHITE, [(sx + 18 * f, sy - 56), (sx + 12 * f, sy - 48), (sx + 24 * f, sy - 55)])
            img = font(16).render("!", True, (220, 40, 40))
            surf.blit(img, (sx + 26 * f - img.get_width() // 2, sy - 72))


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
                    self.add_text(d.x, d.y - 80, "ΕΔΩ! ΕΔΩ!", (255, 255, 255), 22)
                    self.sfx.play("helper")
        else:
            back = p.dir + math.pi
            tx, ty = p.x + math.cos(back) * 70, p.y + math.sin(back) * 45 + 18
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
                        self.sfx.play("v_" + m.t["voice"] if m.t.get("voice") else "growl", gap=0.3)
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
            if m.t.get("voice") and self.on_screen(m.x, m.y):
                m.voice_t = getattr(m, "voice_t", random.uniform(2, 5)) - dt
                if m.voice_t <= 0:
                    m.voice_t = random.uniform(3, 7)
                    self.sfx.play("v_" + m.t["voice"], gap=0.8)
            if m.t["key"] == "gorilla" and d < 500 and self.on_screen(m.x, m.y):
                self.shake = max(self.shake, 1.5)     # η γη τρέμει!
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
        draw_photo(s, 120, 600 + int(math.sin(t * 2) * 5), HERO_T, 1, t * 2, False, 1.6)
        draw_photo(s, 250, 620 + int(math.sin(t * 2 + 1) * 5), HELPER_T, 1, t * 2, False, 1.4)
        draw_photo(s, 990, 620, MT["gorilla"], -1, t * 2, False, 0.75)
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
            size = (180, 150) if boss else (118, 92)
            img = pygame.Surface(size, pygame.SRCALPHA)
            if t.get("photo"):
                sc = 82 / t.get("h", t["r"] * 3.8)
                if t.get("fly"):
                    sc *= 0.85
            else:
                sc = 1.6 if boss else 1.1
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
        page = getattr(self, "album_page", 0)
        self.text(f"Άλμπουμ Τεράτων   {n} / {len(ALBUM_ORDER)}", 34, GOLD, W // 2, 8)
        if page == 0:
            mons = list(MT)
            per_row = 8
            rows = [mons[i:i + per_row] for i in range(0, len(mons), per_row)]
            cw, ch, gap = 128, 150, 8
            for ri, items in enumerate(rows):
                x0 = (W - (cw * len(items) + gap * (len(items) - 1))) // 2
                for i, key in enumerate(items):
                    self.album_card(pygame.Rect(x0 + i * (cw + gap), 56 + ri * (ch + 8), cw, ch), key, alb)
            self.button((W // 2 - 330, 548, 300, 70), "Αρχηγοί  >", (190, 140, 40), self.album_flip, 30)
            self.button((W // 2 + 30, 548, 300, 70), "Πίσω", (80, 90, 140), self.album_close, 30)
        else:
            bosses = list(BOSSES)
            cw, ch, gap = 196, 250, 12
            x0 = (W - (cw * 5 + gap * 4)) // 2
            for i, key in enumerate(bosses):
                self.album_card(pygame.Rect(x0 + i * (cw + gap), 150, cw, ch), key, alb)
            self.button((W // 2 - 330, 548, 300, 70), "<  Τέρατα", (190, 140, 40), self.album_flip, 30)
            self.button((W // 2 + 30, 548, 300, 70), "Πίσω", (80, 90, 140), self.album_close, 30)

    def album_flip(self):
        self.album_page = 1 - getattr(self, "album_page", 0)

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
            nm = t["name"]
            self.text(nm, 16 if len(nm) <= 11 else 14, (60, 40, 30), r.centerx, r.bottom - 44, shadow_px=0)
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
