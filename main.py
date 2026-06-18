import math
import numpy as np
import sounddevice as sd
import vgamepad as vg
from config import NOTE_KEY_MAP, SILENCE_THRESHOLD, BUFFER_SIZE, HOLD_CHUNKS

SAMPLE_RATE = 44100
NOTE_NAMES  = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

BUTTON_MAP = {
    "A":        vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B":        vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X":        vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y":        vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB":       vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB":       vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "INTERACT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,  # remap in-game if needed
    "START":    vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK":     vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
}

gamepad       = vg.VX360Gamepad()
current_note  = None
silent_chunks = 0   # counts consecutive silent chunks before releasing


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


def apply_action(action):
    t = action["type"]
    if t == "lstick":
        gamepad.left_joystick_float(x_value_float=action["x"], y_value_float=action["y"])
    elif t == "rstick":
        gamepad.right_joystick_float(x_value_float=action["x"], y_value_float=action["y"])
    elif t == "trigger":
        if action["side"] == "right":
            gamepad.right_trigger_float(value_float=1.0)
        else:
            gamepad.left_trigger_float(value_float=1.0)
    elif t == "button":
        gamepad.press_button(button=BUTTON_MAP[action["btn"]])
    gamepad.update()


def release_action(action):
    t = action["type"]
    if t == "lstick":
        gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
    elif t == "rstick":
        gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
    elif t == "trigger":
        if action["side"] == "right":
            gamepad.right_trigger_float(value_float=0.0)
        else:
            gamepad.left_trigger_float(value_float=0.0)
    elif t == "button":
        gamepad.release_button(button=BUTTON_MAP[action["btn"]])
    gamepad.update()


def audio_callback(indata, frames, time, status):
    global current_note, silent_chunks
    samples = indata[:, 0].astype(np.float32)
    rms     = float(np.sqrt(np.mean(samples ** 2)))
    freq, conf = yin_pitch(samples)
    note = hz_to_note(freq) if (conf >= SILENCE_THRESHOLD and rms >= 0.01) else None

    if note is not None:
        silent_chunks = 0
        if note == current_note:
            return
        # switched to a different note — release old immediately
        if current_note is not None:
            act = NOTE_KEY_MAP.get(current_note)
            if act:
                release_action(act)
                print(f"  release  {current_note}")
        act = NOTE_KEY_MAP.get(note)
        if act:
            apply_action(act)
            print(f"  {note} ({freq:.1f} Hz, conf {conf:.2f}) -> {act['type']} {act.get('btn') or act.get('side','')}")
        else:
            print(f"  {note} ({freq:.1f} Hz) -> not mapped")
        current_note = note
    else:
        # silence — only release after HOLD_CHUNKS consecutive silent chunks
        if current_note is not None:
            silent_chunks += 1
            if silent_chunks >= HOLD_CHUNKS:
                act = NOTE_KEY_MAP.get(current_note)
                if act:
                    release_action(act)
                    print(f"  release  {current_note}")
                current_note  = None
                silent_chunks = 0


print("Flute Controller ready — Xbox 360 virtual gamepad active.")
print("Notes:", ", ".join(NOTE_KEY_MAP.keys()))
print("Ctrl+C to quit.\n")

with sd.InputStream(
    samplerate=SAMPLE_RATE, channels=1, dtype="float32",
    blocksize=BUFFER_SIZE, callback=audio_callback,
):
    try:
        while True:
            sd.sleep(100)
    except KeyboardInterrupt:
        if current_note:
            act = NOTE_KEY_MAP.get(current_note)
            if act:
                release_action(act)
        print("\nStopped — all inputs released.")
