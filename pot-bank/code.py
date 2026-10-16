# description: bank of potentiometers

import time
import board
import analogio
import digitalio
import usb_midi

import adafruit_midi
from adafruit_midi.control_change import ControlChange

# constants
MIDI_CHANNEL = 0       # MIDI channel 1
THRESH = 400   # Ignore changes smaller than this
SAMPLES = 32

# USB MIDI
midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=MIDI_CHANNEL
)


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

    return sum(adc.value for _ in range(SAMPLES)) // SAMPLES

# MIDI CC assigned to each pot
ccs = (1, 2, 3, 4, 5, 6, 7, 8)

# track last value for each pot
last_vals = [-1, -1, -1, -1, -1, -1, -1, -1]
anchors = [0] * 8

# Main loop
while True:
    for ch in range(8):
        raw = read_mux(ch)
        if last_vals[ch] == -1 or abs(raw - anchors[ch]) > THRESH:
            value = raw >> 9
            if value != last_vals[ch]:
                midi.send(ControlChange(ccs[ch], value))
                last_vals[ch] = value
            anchors[ch] = raw
    time.sleep(0.005)
