import tkinter as tk
import math
import numpy as np
import sounddevice as sd
from config import NOTE_KEY_MAP, SILENCE_THRESHOLD, BUFFER_SIZE

SAMPLE_RATE = 44100
NOTE_NAMES  = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

BG     = "#0f0f1a"
CARD   = "#1a1a2e"
ACCENT = "#00d4ff"
GREEN  = "#00ff88"
DIM    = "#2a2a45"
WHITE  = "#e0e0ff"
GRAY   = "#7777aa"

state = {"note": None, "freq": 0.0, "conf": 0.0, "rms": 0.0}


def yin_pitch(signal, threshold=0.15):
    N = len(signal)
    tau_min = max(1, int(SAMPLE_RATE / 2500))
    tau_max = min(int(SAMPLE_RATE / 200), N // 2)
    fft_n = 1
    while fft_n < 2 * N:
        fft_n *= 2
    X    = np.fft.rfft(signal, n=fft_n)
    r    = np.fft.irfft(X * np.conj(X))[:tau_max]
    diff = 2.0 * (r[0] - r); diff[0] = 0.0
    cumsum = np.cumsum(diff)
    cmnd   = np.ones(tau_max)
    taus   = np.arange(1, tau_max)
    cmnd[1:] = np.where(cumsum[1:] > 0, diff[1:] * taus / cumsum[1:], 1.0)
    hits = np.where(cmnd[tau_min:tau_max] < threshold)[0]
    if len(hits) == 0:
        return 0.0, 0.0
    tau = tau_min + hits[0]
    while tau + 1 < tau_max - 1 and cmnd[tau + 1] < cmnd[tau]:
        tau += 1
    return float(SAMPLE_RATE / tau), float(1.0 - cmnd[tau])


def hz_to_note(freq):
    if freq <= 0:
        return None
    midi = round(12 * math.log2(freq / 440.0) + 69)
    return f"{NOTE_NAMES[midi % 12]}{(midi // 12) - 1}"


def fmt_action(action):
    dirs = {(0,1):"↑",(0,-1):"↓",(-1,0):"←",(1,0):"→"}
    t = action["type"]
    if t == "lstick":
        return "Move " + dirs.get((int(action["x"]), int(action["y"])), "")
    if t == "rstick":
        return "Look " + dirs.get((int(action["x"]), int(action["y"])), "")
    if t == "trigger":
        return f"{'RT' if action['side']=='right' else 'LT'} Fire"
    return f"[{action['btn']}]"


def audio_callback(indata, frames, time, status):
    samples = indata[:, 0].astype(np.float32)
    rms     = float(np.sqrt(np.mean(samples ** 2)))
    freq, conf = yin_pitch(samples)
    note = hz_to_note(freq) if (conf >= SILENCE_THRESHOLD and rms >= 0.01) else None
    state.update(note=note, freq=freq, conf=conf, rms=min(rms * 8, 1.0))


# ── build UI ──────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("Flute Controller — Test")
root.configure(bg=BG)
root.resizable(False, False)

note_var   = tk.StringVar(value="—")
freq_var   = tk.StringVar(value="play a note...")
action_var = tk.StringVar(value="")

# header
hdr = tk.Frame(root, bg=BG, padx=30, pady=18)
hdr.pack(fill="x")
tk.Label(hdr, text="FLUTE CONTROLLER", bg=BG, fg=GRAY,
         font=("Consolas", 11, "bold")).pack()
tk.Label(hdr, textvariable=note_var, bg=BG, fg=ACCENT,
         font=("Consolas", 80, "bold")).pack()
tk.Label(hdr, textvariable=freq_var, bg=BG, fg=GRAY,
         font=("Consolas", 12)).pack()
tk.Label(hdr, textvariable=action_var, bg=BG, fg=GREEN,
         font=("Consolas", 16, "bold")).pack(pady=(4, 0))

# meters
meters = tk.Frame(root, bg=CARD, padx=24, pady=12)
meters.pack(fill="x", padx=20, pady=(0, 8))

BAR_W = 280

def make_bar(parent, label, color=ACCENT):
    row = tk.Frame(parent, bg=CARD)
    row.pack(fill="x", pady=3)
    tk.Label(row, text=label, bg=CARD, fg=GRAY,
             font=("Consolas", 10), width=8, anchor="w").pack(side="left")
    bg = tk.Canvas(row, bg=DIM, width=BAR_W, height=14,
                   bd=0, highlightthickness=0)
    bg.pack(side="left", padx=(6, 0))
    fill = bg.create_rectangle(0, 0, 0, 14, fill=color, width=0)
    return bg, fill

vol_canvas,  vol_fill  = make_bar(meters, "Volume", ACCENT)
conf_canvas, conf_fill = make_bar(meters, "Conf",   GREEN)

# note map tiles
tilemap = tk.Frame(root, bg=CARD, padx=20, pady=12)
tilemap.pack(fill="x", padx=20, pady=(0, 22))
tk.Label(tilemap, text="NOTE MAP", bg=CARD, fg=GRAY,
         font=("Consolas", 10, "bold")).pack(anchor="w", pady=(0, 6))

grid = tk.Frame(tilemap, bg=CARD)
grid.pack(anchor="w")

COLS = 3
tiles = {}
for i, (note, action) in enumerate(NOTE_KEY_MAP.items()):
    cell = tk.Frame(grid, bg=DIM, padx=12, pady=8)
    cell.grid(row=i // COLS, column=i % COLS, padx=5, pady=5, sticky="ew")
    ln = tk.Label(cell, text=note,            bg=DIM, fg=WHITE, font=("Consolas", 14, "bold"))
    la = tk.Label(cell, text=fmt_action(action), bg=DIM, fg=GRAY,  font=("Consolas", 9))
    ln.pack(); la.pack()
    tiles[note] = (cell, ln, la)

prev_note = [None]

def update_ui():
    s    = dict(state)
    note = s["note"]

    note_var.set(note or "—")
    freq_var.set(f"{s['freq']:.1f} Hz  ·  conf {s['conf']:.2f}" if s["freq"] > 0 else "play a note...")
    act = NOTE_KEY_MAP.get(note)
    action_var.set(fmt_action(act) if act else ("(not mapped)" if note else ""))

    vol_canvas.coords(vol_fill,  0, 0, int(s["rms"]  * BAR_W), 14)
    conf_canvas.coords(conf_fill, 0, 0, int(s["conf"] * BAR_W), 14)

    if note != prev_note[0]:
        if prev_note[0] in tiles:
            c, ln, la = tiles[prev_note[0]]
            c.config(bg=DIM); ln.config(bg=DIM, fg=WHITE); la.config(bg=DIM, fg=GRAY)
        if note in tiles:
            c, ln, la = tiles[note]
            c.config(bg=ACCENT); ln.config(bg=ACCENT, fg=BG); la.config(bg=ACCENT, fg=BG)
        prev_note[0] = note

    root.after(50, update_ui)


stream = sd.InputStream(
    samplerate=SAMPLE_RATE, channels=1, dtype="float32",
    blocksize=BUFFER_SIZE, callback=audio_callback,
)
stream.start()
update_ui()

try:
    root.mainloop()
finally:
    stream.stop()
    stream.close()
