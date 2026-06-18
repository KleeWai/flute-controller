# Range: G4–G6 (Hindustani 6-hole C bansuri)
# lstick = left thumbstick (movement)
# rstick = right thumbstick (camera/look)
# trigger = RT/LT analog fire
# button  = face/shoulder buttons
NOTE_KEY_MAP = {
    # Movement — left stick
    "G4": {"type": "lstick",  "x":  0.0, "y":  1.0},  # Forward
    "A4": {"type": "lstick",  "x":  0.0, "y": -1.0},  # Back
    "B4": {"type": "lstick",  "x": -1.0, "y":  0.0},  # Strafe Left
    "D5": {"type": "lstick",  "x":  1.0, "y":  0.0},  # Strafe Right
    # Look — right stick (axis confirmed from in-game test: E5=right, so x=-1 = right)
    "C5": {"type": "rstick",  "x":  1.0, "y":  0.0},  # Look Left
    "E5": {"type": "rstick",  "x": -1.0, "y":  0.0},  # Look Right (confirmed)
    # Fire — triggers
    "F5": {"type": "trigger", "side": "right"},         # Primary Fire (RT)
    "G5": {"type": "trigger", "side": "left"},          # Secondary Fire (LT)
    # Abilities & actions — buttons
    "A5": {"type": "button",  "btn": "LB"},             # Ability 1 (LShift)
    "B5": {"type": "button",  "btn": "RB"},             # Ability 2 (E)
    "C6": {"type": "button",  "btn": "A"},              # Jump (Space)
    "D6": {"type": "button",  "btn": "Y"},              # Ability 3 (Q)
    "E6": {"type": "button",  "btn": "INTERACT"},       # Interact (F)
    "G6": {"type": "button",  "btn": "B"},              # Toggle Crouch
}

SILENCE_THRESHOLD = 0.85
BUFFER_SIZE       = 2048
HOLD_CHUNKS       = 4    # silent chunks before releasing a held note (~185ms)
