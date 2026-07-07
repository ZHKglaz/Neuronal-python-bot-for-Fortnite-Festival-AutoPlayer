import time
import keyboard
import cv2
import numpy as np
import bettercam
import ctypes
from colorama import Fore, Back, Style
import os
import json
import threading
import win32api
import win32gui
import win32con

# Set console title
os.system("title AlphaOne Autoplayer Console")

# Clear the console
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
cls()

# Load configuration
try:
    config = json.load(open("config.json", "r"))
except Exception as e:
    print(Back.RED + Fore.WHITE + f"ERROR: Failed to load configuration file. {str(e)}" + Back.RESET + Fore.RESET)
    exit()

monitor_width = ctypes.windll.user32.GetSystemMetrics(0)
monitor_height = ctypes.windll.user32.GetSystemMetrics(1)

if config.get("console_window_ontop") == "true":
    global hwnd
    hwnd_list = []
    def findit(hwnd, ctx):
        if win32gui.GetWindowText(hwnd).find("AlphaOne Autoplayer Console") != -1:
            hwnd_list.append(hwnd)
    win32gui.EnumWindows(findit, None)
    if len(hwnd_list) == 1:
        hwnd = hwnd_list[0]
        try:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except Exception as e:
            print(Back.RED + Fore.WHITE + f"ERROR: {str(e)} while setting window position." + Back.RESET + Fore.RESET)
    else:
        print(Back.RED + Fore.WHITE + "ERROR: Console window handle not found or multiple windows detected." + Back.RESET + Fore.RESET)

# START
print(f'''
{Fore.RED}   :::::   {Fore.YELLOW}###        {Fore.YELLOW}########   {Fore.GREEN}#+#     #+#{Fore.CYAN}   :::::   {Fore.BLUE}  :::::::  {Fore.MAGENTA}###     ###{Fore.MAGENTA}##########
{Fore.RED}  :+: :+:  {Fore.YELLOW}#+#        {Fore.YELLOW}#+#    #+# {Fore.GREEN}#+#     #+#{Fore.CYAN}  :+: :+:  {Fore.BLUE} :+:   :+: {Fore.MAGENTA}#+#+    #+#{Fore.MAGENTA}#+#       
{Fore.RED} +:+   +:+ {Fore.YELLOW}#+#        {Fore.YELLOW}#+#    #+# {Fore.GREEN}#+#     #+#{Fore.CYAN} +:+   +:+ {Fore.BLUE}+:+     +:+{Fore.MAGENTA}#+# +   #+#{Fore.MAGENTA}#+#       
{Fore.RED}+#+++:+++#+{Fore.YELLOW}#+#        {Fore.YELLOW}#+#    #+# {Fore.GREEN}#+#######+#{Fore.CYAN}+#+++:+++#+{Fore.BLUE}+#+     +#+{Fore.MAGENTA}#+#  +  #+#{Fore.MAGENTA}#+####    
{Fore.RED}+#+     +#+{Fore.YELLOW}#+#        {Fore.YELLOW}########   {Fore.GREEN}#+#     #+#{Fore.CYAN}+#+     +#+{Fore.BLUE}+#+     +#+{Fore.MAGENTA}#+#   + #+#{Fore.MAGENTA}#+#       
{Fore.RED}#+#     #+#{Fore.YELLOW}#+#        {Fore.YELLOW}#+#        {Fore.GREEN}#+#     #+#{Fore.CYAN}#+#     #+#{Fore.BLUE}#+#     #+#{Fore.MAGENTA}#+#    +#+#{Fore.MAGENTA}#+#       
{Fore.RED}###     ###{Fore.YELLOW}#########  {Fore.YELLOW}###        {Fore.GREEN}###     ###{Fore.CYAN}###     ###{Fore.BLUE} #######   {Fore.MAGENTA}###     ###{Fore.MAGENTA}##########
''')

print(Style.RESET_ALL + Fore.RED + "First iterration of my neuronal autoplayer (Fortnite Festival)")
print("Project by ZhKGlaz")
print("Project from : https://github.com/ZHKglaz/Neuronal-python-bot-for-Fortnite-Festival-AutoPlayer")
if not config["always_single_lanemode"] == "true":
    number_of_lanes = int(input("Number of lanes (4 = easy-hard, 5 = expert): "))
else:
    number_of_lanes = config["single_lanemode_lanes"]

assert number_of_lanes in [4, 5], Back.RED + Fore.WHITE + "Number of lanes must be 4 or 5" + Back.RESET + Fore.RESET

print(Fore.GREEN + f"WILL ONLY AUTOPLAY WHILE CAPS LOCK IS ON! CURRENT CAPSLOCK STATUS: " + ("On" if win32api.GetKeyState(0x14) else "Off"))
print(Fore.YELLOW + f"Resolution: {monitor_width}x{monitor_height}" + Fore.RESET)
print(f"Program started, press {str.upper(config['exit_key'])} to exit")

image_found = False
for filename in os.listdir("assets"):
    if filename == str(monitor_height):
        image_found = True
        break
if not image_found:
    print(Back.RED + Fore.WHITE + "No match images in the assets folder found with the current monitor height! Please make sure you have an image made." + Back.RESET + Fore.RESET)
    exit()

# 1080p values:
region_width = 555 if number_of_lanes == 4 else 696 # width of the capture region
region_height = 180 # height of the capture region
height_offset = 190 # higher number is looking higher :O
# scale values
scale_factor = 1080 / monitor_height
min_tile_pixels_top_offset = int(config["min_tile_pixels_top_offset_scaled"] // scale_factor)
if scale_factor != 1:
    region_width = int(region_width // scale_factor)
    region_height = int(region_height // scale_factor)
    height_offset = int(height_offset // scale_factor)

# agrandir la zone de capture vers le haut, pour que la détection
# ("les neurones") voit les notes plus tôt/plus haut sur l'écran.
# Le bas de la zone (aligné sur la ligne de frappe) ne bouge pas : on ajoute
# le même décalage à min_tile_pixels_top_offset pour que la ligne de frappe
# reste physiquement au même endroit sur l'écran.
capture_extra_height = config.get("capture_region_extra_height", 150)  # en pixels, valeur pour 1080p
if scale_factor != 1:
    capture_extra_height = int(capture_extra_height // scale_factor)
region_height += capture_extra_height
min_tile_pixels_top_offset += capture_extra_height

region_fromleft = int(((monitor_width - region_width) // 2) + (8 // scale_factor) if number_of_lanes == 5 else ((monitor_width - region_width) // 2) + 1) # higher offset is looking more right. idk why this is needed since it should be centered. fortnite festival is slightly to the right?
region_fromtop = (monitor_height - region_height) - height_offset
width = region_fromleft + region_width
height = region_fromtop + region_height
section_size = region_width // number_of_lanes

main_camera = bettercam.create(output_color = "GRAY", max_buffer_len=512)
main_camera.start(region = (region_fromleft, region_fromtop, width, height), target_fps=config["capture_fps"])
boxed_screenshot = main_camera.get_latest_frame()

lane_cooldowns = {
    str(config["key_1"]): 0.0,
    str(config["key_2"]): 0.0,
    str(config["key_3"]): 0.0,
    str(config["key_4"]): 0.0,
    str(config["key_5"]): 0.0
}

# NOUVEAU : état de maintien (hold) par voie (dont work)
lane_holding = {
    str(config["key_1"]): False,
    str(config["key_2"]): False,
    str(config["key_3"]): False,
    str(config["key_4"]): False,
    str(config["key_5"]): False
}

# dernière fois qu'une barre de maintien a été vue pour chaque voie
# (utilisé pour un "délai de grâce" avant de relâcher, afin d'éviter les faux
# relâchements dus à une seule frame manquée / course entre threads)
lane_hold_last_seen = {
    str(config["key_1"]): 0.0,
    str(config["key_2"]): 0.0,
    str(config["key_3"]): 0.0,
    str(config["key_4"]): 0.0,
    str(config["key_5"]): 0.0
}

# Délai (en secondes) sans détection avant de considérer que le hold est terminé
hold_release_grace = config.get("hold_release_grace", 0.12)

# NOUVEAU : stockage des dernières détections pour la fenêtre de debug
latest_detections = {
    "tile": [],
    "white": [],
    "battlestage": [],
    "diamond": [],
    "hold": []
}
detections_lock = threading.Lock()

def truncate(n, decimals = 0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def cooldown(key):
    lane_cooldowns[key] = config["max_lane_cooldown"]
    time.sleep(config["max_lane_cooldown"])
    lane_cooldowns[key] = 0.0

def press(key, hold = False):
    print(Fore.GREEN + f"{time.time()}: Pressing {str.capitalize(key)}" + Fore.RESET)
    # if keyboard.is_pressed(key): 
    #    keyboard.release(key)
    keyboard.press(key)
    time.sleep(config["keypress_holdtime"])
    keyboard.release(key)
    threading.Thread(target=cooldown, args=(key,)).start()

def press_tile(key, hold = False):
    if lane_holding[key]:
        # Cette voie est actuellement maintenue par une note hold : on ignore l'appui normal
        return
    if lane_cooldowns[key] == 0.0:
        threading.Thread(target=press, args=(key, hold)).start()
    else:
        print(Fore.RED + f"Skipping lane {key} due to cooldown" + Fore.RESET)

# Nombre de détections consécutives nécessaires avant de vraiment appuyer sur la touche
# (filtre le bruit / les faux positifs isolés d'une frame)
hold_start_confirm_count = config.get("hold_start_confirm_count", 2)
lane_hold_pending_count = {
    str(config["key_1"]): 0,
    str(config["key_2"]): 0,
    str(config["key_3"]): 0,
    str(config["key_4"]): 0,
    str(config["key_5"]): 0
}

# démarrer un maintien de touche (pour les notes longues)
def start_hold(key):
    lane_hold_last_seen[key] = time.time()
    if lane_holding[key]:
        return
    lane_hold_pending_count[key] += 1
    if lane_hold_pending_count[key] >= hold_start_confirm_count:
        lane_holding[key] = True
        keyboard.press(key)
        print(Fore.GREEN + f"{time.time()}: Maintien de {key.capitalize()}" + Fore.RESET)

def stop_hold(key):
    lane_hold_pending_count[key] = 0
    if lane_holding[key]:
        lane_holding[key] = False
        keyboard.release(key)
        print(Fore.YELLOW + f"{time.time()}: Fin du maintien de {key.capitalize()}" + Fore.RESET)

# vérifie régulièrement (depuis le thread principal) si une voie
# maintenue n'a plus été vue depuis trop longtemps, et relâche la touche.
# C'est ce qui évite le relâchement prématuré causé par une seule frame ratée.
def hold_watchdog():
    now = time.time()
    for key in lane_holding:
        if lane_holding[key] and (now - lane_hold_last_seen[key]) > hold_release_grace:
            stop_hold(key)

tile = cv2.imread(f'assets/{monitor_height}/tile{config["tile_filename_suffix"]}.png', cv2.IMREAD_GRAYSCALE)
tile_width = tile.shape[1]
tile_height = tile.shape[0]
tile = tile.astype(np.uint8)
if config["use_white_tile"] == "true":
    white_tile = cv2.imread(f'assets/{monitor_height}/white{config["tile_filename_suffix"]}.png', cv2.IMREAD_GRAYSCALE)
    white_tile_width = white_tile.shape[1]
    white_tile_height = white_tile.shape[0]
    white_tile = white_tile.astype(np.uint8)
if config["use_battlestage_tile"] == "true":
    battlestage_tile = cv2.imread(f'assets/{monitor_height}/battlestage{config["tile_filename_suffix"]}.png', cv2.IMREAD_GRAYSCALE)
    battlestage_tile_width = battlestage_tile.shape[1]
    battlestage_tile_height = battlestage_tile.shape[0]
    battlestage_tile = battlestage_tile.astype(np.uint8)
if config["use_diamond_tile"] == "true":
    diamond_tile = cv2.imread(f'assets/{monitor_height}/diamond{config["tile_filename_suffix"]}.png', cv2.IMREAD_GRAYSCALE)
    diamond_tile_width = diamond_tile.shape[1]
    diamond_tile_height = diamond_tile.shape[0]
    diamond_tile = diamond_tile.astype(np.uint8)
# chargement de l'image de la barre de maintien (hold)
if config.get("use_hold_tile") == "true":
    hold_tile = cv2.imread(f'assets/{monitor_height}/hold{config["tile_filename_suffix"]}.png', cv2.IMREAD_GRAYSCALE)
    hold_tile_width = hold_tile.shape[1]
    hold_tile_height = hold_tile.shape[0]
    hold_tile = hold_tile.astype(np.uint8)

def press_tiles(rectangles, results):
    for (x, y, w, h) in rectangles:
        tile_position = (x + (w // 2), y + (h // 2))
        #print(f"Found tile at {tile_position} confidence: 
        tile_lane = config[f"key_{tile_position[0] // section_size + 1}"]
        if tile_position[1] >= min_tile_pixels_top_offset:
            press_tile(tile_lane)

        if config["debug_positions"]:
            print(f"Found tile in lane {str.capitalize(tile_lane)} with confidence {truncate(results[y][x], 2)}")

def tile_logic(screenshot_np):
    results = cv2.matchTemplate(screenshot_np, tile, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= config["min_confidence"])

    rectangles = []
    for positions in zip(*locations[::-1]):
        rectangles.append((int(positions[0]), int(positions[1]), int(tile_width), int(tile_height)))
        rectangles.append((int(positions[0]), int(positions[1]), int(tile_width), int(tile_height)))
    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)

    with detections_lock:
        latest_detections["tile"] = list(rectangles)

    threading.Thread(target=press_tiles, args=(rectangles, results)).start()

def white_tile_logic(screenshot_np):
    results = cv2.matchTemplate(screenshot_np, white_tile, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= config["white_tile_min_confidence"])

    rectangles = []
    for positions in zip(*locations[::-1]):
        rectangles.append((int(positions[0]), int(positions[1]), int(white_tile_width), int(white_tile_height)))
        rectangles.append((int(positions[0]), int(positions[1]), int(white_tile_width), int(white_tile_height)))
    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)

    with detections_lock:
        latest_detections["white"] = list(rectangles)

    threading.Thread(target=press_tiles, args=(rectangles, results)).start()

def battlestage_tile_logic(screenshot_np):
    results = cv2.matchTemplate(screenshot_np, battlestage_tile, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= config["battlestage_tile_min_confidence"])

    rectangles = []
    for positions in zip(*locations[::-1]):
        rectangles.append((int(positions[0]), int(positions[1]), int(battlestage_tile_width), int(battlestage_tile_height)))
        rectangles.append((int(positions[0]), int(positions[1]), int(battlestage_tile_width), int(battlestage_tile_height)))
    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)

    with detections_lock:
        latest_detections["battlestage"] = list(rectangles)

    threading.Thread(target=press_tiles, args=(rectangles, results)).start()

def diamond_tile_logic(screenshot_np):
    results = cv2.matchTemplate(screenshot_np, diamond_tile, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= config["diamond_tile_min_confidence"])

    rectangles = []
    for positions in zip(*locations[::-1]):
        rectangles.append((int(positions[0]), int(positions[1]), int(diamond_tile_width), int(diamond_tile_height)))
        rectangles.append((int(positions[0]), int(positions[1]), int(diamond_tile_width), int(diamond_tile_height)))
    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)

    with detections_lock:
        latest_detections["diamond"] = list(rectangles)

    threading.Thread(target=press_tiles, args=(rectangles, results)).start()

# logique de détection pour les notes à maintenir (hold)
# On ne cherche que dans une bande proche de la ligne de frappe (pas toute la
# hauteur agrandie), pour éviter les faux positifs sur le décor du haut de l'écran.
hold_search_margin_top = config.get("hold_search_margin_top", 220)  # en pixels, valeur pour 1080p
if scale_factor != 1:
    hold_search_margin_top = int(hold_search_margin_top // scale_factor)

def hold_tile_logic(screenshot_np):
    y_start = max(0, min_tile_pixels_top_offset - hold_search_margin_top)
    search_frame = screenshot_np[y_start:, :]

    results = cv2.matchTemplate(search_frame, hold_tile, cv2.TM_CCOEFF_NORMED)
    locations = np.where(results >= config["hold_tile_min_confidence"])

    rectangles = []
    for positions in zip(*locations[::-1]):
        rectangles.append((int(positions[0]), int(positions[1]) + y_start, int(hold_tile_width), int(hold_tile_height)))
        rectangles.append((int(positions[0]), int(positions[1]) + y_start, int(hold_tile_width), int(hold_tile_height)))
    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)

    with detections_lock:
        latest_detections["hold"] = list(rectangles)

    for (x, y, w, h) in rectangles:
        tile_position = (x + (w // 2), y + (h // 2))
        tile_lane = config[f"key_{tile_position[0] // section_size + 1}"]
        if tile_position[1] >= min_tile_pixels_top_offset:
            start_hold(tile_lane)

            if config["debug_positions"]:
                print(f"Found hold tile in lane {str.capitalize(tile_lane)} with confidence {truncate(results[y - y_start][x], 2)}")

    # le relâchement ne se fait plus ici (une seule frame manquée ne suffit
    # plus à couper le hold). C'est hold_watchdog(), appelé dans la boucle
    # principale, qui décide du relâchement en fonction du délai de grâce.

# fenêtre de debug visuel ("ce que voient les neurones")
DEBUG_COLORS = {
    "tile": (0, 255, 0),          # vert
    "white": (255, 255, 0),       # cyan
    "battlestage": (0, 165, 255), # orange
    "diamond": (255, 0, 255),     # magenta
    "hold": (203, 66, 245)        # rose/violet
}

def show_debug_window(screenshot_np):
    if screenshot_np is None:
        return
    debug_frame = cv2.cvtColor(screenshot_np, cv2.COLOR_GRAY2BGR)

    # Ligne indiquant le seuil de frappe (min_tile_pixels_top_offset)
    cv2.line(debug_frame, (0, min_tile_pixels_top_offset), (debug_frame.shape[1], min_tile_pixels_top_offset), (0, 0, 255), 1)

    with detections_lock:
        detections_snapshot = {k: list(v) for k, v in latest_detections.items()}

    for category, rectangles in detections_snapshot.items():
        color = DEBUG_COLORS.get(category, (255, 255, 255))
        for (x, y, w, h) in rectangles:
            cv2.rectangle(debug_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(debug_frame, category, (x, max(0, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # Petit indicateur en haut à gauche : quelles voies sont actuellement maintenues
    y_offset = 15
    for key, holding in lane_holding.items():
        status_color = (0, 255, 0) if holding else (100, 100, 100)
        cv2.putText(debug_frame, f"{key.upper()}: {'HOLD' if holding else '-'}", (5, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
        y_offset += 15

    # Agrandir la fenêtre pour que ce soit bien lisible (réglable via "debug_window_scale" dans config.json)
    debug_scale = config.get("debug_window_scale", 4)
    debug_frame = cv2.resize(debug_frame, None, fx=debug_scale, fy=debug_scale, interpolation=cv2.INTER_NEAREST)
    cv2.imshow("AlphaOne Debug View", debug_frame)
    cv2.waitKey(1)

show_debug = config.get("show_debug_visuals") == "true"

while not keyboard.is_pressed(config['exit_key']):
    screenshot_np = main_camera.get_latest_frame()
    capslock_status = win32api.GetKeyState(0x14)
    if capslock_status and screenshot_np is not None:
        threading.Thread(target=tile_logic, args=(screenshot_np,)).start()
        if config["use_white_tile"] == "true":
            threading.Thread(target=white_tile_logic, args=(screenshot_np,)).start()
        if config["use_battlestage_tile"] == "true":
            threading.Thread(target=battlestage_tile_logic, args=(screenshot_np,)).start()
        if config["use_diamond_tile"] == "true":
            threading.Thread(target=diamond_tile_logic, args=(screenshot_np,)).start()
        if config.get("use_hold_tile") == "true":
            threading.Thread(target=hold_tile_logic, args=(screenshot_np,)).start()

        # vérifie les relâchements de hold à chaque frame
        hold_watchdog()

    # fenêtre de debug (mise à jour à chaque frame, capslock ou non)
    if show_debug and screenshot_np is not None:
        show_debug_window(screenshot_np)

# sécurité - relâcher toute touche restée maintenue avant de quitter
for key in lane_holding:
    if lane_holding[key]:
        stop_hold(key)

if show_debug:
    cv2.destroyAllWindows()

main_camera.stop()
if config["console_window_ontop"] == "true":
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

print(Fore.WHITE + Back.RED + "Stop key pressed. Exiting AlphaOne..." + Fore.RESET + Back.RESET)
