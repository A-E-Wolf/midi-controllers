# description: includes buttons and potentiometers

import time
import board
import analogio
import digitalio
import usb_midi

import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# constants
MIDI_CHANNEL = 0       # MIDI channel 1
UPDATE_THRESHOLD = 2   # Ignore changes smaller than this

# USB MIDI
midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=MIDI_CHANNEL
)

###### buttons ######
buttons = [digitalio.DigitalInOut(b) for b in (
    board.GP0,
    board.GP1,
    board.GP2,
    board.GP3,
    board.GP4,
    board.GP5,
    board.GP6,
    )]

for i, b in enumerate(buttons):
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP



# MIDI notes: one per button
notes = 10, 11, 12, 13, 0, 1, 2
velocity = 100

# Track each button's previous state
last_pressed = [False] * len(buttons)
#####################

###### pots ######
pots = [analogio.AnalogIn(p) for p in (
    board.GP26,
    board.GP27,
    board.GP28
    )]

# MIDI CC assigned to each pot
ccs = (1, 2, 3)

# track last value for each pot
last_vals = [-1, -1, -1]
#####################

# Convert ADC → MIDI
def read_midi_value(pot):
    # Pico ADC is 0–65535
    value = pot.value

    # Convert to MIDI's 0–127 range
    midi_value = value * 127 // 65535

    return midi_value

# Main loop
while True:
    for i, button in enumerate(buttons):
        pressed = not button.value

        if pressed and not last_pressed[i]:
            midi.send(NoteOn(notes[i], velocity))

        elif not pressed and last_pressed[i]:
            midi.send(NoteOff(notes[i], 0))

        last_pressed[i] = pressed


    for i, pot in enumerate(pots):
        value = sum(read_midi_value(pot) for _ in range(64)) // 64

        # Only transmit when the knob has actually moved
        if abs(value - last_vals[i]) >= UPDATE_THRESHOLD:
            midi.send(ControlChange(ccs[i], value))
            last_vals[i] = value

    time.sleep(0.005)
