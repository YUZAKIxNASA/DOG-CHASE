# DOG CHASE

An original 2D arcade maze-chase game built with **Python 3** and **Pygame**.  
Guide a nimble dog through moonlit garden hedge mazes, collect every **Bone** and **Golden Coin**, grab **Power Treats** to turn the tables, and outsmart four unique human chasers powered by A* pathfinding.

---

## Gameplay Features

### Playable Dog
- Smooth 4-directional grid movement with responsive corner buffering and instant 180° reversals.
- Directional animations (tail wagging, walking paws, bounce, power-up shield aura) and horizontal wraparound tunnels.
- Full support for replacing the default vector-rendered dog with custom external images.

### Four Human Enemies & A* Pathfinding
Each human character has a distinct outfit, headgear, and AI personality driven by **A\*** grid pathfinding (`enemy.py`), alternating between **Scatter**, **Chase**, **Frightened**, and **Respawning** states:
- **Officer Miller** *(Blue Uniform & Cap)* — **Direct Chaser**: Tracks the Dog's exact tile.
- **Chef Rosa** *(Crimson Apron & Toque)* — **Corridor Ambusher**: Targets 4 tiles ahead of the Dog's facing direction.
- **Jogger Leo** *(Emerald Tracksuit & Headband)* — **Vector Flanker**: Projects cut-off angles relative to Officer Miller and the Dog.
- **Inspector Vance** *(Amber Trenchcoat & Fedora)* — **Tactical Patroller**: Chases at long range and peels away to patrol corners when close.

### Collectibles & Power-Ups
- **Bones (`+10 pts`)**: Primary collectible scattered across pathways; collect all bones in a maze to clear the level.
- **Golden Coins (`+50 pts`)**: Bonus high-value treasures placed in deeper corridors.
- **Power Treats (`+100 pts`)**: Grants temporary protective shield, speed boost, and frightens all humans so you can tag them for `+200` / `+400` / `+800` / `+1600` combo points.

### 5 Progressive Mazes
1. **Garden Courtyard** (`19×15`) — Compact courtyard using Fixed Camera in `Auto` mode.
2. **Hedge Labyrinth** (`23×17`) — Twisting garden lanes using Smooth Follow Camera.
3. **Lantern Plaza** (`27×19`) — Cross-plaza corridors with horizontal wrap tunnels.
4. **Moonlit Estates** (`31×21`) — Large estate maze showcasing Dead Zone & Look-Ahead tracking.
5. **Grand Manor** (`35×23`) — Full estate challenge; subsequent levels loop with faster human speeds and shorter power-up windows.

Every maze automatically verifies 100% collectible reachability via flood-fill from the Dog's spawn tile.

### 2D Top-Down Camera System
- **Auto Mode**: Fixed full-map view on compact mazes, Smooth Follow on larger maps.
- **Fixed Mode** & **Smooth Follow Mode** selectable anytime in Settings.
- **Camera Bounds** clamping, **Smooth Lerp Movement**, **Adjustable Zoom** (`0.85x`–`1.45x`), **Trauma Camera Shake**, **Dead Zone**, **Look-Ahead**, **Camera Reset** on spawn, and instant **Full Maze View** (`V` or HUD button).

### Audio, UI & Local Storage
- **Synthesized Audio (`audio.py`)**: Original `.wav` sound effects (`bone`, `coin`, `powerup`, `scare`, `hit`, `level_complete`, `game_over`) and looping background music (`bgm.wav`) with independent SFX/Music volume controls and mute toggle.
- **Arcade Menus & HUD**: Main Menu, How to Play, Settings, Pause Menu, Victory Screen, Game Over Screen, and live Gameplay HUD (Score, Best, Bones, Lives, Shield Timer, Camera Mode, Mute, Pause).
- **Local Persistence**: Automatically saves high scores, best level, and lifetime totals in `data/highscore.json` and user preferences in `data/settings.json`.

---

## Project Structure

```text
DOG-CHASE/
├── main.py                # Application entry point and main Pygame loop
├── game.py                # Game state machine, progression, collisions, and update/render orchestration
├── settings.py            # Constants, color palette, JSON persistence, and external sprite loader
├── maze.py                # Multi-level maze layouts, flood-fill verification, and tile rendering
├── player.py              # DogPlayer movement, corner buffering, and animations
├── enemy.py               # A* pathfinding and 4 HumanEnemy AI personalities
├── collectibles.py        # Bones, Golden Coins, Power-Ups, and pickup detection
├── camera.py              # 2D top-down camera (fixed, follow, bounds, zoom, shake, dead zone, look-ahead)
├── audio.py               # Procedural WAV generator and Pygame mixer audio manager
├── ui.py                  # Gameplay HUD, particle bursts, floating score popups, and UI buttons
├── menu.py                # Main Menu, How to Play, Settings, Pause, Victory, and Game Over screens
├── assets/
│   ├── characters/        # Optional custom Dog sprites
│   ├── enemies/           # Optional custom Human enemy sprites
│   ├── collectibles/      # Optional custom Bone, Coin, and Power-Up sprites
│   ├── backgrounds/       # Optional custom background image
│   ├── sounds/            # Generated/replaceable WAV sound effects
│   └── music/             # Generated/replaceable WAV background music
├── data/
│   ├── highscore.json     # Persisted high score and lifetime stats
│   └── settings.json      # Persisted display, audio, camera, and control settings
├── tests/
│   └── test_dog_chase.py  # Unit & integration tests (supports headless environments)
├── requirements.txt       # Python dependencies
├── LICENSE                # Project license
└── README.md              # Documentation
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **pip**

### Installation & Run

```bash
pip install -r requirements.txt
python main.py
```

---

## Controls

| Action | Default Keys | Notes |
|---|---|---|
| Move Up / Down / Left / Right | `Arrow Keys` or `WASD` | Remappable in **Settings** |
| Pause / Resume | `ESC` or `P` | Also clickable on HUD |
| Toggle Full Maze View | `V` | Also clickable via `Cam` button on HUD |
| Mute / Unmute Audio | `M` | Also clickable via `Audio` button on HUD |

---

## Settings Overview

Accessible from both the **Main Menu** and the **Pause Menu**:
- **Resolution Presets**: `960x640`, `1120x720`, `1280x800`, `1440x900`
- **Fullscreen**: Toggle windowed resizable vs. fullscreen mode
- **FPS Cap**: `30`, `60`, or `120` FPS
- **Graphics Quality**: `High` (particles, glows, bevels, blossoms) or `Classic`
- **Audio**: Sound Effects Volume, Music Volume, and Mute toggle
- **Camera**: Mode (`Auto` / `Fixed` / `Follow`), Zoom, Shake, Dead Zone, and Look-Ahead
- **Keyboard Controls**: Click any action button in Settings and press a new key to rebind

---

## Replacing Assets

All graphics and audio work out of the box with built-in procedural rendering and synthesized `.wav` files. To customize any asset, place your own `.png` or `.wav` files in the corresponding folder:

- **Dog Sprite**: `assets/characters/dog.png` (or directional `dog_up.png`, `dog_down.png`, `dog_left.png`, `dog_right.png`)
- **Human Enemies**: `assets/enemies/miller.png`, `rosa.png`, `leo.png`, `vance.png`
- **Collectibles**: `assets/collectibles/bone.png`, `coin.png`, `powerup.png`
- **Background**: `assets/backgrounds/background.png`
- **Sound Effects**: `assets/sounds/bone.wav`, `coin.wav`, `powerup.wav`, `scare.wav`, `hit.wav`, `level_complete.wav`, `game_over.wav`
- **Background Music**: `assets/music/bgm.wav`

---

## Running Tests

Run the automated test suite to verify maze reachability, player movement and wall collision, A* pathfinding, enemy AI states, collectibles, camera modes, audio asset generation, and the game state machine:

```bash
python -m unittest discover -s tests -v
```

---

## License

See [LICENSE](LICENSE) for license details.

