# description: USB midi controller configuration for
# overtones-minimal.pd Pure Data patch

import time
import board
import analogio
import digitalio
import usb_midi

import adafruit_midi
from adafruit_midi.control_change import ControlChange

# constants ###########################################
MIDI_CHANNEL = 0    # MIDI channel 1
SAMPLES = 32        # collect and average sample values

# 16-bit ADC produces values ranging 0 to 65,535
# scale to midi range 0 - 127
# threshold value of 512 = 1 midi step
THRESH = 400        # Ignore changes smaller than this
#######################################################

# USB MIDI
midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=MIDI_CHANNEL
)

# buttons #############################################
# button qty: 2

buttons = [digitalio.DigitalInOut(b) for b in (
    board.GP0,
    board.GP1
    )]

for i, b in enumerate(buttons):
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP

# MIDI notes: one per button
notes = 0, 1
velocity = 100

# Track each button's previous state
last_pressed = [False] * len(buttons)
#######################################################

# pots ################################################
# pot qty: 5

# selection switch pins
s0 = digitalio.DigitalInOut(board.GP4)
s1 = digitalio.DigitalInOut(board.GP5)
s2 = digitalio.DigitalInOut(board.GP6)
for s in (s0, s1, s2):
    s.direction = digitalio.Direction.OUTPUT

# analog input tied to multiplexer output
adc = analogio.AnalogIn(board.GP26)

def read_mux(channel):
    # Separate channel integer into binary values at bit positions,
    # use to select mux channel via selection pins
    s0.value = (channel & 0x01) > 0
    s1.value = (channel & 0x02) > 0
    s2.value = (channel & 0x04) > 0

    # slight delay between selecting channel and reading input
    time.sleep(0.001)
    adc.value

    # average of sample values for increased accuracy
    return sum(adc.value for _ in range(SAMPLES)) // SAMPLES

# MIDI CC assigned to each pot
ccs = (1, 2, 3, 4, 5)

# track last value for each pot
last_vals = [-1, -1, -1, -1, -1]
anchors = [0] * 5
#######################################################

# Main loop
while True:
    for i, button in enumerate(buttons):
        pressed = not button.value

        if pressed and not last_pressed[i]:
            midi.send(NoteOn(notes[i], velocity))

        elif not pressed and last_pressed[i]:
            midi.send(NoteOff(notes[i], 0))

        last_pressed[i] = pressed

    for ch in range(5):
        raw = read_mux(ch)
        if last_vals[ch] == -1 or abs(raw - anchors[ch]) > THRESH:
            value = raw >> 9
            if value != last_vals[ch]:
                midi.send(ControlChange(ccs[ch], value))
                last_vals[ch] = value
            anchors[ch] = raw
    time.sleep(0.005)