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
import heapq
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

# ---------------------------------------------------------------- δυσκολία
DIFFICULTIES = [
    dict(name="Εύκολο",   color=(70, 160, 90),  hp=0.8, speed=0.9,  dmg=0.6, elite=0.05, dodge=0.0,
         pack=False, help_cd=45, aim=520, extra=0, grow=0.06),
    dict(name="Κανονικό", color=(220, 150, 40), hp=1.4, speed=1.12, dmg=1.0, elite=0.15, dodge=0.22,
         pack=True, help_cd=75, aim=450, extra=2, grow=0.15),
    dict(name="Δύσκολο",  color=(210, 60, 60),  hp=2.0, speed=1.25, dmg=1.4, elite=0.28, dodge=0.42,
         pack=True, help_cd=100, aim=380, extra=5, grow=0.2),
]
# τρέχουσες τιμές (αλλάζουν σε κάθε κόσμο ανάλογα με δυσκολία και πόσο μακριά είσαι)
CURRENT = dict(hp=1.0, speed=1.0, dmg=1.0, elite=0.0, dodge=0.0, pack=False)

WHITE = (255, 255, 255)
SKIN = (255, 220, 180)
GOLD = (255, 205, 40)

# ---------------------------------------------------------------- τέρατα
# voice: ποια φωνή κάνει · shoot: κάθε πόσα δευτερόλεπτα ρίχνει βολή · fly: πετάει πάνω από τα κτίρια
MT = {
    "slime":    dict(name="Γλίτσα",      color=(90, 210, 90),   hp=2, speed=1.7, dmg=16, reward=2, r=18, voice="chirp"),
    "goblin":   dict(name="Γκόμπλιν",    color=(110, 170, 60),  hp=3, speed=2.4, dmg=20, reward=3, r=20),
    "ghost":    dict(name="Φάντασμα",    color=(220, 225, 255), hp=2, speed=3.0, dmg=18, reward=3, r=17, fly=True,
                     voice="howl"),
    "troll":    dict(name="Τρολ",        color=(120, 140, 110), hp=7, speed=1.4, dmg=34, reward=6, r=30, voice="roar"),
    "spider":   dict(name="Αράχνη",      color=(70, 55, 85),    hp=2, speed=3.2, dmg=16, reward=3, r=18),
    "bat":      dict(name="Νυχτερίδα",   color=(95, 65, 120),   hp=1, speed=3.6, dmg=12, reward=2, r=15, fly=True,
                     voice="screech"),
    "mummy":    dict(name="Μούμια",      color=(225, 215, 180), hp=5, speed=1.5, dmg=26, reward=5, r=20, voice="groan"),
    "dragon":   dict(name="Δρακάκι",     color=(220, 80, 50),   hp=5, speed=2.2, dmg=24, reward=6, r=24, shoot=3.0,
                     voice="screech"),
    # ---- καινούργια τέρατα
    "skeleton": dict(name="Σκελετός",    color=(235, 235, 225), hp=3, speed=2.4, dmg=18, reward=3, r=19, voice="rattle"),
    "zombie":   dict(name="Ζόμπι",       color=(120, 175, 110), hp=4, speed=1.5, dmg=22, reward=3, r=20, voice="groan"),
    "cyclops":  dict(name="Κύκλωπας",    color=(170, 140, 220), hp=8, speed=1.5, dmg=32, reward=7, r=28, voice="roar"),
    "yeti":     dict(name="Γιέτι",       color=(235, 240, 250), hp=6, speed=2.0, dmg=26, reward=5, r=26, voice="roar"),
    "mushroom": dict(name="Μανιταράκι",  color=(230, 70, 70),   hp=3, speed=1.8, dmg=14, reward=3, r=18, voice="chirp",
                     shoot=3.5, shot_col=(150, 230, 90)),
    "octopus":  dict(name="Χταπόδι",     color=(240, 110, 160), hp=4, speed=1.9, dmg=18, reward=4, r=22, voice="chirp",
                     shoot=3.0, shot_col=(80, 40, 110)),
    "robot":    dict(name="Ρομπότ",      color=(160, 170, 195), hp=6, speed=1.8, dmg=22, reward=5, r=22, voice="beep",
                     shoot=2.6, shot_col=(255, 60, 60)),
    "alien":    dict(name="Εξωγήινος",   color=(120, 230, 120), hp=3, speed=2.8, dmg=16, reward=4, r=18, fly=True,
                     voice="beep", shoot=3.0, shot_col=(120, 255, 120)),
    "scorpion": dict(name="Σκορπιός",    color=(200, 120, 40),  hp=4, speed=2.7, dmg=20, reward=4, r=22, voice="rattle"),
    "golem":    dict(name="Πέτρινο Γκόλεμ", color=(140, 135, 125), hp=10, speed=1.2, dmg=35, reward=8, r=30,
                     voice="roar"),
}
BOSS_REWARD = 40
BOSSES = {
    "boss_troll":    dict(name="Βασιλιάς Τρολ",     base="troll",    color=(110, 120, 150), hp=60, speed=1.6, dmg=40,
                          r=52, scale=1.9, shoot=2.2, shot_col=(140, 120, 100)),
    "boss_spider":   dict(name="Βασίλισσα Αράχνη",  base="spider",   color=(110, 40, 120),  hp=70, speed=2.1, dmg=30,
                          r=50, scale=2.6, shoot=2.4, shot_col=(240, 240, 240), summon="spider"),
    "boss_mummy":    dict(name="Φαραώ Μούμια",      base="mummy",    color=(240, 210, 120), hp=85, speed=1.7, dmg=40,
                          r=48, scale=2.3, shoot=2.0, shot_col=(230, 200, 120), summon="mummy"),
    "boss_dragon":   dict(name="Παγο-Δράκος",       base="dragon",   color=(90, 170, 235),  hp=95, speed=2.0, dmg=40,
                          r=55, scale=2.3, shoot=1.6, shot_col=(170, 230, 255)),
    "boss_ghost":    dict(name="Βασιλιάς Φάντασμα", base="ghost",    color=(200, 180, 255), hp=120, speed=2.2, dmg=40,
                          r=52, scale=2.8, shoot=1.5, shot_col=(200, 120, 255), summon="bat", fly=True),
    "boss_golem":    dict(name="Βασιλιάς της Λάβας", base="golem",   color=(200, 80, 40),   hp=140, speed=1.6, dmg=45,
                          r=55, scale=2.0, shoot=1.6, shot_col=(255, 120, 30), summon="dragon"),
    "boss_cyclops":  dict(name="Γίγαντας Κύκλωπας", base="cyclops",  color=(110, 170, 90),  hp=170, speed=1.7, dmg=50,
                          r=55, scale=2.1, shoot=2.0, shot_col=(150, 120, 90), summon="goblin"),
    "boss_scorpion": dict(name="Βασιλιάς Σκορπιός", base="scorpion", color=(230, 170, 50),  hp=190, speed=2.2, dmg=50,
                          r=52, scale=2.4, shoot=1.8, shot_col=(120, 255, 80), summon="scorpion"),
    "boss_skeleton": dict(name="Βασιλιάς Σκελετός", base="skeleton", color=(250, 245, 220), hp=210, speed=2.0, dmg=50,
                          r=50, scale=2.4, shoot=1.6, shot_col=(200, 255, 255), summon="skeleton"),
    "boss_alien":    dict(name="Εξωγήινος Αυτοκράτορας", base="alien", color=(160, 100, 240), hp=260, speed=2.2,
                          dmg=55, r=50, scale=2.6, shoot=1.3, shot_col=(120, 255, 120), summon="alien", fly=True),
    "boss_octopus":  dict(name="Γιγάντιο Χταπόδι",  base="octopus",  color=(230, 80, 140),  hp=290, speed=1.8, dmg=55,
                          r=58, scale=2.6, shoot=1.2, shot_col=(70, 30, 90), summon="octopus"),
    "boss_slime":    dict(name="Βασίλισσα Ζελέ",    base="slime",    color=(255, 120, 200), hp=320, speed=1.8, dmg=55,
                          r=55, scale=3.0, shoot=1.3, shot_col=(255, 150, 220), summon="slime"),
    "boss_robot":    dict(name="Σούπερ Ρομπότ",     base="robot",    color=(170, 180, 210), hp=360, speed=1.9, dmg=60,
                          r=55, scale=2.6, shoot=1.0, shot_col=(255, 60, 60), summon="robot"),
    "boss_yeti":     dict(name="Τρομερός Γιέτι",    base="yeti",     color=(225, 235, 250), hp=400, speed=2.0, dmg=60,
                          r=58, scale=2.5, shoot=1.2, shot_col=(200, 230, 255), summon="yeti"),
    "boss_storm":    dict(name="Δράκος της Καταιγίδας", base="dragon", color=(110, 90, 220), hp=460, speed=2.3,
                          dmg=65, r=58, scale=2.7, shoot=0.9, shot_col=(255, 255, 120), summon="bat", fly=True),
}
for k, v in MT.items():
    v["key"], v["boss"] = k, False
    v.setdefault("base", k)
for k, v in BOSSES.items():
    v["key"], v["boss"] = k, True
    v["reward"] = BOSS_REWARD
ALBUM_ORDER = list(MT) + list(BOSSES)
ALL_TYPES = {**MT, **BOSSES}

# ---------------------------------------------------------------- όπλα (αγοράζονται στο κατάστημα)
# kind: gun = πυροβολεί · melee = χτυπάει από κοντά (μαχαίρι, σπαθί, σφυρί)
WEAPONS = {
    "pistol":    dict(name="Πιστόλι",       kind="gun",   price=0,   cd=0.24, angles=[0], dmg=1, color=(255, 240, 120)),
    "knife":     dict(name="Μαχαίρι",       kind="melee", price=0,   cd=0.26, reach=64, arc=2.2, dmg=2, color=(230, 235, 245)),
    "smg":       dict(name="Πολυβόλο",      kind="gun",   price=80,  cd=0.09, angles=[0], dmg=1, jitter=0.09,
                      color=(255, 210, 90)),
    "shotgun":   dict(name="Καραμπίνα",     kind="gun",   price=120, cd=0.55, angles=[-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3],
                      dmg=1, life=0.45, color=(255, 170, 80)),
    "sword":     dict(name="Σπαθί Φωτιάς",  kind="melee", price=160, cd=0.34, reach=88, arc=2.6, dmg=4,
                      color=(255, 130, 40)),
    "ice":       dict(name="Όπλο Πάγου",    kind="gun",   price=200, cd=0.15, angles=[0], dmg=1, freeze=True,
                      color=(150, 225, 255)),
    "laser":     dict(name="Λέιζερ",        kind="gun",   price=280, cd=0.11, angles=[0], dmg=2, pierce=True,
                      color=(255, 90, 210)),
    "hammer":    dict(name="Σφυρί Βροντής", kind="melee", price=350, cd=0.55, reach=104, arc=3.1, dmg=8, knock=70,
                      color=(120, 200, 255)),
    "rocket":    dict(name="Ρουκετοβόλο",   kind="gun",   price=450, cd=0.5, angles=[0], dmg=3, splash=100,
                      color=(255, 120, 40)),
    "lightning": dict(name="Κεραυνοβόλο",   kind="gun",   price=600, cd=0.10, angles=[0], dmg=4, pierce=True,
                      color=(255, 255, 110)),
}
WEAPON_ORDER = list(WEAPONS)

# ---------------------------------------------------------------- κατάστημα: αντικείμενα, αναβαθμίσεις, στολές
ITEMS = {
    "bomb":    dict(name="3 Βόμβες",        price=40, add=3, desc="ΜΠΟΥΜ!"),
    "icebomb": dict(name="3 Βόμβες Πάγου",  price=60, add=3, desc="Παγώνει τα τέρατα"),
    "potion":  dict(name="Φίλτρο Ζωής",     price=50, add=1, desc="Σε σώζει!"),
}
UPGRADES = {
    "armor":   dict(name="Πανοπλία",           prices=[80, 160, 260], desc="+30 ζωή"),
    "dogbite": dict(name="Σκύλος-Φύλακας",     prices=[150],          desc="Δαγκώνει τέρατα"),
    "magnet":  dict(name="Μόνιμος Μαγνήτης",   prices=[120],          desc="Κύπελλα από μακριά"),
    "boots":   dict(name="Γρήγορα Παπούτσια",  prices=[100],          desc="Τρέχεις πιο γρήγορα"),
}
OUTFITS = {
    "explorer": dict(name="Εξερευνητής", price=0,   body=(230, 120, 40), legs=(50, 70, 140),  head="cap",
                     hat=(200, 40, 40)),
    "knight":   dict(name="Ιππότης",     price=100, body=(185, 190, 205), legs=(120, 125, 140), head="helmet",
                     hat=(170, 175, 190), plume=(220, 40, 40)),
    "ninja":    dict(name="Νίντζα",      price=150, body=(40, 40, 50),   legs=(30, 30, 40),   head="mask",
                     hat=(35, 35, 45), band=(220, 40, 40)),
    "dino":     dict(name="Δεινόσαυρος", price=250, body=(80, 170, 70),  legs=(60, 140, 55),  head="dino",
                     hat=(80, 170, 70)),
    "astro":    dict(name="Αστροναύτης", price=300, body=(240, 240, 245), legs=(210, 210, 220), head="astro",
                     hat=(240, 240, 245)),
    "gold":     dict(name="Χρυσός Ήρωας", price=450, body=(240, 190, 50), legs=(200, 150, 30), head="crown",
                     hat=(255, 210, 60), cape=(140, 50, 200)),
}

# ---------------------------------------------------------------- κόσμοι
WORLDS = [
    dict(key="city", name="Πόλη", boss="boss_troll",
         pool={"slime": 5, "goblin": 4, "ghost": 2, "troll": 1, "zombie": 2, "skeleton": 1},
         ground=(158, 155, 148), road=(62, 62, 68), park=(72, 140, 72), park_chance=0.2,
         solid="building", side_spots=("bin", "bin", "bush"), road_spot="car", park_spot="bush", tree="round"),
    dict(key="forest", name="Δάσος", boss="boss_spider",
         pool={"goblin": 4, "spider": 4, "slime": 3, "bat": 2, "mushroom": 3},
         ground=(72, 128, 62), road=(145, 108, 68), park=(115, 170, 85), park_chance=0.25,
         solid="grove", side_spots=("mushroom", "bush", "bush"), road_spot="log", park_spot="bush", tree="round_dark"),
    dict(key="beach", name="Παραλία", boss="boss_mummy",
         pool={"slime": 3, "mummy": 3, "spider": 2, "goblin": 2, "dragon": 1, "octopus": 3, "scorpion": 2},
         ground=(236, 214, 160), road=(212, 186, 132), park=(240, 222, 170), park_chance=0.3,
         solid="hut", side_spots=("sandcastle", "umbrella"), road_spot="boat", park_spot="umbrella", tree="palm"),
    dict(key="snow", name="Χιόνια", boss="boss_dragon",
         pool={"ghost": 3, "troll": 2, "bat": 3, "dragon": 2, "goblin": 2, "yeti": 3},
         ground=(236, 241, 248), road=(196, 206, 222), park=(225, 235, 245), park_chance=0.25,
         solid="cabin", side_spots=("snowman", "snowpile"), road_spot="sled", park_spot="snowpile", tree="pine"),
    dict(key="haunted", name="Στοιχειωμένο", boss="boss_ghost",
         pool={"ghost": 4, "bat": 4, "mummy": 3, "spider": 2, "skeleton": 3, "zombie": 3},
         ground=(64, 60, 74), road=(98, 94, 104), park=(52, 72, 52), park_chance=0.3,
         solid="crypt", side_spots=("pumpkin", "tomb"), road_spot="coffin", park_spot="tomb", tree="dead", dark=True),
    dict(key="volcano", name="Ηφαίστειο", boss="boss_golem",
         pool={"dragon": 4, "troll": 2, "goblin": 2, "golem": 3, "skeleton": 2},
         ground=(78, 62, 58), road=(52, 40, 38), park=(70, 52, 46), park_chance=0.25,
         solid="rock", side_spots=("rock", "crystal"), road_spot="rock", park_spot="rock", tree="dead"),
    dict(key="jungle", name="Ζούγκλα", boss="boss_cyclops",
         pool={"spider": 3, "bat": 2, "goblin": 3, "slime": 2, "mushroom": 3, "cyclops": 2},
         ground=(48, 118, 52), road=(128, 96, 56), park=(80, 160, 70), park_chance=0.3,
         solid="grove", side_spots=("bush", "mushroom"), road_spot="log", park_spot="bush", tree="palm"),
    dict(key="desert", name="Έρημος", boss="boss_scorpion",
         pool={"mummy": 4, "spider": 2, "dragon": 2, "scorpion": 5, "skeleton": 2},
         ground=(232, 202, 140), road=(206, 172, 112), park=(232, 202, 140), park_chance=0.25,
         solid="pyramid", side_spots=("cactus", "pot"), road_spot="pot", park_spot="cactus", tree="palm"),
    dict(key="castle", name="Κάστρο", boss="boss_skeleton",
         pool={"ghost": 3, "bat": 3, "troll": 2, "skeleton": 4, "zombie": 3, "golem": 1},
         ground=(128, 126, 132), road=(92, 90, 98), park=(70, 125, 70), park_chance=0.25,
         solid="castle", side_spots=("barrel", "crate"), road_spot="barrel", park_spot="bush", tree="round_dark"),
    dict(key="moon", name="Φεγγάρι", boss="boss_alien",
         pool={"ghost": 2, "slime": 3, "alien": 5, "robot": 3},
         ground=(186, 186, 198), road=(140, 140, 156), park=(60, 58, 80), park_chance=0.3,
         solid="dome", side_spots=("rock", "crystal"), road_spot="crystal", park_spot="rock", tree="none"),
    # ---- καινούργιες πίστες
    dict(key="sea", name="Βυθός", boss="boss_octopus",
         pool={"octopus": 5, "slime": 3, "ghost": 2, "scorpion": 2, "skeleton": 2},
         ground=(214, 200, 150), road=(40, 110, 170), park=(70, 150, 190), park_chance=0.3,
         solid="coral", side_spots=("shell", "seaweed"), road_spot="chest", park_spot="seaweed", tree="kelp"),
    dict(key="candy", name="Καραμελοχώρα", boss="boss_slime",
         pool={"slime": 5, "mushroom": 3, "bat": 2, "goblin": 2, "zombie": 2},
         ground=(255, 205, 230), road=(250, 240, 222), park=(190, 245, 215), park_chance=0.3,
         solid="cake", side_spots=("lollipop", "candy"), road_spot="candy", park_spot="lollipop", tree="lollipop"),
    dict(key="factory", name="Εργοστάσιο", boss="boss_robot",
         pool={"robot": 6, "alien": 2, "golem": 2, "zombie": 2, "spider": 2},
         ground=(112, 117, 128), road=(66, 68, 76), park=(90, 95, 105), park_chance=0.2,
         solid="machine", side_spots=("crate", "barrel"), road_spot="barrel", park_spot="crate", tree="none"),
    dict(key="iceberg", name="Παγόβουνο", boss="boss_yeti",
         pool={"yeti": 5, "ghost": 2, "bat": 2, "troll": 2, "golem": 2},
         ground=(205, 232, 250), road=(150, 200, 235), park=(225, 245, 255), park_chance=0.25,
         solid="ice", side_spots=("snowpile", "crystal"), road_spot="snowpile", park_spot="snowman", tree="pine"),
    dict(key="sky", name="Σύννεφα", boss="boss_storm",
         pool={"bat": 3, "alien": 3, "dragon": 3, "ghost": 3, "cyclops": 2},
         ground=(248, 250, 255), road=(150, 200, 250), park=(255, 240, 250), park_chance=0.3,
         solid="cloud", side_spots=("cloudpuff", "crystal"), road_spot="cloudpuff", park_spot="cloudpuff", tree="none"),
]
WORLD_GOALS = [30, 35, 40, 45, 50, 50, 55, 60, 65, 70, 60, 65, 70, 75, 80]   # τέρατα πριν έρθει ο αρχηγός
for _w, _g in zip(WORLDS, WORLD_GOALS):
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


def draw_crown(surf, x, y, w):
    pts = [(x - w, y), (x - w, y - w * 0.8), (x - w * 0.5, y - w * 0.35), (x, y - w), (x + w * 0.5, y - w * 0.35),
           (x + w, y - w * 0.8), (x + w, y)]
    pygame.draw.polygon(surf, GOLD, pts)
    pygame.draw.polygon(surf, (180, 120, 10), pts, 2)
    pygame.draw.circle(surf, (230, 40, 60), (int(x), int(y - w * 0.3)), max(2, int(w * 0.18)))


HEAD_TOP = {"troll": 51, "ghost": 36, "spider": 18, "mummy": 36, "dragon": 36, "goblin": 34, "slime": 20, "bat": 30,
            "skeleton": 36, "zombie": 36, "cyclops": 56, "yeti": 52, "mushroom": 34, "octopus": 40, "robot": 46,
            "alien": 44, "scorpion": 22, "golem": 56}


def draw_monster_type(surf, sx, sy, t, f, ph, flash=False, scale=None):
    """Σχεδιάζει οποιοδήποτε τέρας (και αρχηγό με στέμμα) με κέντρο τα πόδια στο (sx, sy)."""
    scale = scale if scale is not None else t.get("scale", 1.0)
    fn = DRAWERS[t["base"]]
    col = t["color"] if t["boss"] else None
    top = sy - HEAD_TOP.get(t["base"], 40) * scale
    if abs(scale - 1.0) < 0.01:
        fn(surf, sx, sy, f, ph, flash, col)
    else:
        tmp = pygame.Surface((170, 170), pygame.SRCALPHA)
        fn(tmp, 85, 125, f, ph, flash, col)
        sw = int(170 * scale)
        img = pygame.transform.scale(tmp, (sw, sw))
        surf.blit(img, (sx - sw // 2, sy - int(125 * scale)))
    if t["boss"]:
        bob = math.sin(ph) * 5 * scale if t["base"] in ("ghost", "bat", "alien") else 0
        dx = 12 * f * scale if t["base"] in ("spider", "dragon", "scorpion") else 0
        draw_crown(surf, sx + dx, top + 4 * scale + bob, 9 * scale)
# ---------------------------------------------------------------- καινούργια τέρατα (σχέδια)
def draw_skeleton(surf, sx, sy, f, ph, flash, col=None):
    bone = WHITE if flash else (col or (235, 235, 225))
    dark = (60, 60, 70)
    sw = math.sin(ph * 1.8) * 6
    shadow(surf, sx, sy + 20, 26)
    limb(surf, bone, (sx - 4, sy + 2), (sx - 4 + sw, sy + 18), 4)
    limb(surf, bone, (sx + 4, sy + 2), (sx + 4 - sw, sy + 18), 4)
    pygame.draw.ellipse(surf, bone, (sx - 8, sy - 2, 16, 7))
    pygame.draw.line(surf, bone, (sx, sy - 2), (sx, sy - 18), 3)
    for i in range(4):
        y = sy - 16 + i * 4
        pygame.draw.arc(surf, bone, (sx - 9, y - 3, 18, 8), 3.4, 6.0, 2)
    limb(surf, bone, (sx - 6 * f, sy - 15), (sx - 10 * f, sy - 2 + sw * 0.4), 3)
    hand = (sx + 14 * f, sy - 6 - sw * 0.3)
    limb(surf, bone, (sx + 6 * f, sy - 15), hand, 3)
    # κόκαλο-ρόπαλο
    end = (hand[0] + 6 * f, hand[1] - 18)
    pygame.draw.line(surf, bone, hand, end, 4)
    for p_ in (hand, end):
        pygame.draw.circle(surf, bone, (int(p_[0] - 2), int(p_[1])), 3)
        pygame.draw.circle(surf, bone, (int(p_[0] + 2), int(p_[1])), 3)
    hx, hy = sx + 2 * f, sy - 27
    pygame.draw.circle(surf, bone, (hx, hy), 10)
    pygame.draw.rect(surf, bone, (hx - 6, hy + 4, 12, 7), border_radius=2)
    pygame.draw.circle(surf, dark, (hx - 4 + 2 * f, hy - 1), 3)
    pygame.draw.circle(surf, dark, (hx + 4 + 2 * f, hy - 1), 3)
    pygame.draw.circle(surf, (255, 80, 80), (hx - 4 + 2 * f, hy - 1), 1)
    pygame.draw.circle(surf, (255, 80, 80), (hx + 4 + 2 * f, hy - 1), 1)
    for i in range(-2, 3):
        pygame.draw.line(surf, dark, (hx + i * 2.5, hy + 6), (hx + i * 2.5, hy + 10), 1)


def draw_zombie(surf, sx, sy, f, ph, flash, col=None):
    skin = WHITE if flash else (col or (120, 175, 110))
    shirt = WHITE if flash else (80, 110, 170)
    pants = WHITE if flash else (110, 80, 60)
    sw = math.sin(ph * 1.1) * 5
    shadow(surf, sx, sy + 20, 28)
    limb(surf, pants, (sx - 4, sy + 3), (sx - 4 + sw, sy + 18), 7)
    limb(surf, pants, (sx + 4, sy + 3), (sx + 4 - sw, sy + 18), 7)
    pygame.draw.rect(surf, shirt, (sx - 10, sy - 16, 20, 21), border_radius=5)
    for i in range(3):   # σκισμένο πουκάμισο
        x = sx - 8 + i * 7
        pygame.draw.polygon(surf, skin, [(x, sy + 5), (x + 3, sy - 1), (x + 6, sy + 5)])
    a = math.sin(ph * 1.1) * 3
    limb(surf, skin, (sx + 2 * f, sy - 12), (sx + 22 * f, sy - 13 + a), 6)
    limb(surf, skin, (sx - 5 * f, sy - 9), (sx + 18 * f, sy - 7 - a), 6)
    hx, hy = sx + 1 * f, sy - 27
    pygame.draw.circle(surf, skin, (hx, hy), 10)
    pygame.draw.polygon(surf, (60, 50, 40), [(hx - 10, hy - 4), (hx - 6, hy - 12), (hx, hy - 9), (hx + 5, hy - 13),
                                             (hx + 10, hy - 4)])
    pygame.draw.circle(surf, WHITE, (hx + 4 * f, hy - 1), 4)
    pygame.draw.circle(surf, (20, 20, 20), (hx + 5 * f, hy - 1), 2)
    pygame.draw.circle(surf, (230, 230, 200), (hx - 3 * f, hy), 2)
    pygame.draw.line(surf, (60, 30, 30), (hx - 4, hy + 5), (hx + 4, hy + 6), 2)
    pygame.draw.line(surf, (60, 60, 60), (hx - 7, hy - 6), (hx - 2, hy - 3), 1)


def draw_cyclops(surf, sx, sy, f, ph, flash, col=None):
    skin = WHITE if flash else (col or (170, 140, 220))
    dark = WHITE if flash else shade(skin, 0.7)
    sw = math.sin(ph) * 6
    shadow(surf, sx, sy + 26, 50)
    limb(surf, dark, (sx - 10, sy + 4), (sx - 10 + sw, sy + 24), 12)
    limb(surf, dark, (sx + 10, sy + 4), (sx + 10 - sw, sy + 24), 12)
    limb(surf, skin, (sx - 18 * f, sy - 16), (sx - 24 * f, sy + 4 + sw * 0.5), 10)
    pygame.draw.ellipse(surf, skin, (sx - 21, sy - 28, 42, 38))
    pygame.draw.polygon(surf, (140, 100, 60), [(sx - 20, sy + 2), (sx + 20, sy + 2), (sx + 16, sy + 12), (sx + 6, sy + 8),
                                               (sx - 4, sy + 13), (sx - 16, sy + 9)])
    hx, hy = sx + 3 * f, sy - 40
    pygame.draw.circle(surf, skin, (hx, hy), 16)
    pygame.draw.polygon(surf, (240, 230, 200), [(hx - 4, hy - 14), (hx, hy - 26), (hx + 4, hy - 14)])
    pygame.draw.circle(surf, WHITE, (hx + 2 * f, hy - 2), 9)
    pygame.draw.circle(surf, (230, 60, 60), (hx + 5 * f, hy - 2), 5)
    pygame.draw.circle(surf, (20, 20, 20), (hx + 6 * f, hy - 2), 2)
    pygame.draw.line(surf, dark, (hx - 9, hy - 12), (hx + 10, hy - 10), 3)
    pygame.draw.arc(surf, (60, 20, 20), (hx - 8, hy + 2, 16, 10), 3.4, 6.0, 3)
    hand = (sx + 26 * f, sy - 2 + sw * 0.3)
    club = (sx + 34 * f, sy - 42)
    limb(surf, skin, (sx + 18 * f, sy - 16), hand, 10)
    limb(surf, (120, 80, 40), hand, club, 9)
    pygame.draw.circle(surf, (110, 70, 35), (int(club[0]), int(club[1])), 11)


def draw_yeti(surf, sx, sy, f, ph, flash, col=None):
    fur = WHITE if flash else (col or (235, 240, 250))
    shadowc = WHITE if flash else shade(fur, 0.82)
    face = WHITE if flash else (110, 160, 220)
    sw = math.sin(ph * 1.2) * 6
    shadow(surf, sx, sy + 24, 46)
    limb(surf, shadowc, (sx - 9, sy + 4), (sx - 9 + sw, sy + 22), 12)
    limb(surf, shadowc, (sx + 9, sy + 4), (sx + 9 - sw, sy + 22), 12)
    for dx, dy, r in ((-12, -10, 14), (12, -10, 14), (0, -16, 16), (0, -2, 15), (-10, 2, 10), (10, 2, 10)):
        pygame.draw.circle(surf, fur, (sx + dx, sy + dy), r)
    a = math.sin(ph * 1.2) * 4
    for side in (-1, 1):
        pygame.draw.circle(surf, fur, (sx + side * 22, sy - 10 + a * side), 9)
        pygame.draw.circle(surf, fur, (sx + side * 25, sy + 4 + a * side), 8)
        pygame.draw.circle(surf, face, (sx + side * 26, sy + 10 + a * side), 5)
    hx, hy = sx + 2 * f, sy - 34
    for dx, dy in ((-8, -4), (8, -4), (0, -10), (0, 2)):
        pygame.draw.circle(surf, fur, (hx + dx, hy + dy), 11)
    pygame.draw.ellipse(surf, face, (hx - 9 + 2 * f, hy - 5, 18, 15))
    pygame.draw.polygon(surf, (200, 200, 210), [(hx - 12, hy - 12), (hx - 18, hy - 24), (hx - 7, hy - 15)])
    pygame.draw.polygon(surf, (200, 200, 210), [(hx + 12, hy - 12), (hx + 18, hy - 24), (hx + 7, hy - 15)])
    pygame.draw.circle(surf, (20, 30, 60), (hx - 3 + 3 * f, hy - 1), 2)
    pygame.draw.circle(surf, (20, 30, 60), (hx + 3 + 3 * f, hy - 1), 2)
    pygame.draw.rect(surf, (40, 30, 60), (hx - 5 + 2 * f, hy + 4, 10, 5), border_radius=2)
    pygame.draw.polygon(surf, WHITE, [(hx - 4 + 2 * f, hy + 4), (hx - 2 + 2 * f, hy + 8), (hx + 2 * f, hy + 4)])
    pygame.draw.polygon(surf, WHITE, [(hx + 1 + 2 * f, hy + 4), (hx + 3 + 2 * f, hy + 8), (hx + 5 + 2 * f, hy + 4)])


def draw_mushroom(surf, sx, sy, f, ph, flash, col=None):
    cap = WHITE if flash else (col or (230, 70, 70))
    stem = WHITE if flash else (245, 230, 200)
    hop = abs(math.sin(ph * 2)) * 5
    y = sy - hop
    shadow(surf, sx, sy + 18, 30)
    sw = math.sin(ph * 2) * 4
    limb(surf, (200, 170, 130), (sx - 5, y + 8), (sx - 6 + sw, y + 17), 5)
    limb(surf, (200, 170, 130), (sx + 5, y + 8), (sx + 6 - sw, y + 17), 5)
    pygame.draw.rect(surf, stem, (sx - 10, y - 12, 20, 24), border_radius=8)
    pygame.draw.circle(surf, (20, 20, 20), (sx - 4 + 3 * f, y - 3), 3)
    pygame.draw.circle(surf, (20, 20, 20), (sx + 4 + 3 * f, y - 3), 3)
    pygame.draw.line(surf, (20, 20, 20), (sx - 7 + 3 * f, y - 8), (sx - 2 + 3 * f, y - 6), 2)
    pygame.draw.line(surf, (20, 20, 20), (sx + 7 + 3 * f, y - 8), (sx + 2 + 3 * f, y - 6), 2)
    pygame.draw.arc(surf, (120, 40, 40), (sx - 4 + 3 * f, y + 1, 8, 6), 0.2, 2.9, 2)
    pygame.draw.ellipse(surf, cap, (sx - 22, y - 32, 44, 28))
    pygame.draw.rect(surf, cap, (sx - 22, y - 18, 44, 6), border_radius=3)
    for dx, dy, r in ((-12, -22, 4), (4, -26, 5), (12, -16, 3), (-3, -16, 3)):
        pygame.draw.circle(surf, WHITE, (sx + dx, int(y + dy)), r)


def draw_octopus(surf, sx, sy, f, ph, flash, col=None):
    body = WHITE if flash else (col or (240, 110, 160))
    dark = WHITE if flash else shade(body, 0.75)
    shadow(surf, sx, sy + 18, 40)
    for i in range(6):
        x0 = sx - 15 + i * 6
        pts = []
        for k in range(6):
            yy = sy - 6 + k * 4.5
            xx = x0 + (i - 2.5) * k * 1.6 + math.sin(ph * 2.5 + i + k * 0.7) * 3
            pts.append((xx, yy))
        pygame.draw.lines(surf, dark, False, pts, 6)
        for k in (2, 4):
            pygame.draw.circle(surf, (255, 200, 220), (int(pts[k][0]), int(pts[k][1])), 2)
    pygame.draw.ellipse(surf, body, (sx - 19, sy - 40, 38, 40))
    pygame.draw.ellipse(surf, shade(body, 1.15), (sx - 11, sy - 36, 12, 10))
    for dx in (-7, 7):
        pygame.draw.circle(surf, WHITE, (sx + dx + 3 * f, sy - 18), 6)
        pygame.draw.circle(surf, (20, 20, 20), (sx + dx + 5 * f, sy - 18), 3)
    pygame.draw.ellipse(surf, (120, 30, 60), (sx - 4 + 3 * f, sy - 10, 8, 6))


def draw_robot(surf, sx, sy, f, ph, flash, col=None):
    metal = WHITE if flash else (col or (160, 170, 195))
    dark = WHITE if flash else shade(metal, 0.6)
    sw = math.sin(ph * 1.5) * 4
    shadow(surf, sx, sy + 20, 36)
    pygame.draw.rect(surf, dark, (sx - 12 + sw, sy + 6, 9, 14))
    pygame.draw.rect(surf, dark, (sx + 3 - sw, sy + 6, 9, 14))
    pygame.draw.rect(surf, (50, 50, 60), (sx - 14 + sw, sy + 16, 13, 5))
    pygame.draw.rect(surf, (50, 50, 60), (sx + 1 - sw, sy + 16, 13, 5))
    pygame.draw.rect(surf, metal, (sx - 15, sy - 20, 30, 28), border_radius=5)
    pygame.draw.rect(surf, dark, (sx - 15, sy - 20, 30, 28), 2, border_radius=5)
    light = (255, 60, 60) if int(ph * 2) % 2 else (255, 200, 60)
    pygame.draw.circle(surf, light, (sx, sy - 7), 5)
    pygame.draw.rect(surf, (60, 200, 255), (sx - 10, sy - 16, 6, 3))
    pygame.draw.rect(surf, (60, 255, 120), (sx + 4, sy - 16, 6, 3))
    for side in (-1, 1):
        a = math.sin(ph * 1.5) * 4 * side
        limb(surf, dark, (sx + side * 15, sy - 14), (sx + side * 22, sy - 2 + a), 6)
        pygame.draw.circle(surf, (90, 90, 100), (int(sx + side * 22), int(sy + 1 + a)), 5)
    pygame.draw.rect(surf, metal, (sx - 11, sy - 38, 22, 17), border_radius=4)
    pygame.draw.rect(surf, (30, 30, 40), (sx - 8, sy - 33, 16, 7), border_radius=3)
    pygame.draw.rect(surf, (255, 50, 50), (sx - 6 + 3 * f, sy - 31, 6, 3))
    pygame.draw.line(surf, dark, (sx, sy - 38), (sx, sy - 46), 2)
    pygame.draw.circle(surf, light, (sx, sy - 47), 3)


def draw_alien(surf, sx, sy, f, ph, flash, col=None):
    skin = WHITE if flash else (col or (120, 230, 120))
    bob = math.sin(ph * 2) * 4
    shadow(surf, sx, sy + 20, 30)
    y = sy - 8 + bob
    # ιπτάμενος δίσκος
    pygame.draw.ellipse(surf, (150, 150, 170), (sx - 24, y + 2, 48, 14))
    pygame.draw.ellipse(surf, (200, 200, 220), (sx - 20, y + 2, 40, 8))
    for i in range(5):
        c = (255, 230, 80) if (i + int(ph * 3)) % 2 else (255, 100, 100)
        pygame.draw.circle(surf, c, (sx - 16 + i * 8, int(y + 11)), 2)
    pygame.draw.ellipse(surf, skin, (sx - 7, y - 12, 14, 16))
    pygame.draw.circle(surf, skin, (sx + 1 * f, int(y - 22)), 11)
    pygame.draw.ellipse(surf, (20, 20, 30), (sx - 8 + 2 * f, y - 26, 7, 10))
    pygame.draw.ellipse(surf, (20, 20, 30), (sx + 1 + 2 * f, y - 26, 7, 10))
    pygame.draw.circle(surf, WHITE, (sx - 6 + 2 * f, int(y - 24)), 1)
    pygame.draw.circle(surf, WHITE, (sx + 3 + 2 * f, int(y - 24)), 1)
    for side in (-1, 1):
        pygame.draw.line(surf, skin, (sx + side * 4, y - 31), (sx + side * 8, y - 40), 2)
        pygame.draw.circle(surf, (255, 230, 80), (sx + side * 8, int(y - 41)), 3)
    if not flash:
        dome = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(dome, (180, 230, 255, 70), (18, 18), 17)
        pygame.draw.circle(dome, (220, 245, 255, 140), (18, 18), 17, 2)
        surf.blit(dome, (sx - 18, int(y - 36)))


def draw_scorpion(surf, sx, sy, f, ph, flash, col=None):
    body = WHITE if flash else (col or (200, 120, 40))
    dark = WHITE if flash else shade(body, 0.7)
    shadow(surf, sx, sy + 14, 50)
    for side in (-1, 1):
        for i in range(3):
            a = math.sin(ph * 3 + i + side) * 3
            pygame.draw.line(surf, dark, (sx - 4 + i * 6, sy + 2), (sx - 8 + i * 9 + side * 4, sy + 12 + a), 3)
    pygame.draw.ellipse(surf, body, (sx - 16, sy - 8, 32, 18))
    # ουρά που καμπυλώνει πάνω από την πλάτη
    wig = math.sin(ph * 2) * 2
    offs = [(-14, -2), (-22, -8), (-26, -18), (-23, -28), (-14, -34), (-4, -32)]
    pts = [(sx + dx * f + (wig if i > 2 else 0), sy + dy) for i, (dx, dy) in enumerate(offs)]
    for k, p_ in enumerate(pts):
        pygame.draw.circle(surf, body if k % 2 else dark, (int(p_[0]), int(p_[1])), 7 - k // 2)
    tip = pts[-1]
    pygame.draw.polygon(surf, (40, 40, 40), [(tip[0], tip[1] - 3), (tip[0] + 9 * f, tip[1] + 5), (tip[0] - 2 * f, tip[1] + 4)])
    # δαγκάνες
    for side in (-1, 1):
        cx, cy = sx + 22 * f, sy - 2 + side * 7
        pygame.draw.line(surf, dark, (sx + 12 * f, sy + side * 3), (cx, cy), 4)
        o = abs(math.sin(ph * 3)) * 0.6
        pygame.draw.polygon(surf, body, [(cx, cy - 5), (cx + 12 * f, cy - 5 - o * 6), (cx + 6 * f, cy), (cx + 12 * f, cy + 5 + o * 6),
                                         (cx, cy + 5)])
    pygame.draw.circle(surf, (20, 20, 20), (sx + 12 * f, sy - 4), 2)
    pygame.draw.circle(surf, (20, 20, 20), (sx + 9 * f, sy - 5), 2)


def draw_golem(surf, sx, sy, f, ph, flash, col=None):
    stone = WHITE if flash else (col or (140, 135, 125))
    dark = WHITE if flash else shade(stone, 0.7)
    glow = (255, 160, 40) if col is None or not flash else WHITE
    sw = math.sin(ph) * 5
    shadow(surf, sx, sy + 26, 56)
    pygame.draw.rect(surf, dark, (sx - 16 + sw, sy + 2, 13, 22), border_radius=4)
    pygame.draw.rect(surf, dark, (sx + 3 - sw, sy + 2, 13, 22), border_radius=4)
    pygame.draw.rect(surf, stone, (sx - 22, sy - 30, 44, 36), border_radius=8)
    pygame.draw.line(surf, glow, (sx - 10, sy - 22), (sx - 2, sy - 10), 3)
    pygame.draw.line(surf, glow, (sx - 2, sy - 10), (sx + 8, sy - 16), 3)
    pygame.draw.line(surf, glow, (sx + 6, sy - 2), (sx + 14, sy - 8), 2)
    for side in (-1, 1):
        a = math.sin(ph) * 4 * side
        pygame.draw.rect(surf, stone, (sx + side * 22 - (10 if side > 0 else 6), sy - 28 + a, 16, 20), border_radius=5)
        pygame.draw.rect(surf, dark, (sx + side * 26 - 9, sy - 8 + a, 18, 18), border_radius=6)
    pygame.draw.rect(surf, stone, (sx - 12 + 2 * f, sy - 50, 24, 22), border_radius=6)
    pygame.draw.rect(surf, glow, (sx - 7 + 3 * f, sy - 43, 5, 4))
    pygame.draw.rect(surf, glow, (sx + 3 + 3 * f, sy - 43, 5, 4))
    pygame.draw.line(surf, dark, (sx - 6 + 2 * f, sy - 34), (sx + 6 + 2 * f, sy - 34), 2)
    for _i in range(3):
        pygame.draw.circle(surf, dark, (sx - 14 + _i * 14, sy - 26 + (_i % 2) * 18), 3)


DRAWERS.update({"skeleton": draw_skeleton, "zombie": draw_zombie, "cyclops": draw_cyclops, "yeti": draw_yeti,
                "mushroom": draw_mushroom, "octopus": draw_octopus, "robot": draw_robot, "alien": draw_alien,
                "scorpion": draw_scorpion, "golem": draw_golem})


# ---------------------------------------------------------------- όπλα (σχέδια)
GUN_LEN = {"pistol": 24, "smg": 33, "shotgun": 42, "ice": 32, "laser": 34, "rocket": 42, "lightning": 38}


def draw_weapon(surf, x, y, ang, key, t=0.0):
    """Σχεδιάζει όπλο με τη λαβή στο (x, y), να δείχνει προς τη γωνία ang."""
    ca, sa = math.cos(ang), math.sin(ang)
    fl = 1 if ca >= 0 else -1

    def P(d, s=0.0):
        s *= fl
        return (x + ca * d - sa * s, y + sa * d + ca * s)

    def poly(col, pts, outline=(25, 25, 30)):
        pp = [P(d, s) for d, s in pts]
        pygame.draw.polygon(surf, col, pp)
        if outline:
            pygame.draw.polygon(surf, outline, pp, 2)

    def line(col, d0, s0, d1, s1, w):
        a, b = P(d0, s0), P(d1, s1)
        pygame.draw.line(surf, col, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), w)

    def dot(col, d, s, r):
        p_ = P(d, s)
        pygame.draw.circle(surf, col, (int(p_[0]), int(p_[1])), r)

    if key == "pistol":
        poly((60, 60, 70), [(-2, 0), (5, 0), (3, 11), (-4, 11)])
        poly((150, 155, 170), [(-4, -6), (20, -6), (20, 1), (-4, 1)])
        line((220, 225, 235), -2, -5, 18, -5, 2)
        poly((80, 80, 90), [(20, -5), (25, -5), (25, -1), (20, -1)])
        line((25, 25, 30), 4, 1, 8, 6, 2)
        dot((255, 200, 60), 2, -7, 2)
    elif key == "smg":
        poly((50, 50, 58), [(-14, -2), (-6, -4), (-6, 3), (-14, 4)])
        poly((40, 40, 48), [(-6, -6), (24, -6), (24, 3), (-6, 3)])
        poly((70, 70, 80), [(6, 3), (12, 3), (13, 15), (7, 15)])
        line((255, 150, 40), -4, -4, 22, -4, 2)
        poly((120, 125, 135), [(24, -4), (34, -4), (34, 0), (24, 0)])
        poly((60, 60, 70), [(16, 3), (20, 3), (20, 10), (16, 10)])
        poly((30, 30, 35), [(4, -10), (14, -10), (14, -6), (4, -6)])
    elif key == "shotgun":
        poly((150, 95, 45), [(-18, -2), (2, -4), (2, 4), (-16, 8)], (80, 50, 20))
        poly((50, 50, 58), [(2, -6), (14, -6), (14, 4), (2, 4)])
        poly((150, 155, 165), [(14, -6), (43, -6), (43, -2), (14, -2)])
        poly((130, 135, 145), [(14, -2), (43, -2), (43, 2), (14, 2)])
        poly((170, 110, 55), [(20, 2), (32, 2), (32, 6), (20, 6)], (80, 50, 20))
        dot((255, 200, 60), 43, -4, 2)
    elif key == "ice":
        poly((225, 240, 252), [(-4, -6), (22, -5), (22, 4), (-4, 5)], (70, 120, 170))
        glow = 150 + int(math.sin(t * 8) * 60)
        poly((90, glow, 255), [(2, -13), (14, -13), (14, -6), (2, -6)], (40, 80, 150))
        poly((70, 150, 230), [(22, -4), (33, -2), (33, 1), (22, 3)])
        dot((200, 245, 255), 33, 0, 3)
        line((70, 120, 170), 8, -1, 14, -1, 2)
        line((70, 120, 170), 11, -4, 11, 2, 2)
        poly((90, 100, 120), [(0, 5), (6, 5), (4, 13), (-2, 13)])
    elif key == "laser":
        poly((110, 50, 170), [(-6, -5), (26, -3), (26, 3), (-6, 6)], (50, 20, 80))
        for d in (4, 11, 18):
            c = 180 + int(math.sin(t * 10 + d) * 70)
            dot((255, max(0, c - 80), 230), d, 0, 3)
        poly((200, 200, 220), [(26, -4), (35, -2), (35, 2), (26, 4)])
        dot((255, 120, 230), 35, 0, 4)
        dot(WHITE, 35, 0, 2)
        poly((60, 30, 90), [(0, 6), (6, 6), (4, 13), (-2, 13)])
    elif key == "rocket":
        poly((95, 115, 65), [(-16, -7), (32, -7), (32, 7), (-16, 7)], (40, 55, 25))
        line((130, 150, 90), -14, -4, 30, -4, 2)
        poly((220, 50, 40), [(32, -6), (44, 0), (32, 6)], (100, 20, 20))
        poly((60, 70, 40), [(4, -14), (12, -14), (12, -7), (4, -7)])
        dot((120, 220, 255), 8, -11, 2)
        poly((50, 55, 40), [(0, 7), (6, 7), (4, 15), (-2, 15)])
        poly((50, 55, 40), [(16, 7), (21, 7), (19, 13), (14, 13)])
    elif key == "lightning":
        line((150, 110, 30), -10, 0, 30, 0, 6)
        line((255, 210, 60), -10, -1, 30, -1, 2)
        for d in (2, 14):
            poly((255, 215, 70), [(d, -4), (d + 4, -4), (d + 4, 4), (d, 4)], (150, 110, 30))
        c = P(36, 0)
        r = 7 + int(math.sin(t * 15) * 2)
        pygame.draw.circle(surf, (255, 255, 160), (int(c[0]), int(c[1])), r + 3)
        pygame.draw.circle(surf, (255, 240, 80), (int(c[0]), int(c[1])), r)
        pygame.draw.circle(surf, WHITE, (int(c[0]), int(c[1])), 3)
        for k in range(3):
            a = t * 7 + k * 2.1
            ex, ey = c[0] + math.cos(a) * (r + 7), c[1] + math.sin(a) * (r + 7)
            mx, my = (c[0] + ex) / 2 + math.sin(t * 30 + k) * 3, (c[1] + ey) / 2 + math.cos(t * 30 + k) * 3
            pygame.draw.lines(surf, (255, 255, 150), False, [c, (mx, my), (ex, ey)], 2)
    elif key == "knife":
        poly((90, 55, 30), [(-2, -3), (8, -3), (8, 3), (-2, 3)], (50, 30, 15))
        line((200, 170, 60), 8, -6, 8, 6, 3)
        poly((215, 222, 235), [(9, -3), (24, -2), (30, 1), (9, 3)], (90, 95, 110))
        line(WHITE, 11, -2, 24, -1, 1)
    elif key == "sword":
        poly((110, 60, 30), [(-4, -3), (10, -3), (10, 3), (-4, 3)], (60, 30, 15))
        dot((255, 210, 60), -5, 0, 4)
        poly((255, 200, 50), [(10, -9), (13, -9), (13, 9), (10, 9)], (150, 100, 20))
        poly((255, 110, 30), [(13, -4), (44, -3), (52, 0), (44, 3), (13, 4)], (150, 40, 10))
        poly((255, 220, 90), [(14, -1), (44, -1), (48, 0), (44, 1), (14, 1)], None)
        for k in range(4):
            fd = 18 + k * 9
            fs = math.sin(t * 14 + k * 1.7) * 4 - 6
            dot((255, 150 + k * 20, 40), fd, fs, 3 - k % 2)
    elif key == "hammer":
        poly((140, 95, 50), [(-2, -2), (36, -2), (36, 2), (-2, 2)], (70, 45, 20))
        poly((90, 150, 220), [(32, -14), (50, -14), (50, 14), (32, 14)], (30, 60, 110))
        poly((140, 200, 255), [(34, -12), (48, -12), (48, -6), (34, -6)], None)
        poly((255, 230, 80), [(41, -8), (38, 0), (42, 0), (39, 8), (45, -1), (41, -1)], None)
    else:
        line((60, 60, 70), 0, 0, 20, 0, 6)


def draw_bomb_icon(surf, x, y, kind="bomb", s=1.0, t=0.0):
    body = (40, 40, 50) if kind == "bomb" else (90, 170, 240)
    pygame.draw.circle(surf, body, (int(x), int(y)), int(12 * s))
    pygame.draw.circle(surf, (255, 255, 255), (int(x - 4 * s), int(y - 4 * s)), max(1, int(3 * s)))
    pygame.draw.rect(surf, (90, 90, 100), (x - 4 * s, y - 16 * s, 8 * s, 5 * s))
    pygame.draw.line(surf, (160, 120, 70), (x, y - 16 * s), (x + 6 * s, y - 22 * s), max(1, int(2 * s)))
    sp = 3 + math.sin(t * 20) * 1.5
    pygame.draw.circle(surf, (255, 200, 60), (int(x + 6 * s), int(y - 22 * s)), max(1, int(sp * s)))
    if kind == "icebomb":
        for a in range(3):
            r = math.radians(a * 60)
            pygame.draw.line(surf, WHITE, (x - math.cos(r) * 7 * s, y - math.sin(r) * 7 * s),
                             (x + math.cos(r) * 7 * s, y + math.sin(r) * 7 * s), max(1, int(2 * s)))


def draw_potion_icon(surf, x, y, s=1.0):
    pygame.draw.circle(surf, (230, 50, 90), (int(x), int(y + 3 * s)), int(11 * s))
    pygame.draw.rect(surf, (200, 220, 240), (x - 4 * s, y - 14 * s, 8 * s, 9 * s))
    pygame.draw.rect(surf, (150, 100, 60), (x - 5 * s, y - 17 * s, 10 * s, 4 * s))
    pygame.draw.circle(surf, (255, 170, 190), (int(x - 4 * s), int(y)), max(1, int(3 * s)))
    pygame.draw.circle(surf, (255, 255, 255), (int(x + 3 * s), int(y + 6 * s)), max(1, int(2 * s)))


# ---------------------------------------------------------------- ο νέος ήρωας
def draw_player(surf, sx, sy, aim, walk, outfit="explorer", weapon="pistol", swing=0.0, t=0.0):
    o = OUTFITS.get(outfit, OUTFITS["explorer"])
    f = 1 if math.cos(aim) >= 0 else -1
    sw = math.sin(walk) * 7 if walk is not None else 0
    body, legs = o["body"], o["legs"]
    shadow(surf, sx, sy + 24, 34)
    # κάπα
    if o.get("cape"):
        fl = math.sin(t * 6) * 3
        pygame.draw.polygon(surf, o["cape"], [(sx - 9, sy - 18), (sx + 9, sy - 18), (sx + 2 - 14 * f, sy + 14 + fl),
                                              (sx - 4 - 18 * f, sy + 10 - fl)])
    # σακίδιο / φιάλες αστροναύτη
    if o["head"] == "astro":
        pygame.draw.rect(surf, (200, 200, 210), (sx - 7 - 10 * f, sy - 17, 13, 20), border_radius=4)
    elif o["head"] in ("cap",):
        pygame.draw.rect(surf, (130, 90, 45), (sx - 7 - 10 * f, sy - 15, 13, 17), border_radius=4)
    boots = (60, 40, 25) if o["head"] != "astro" else (180, 180, 190)
    limb(surf, legs, (sx - 5, sy + 4), (sx - 5 + sw, sy + 20), 8)
    limb(surf, legs, (sx + 5, sy + 4), (sx + 5 - sw, sy + 20), 8)
    pygame.draw.ellipse(surf, boots, (sx - 5 + sw - 5 + 2 * f, sy + 18, 12, 8))
    pygame.draw.ellipse(surf, boots, (sx + 5 - sw - 5 + 2 * f, sy + 18, 12, 8))
    limb(surf, body, (sx - 7 * f, sy - 11), (sx - 10 * f, sy + 2 - sw * 0.5), 7)
    pygame.draw.rect(surf, body, (sx - 12, sy - 18, 24, 25), border_radius=7)
    pygame.draw.rect(surf, shade(body, 1.2), (sx - 9, sy - 15, 7, 10), border_radius=3)
    pygame.draw.rect(surf, (80, 50, 25) if o["head"] != "gold" else (150, 60, 200), (sx - 12, sy + 2, 24, 5))
    pygame.draw.rect(surf, GOLD, (sx - 3, sy + 2, 6, 5))
    if o["head"] == "dino":
        for i in range(3):
            pygame.draw.polygon(surf, (250, 220, 60), [(sx - 13 * f, sy - 14 + i * 7), (sx - 19 * f, sy - 11 + i * 7),
                                                       (sx - 13 * f, sy - 8 + i * 7)])
    # κεφάλι
    hx, hy = sx + 1 * f, sy - 31
    head = o["head"]
    pygame.draw.circle(surf, SKIN, (hx, hy), 12)
    if head == "cap":
        pygame.draw.circle(surf, (110, 70, 40), (hx, hy - 3), 12, draw_top_left=True, draw_top_right=True)
        pygame.draw.circle(surf, o["hat"], (hx, hy - 4), 12, draw_top_left=True, draw_top_right=True)
        pygame.draw.rect(surf, o["hat"], (hx + (2 if f > 0 else -16), hy - 6, 14, 4), border_radius=2)
        pygame.draw.circle(surf, WHITE, (hx, hy - 14), 2)
    elif head == "helmet":
        pygame.draw.circle(surf, o["hat"], (hx, hy), 13)
        pygame.draw.rect(surf, (40, 40, 50), (hx - 9 + 3 * f, hy - 2, 18, 4))
        pygame.draw.line(surf, (230, 230, 240), (hx - 8, hy - 9), (hx + 2, hy - 11), 2)
        for i in range(4):
            pygame.draw.circle(surf, o["plume"], (hx - 3 * f - i * 3 * f, hy - 15 - i * 2), 4)
    elif head == "mask":
        pygame.draw.circle(surf, o["hat"], (hx, hy), 13)
        pygame.draw.rect(surf, SKIN, (hx - 9 + 3 * f, hy - 4, 16, 6), border_radius=3)
        pygame.draw.rect(surf, o["band"], (hx - 13, hy - 9, 26, 4))
        tail = math.sin(t * 8) * 3
        pygame.draw.line(surf, o["band"], (hx - 12 * f, hy - 7), (hx - 22 * f, hy - 3 + tail), 3)
        pygame.draw.line(surf, o["band"], (hx - 12 * f, hy - 7), (hx - 20 * f, hy + 3 + tail), 3)
    elif head == "dino":
        pygame.draw.circle(surf, o["hat"], (hx, hy - 2), 14, draw_top_left=True, draw_top_right=True)
        pygame.draw.rect(surf, o["hat"], (hx - 14, hy - 3, 4, 10))
        pygame.draw.rect(surf, o["hat"], (hx + 10, hy - 3, 4, 10))
        for i in range(-2, 3):
            pygame.draw.polygon(surf, WHITE, [(hx + i * 5 - 2, hy - 3), (hx + i * 5 + 2, hy - 3), (hx + i * 5, hy + 1)])
        for i in range(3):
            pygame.draw.polygon(surf, (250, 220, 60), [(hx - 6 + i * 6, hy - 14 + abs(i - 1) * 2),
                                                       (hx - 3 + i * 6, hy - 22 + abs(i - 1) * 2),
                                                       (hx + i * 6, hy - 14 + abs(i - 1) * 2)])
    elif head == "crown":
        pygame.draw.circle(surf, (120, 70, 30), (hx, hy - 3), 12, draw_top_left=True, draw_top_right=True)
        draw_crown(surf, hx, hy - 9, 9)
    if head != "mask":
        pygame.draw.circle(surf, (30, 30, 30), (hx + 4 * f, hy + 1), 2)
        pygame.draw.circle(surf, (30, 30, 30), (hx + 9 * f, hy + 1), 2) if head != "helmet" else None
        if head != "helmet":
            pygame.draw.arc(surf, (160, 70, 60), (hx + 2 * f - 3, hy + 3, 8, 6), 3.4, 6.0, 2)
    else:
        pygame.draw.circle(surf, (30, 30, 30), (hx + 2 * f, hy - 1), 2)
        pygame.draw.circle(surf, (30, 30, 30), (hx + 7 * f, hy - 1), 2)
    if head == "astro":
        g = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(g, (170, 220, 255, 80), (20, 20), 18)
        pygame.draw.circle(g, (230, 245, 255, 200), (20, 20), 18, 3)
        pygame.draw.circle(g, (255, 255, 255, 200), (13, 12), 4)
        surf.blit(g, (hx - 20, hy - 20))
    # όπλο στο χέρι
    wkind = WEAPONS.get(weapon, WEAPONS["pistol"])["kind"]
    ang = aim + (swing * 1.6 * f if wkind == "melee" else 0)
    shx, shy = sx + 4 * f, sy - 11
    hand = (shx + math.cos(ang) * 12, shy + math.sin(ang) * 12)
    behind = math.sin(ang) < -0.6
    if behind:
        draw_weapon(surf, hand[0], hand[1], ang, weapon, t)
    limb(surf, body, (shx, shy), hand, 7)
    pygame.draw.circle(surf, SKIN if head not in ("helmet", "astro") else o["hat"], (int(hand[0]), int(hand[1])), 4)
    if not behind:
        draw_weapon(surf, hand[0], hand[1], ang, weapon, t)


_icon_cache = {}


def weapon_icon(key, w, h, t=0.0):
    """Εικονίδιο όπλου που χωράει σε κουτί w x h (για κουμπιά και κατάστημα)."""
    img = _icon_cache.get((key, w, h))
    if img is None:
        tmp = pygame.Surface((100, 60), pygame.SRCALPHA)
        draw_weapon(tmp, 24, 30, 0, key, 0.0)
        r = tmp.get_bounding_rect()
        part = tmp.subsurface(r).copy()
        k = min(w / max(1, r.w), h / max(1, r.h))
        part = pygame.transform.smoothscale(part, (max(1, int(r.w * k)), max(1, int(r.h * k))))
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        img.blit(part, ((w - part.get_width()) // 2, (h - part.get_height()) // 2))
        _icon_cache[(key, w, h)] = img
    return img


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
        self.snd["slash"] = m(0.16, lambda t, p: (_noise() * 0.6 + _tri(300 + 900 * p, t) * 0.3) * math.sin(math.pi * p), 0.3)
        self.snd["rocket"] = m(0.32, lambda t, p: (_noise() * 0.6 + _sq(110 - 50 * p, t) * 0.4) * (1 - p) ** 0.6, 0.3)
        self.snd["v_beep"] = m(0.42, lambda t, p: _sq(880 if int(p * 6) % 2 else 660, t) * (1 - (p * 6) % 1 * 0.5), 0.14)
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
        elif key == "volcano":
            for _ in range(260):
                x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
                pts = [(x, y)]
                for _k in range(4):
                    x += rnd.randint(-22, 22)
                    y += rnd.randint(-22, 22)
                    pts.append((x, y))
                pygame.draw.lines(bg, (255, 110, 30), False, pts, 3)
                pygame.draw.lines(bg, (255, 210, 80), False, pts, 1)
        elif key == "moon":
            for _ in range(400):
                x, y, r = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H), rnd.randint(6, 26)
                pygame.draw.circle(bg, shade(th["road"], 0.82), (x, y), r)
                pygame.draw.circle(bg, shade(th["road"], 1.12), (x - 2, y - 2), r, 2)
        elif key == "sea":
            for _ in range(500):
                x, y, r = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H), rnd.randint(2, 6)
                pygame.draw.circle(bg, (130, 200, 240), (x, y), r, 1)
            for _ in range(160):
                x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
                pygame.draw.arc(bg, (70, 150, 210), (x, y, 40, 14), 0.3, 2.8, 2)
        elif key == "candy":
            for _ in range(2500):
                x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
                c = rnd.choice([(255, 80, 120), (80, 200, 255), (255, 220, 60), (140, 230, 120), (200, 120, 255)])
                a = rnd.random() * 3.14
                pygame.draw.line(bg, c, (x, y), (x + math.cos(a) * 6, y + math.sin(a) * 6), 3)
        elif key == "factory":
            for i in range(NB + 1):
                c = i * BLOCK + ROAD // 2
                for t_ in range(0, WORLD_W, 40):
                    col = (240, 200, 40) if (t_ // 40) % 2 else (40, 40, 40)
                    pygame.draw.rect(bg, col, (c - 4, t_, 8, 40))
                    pygame.draw.rect(bg, col, (t_, c - 4, 40, 8))
        elif key == "iceberg":
            for _ in range(300):
                x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
                pts = [(x, y)]
                for _k in range(3):
                    x += rnd.randint(-25, 25)
                    y += rnd.randint(-25, 25)
                    pts.append((x, y))
                pygame.draw.lines(bg, (230, 248, 255), False, pts, 2)
        elif key == "sky":
            for _ in range(200):
                x, y = rnd.randint(0, WORLD_W), rnd.randint(0, WORLD_H)
                for dx, dy, r in ((0, 0, 14), (14, -4, 11), (-12, 2, 10), (24, 3, 9)):
                    pygame.draw.circle(bg, (215, 235, 255), (x + dx, y + dy), r)
        elif key in ("haunted", "castle"):
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
            if th["tree"] not in ("dead", "none", "kelp", "lollipop"):
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
        elif key == "volcano":
            pygame.draw.circle(bg, (200, 60, 20), c, 34)
            pygame.draw.circle(bg, (255, 140, 30), c, 24)
            pygame.draw.circle(bg, (255, 230, 120), c, 10)
        elif key == "jungle":
            pygame.draw.circle(bg, (60, 140, 180), c, 30)
            for _ in range(30):
                x, y = rnd.randint(g.x + 5, g.right - 5), rnd.randint(g.y + 5, g.bottom - 5)
                pygame.draw.circle(bg, rnd.choice([(255, 80, 120), (255, 200, 40), (200, 80, 255)]), (x, y), 4)
        elif key == "desert":
            pygame.draw.circle(bg, (70, 170, 210), c, 32)
            pygame.draw.circle(bg, (110, 200, 120), c, 40, 6)
        elif key == "castle":
            pygame.draw.circle(bg, (150, 150, 160), c, 26)
            pygame.draw.circle(bg, (110, 160, 220), c, 18)
            for _ in range(25):
                x, y = rnd.randint(g.x + 5, g.right - 5), rnd.randint(g.y + 5, g.bottom - 5)
                pygame.draw.circle(bg, rnd.choice([(230, 60, 60), (255, 255, 255), (250, 200, 60)]), (x, y), 3)
        elif key == "moon":
            for _ in range(60):
                x, y = rnd.randint(g.x + 5, g.right - 5), rnd.randint(g.y + 5, g.bottom - 5)
                pygame.draw.circle(bg, rnd.choice([(255, 255, 255), (200, 220, 255), (255, 240, 180)]), (x, y), 1)
            pygame.draw.circle(bg, (90, 200, 255), c, 22)
            pygame.draw.circle(bg, (60, 120, 220), c, 22, 4)
            pygame.draw.circle(bg, (90, 180, 90), (c[0] - 6, c[1] - 4), 7)
        elif key == "sea":
            pygame.draw.circle(bg, (240, 220, 160), c, 30)
            for k in range(8):
                a = k * 0.785
                pygame.draw.circle(bg, (255, 120, 120) if k % 2 else (255, 200, 80),
                                   (int(c[0] + math.cos(a) * 20), int(c[1] + math.sin(a) * 20)), 6)
            pygame.draw.circle(bg, (255, 240, 200), c, 8)
        elif key == "candy":
            pygame.draw.circle(bg, (255, 120, 180), c, 30)
            pygame.draw.circle(bg, (255, 255, 255), c, 22, 6)
            pygame.draw.circle(bg, (120, 200, 255), c, 12)
        elif key == "factory":
            pygame.draw.circle(bg, (80, 85, 95), c, 30)
            for k in range(8):
                a = k * 0.785
                pygame.draw.circle(bg, (150, 155, 165), (int(c[0] + math.cos(a) * 26), int(c[1] + math.sin(a) * 26)), 7)
            pygame.draw.circle(bg, (150, 155, 165), c, 18)
            pygame.draw.circle(bg, (80, 85, 95), c, 7)
        elif key == "iceberg":
            pygame.draw.circle(bg, (160, 215, 245), c, 30)
            pygame.draw.circle(bg, WHITE, (c[0] - 8, c[1] - 8), 8)
        elif key == "sky":
            for k in range(7):
                col = [(255, 80, 80), (255, 160, 60), (255, 230, 70), (110, 220, 110), (90, 170, 255), (120, 100, 230),
                       (190, 110, 230)][k]
                pygame.draw.arc(bg, col, (c[0] - 40 + k * 3, c[1] - 30 + k * 3, 80 - k * 6, 70 - k * 6), 0, 3.14, 4)
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


def solid_rock(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (60, 48, 44), r, border_radius=26)
    for _ in range(int(r.w * r.h / 2500)):
        x, y = rnd.randint(r.x + 15, r.right - 15), rnd.randint(r.y + 15, r.bottom - 15)
        rr = rnd.randint(14, 26)
        pygame.draw.circle(bg, rnd.choice([(80, 64, 58), (70, 56, 52), (95, 78, 70)]), (x, y), rr)
        pygame.draw.circle(bg, (110, 92, 84), (x - rr // 3, y - rr // 3), rr // 3)
    for _ in range(4):
        x, y = rnd.randint(r.x + 10, r.right - 10), rnd.randint(r.y + 10, r.bottom - 10)
        pts = [(x, y)]
        for _k in range(3):
            x += rnd.randint(-20, 20)
            y += rnd.randint(-20, 20)
            pts.append((min(max(x, r.x + 4), r.right - 4), min(max(y, r.y + 4), r.bottom - 4)))
        pygame.draw.lines(bg, (255, 120, 30), False, pts, 4)
        pygame.draw.lines(bg, (255, 220, 100), False, pts, 1)
    pygame.draw.rect(bg, (35, 28, 26), r, 3, border_radius=26)


def solid_pyramid(bg, b, rnd):
    r = b.rect
    steps = 5
    for i in range(steps):
        k = i * min(r.w, r.h) // (2 * steps + 1)
        rr = r.inflate(-2 * k, -2 * k)
        pygame.draw.rect(bg, shade((222, 186, 120), 0.82 + i * 0.05), rr)
        pygame.draw.rect(bg, (170, 135, 80), rr, 2)
    pygame.draw.rect(bg, (60, 40, 20), (r.centerx - 10, r.bottom - 24, 20, 24), border_top_left_radius=10,
                     border_top_right_radius=10)


def solid_castle(bg, b, rnd):
    r = b.rect
    roof, face = _face(r, 44)
    pygame.draw.rect(bg, (150, 148, 156), roof)
    for x in range(roof.x, roof.right, 22):
        for y in range(roof.y, roof.bottom, 14):
            pygame.draw.rect(bg, (128, 126, 134), (x + (y // 14 % 2) * 11, y, 22, 14), 1)
    for x in range(r.x, r.right - 10, 24):
        pygame.draw.rect(bg, (110, 108, 116), (x, r.y, 14, 12))
    for cx, cy in ((r.x + 16, r.y + 16), (r.right - 16, r.y + 16)):
        pygame.draw.circle(bg, (120, 118, 126), (cx, cy), 18)
        pygame.draw.circle(bg, (170, 60, 60), (cx, cy), 11)
    pygame.draw.rect(bg, (100, 98, 106), face)
    for wx in range(r.x + 14, r.right - 20, 30):
        pygame.draw.rect(bg, (40, 30, 30), (wx, face.y + 10, 8, 18), border_top_left_radius=4, border_top_right_radius=4)
    pygame.draw.rect(bg, (90, 55, 30), (r.centerx - 14, r.bottom - 30, 28, 30), border_top_left_radius=14,
                     border_top_right_radius=14)
    pygame.draw.rect(bg, (60, 58, 66), r, 2)


def solid_dome(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (120, 125, 140), r, border_radius=30)
    pygame.draw.rect(bg, (200, 205, 220), r.inflate(-12, -12), border_radius=26)
    pygame.draw.ellipse(bg, (90, 170, 230), r.inflate(-r.w // 3, -r.h // 3))
    pygame.draw.ellipse(bg, (170, 225, 255), r.inflate(-r.w // 3, -r.h // 3).inflate(-r.w // 4, -r.h // 4).move(-10, -10))
    for _ in range(3):
        x, y = rnd.randint(r.x + 14, r.right - 14), rnd.randint(r.y + 14, r.bottom - 14)
        pygame.draw.circle(bg, (255, 80, 80) if rnd.random() < 0.5 else (80, 255, 120), (x, y), 4)
    pygame.draw.rect(bg, (70, 75, 90), r, 3, border_radius=30)


def solid_coral(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (190, 90, 110), r, border_radius=26)
    for _ in range(int(r.w * r.h / 1300)):
        x, y = rnd.randint(r.x + 10, r.right - 10), rnd.randint(r.y + 10, r.bottom - 10)
        c = rnd.choice([(255, 110, 140), (255, 170, 80), (180, 100, 220), (255, 220, 90), (100, 210, 200)])
        kind = rnd.random()
        if kind < 0.4:
            for k in range(5):
                a = -1.57 + (k - 2) * 0.45
                pygame.draw.line(bg, c, (x, y), (x + math.cos(a) * 16, y + math.sin(a) * 16), 5)
                pygame.draw.circle(bg, shade(c, 1.2), (int(x + math.cos(a) * 16), int(y + math.sin(a) * 16)), 4)
        elif kind < 0.7:
            pygame.draw.circle(bg, c, (x, y), rnd.randint(9, 16))
            pygame.draw.circle(bg, shade(c, 0.8), (x, y), rnd.randint(3, 6))
        else:
            pygame.draw.ellipse(bg, c, (x - 14, y - 8, 28, 16))
    pygame.draw.rect(bg, (120, 50, 70), r, 3, border_radius=26)


def solid_cake(bg, b, rnd):
    r = b.rect
    roof, face = _face(r, 46)
    base = rnd.choice([(255, 190, 210), (200, 150, 110), (255, 235, 190), (190, 230, 255)])
    pygame.draw.rect(bg, base, roof, border_radius=10)
    icing = rnd.choice([(255, 255, 255), (255, 120, 170), (140, 90, 60)])
    pygame.draw.rect(bg, icing, roof.inflate(-12, -12), border_radius=10)
    for _ in range(30):
        x, y = rnd.randint(roof.x + 10, roof.right - 10), rnd.randint(roof.y + 10, roof.bottom - 10)
        pygame.draw.circle(bg, rnd.choice([(255, 60, 90), (60, 180, 255), (255, 220, 50), (120, 220, 100)]), (x, y), 3)
    for k in range(3):
        cx = roof.x + (k + 1) * roof.w // 4
        pygame.draw.circle(bg, (220, 30, 50), (cx, roof.y + 18), 9)
        pygame.draw.circle(bg, (255, 150, 160), (cx - 3, roof.y + 15), 3)
    pygame.draw.rect(bg, shade(base, 0.8), face)
    for x in range(face.x, face.right, 18):
        pygame.draw.circle(bg, icing, (x + 9, face.y), 9)
    pygame.draw.rect(bg, (150, 80, 50), (r.centerx - 10, r.bottom - 24, 20, 24), border_top_left_radius=10,
                     border_top_right_radius=10)
    pygame.draw.rect(bg, (120, 70, 60), r, 2, border_radius=10)


def solid_machine(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (120, 125, 138), r)
    for x in range(r.x, r.right, 40):
        pygame.draw.line(bg, (100, 104, 116), (x, r.y), (x, r.bottom), 2)
    for _ in range(3):
        cx, cy = rnd.randint(r.x + 30, r.right - 30), rnd.randint(r.y + 30, r.bottom - 30)
        rr = rnd.randint(16, 26)
        for k in range(8):
            a = k * 0.785
            pygame.draw.circle(bg, (90, 95, 105), (int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr)), 6)
        pygame.draw.circle(bg, (90, 95, 105), (cx, cy), rr)
        pygame.draw.circle(bg, (160, 165, 175), (cx, cy), rr - 6)
        pygame.draw.circle(bg, (70, 72, 80), (cx, cy), 6)
    for k in range(2):
        y = r.y + 14 + k * 20
        pygame.draw.line(bg, (180, 110, 60), (r.x, y), (r.right, y), 8)
    for x in range(r.x + 10, r.right - 10, 26):
        pygame.draw.circle(bg, rnd.choice([(255, 60, 60), (60, 255, 120), (255, 220, 60)]), (x, r.bottom - 10), 4)
    pygame.draw.rect(bg, (60, 62, 70), r, 3)


def solid_ice(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (150, 210, 245), r, border_radius=8)
    for _ in range(int(r.w * r.h / 3000)):
        x, y = rnd.randint(r.x + 10, r.right - 30), rnd.randint(r.y + 10, r.bottom - 30)
        w, h = rnd.randint(20, 40), rnd.randint(20, 40)
        pygame.draw.rect(bg, rnd.choice([(190, 230, 255), (170, 220, 250), (210, 240, 255)]), (x, y, w, h))
        pygame.draw.line(bg, WHITE, (x + 3, y + 3), (x + w - 6, y + 3), 2)
    pygame.draw.rect(bg, (90, 150, 200), r, 3, border_radius=8)


def solid_cloud(bg, b, rnd):
    r = b.rect
    pygame.draw.rect(bg, (230, 238, 252), r, border_radius=40)
    for _ in range(int(r.w * r.h / 1600)):
        x, y = rnd.randint(r.x + 15, r.right - 15), rnd.randint(r.y + 15, r.bottom - 15)
        rr = rnd.randint(18, 30)
        pygame.draw.circle(bg, (215, 225, 245), (x + 3, y + 4), rr)
        pygame.draw.circle(bg, WHITE, (x, y), rr)
    for k, col in enumerate([(255, 90, 90), (255, 180, 60), (255, 235, 80), (110, 220, 110), (90, 170, 255)]):
        pygame.draw.line(bg, col, (r.x + 20, r.bottom - 30 + k * 4), (r.right - 20, r.bottom - 30 + k * 4), 3)
    pygame.draw.rect(bg, (190, 200, 230), r, 3, border_radius=40)


SOLID_DRAW = {"building": solid_building, "grove": solid_grove, "hut": solid_hut, "cabin": solid_cabin,
              "crypt": solid_crypt, "rock": solid_rock, "pyramid": solid_pyramid, "castle": solid_castle,
              "dome": solid_dome, "coral": solid_coral, "cake": solid_cake, "machine": solid_machine,
              "ice": solid_ice, "cloud": solid_cloud}


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
    elif k == "rock":
        pygame.draw.ellipse(bg, (60, 55, 55), (x - 24, y - 12, 48, 30))
        pygame.draw.ellipse(bg, (120, 112, 108), (x - 22, y - 16, 44, 28))
        pygame.draw.ellipse(bg, (160, 152, 146), (x - 14, y - 13, 18, 10))
    elif k == "crystal":
        for dx, hgt, col in ((-10, 26, (200, 80, 255)), (8, 32, (120, 200, 255)), (0, 40, (255, 100, 200))):
            pts = [(x + dx - 7, y + 10), (x + dx, y + 10 - hgt), (x + dx + 7, y + 10)]
            pygame.draw.polygon(bg, col, pts)
            pygame.draw.polygon(bg, WHITE, pts, 1)
    elif k == "cactus":
        pygame.draw.rect(bg, (60, 150, 70), (x - 7, y - 30, 14, 42), border_radius=7)
        pygame.draw.rect(bg, (60, 150, 70), (x - 20, y - 16, 10, 18), border_radius=5)
        pygame.draw.rect(bg, (60, 150, 70), (x + 10, y - 22, 10, 16), border_radius=5)
        pygame.draw.line(bg, (40, 110, 50), (x, y - 26), (x, y + 8), 2)
        pygame.draw.circle(bg, (255, 120, 180), (x, y - 31), 4)
    elif k == "pot":
        pygame.draw.ellipse(bg, (190, 110, 60), (x - 16, y - 16, 32, 32))
        pygame.draw.rect(bg, (170, 95, 50), (x - 9, y - 22, 18, 8))
        pygame.draw.line(bg, (120, 60, 30), (x - 14, y - 2), (x + 14, y - 2), 3)
    elif k == "barrel":
        pygame.draw.ellipse(bg, (140, 90, 45), (x - 15, y - 18, 30, 36))
        pygame.draw.line(bg, (70, 70, 75), (x - 14, y - 8), (x + 14, y - 8), 3)
        pygame.draw.line(bg, (70, 70, 75), (x - 14, y + 8), (x + 14, y + 8), 3)
        pygame.draw.ellipse(bg, (170, 115, 60), (x - 12, y - 18, 24, 10))
    elif k == "crate":
        pygame.draw.rect(bg, (170, 120, 60), (x - 16, y - 16, 32, 32))
        pygame.draw.rect(bg, (110, 75, 35), (x - 16, y - 16, 32, 32), 3)
        pygame.draw.line(bg, (110, 75, 35), (x - 16, y - 16), (x + 16, y + 16), 3)
        pygame.draw.line(bg, (110, 75, 35), (x + 16, y - 16), (x - 16, y + 16), 3)
    elif k == "shell":
        pygame.draw.ellipse(bg, (250, 200, 180), (x - 18, y - 12, 36, 26))
        for i in range(-2, 3):
            pygame.draw.line(bg, (220, 150, 130), (x, y + 12), (x + i * 8, y - 10), 2)
        pygame.draw.ellipse(bg, (190, 130, 110), (x - 18, y - 12, 36, 26), 2)
    elif k == "seaweed":
        for i in range(-2, 3):
            pts = [(x + i * 6 + math.sin(j) * 4, y + 12 - j * 7) for j in range(6)]
            pygame.draw.lines(bg, (40, 160, 90), False, pts, 5)
    elif k == "chest":
        pygame.draw.rect(bg, (140, 85, 40), (x - 20, y - 12, 40, 26), border_radius=4)
        pygame.draw.rect(bg, (170, 110, 50), (x - 20, y - 16, 40, 10), border_radius=5)
        pygame.draw.rect(bg, (230, 190, 60), (x - 20, y - 8, 40, 4))
        pygame.draw.rect(bg, (230, 190, 60), (x - 4, y - 10, 8, 10))
        pygame.draw.rect(bg, (80, 50, 20), (x - 20, y - 16, 40, 30), 2, border_radius=4)
    elif k == "lollipop":
        pygame.draw.line(bg, (250, 250, 250), (x, y + 14), (x, y - 6), 4)
        pygame.draw.circle(bg, (255, 100, 160), (x, y - 16), 16)
        for rr, col in ((12, WHITE), (8, (255, 100, 160)), (4, WHITE)):
            pygame.draw.circle(bg, col, (x, y - 16), rr, 3)
    elif k == "candy":
        col = random.choice([(255, 80, 80), (80, 180, 255), (120, 220, 100), (255, 200, 60)])
        pygame.draw.ellipse(bg, col, (x - 14, y - 10, 28, 20))
        pygame.draw.polygon(bg, col, [(x - 14, y), (x - 26, y - 10), (x - 26, y + 10)])
        pygame.draw.polygon(bg, col, [(x + 14, y), (x + 26, y - 10), (x + 26, y + 10)])
        pygame.draw.line(bg, WHITE, (x - 6, y - 8), (x - 2, y + 8), 3)
        pygame.draw.line(bg, WHITE, (x + 4, y - 8), (x + 8, y + 8), 3)
    elif k == "cloudpuff":
        for dx, dy, r in ((-12, 4, 14), (12, 4, 14), (0, -6, 16), (0, 6, 14)):
            pygame.draw.circle(bg, (210, 220, 240), (x + dx + 2, y + dy + 3), r)
            pygame.draw.circle(bg, WHITE, (x + dx, y + dy), r)
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
    elif kind == "kelp":
        for i in range(-1, 2):
            pts = [(sx + i * 10 + math.sin(j * 0.9) * 6, sy - j * 12) for j in range(7)]
            pygame.draw.lines(surf, (30, 140, 80), False, pts, 7)
            for p_ in pts[2::2]:
                pygame.draw.ellipse(surf, (60, 180, 100), (p_[0] - 2, p_[1] - 5, 12, 7))
    elif kind == "lollipop":
        pygame.draw.line(surf, WHITE, (sx, sy + 6), (sx, sy - 40), 6)
        col = [(255, 100, 160), (120, 200, 255), (255, 200, 60)][(sx // 7 + sy // 11) % 3]
        pygame.draw.circle(surf, col, (sx, sy - 52), r)
        for rr in range(r - 6, 4, -8):
            pygame.draw.circle(surf, WHITE, (sx, sy - 52), rr, 3)
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
        self.outfit, self.weapon, self.swing = "explorer", "pistol", 0.0

    def protected(self):
        return self.invuln > 0 or self.shield_t > 0

    def gun_tip(self):
        if self.is_player:
            ln = 16 + GUN_LEN.get(self.weapon, 26)
            return self.x + 4 * math.cos(self.dir) + math.cos(self.dir) * ln, self.y - 11 + math.sin(self.dir) * ln
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
            draw_player(surf, sx, sy, self.dir, self.walk if self.moving else None, self.outfit, self.weapon,
                        self.swing, t)
        else:
            draw_hero(surf, sx, sy, self.dir, self.walk if self.moving else None, self.shirt, self.helmet)
        if self.shield_t > 0:
            pygame.draw.circle(surf, (120, 200, 255), (sx, sy - 6), 34, 3)
            pygame.draw.circle(surf, (200, 240, 255), (sx, sy - 6), 30 + int(math.sin(t * 8) * 2), 1)
        if self.is_player:
            bob = int(math.sin(t * 5) * 3)
            pts = [(sx - 9, sy - 62 + bob), (sx + 9, sy - 62 + bob), (sx, sy - 51 + bob)]
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
        self.bite_t = self.bite_cd = 0.0

    def draw(self, surf, cam, t):
        sx, sy = int(self.x - cam[0]), int(self.y - cam[1])
        f = 1 if math.cos(self.dir) >= 0 else -1
        draw_dog(surf, sx, sy, f, self.walk, self.moving, self.barking > 0 or self.bite_t > 0)
        if self.barking > 0:
            pygame.draw.circle(surf, WHITE, (sx + 22 * f, sy - 34), 9)
            pygame.draw.polygon(surf, WHITE, [(sx + 16 * f, sy - 28), (sx + 12 * f, sy - 20), (sx + 21 * f, sy - 27)])
            img = font(16).render("!", True, (220, 40, 40))
            surf.blit(img, (sx + 22 * f - img.get_width() // 2, sy - 44))


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
        self.r = mtype["r"]
        self.elite = (not self.boss) and random.random() < CURRENT["elite"]   # χρυσό, πιο δυνατό τέρας
        hp = mtype["hp"] * (CURRENT.get("boss_hp", 1) if self.boss else CURRENT["hp"])
        if self.elite:
            hp *= 2
            self.r = int(self.r * 1.15)
        self.maxhp = self.hp = max(1, round(hp))
        self.speed = mtype["speed"] * CURRENT["speed"] * (1.1 if self.elite else 1)
        self.dmg = mtype["dmg"] * CURRENT["dmg"]
        self.reward = mtype["reward"] * (2 if self.elite else 1)
        self.dodge_t, self.dodge_v = 0.0, (0.0, 0.0)
        self.enraged = False
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
        if self.elite:
            rr = self.r + 12 + int(math.sin(t * 6) * 3)
            pygame.draw.ellipse(surf, (255, 210, 60), (sx - rr, sy + 8, rr * 2, 22), 3)
            draw_monster_type(surf, sx, sy, self.t, self.face, self.wobble, self.flash > 0,
                              scale=self.t.get("scale", 1.0) * 1.2)
            for i in range(3):
                a = t * 2.5 + i * 2.1
                pygame.draw.circle(surf, (255, 230, 90), (sx + int(math.cos(a) * rr), sy - self.r + int(math.sin(a) * 12)), 3)
        else:
            draw_monster_type(surf, sx, sy, self.t, self.face, self.wobble, self.flash > 0)
        if self.slow_t > 0:
            pygame.draw.circle(surf, (150, 225, 255), (sx, sy - int(self.r * 0.5)), self.r + 6, 2)
            for i in range(3):
                a = t * 3 + i * 2.1
                pygame.draw.circle(surf, WHITE, (sx + int(math.cos(a) * self.r), sy - int(self.r * 0.5) + int(math.sin(a) * self.r)), 2)
        if self.hp < self.maxhp and not self.boss:
            w = self.r * 2
            top = sy - int(self.r * 2.6) - 10
            pygame.draw.rect(surf, (60, 0, 0), (sx - self.r, top, w, 5))
            pygame.draw.rect(surf, (230, 40, 40), (sx - self.r, top, int(w * self.hp / self.maxhp), 5))


class Bullet:
    def __init__(self, x, y, angle, owner, weapon):
        self.x, self.y, self.owner = x, y, owner
        self.vx = math.cos(angle) * BULLET_SPEED
        self.vy = math.sin(angle) * BULLET_SPEED
        self.life = weapon.get("life", 1.0)
        self.dmg = weapon["dmg"]
        self.pierce = weapon.get("pierce", False)
        self.freeze = weapon.get("freeze", False)
        self.splash = weapon.get("splash", 0)
        self.seen = set()
        self.color = weapon["color"] if owner == "player" else (255, 170, 80)
        self.hit = set()

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt
        return self.life > 0 and 0 < self.x < WORLD_W and 0 < self.y < WORLD_H

    def draw(self, surf, cam):
        x, y = int(self.x - cam[0]), int(self.y - cam[1])
        if self.splash:
            pygame.draw.circle(surf, (255, 200, 60), (x, y), 7)
            pygame.draw.circle(surf, self.color, (x, y), 5)
            pygame.draw.circle(surf, (255, 255, 200), (int(x - self.vx), int(y - self.vy)), 3)
        elif self.pierce:
            pygame.draw.line(surf, self.color, (x, y), (int(x - self.vx * 2), int(y - self.vy * 2)), 5)
            pygame.draw.line(surf, WHITE, (x, y), (int(x - self.vx * 2), int(y - self.vy * 2)), 2)
        else:
            pygame.draw.circle(surf, self.color, (x, y), 5 if self.owner == "player" else 4)
            if self.freeze:
                pygame.draw.circle(surf, WHITE, (x, y), 2)


class Bomb:
    """Βόμβα που πετάει ο ήρωας: πετάει σε τόξο, πέφτει και σκάει."""

    def __init__(self, x, y, tx, ty, kind):
        self.x0, self.y0, self.tx, self.ty, self.kind = x, y, tx, ty, kind
        self.x, self.y = x, y
        self.t, self.fly_time, self.fuse = 0.0, 0.55, 0.7
        self.done = False

    def update(self, dt):
        self.t += dt
        k = min(1.0, self.t / self.fly_time)
        self.x = self.x0 + (self.tx - self.x0) * k
        self.y = self.y0 + (self.ty - self.y0) * k
        self.h = math.sin(k * math.pi) * 70
        return self.t >= self.fly_time + self.fuse

    def draw(self, surf, cam, t):
        x, y = int(self.x - cam[0]), int(self.y - cam[1])
        shadow(surf, x, y + 6, 22)
        blink = self.t > self.fly_time and int(self.t * 12) % 2 == 0
        draw_bomb_icon(surf, x, y - int(getattr(self, "h", 0)), self.kind, 1.1, t)
        if blink:
            pygame.draw.circle(surf, (255, 60, 60), (x, y - int(getattr(self, "h", 0))), 15, 3)


class SlashFX:
    """Το «σβουτς» από μαχαίρι / σπαθί / σφυρί."""

    def __init__(self, x, y, ang, reach, arc, color):
        self.x, self.y, self.ang, self.reach, self.arc, self.color = x, y, ang, reach, arc, color
        self.life = 0.18

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surf, cam, t):
        x, y = self.x - cam[0], self.y - cam[1]
        k = max(0.0, self.life / 0.18)
        fx = pygame.Surface((self.reach * 2 + 20, self.reach * 2 + 20), pygame.SRCALPHA)
        c = (self.reach + 10, self.reach + 10)
        pts_out, pts_in = [], []
        n = 12
        for i in range(n + 1):
            a = self.ang - self.arc / 2 + self.arc * i / n
            pts_out.append((c[0] + math.cos(a) * self.reach, c[1] + math.sin(a) * self.reach))
            pts_in.append((c[0] + math.cos(a) * self.reach * 0.45, c[1] + math.sin(a) * self.reach * 0.45))
        pygame.draw.polygon(fx, (*self.color, int(150 * k)), pts_out + pts_in[::-1])
        pygame.draw.lines(fx, (255, 255, 255, int(230 * k)), False, pts_out, 4)
        surf.blit(fx, (x - c[0], y - c[1]))


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


POWER_KINDS = ["heart", "shield", "shoes", "magnet", "team", "bombs"]
POWER_NAMES = {"heart": "Καρδιά!", "shield": "Ασπίδα!", "shoes": "Παπούτσια ταχύτητας!", "magnet": "Μαγνήτης!", "team": "Ήρθε η ομάδα!", "bombs": "+2 Βόμβες!"}


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
    elif kind == "bombs":
        draw_bomb_icon(surf, x, y + 3 * s, "bomb", 0.9 * s)
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
DEFAULT_SAVE = dict(trophies=5, best=5, unlocked=1, cleared=[], album={}, sound=True, difficulty=1,
                    owned=["pistol", "knife"], weapon="pistol", items={"bomb": 3, "icebomb": 0, "potion": 0},
                    upgrades={}, outfit="explorer", outfits=["explorer"], version=3)


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
        s = self.save
        # μετατροπή παλιάς αποθήκευσης στη νέα έκδοση
        if not isinstance(s.get("weapon"), str) or s["weapon"] not in WEAPONS:
            s["weapon"] = "pistol"
        s["owned"] = [w for w in s.get("owned", []) if w in WEAPONS] or ["pistol", "knife"]
        for w in ("pistol", "knife"):
            if w not in s["owned"]:
                s["owned"].append(w)
        if s["weapon"] not in s["owned"]:
            s["weapon"] = "pistol"
        for k in ITEMS:
            s["items"].setdefault(k, 0)
        s["album"] = {k: v for k, v in s["album"].items() if k in ALL_TYPES}
        keys = [w["key"] for w in WORLDS]
        s["cleared"] = [c for c in s["cleared"] if c in keys]
        s["unlocked"] = max(1, min(len(WORLDS), max(s["unlocked"], len(s["cleared"]) + 1)))
        if s["outfit"] not in OUTFITS:
            s["outfit"] = "explorer"

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
        d = self.diff = DIFFICULTIES[self.save.get("difficulty", 1)]
        CURRENT.update(hp=d["hp"] * (1 + d["grow"] * idx), speed=min(1.6, d["speed"] * (1 + 0.03 * idx)),
                       dmg=d["dmg"] * (1 + d["grow"] * 0.5 * idx), elite=min(0.5, d["elite"] + 0.02 * idx),
                       dodge=d["dodge"], pack=d["pack"], boss_hp=d["hp"])
        self.max_monsters = MONSTERS_ALIVE + d["extra"] + idx // 2
        self.world = World(idx)
        self.player = Human(*HQ, is_player=True)
        p = self.player
        p.outfit, p.weapon = self.save["outfit"], self.save["weapon"]
        p.maxhp = p.hp = self.max_hp()
        p.swing_t = 0.0
        self.dog = Dog(HQ[0] + 40, HQ[1] + 25)
        self.bombs, self.fx, self.ring_fx = [], [], []
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
        for _ in range(self.max_monsters):
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
            self.help_cd = self.diff["help_cd"]
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
        return WEAPONS[self.save["weapon"]]

    def cycle_weapon(self):
        owned = [w for w in WEAPON_ORDER if w in self.save["owned"]]
        i = owned.index(self.save["weapon"]) if self.save["weapon"] in owned else -1
        self.save["weapon"] = owned[(i + 1) % len(owned)]
        if self.state == "play":
            p = self.player
            p.weapon = self.save["weapon"]
            self.add_text(p.x, p.y - 70, self.weapon()["name"], self.weapon()["color"], 22)
        self.sfx.play("coin")

    def upg(self, key):
        return self.save["upgrades"].get(key, 0)

    def max_hp(self):
        return PLAYER_MAX_HP + 30 * self.upg("armor")

    def throw_bomb(self, kind):
        items = self.save["items"]
        if self.state != "play" or self.dead_timer > 0 or items.get(kind, 0) <= 0:
            return
        p = self.player
        tgt = self.auto_target(p, 420)
        if tgt:
            tx, ty = tgt.x, tgt.y
        else:
            tx, ty = p.x + math.cos(p.dir) * 260, p.y + math.sin(p.dir) * 260
        d = math.hypot(tx - p.x, ty - p.y)
        if d > 380:
            tx, ty = p.x + (tx - p.x) / d * 380, p.y + (ty - p.y) / d * 380
        items[kind] -= 1
        self.bombs.append(Bomb(p.x, p.y - 20, tx, ty, kind))
        self.sfx.play("flee")

    def bomb_explode(self, b):
        radius = 150
        ice = b.kind == "icebomb"
        dmg = (3 if ice else 9) * max(1.0, CURRENT["hp"])
        cols = [(150, 225, 255), WHITE, (90, 170, 240)] if ice else [(255, 140, 40), (255, 220, 80), (200, 60, 30), (90, 90, 90)]
        for _ in range(60):
            self.particles.append(Particle(b.x, b.y, random.choice(cols), star=ice, speed=10))
        self.ring_fx.append([b.x, b.y, 0.0, radius, cols[0]])
        self.sfx.play("boss" if not ice else "powerup")
        self.shake = max(self.shake, 9)
        for m in self.monsters[:]:
            cx, cy = m.hit_center()
            if math.hypot(cx - b.x, cy - b.y) < radius + m.r:
                if m.state == "hidden":
                    self.reveal(m)
                m.hp -= dmg
                m.flash = 0.15
                if ice:
                    m.slow_t = 5.0
                if m.hp <= 0:
                    self.kill_monster(m, "player")

    def melee(self, wpn):
        p = self.player
        p.swing_t = 0.22
        hx, hy = p.x, p.y - 12
        self.fx.append(SlashFX(hx, hy, p.dir, wpn["reach"] + 10, wpn["arc"], wpn["color"]))
        self.sfx.play("slash")
        hit = False
        for m in self.monsters[:]:
            if m.state == "hidden":
                continue
            cx, cy = m.hit_center()
            d = math.hypot(cx - hx, cy - hy)
            if d > wpn["reach"] + m.r:
                continue
            da = (math.atan2(cy - hy, cx - hx) - p.dir + math.pi) % (2 * math.pi) - math.pi
            if abs(da) > wpn["arc"] / 2 and d > m.r + 10:
                continue
            hit = True
            m.hp -= wpn["dmg"]
            m.flash = 0.12
            kb = wpn.get("knock", 25)
            if not m.boss:
                nx, ny = m.x + (cx - hx) / (d or 1) * kb, m.y + (cy - hy) / (d or 1) * kb
                if m.fly or not self.world.blocked(nx, ny, m.r):
                    m.x, m.y = nx, ny
            if m.hp <= 0:
                self.kill_monster(m, "player")
        if hit:
            self.sfx.play("hit")
            if wpn.get("knock"):
                self.shake = max(self.shake, 5)

    def auto_target(self, h, rng=None):
        best, bd = None, rng or self.diff["aim"]
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
        if wpn["kind"] == "melee":
            self.melee(wpn)
            return
        tx, ty = p.gun_tip()
        j = wpn.get("jitter", 0.03)
        for a in wpn["angles"]:
            self.bullets.append(Bullet(tx, ty, p.dir + a + random.uniform(-j, j), "player", wpn))
        self.particles.append(Particle(tx, ty, (255, 230, 140), speed=2))
        self.sfx.play("laser" if wpn.get("pierce") else ("rocket" if wpn.get("splash") else "shoot"))

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
        for b in self.bombs[:]:
            if b.update(dt):
                self.bombs.remove(b)
                self.bomb_explode(b)
        self.fx = [o for o in self.fx if o.update(dt)]
        for r in self.ring_fx:
            r[2] += dt
        self.ring_fx = [r for r in self.ring_fx if r[2] < 0.35]
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
                p.hp, p.invuln = self.max_hp(), 2.5
                self.dog.x, self.dog.y = HQ[0] + 40, HQ[1] + 25
            return
        mx, my = self.move_input()
        p.moving = bool(mx or my)
        p.swing_t = max(0.0, getattr(p, "swing_t", 0) - dt)
        p.swing = (1 - p.swing_t / 0.22) * 2 - 1 if p.swing_t > 0 else 0.0
        p.weapon = self.save["weapon"]
        sp = PLAYER_SPEED * (1.6 if p.speed_t > 0 else 1) * (1.15 if self.upg("boots") else 1)
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
            p.hp = min(p.maxhp, p.hp + 6 * dt)

    def update_dog(self, dt):
        d, p, world = self.dog, self.player, self.world
        d.barking = max(0, d.barking - dt)
        d.bite_t = max(0, d.bite_t - dt)
        d.bite_cd = max(0, d.bite_cd - dt)
        d.moving = False
        if self.upg("dogbite") and self.dead_timer <= 0:
            prey, bd = None, 260
            for m in self.monsters:
                if m.state == "chase" and not m.fly and dist(m, p) < 320:
                    dd = dist(m, d)
                    if dd < bd:
                        prey, bd = m, dd
            if prey:
                d.target = None
                if bd > prey.r + 14:
                    d.moving = d.steer(world, prey.x, prey.y, DOG_SPEED * 1.2, dt)
                else:
                    d.dir = math.atan2(prey.y - d.y, prey.x - d.x)
                    if d.bite_cd <= 0:
                        d.bite_cd, d.bite_t = 0.7, 0.2
                        prey.hp -= max(1, round(CURRENT["hp"]))
                        prey.flash = 0.1
                        self.add_text(d.x, d.y - 40, "ΧΑΜ!", (255, 230, 120), 20)
                        self.sfx.play("bark", gap=0.3)
                        if prey.hp <= 0:
                            self.kill_monster(prey, "player")
                if d.moving:
                    d.walk += dt * 14
                return
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
                    self.add_text(d.x, d.y - 45, "ΓΑΒ! ΓΑΒ!", (255, 255, 255), 22)
                    self.sfx.play("bark")
        else:
            back = p.dir + math.pi
            tx, ty = p.x + math.cos(back) * 50, p.y + math.sin(back) * 35 + 14
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
                self.bullets.append(Bullet(tx, ty, a.dir + random.uniform(-0.09, 0.09), "ally", WEAPONS["pistol"]))
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
                    self.reveal(m)
                    if CURRENT["pack"]:      # ενέδρα: ξυπνάνε και τα διπλανά τέρατα!
                        for o in self.monsters:
                            if o.state == "hidden" and o is not m and dist(o, m) < 280:
                                self.reveal(o)
                    break
            return
        speed = m.speed * (0.4 if m.slow_t > 0 else 1)
        if m.dodge_t > 0:          # πηδάει στο πλάι για να αποφύγει σφαίρα
            m.dodge_t -= dt
            nx, ny = m.x + m.dodge_v[0] * speed * 2.6, m.y + m.dodge_v[1] * speed * 2.6
            if m.fly or not world.blocked(nx, ny, m.r):
                m.x, m.y = nx, ny
            return
        if m.boss and not m.enraged and m.hp <= m.maxhp / 2:
            m.enraged = True
            m.speed *= 1.35
            m.summon_t = 1.0
            self.set_banner(f"Ο {m.t['name']} ΘΥΜΩΣΕ!", 3.0, (255, 80, 80))
            self.sfx.play("boss")
            self.shake = 8
        if m.state == "chase":
            if not m.fled and m.maxhp >= 2 and m.hp <= m.maxhp / 2:
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
                        m.shoot_t = m.t["shoot"] * (0.6 if m.enraged else 1) + random.uniform(0, 0.8)
                        ang = math.atan2(target.y - 8 - cy, target.x - cx)
                        if m.boss:
                            for da in ((-0.4, -0.2, 0, 0.2, 0.4) if m.enraged else (-0.25, 0, 0.25)):
                                self.shots.append(Shot(cx, cy, ang + da, 5.2, 16, m.t["shot_col"], ghost=m.fly))
                        else:
                            self.shots.append(Shot(cx, cy, ang, 5.5, 12, (255, 140, 40)))
                        if self.on_screen(m.x, m.y):
                            self.sfx.play("fire")
            if m.boss and m.t.get("summon"):
                m.summon_t -= dt
                if m.summon_t <= 0 and len(self.monsters) < 28:
                    m.summon_t = 4.5 if m.enraged else 7.0
                    for k in (-1, 1):
                        x, y = m.x + k * 60, m.y + 30
                        if not world.blocked(x, y, 20) or MT[m.t["summon"]].get("fly"):
                            self.monsters.append(Monster(None, MT[m.t["summon"]], x, y))
                            self.poof(x, y, (200, 200, 255), 10)
            for h in humans:
                if not h.protected() and dist(m, h) < m.r + h.r + 2:
                    h.hp -= m.dmg * dt
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
                    m.hp = m.maxhp
                m.state, m.path = "hidden", None
                m.x, m.y = m.spot.x, m.spot.y

    def update_bullets(self, dt):
        world = self.world
        alive = []
        for b in self.bullets:
            if not b.update(dt) or world.blocked(b.x, b.y, 0):
                continue
            used = False
            if CURRENT["dodge"] > 0:
                for m in self.monsters:
                    if m.state != "chase" or m.boss or id(m) in b.seen:
                        continue
                    if abs(m.x - b.x) < 110 and abs(m.y - b.y) < 110:
                        b.seen.add(id(m))
                        if random.random() < CURRENT["dodge"]:
                            l = math.hypot(b.vx, b.vy) or 1
                            side = random.choice((-1, 1))
                            m.dodge_v = (-b.vy / l * side, b.vx / l * side)
                            m.dodge_t = 0.28
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
                    if b.splash:
                        self.explode(b.x, b.y, b.splash, b.dmg, m)
                    if m.hp <= 0:
                        self.kill_monster(m, b.owner)
                    if not b.pierce:
                        used = True
                        break
            if not used:
                alive.append(b)
        self.bullets = alive

    def reveal(self, m):
        m.state, m.lost = "chase", 0
        if m.spot:
            m.spot.occupant, m.spot = None, None
        if self.on_screen(m.x, m.y, 200):
            self.sfx.play("v_" + m.t["voice"] if m.t.get("voice") else "growl", gap=0.3)
            self.add_text(m.x, m.y - 50, "!", (255, 60, 60), 34)

    def explode(self, x, y, radius, dmg, skip):
        for _ in range(24):
            self.particles.append(Particle(x, y, random.choice([(255, 140, 40), (255, 220, 80), (200, 60, 30)]),
                                           speed=7))
        self.sfx.play("poof", gap=0.05)
        self.shake = max(self.shake, 3)
        for o in self.monsters[:]:
            if o is skip or o.state == "hidden":
                continue
            cx, cy = o.hit_center()
            if math.hypot(cx - x, cy - y) < radius + o.r:
                o.hp -= dmg
                o.flash = 0.1
                if o.hp <= 0:
                    self.kill_monster(o, "player")

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
        rad = 520 if p.magnet_t > 0 else (300 if self.upg("magnet") else 110)
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
            p.hp = p.maxhp
            if self.lives < LIVES:
                self.lives += 1
        elif kind == "shield":
            p.shield_t = 8.0
        elif kind == "shoes":
            p.speed_t = 8.0
        elif kind == "magnet":
            p.magnet_t = 12.0
        elif kind == "bombs":
            self.save["items"]["bomb"] = self.save["items"].get("bomb", 0) + 2
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
        self.poof(cx, cy, m.t["color"], 45 if m.elite else 26)
        if m.elite and owner == "player":
            self.add_text(m.x, m.y - 70, "ΧΡΥΣΟ ΤΕΡΑΣ! x2", GOLD, 26)
        if owner == "player":
            for _ in range(m.reward):
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
        if not self.boss_spawned or len(self.monsters) < self.max_monsters // 2:
            self.spawn_monster()

    def human_died(self, h, killer):
        if not h.alive or (h.is_player and self.dead_timer > 0):
            return
        if h.is_player and self.save["items"].get("potion", 0) > 0:
            self.save["items"]["potion"] -= 1
            h.hp = h.maxhp
            h.invuln = 2.0
            self.add_text(h.x, h.y - 70, "ΦΙΛΤΡΟ ΖΩΗΣ!", (255, 120, 170), 28)
            self.sfx.play("powerup")
            for _ in range(30):
                self.particles.append(Particle(h.x, h.y - 20, (255, 120, 170), star=True, speed=6))
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
        s["items"]["bomb"] = s["items"].get("bomb", 0) + 3
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
        for bm in self.bombs:
            bm.draw(s, cam, t)
        for fx in self.fx:
            fx.draw(s, cam, t)
        for x, y, age, rad, col in self.ring_fx:
            k = age / 0.35
            pygame.draw.circle(s, col, (int(x - cam[0]), int(y - cam[1])), max(2, int(rad * k)), max(2, int(10 * (1 - k))))
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
        hp = max(0, p.hp) / p.maxhp
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
            pygame.draw.rect(s, (230, 50, 60), (W // 2 - 200, 44, int(400 * max(0, b.hp) / b.maxhp), 20),
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
        s.blit(weapon_icon(self.save["weapon"], 76, 40, self.t), (wc[0] - 38, wc[1] - 32))
        self.text(wpn["name"], 14, WHITE, wc[0], wc[1] + 14, shadow_px=1)
        if len(self.save["owned"]) > 1:
            self.hot.append((pygame.Rect(wc[0] - 46, wc[1] - 46, 92, 92), self.cycle_weapon))
        # βόμβες
        items = self.save["items"]
        for kind, bc in (("bomb", (W - 245, H - 196)), ("icebomb", (W - 355, H - 80) if self.touch_seen
                                                          else (W - 470, H - 80))):
            n = items.get(kind, 0)
            col = ((200, 70, 50) if kind == "bomb" else (60, 130, 200)) if n > 0 else (100, 100, 110)
            pygame.draw.circle(s, (0, 0, 0), (bc[0], bc[1] + 4), 40)
            pygame.draw.circle(s, col, bc, 40)
            pygame.draw.circle(s, WHITE, bc, 40, 3)
            draw_bomb_icon(s, bc[0], bc[1] - 4, kind, 1.3, self.t)
            self.text(f"x{n}", 18, WHITE, bc[0] + 22, bc[1] + 10, shadow_px=2)
            self.hot.append((pygame.Rect(bc[0] - 40, bc[1] - 40, 80, 80), lambda k=kind: self.throw_bomb(k)))
        if items.get("potion", 0) > 0:
            draw_potion_icon(s, 330, 40, 1.0)
            self.text(f"x{items['potion']}", 18, WHITE, 344, 34, center=False, shadow_px=2)
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
            self.text("WASD: κίνηση · ποντίκι/SPACE: φωτιά · Q: όπλο · E/F: βόμβα · H: βοήθεια · P: παύση", 17, WHITE, W // 2, H - 30, shadow_px=2)
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
        self.text("MONSTER HUNTER", 58, GOLD, W // 2, 12, shadow_px=4)
        self.text("Κυνήγι Τεράτων", 22, WHITE, W // 2, 80, shadow_px=2)
        draw_trophy(s, W - 160, 40, 1.5)
        self.text(str(self.trophies), 36, GOLD, W - 136, 18, center=False)
        cw, ch, gap = 186, 112, 14
        x0 = (W - (cw * 5 + gap * 4)) // 2
        for i, th in enumerate(WORLDS):
            r = pygame.Rect(x0 + (i % 5) * (cw + gap), 114 + (i // 5) * (ch + 10), cw, ch)
            unlocked = i < self.save["unlocked"]
            pygame.draw.rect(s, (0, 0, 0), r.move(0, 4), border_radius=14)
            pygame.draw.rect(s, th["ground"], r, border_radius=14)
            pygame.draw.rect(s, th["road"], (r.x, r.bottom - 30, r.w, 30), border_bottom_left_radius=14,
                             border_bottom_right_radius=14)
            draw_monster_type(s, r.centerx, r.y + 64 + int(math.sin(t * 2 + i) * 2), BOSSES[th["boss"]], 1, t * 3,
                              flash=False, scale=0.7)
            pygame.draw.rect(s, WHITE, r, 3, border_radius=14)
            self.text(f"{i + 1}. {th['name']}", 17, WHITE, r.centerx, r.bottom - 26, shadow_px=2)
            if not unlocked:
                ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
                ov.fill((10, 10, 20, 195))
                s.blit(ov, r.topleft)
                draw_lock(s, r.centerx, r.centery, 1.0)
            else:
                if th["key"] in self.save["cleared"]:
                    cx, cy = r.right - 18, r.y + 18
                    pts = [(cx + math.cos(a) * (12 if j % 2 == 0 else 5), cy + math.sin(a) * (12 if j % 2 == 0 else 5))
                           for j, a in enumerate([-math.pi / 2 + j * math.pi / 5 for j in range(10)])]
                    pygame.draw.polygon(s, GOLD, pts)
                    pygame.draw.polygon(s, (150, 100, 10), pts, 2)
                if i >= 10 and th["key"] not in self.save["cleared"]:
                    self.text("ΝΕΟ!", 15, (255, 240, 120), r.x + 26, r.y + 6, shadow_px=1)
                self.hot.append((r, lambda i=i: self.start_world(i)))
        n_alb = len([k for k in ALBUM_ORDER if k in self.save["album"]])
        d = DIFFICULTIES[self.save.get("difficulty", 1)]
        bw, gap = 250, 14
        bx = (W - (bw * 4 + gap * 3)) // 2
        self.button((bx, 492, bw, 66), "Κατάστημα", (220, 150, 30), self.open_shop, 28)
        self.button((bx + (bw + gap), 492, bw, 66), f"Άλμπουμ {n_alb}/{len(ALBUM_ORDER)}", (150, 80, 190),
                    lambda: self.open_album("menu"), 24)
        self.button((bx + 2 * (bw + gap), 492, bw, 66), f"Δυσκολία: {d['name']}", d["color"], self.cycle_difficulty, 20)
        self.button((bx + 3 * (bw + gap), 492, bw, 66), "Ήχος: " + ("ON" if self.sfx.on else "OFF"),
                    (70, 140, 90) if self.sfx.on else (110, 110, 110), self.toggle_sound, 24)
        self.text(f"Όπλα: {len(self.save['owned'])}/{len(WEAPONS)}   ·   Ρεκόρ κυπέλλων: {self.save['best']}", 19,
                  (200, 210, 240), W // 2, 574, shadow_px=1)
        draw_player(s, 90, 652, -0.1, t * 6, self.save["outfit"], self.save["weapon"], 0.0, t)
        draw_dog(s, 160, 664, 1, t * 6, True, int(t * 2) % 3 == 0)
        draw_monster_type(s, 1030, 668, MT["troll"], -1, t * 3, scale=1.2)
        draw_monster_type(s, 940, 660, MT["ghost"], -1, t * 3, scale=1.1)

    def cycle_difficulty(self):
        self.save["difficulty"] = (self.save.get("difficulty", 1) + 1) % len(DIFFICULTIES)
        self.sfx.play("coin")
        self.save_game()

    def open_album(self, back):
        self.album_back = back
        self.state = "album"

    def build_album_cache(self):
        cache = {}
        for key in ALBUM_ORDER:
            t = ALL_TYPES[key]
            boss = t["boss"]
            size = (170, 100) if boss else (118, 92)
            img = pygame.Surface(size, pygame.SRCALPHA)
            sc = 1.0 if boss else 1.05
            draw_monster_type(img, size[0] // 2, size[1] - 20, t, 1, 0.0, scale=sc)
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
            cw, ch, gap = 128, 148, 8
            for ri, items in enumerate(rows):
                x0 = (W - (cw * len(items) + gap * (len(items) - 1))) // 2
                for i, key in enumerate(items):
                    self.album_card(pygame.Rect(x0 + i * (cw + gap), 54 + ri * (ch + 8), cw, ch), key, alb)
            self.button((W // 2 - 330, 548, 300, 70), "Αρχηγοί  >", (190, 140, 40), self.album_flip, 30)
            self.button((W // 2 + 30, 548, 300, 70), "Πίσω", (80, 90, 140), self.album_close, 30)
        else:
            bosses = list(BOSSES)
            cw, ch, gap = 196, 150, 12
            x0 = (W - (cw * 5 + gap * 4)) // 2
            for i, key in enumerate(bosses):
                self.album_card(pygame.Rect(x0 + (i % 5) * (cw + gap), 52 + (i // 5) * (ch + 6), cw, ch), key, alb)
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
            fs = 16
            while fs > 10 and font(fs).size(nm)[0] > r.w - 10:
                fs -= 1
            self.text(nm, fs, (60, 40, 30), r.centerx, r.bottom - 44, shadow_px=0)
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
        self.text("ΠΑΥΣΗ", 60, WHITE, W // 2, 70)
        self.button((W // 2 - 170, 170, 340, 76), "Συνέχεια", (60, 160, 90), self.resume, 34)
        self.button((W // 2 - 170, 262, 340, 76), "Κατάστημα", (220, 150, 30), lambda: self.open_shop("pause"), 32)
        self.button((W // 2 - 170, 354, 340, 76), "Άλμπουμ", (150, 80, 190), lambda: self.open_album("pause"), 32)
        self.button((W // 2 - 170, 446, 340, 76), "Μενού", (90, 90, 140), self.to_menu, 32)
        self.button((W // 2 - 170, 538, 340, 66), "Ήχος: " + ("ON" if self.sfx.on else "OFF"),
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
        if True:
            self.text("Δώρο: +3 Βόμβες και κύπελλα για το κατάστημα!", 30, (255, 200, 120), W // 2, y)
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

    # ------------------------------------------------------------ κατάστημα
    def open_shop(self, back="menu"):
        self.shop_back = back if isinstance(back, str) else "menu"
        self.shop_tab = getattr(self, "shop_tab", "weapons")
        self.shop_msg = None
        self.state = "shop"

    def shop_close(self):
        self.save_game()
        self.state = getattr(self, "shop_back", "menu")

    def shop_say(self, txt, col=(255, 230, 120)):
        self.shop_msg = [txt, 2.2, col]

    def pay(self, price):
        if self.save["trophies"] < price:
            self.shop_say(f"Θέλεις {price - self.save['trophies']} κύπελλα ακόμα!", (255, 120, 120))
            self.sfx.play("hurt")
            return False
        self.save["trophies"] -= price
        self.sfx.play("powerup")
        for _ in range(20):
            self.ui_particles.append([random.uniform(300, 820), 640, random.uniform(-3, 3), random.uniform(-9, -4),
                                      random.choice([GOLD, (255, 255, 255), (255, 150, 200)])])
        return True

    def shop_weapon(self, key):
        s = self.save
        if key in s["owned"]:
            s["weapon"] = key
            self.shop_say(f"Διάλεξες: {WEAPONS[key]['name']}")
            self.sfx.play("coin")
        elif self.pay(WEAPONS[key]["price"]):
            s["owned"].append(key)
            s["weapon"] = key
            self.shop_say(f"Αγόρασες: {WEAPONS[key]['name']}!", (140, 255, 160))
        self.save_game()

    def shop_item(self, key):
        it = ITEMS[key]
        if self.pay(it["price"]):
            self.save["items"][key] = self.save["items"].get(key, 0) + it["add"]
            self.shop_say(f"Αγόρασες: {it['name']}!", (140, 255, 160))
            self.save_game()

    def shop_upgrade(self, key):
        u = UPGRADES[key]
        lvl = self.upg(key)
        if lvl >= len(u["prices"]):
            self.shop_say("Το έχεις στο μέγιστο!")
            return
        if self.pay(u["prices"][lvl]):
            self.save["upgrades"][key] = lvl + 1
            self.shop_say(f"Αναβάθμιση: {u['name']}!", (140, 255, 160))
            self.save_game()

    def shop_outfit(self, key):
        s = self.save
        if key in s["outfits"]:
            s["outfit"] = key
            self.shop_say(f"Φοράς: {OUTFITS[key]['name']}")
            self.sfx.play("coin")
        elif self.pay(OUTFITS[key]["price"]):
            s["outfits"].append(key)
            s["outfit"] = key
            self.shop_say(f"Νέα στολή: {OUTFITS[key]['name']}!", (140, 255, 160))
        if self.state == "shop" and getattr(self, "player", None) is not None:
            self.player.outfit = s["outfit"]
        self.save_game()

    @staticmethod
    def weapon_stars(w):
        if w["kind"] == "melee":
            power = w["dmg"] / w["cd"] * 1.1
        else:
            power = w["dmg"] * len(w["angles"]) * (0.55 if w.get("life") else 1) / w["cd"]
            if w.get("splash"):
                power *= 2.2
            if w.get("pierce"):
                power *= 1.4
        return max(1, min(5, int(power / 7) + 1))

    def shop_card(self, r, title, price, status, action, draw_icon, desc="", owned=False, selected=False):
        s = self.screen
        pygame.draw.rect(s, (0, 0, 0), r.move(0, 5), border_radius=16)
        base = (70, 110, 80) if selected else ((70, 75, 115) if owned else (60, 55, 90))
        pygame.draw.rect(s, base, r, border_radius=16)
        pygame.draw.rect(s, GOLD if selected else WHITE, r, 3, border_radius=16)
        draw_icon(r)
        fs = 18
        while fs > 11 and font(fs).size(title)[0] > r.w - 12:
            fs -= 1
        self.text(title, fs, WHITE, r.centerx, r.y + 92, shadow_px=2)
        if desc:
            ds = 14
            while ds > 9 and font(ds).size(desc)[0] > r.w - 10:
                ds -= 1
            self.text(desc, ds, (210, 215, 240), r.centerx, r.y + 118, shadow_px=1)
        if status:
            col = (140, 255, 160) if selected else (220, 220, 255)
            self.text(status, 16, col, r.centerx, r.bottom - 30, shadow_px=1)
        elif price is not None:
            afford = self.save["trophies"] >= price
            draw_trophy(s, r.centerx - 34, r.bottom - 17, 0.9)
            self.text(str(price), 22, GOLD if afford else (255, 110, 110), r.centerx - 18, r.bottom - 32,
                      center=False, shadow_px=2)
        self.hot.append((r, action))

    def draw_shop(self):
        s, t = self.screen, self.t
        s.fill((40, 30, 70))
        for i in range(10):
            pygame.draw.circle(s, (52, 40, 88), (int(60 + i * 115), int(60 + (i % 3) * 230)), 70)
        self.text("ΚΑΤΑΣΤΗΜΑ", 44, GOLD, W // 2, 8, shadow_px=4)
        draw_trophy(s, W - 170, 34, 1.5)
        self.text(str(self.trophies), 34, GOLD, W - 146, 14, center=False)
        tabs = [("weapons", "Όπλα"), ("items", "Βόμβες & Δώρα"), ("style", "Στολές")]
        for i, (key, name) in enumerate(tabs):
            sel = self.shop_tab == key
            r = pygame.Rect(W // 2 - 390 + i * 265, 66, 250, 50)
            pygame.draw.rect(s, (0, 0, 0), r.move(0, 4), border_radius=14)
            pygame.draw.rect(s, (220, 150, 30) if sel else (80, 70, 120), r, border_radius=14)
            pygame.draw.rect(s, WHITE, r, 2, border_radius=14)
            self.text(name, 22, WHITE, r.centerx, r.y + 11, shadow_px=2)
            self.hot.append((r, lambda k=key: setattr(self, "shop_tab", k)))
        cw, ch, gap = 200, 186, 12
        x0 = (W - (cw * 5 + gap * 4)) // 2
        cell = lambda i: pygame.Rect(x0 + (i % 5) * (cw + gap), 132 + (i // 5) * (ch + 12), cw, ch)
        sv = self.save
        if self.shop_tab == "weapons":
            for i, key in enumerate(WEAPON_ORDER):
                w = WEAPONS[key]
                owned, sel = key in sv["owned"], sv["weapon"] == key
                stars = "★" * self.weapon_stars(w) + "☆" * (5 - self.weapon_stars(w))
                kind = "κοντινή μάχη" if w["kind"] == "melee" else ("εκρηκτικό" if w.get("splash") else
                                                                   ("παγώνει" if w.get("freeze") else ""))
                self.shop_card(cell(i), w["name"], w["price"], "ΔΙΑΛΕΓΜΕΝΟ" if sel else ("ΔΙΑΛΕΞΕ" if owned else None),
                               lambda k=key: self.shop_weapon(k),
                               lambda r, k=key: s.blit(weapon_icon(k, 150, 62), (r.centerx - 75, r.y + 18)),
                               f"{stars} {kind}".strip(), owned, sel)
        elif self.shop_tab == "items":
            i = 0
            for key, it in ITEMS.items():
                def icon(r, k=key):
                    if k == "potion":
                        draw_potion_icon(s, r.centerx, r.y + 52, 2.2)
                    else:
                        for j in range(3):
                            draw_bomb_icon(s, r.centerx - 36 + j * 36, r.y + 58, k, 1.3, t)
                self.shop_card(cell(i), it["name"], it["price"], None, lambda k=key: self.shop_item(k), icon,
                               f"Έχεις: {sv['items'].get(key, 0)}")
                i += 1
            for key, u in UPGRADES.items():
                lvl = self.upg(key)
                maxed = lvl >= len(u["prices"])

                def icon(r, k=key):
                    cx, cy = r.centerx, r.y + 50
                    if k == "armor":
                        pts = [(cx - 26, cy - 26), (cx + 26, cy - 26), (cx + 26, cy), (cx, cy + 30), (cx - 26, cy)]
                        pygame.draw.polygon(s, (170, 180, 200), pts)
                        pygame.draw.polygon(s, WHITE, pts, 3)
                        pygame.draw.line(s, (120, 130, 150), (cx, cy - 22), (cx, cy + 24), 4)
                    elif k == "dogbite":
                        draw_dog(s, cx, cy + 14, 1, t * 6, True, True)
                        self.text("ΧΑΜ!", 16, (255, 230, 120), cx + 30, cy - 30, shadow_px=1)
                    elif k == "magnet":
                        draw_power_icon(s, "magnet", cx, cy, 2.0)
                    elif k == "boots":
                        draw_power_icon(s, "shoes", cx, cy, 2.0)
                lv = f"Επίπεδο {lvl}/{len(u['prices'])}" if len(u["prices"]) > 1 else u["desc"]
                self.shop_card(cell(i), u["name"], None if maxed else u["prices"][lvl], "ΜΕΓΙΣΤΟ!" if maxed else None,
                               lambda k=key: self.shop_upgrade(k), icon, lv, maxed, maxed)
                i += 1
        else:
            for i, (key, o) in enumerate(OUTFITS.items()):
                owned, sel = key in sv["outfits"], sv["outfit"] == key
                self.shop_card(cell(i), o["name"], o["price"], "ΦΟΡΑΣ ΤΗΝ" if sel else ("ΦΟΡΕΣΕ" if owned else None),
                               lambda k=key: self.shop_outfit(k),
                               lambda r, k=key: draw_player(s, r.centerx, r.y + 62, -0.15, t * 5, k, sv["weapon"], 0, t),
                               "", owned, sel)
        if self.shop_msg:
            txt, dur, col = self.shop_msg
            self.shop_msg[1] -= 1 / 60
            if self.shop_msg[1] <= 0:
                self.shop_msg = None
            img = font(26).render(txt, True, col)
            bg = pygame.Surface((img.get_width() + 40, 46), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            s.blit(bg, (W // 2 - bg.get_width() // 2, 536))
            s.blit(img, (W // 2 - img.get_width() // 2, 542))
        for pp in self.ui_particles:
            pp[0] += pp[2]
            pp[1] += pp[3]
            pp[3] += 0.3
            pygame.draw.rect(s, pp[4], (int(pp[0]), int(pp[1]), 8, 8))
        self.ui_particles = [pp for pp in self.ui_particles if pp[1] < H + 20]
        self.button((W // 2 - 140, 600, 280, 70), "Πίσω", (80, 90, 140), self.shop_close, 32)

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
        elif st == "shop":
            self.shop_close()
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
                elif e.key == pygame.K_e and self.state == "play":
                    self.throw_bomb("bomb")
                elif e.key == pygame.K_f and self.state == "play":
                    self.throw_bomb("icebomb")
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
        elif st == "shop":
            self.draw_shop()
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
