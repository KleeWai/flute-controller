# flute-controller

Play Overwatch (or any gamepad-supported game) with a flute.

Listens to your microphone, detects the pitch you're playing in real time, and maps each note to a virtual Xbox 360 controller input — movement, camera, abilities, and fire. Built for a Hindustani 6-hole C bansuri (range G4–G6).

https://github.com/user-attachments/assets/flute-controller-demo

---

## How it works

1. `sounddevice` captures mic input in chunks
2. A pure-NumPy YIN algorithm detects the fundamental pitch
3. The note is looked up in `config.py`'s `NOTE_KEY_MAP`
4. `vgamepad` sends the input to a virtual Xbox 360 controller (via ViGEmBus)

No keyboard simulation — the virtual gamepad is seen as real hardware, so it's safe with anti-cheat systems like Easy Anti-Cheat and Blizzard's Defense Matrix.

---

## Requirements

- Windows 10/11
- Python 3.9+
- [ViGEmBus driver](https://github.com/nefarius/ViGEmBus/releases) (virtual gamepad driver — one-time install)

---

## Setup

```bash
pip install -r requirements.txt
```

**requirements.txt**
```
sounddevice
vgamepad
numpy
```

---

## Usage

**Game mode** — connects the virtual controller, no window:
```bash
python main.py
```

**Test mode** — visual UI showing detected note, confidence, and active tile:
```bash
python ui.py
```

Tab into your game after starting `main.py`. Windows sees the virtual controller as a plugged-in Xbox 360 pad.

---

## Default note map (Overwatch 2)

| Note | Hz   | Action           |
|------|------|------------------|
| G4   | 392  | Forward          |
| A4   | 440  | Back             |
| B4   | 494  | Strafe Left      |
| C5   | 523  | Look Left        |
| D5   | 587  | Strafe Right     |
| E5   | 659  | Look Right       |
| F5   | 698  | Primary Fire     |
| G5   | 784  | Secondary Fire   |
| A5   | 880  | Ability 1 (LB)   |
| B5   | 988  | Ability 2 (RB)   |
| C6   | 1047 | Jump             |
| D6   | 1175 | Ability 3        |
| E6   | 1319 | Interact         |
| G6   | 1568 | Toggle Crouch    |

---

## Configuration

Edit `config.py` to remap notes or tune detection:

```python
NOTE_KEY_MAP = {
    "G4": {"type": "lstick", "x": 0.0, "y": 1.0},   # Forward
    "E5": {"type": "rstick", "x": -1.0, "y": 0.0},  # Look Right
    "F5": {"type": "trigger", "side": "right"},       # Primary Fire
    "C6": {"type": "button", "btn": "A"},             # Jump
    ...
}

SILENCE_THRESHOLD = 0.85  # raise if ghost notes fire; lower if real notes get dropped
BUFFER_SIZE       = 2048  # lower for less latency, raise for better low-note accuracy
HOLD_CHUNKS       = 4     # silent chunks before releasing a held note (~185ms)
```

**Action types:**
- `lstick` — left thumbstick (movement), `x`/`y` from -1.0 to 1.0
- `rstick` — right thumbstick (camera), `x`/`y` from -1.0 to 1.0
- `trigger` — analog trigger, `side`: `"right"` (RT) or `"left"` (LT)
- `button` — digital button, `btn`: `A`, `B`, `X`, `Y`, `LB`, `RB`, `START`, `BACK`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Ghost notes between held notes | Raise `SILENCE_THRESHOLD` to `0.90` |
| Real notes not registering | Lower `SILENCE_THRESHOLD` to `0.80` |
| Note flickers on/off mid-breath | Raise `HOLD_CHUNKS` to `6` |
| Low notes (G4) unreliable | Get closer to the mic |
| Wrong note detected | You may be landing on a microtone — adjust embouchure |
