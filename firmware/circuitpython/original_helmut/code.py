import board
import neopixel
import time
import displayio
import digitalio
import usb_midi
import busio
import rotaryio
import asyncio
from analogio import AnalogIn
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
from adafruit_st7789 import ST7789
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.system_exclusive import SystemExclusive
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.pitch_bend import PitchBend

''' Firmware for MIDi Captain STD, Blue or Gold

    by Helmut Keller Audio

    The MIDI Control Change (CC) numbers 11 to 24 are implemented in both
    directions (transmit and receive). The DAW should transmit CC comands whenever the
    state of an mapped DAW control has changed.

    The following mapping is fixed for the MIDI Captain controls:

    CC 11         rotary encoder
    CC 12 and 13  expresion pedal inputs "EXP1" and "EXP2"
    CC 14         push button of the rotary encoder
    CC 15 to 18   footswitches "1" to "4"
    CC 19         footswitch "Up"
    CC 20 to 23   footswitches "A" to "D"
    CC 24         footswitch "Up"

    CC 25  when revecved it sets the tuner mode of the MIDI Captain

    In tuner mode the center part of the dispaly shows note command values
    as note names and pitchwheel command values (8192 equals 200 cent pitch deviation)
    as a pointer.

    In normal mode the center part of the display shows a
    name (e.g. Song name) which is set by a sytem exclusive command

    For each CC number expept 19 und 24 there are small display elements
    showing a descriptive name and the value as a bar.
    The default colors and the names of the display elements are set by
    the configurtatin file "HKAudioSetup.txt". The colors and names can be set
    by system exclusive commands too.

    The LEDs of the footswitches reflect the value the CC values too
    They use the same color as the small display elements.

    The battery voltage of the MIDI Captain is displayed on a small display
    element too. '''

''' Firmware version: '''

VersionStr = "V 1.0.0"
HelloStr = "HK Audio\n" + VersionStr

''' Note Names '''

NoteNames = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]

''' Colors: '''

black = (0, 0, 0)

dark_red = (128, 0, 0)
dark_green = (0, 128, 0)
dark_blue = (0, 0, 128)

dark_yellow = (128, 128, 0)
dark_cyan = (0, 128, 128)
dark_magenta = (128, 0, 128)

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

grey = (128, 128, 128)

orange = (255, 128, 0)
lime = (128, 255, 0)
spring = (0, 255, 128)
azure = (0, 128, 255)
violet = (128, 0, 255)
purple = (255, 0, 128)

yellow = (255, 255, 0)
cyan = (0, 255, 255)
magenta = (255, 0, 255)

pastel_red = (255, 128, 128)
pastel_green = (128, 255, 128)
pastel_blue = (128, 128, 255)

pastel_yellow = (255, 255, 128)
pastel_cyan = (128, 255, 255)
pastel_magenta = (255, 128, 255)

white = (255, 255, 255)

''' Color palette: '''

palette = displayio.Palette(27)

palette[0] = black
palette[1] = dark_red
palette[2] = dark_yellow
palette[3] = dark_green
palette[4] = dark_cyan
palette[5] = dark_blue
palette[6] = dark_magenta
palette[7] = grey
palette[8] = red
palette[9] = orange
palette[10] = yellow
palette[11] = lime
palette[12] = green
palette[13] = spring
palette[14] = cyan
palette[15] = azure
palette[16] = blue
palette[17] = violet
palette[18] = magenta
palette[19] = purple
palette[20] = pastel_red
palette[21] = pastel_yellow
palette[22] = pastel_green
palette[23] = pastel_cyan
palette[24] = pastel_blue
palette[25] = pastel_magenta
palette[26] = white

''' Dark color palette for display elements: '''

dark_palette = displayio.Palette(27)
dark_f = 3

for i in range(27):
    dc = palette[i]
    dcr = dc // 65536
    dc = dc % 65536
    dcg = dc // 256
    dcb = dc % 256
    dc = dcr // dark_f * 65536 + dcg // dark_f * 256 + dcb // dark_f
    dark_palette[i] = dc

''' Dimmed color palette for LEDs: '''

dim_palette = displayio.Palette(27)
dim_f = 12

for i in range(27):

    dc = palette[i]
    dcr = dc // 65536
    dc = dc % 65536
    dcg = dc // 256
    dcb = dc % 256
    dc = dcr // dim_f * 65536 + dcg // dim_f * 256 + dcb // dim_f
    dim_palette[i] = dc

''' Array of color palette indices of the 14 CCs and the main text display: '''

color_index = [4, 2, 2, 4, 16, 16, 10, 12, 26, 8, 8, 8, 8, 26, 0]

''' Array of dispaly element indices of the 14 CCs the main text display: '''

display_index = [13, 0, 1, 12, 2, 3, 4, 5, -1, 7, 8, 9, 10, -1, 6]

''' Array of the neopixel pins of the 10 Leds, 3 neopixel pins  per LED: '''

pixelpin = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [9, 10, 11],
        [12, 13, 14],
        [15, 16, 17],
        [18, 19, 20],
        [21, 22, 23],
        [24, 25, 26],
        [27, 28, 29],
    ]

''' Function to set a LED to full brightness: '''

def LED_on(x):

    for i in pixelpin[x]:
        LED[i] = palette[color_index[x+4]]

    return


'''Function set a LED  to dimed brightness: '''

def LED_dim(x):

    for i in pixelpin[x]:
        LED[i] = dim_palette[color_index[x+4]]

    return

''' Initialize the neopixel LEDs: '''

neo_pin = board.GP7
LED_count = 30
LED_brightness = 0.3

LED = neopixel.NeoPixel(neo_pin, LED_count, brightness=LED_brightness, auto_write=True)

''' Switch class: '''

class Switch:
    def __init__(self, pin):
        self.switch = digitalio.DigitalInOut(pin)          # hardware assingment
        self.switch.direction = digitalio.Direction.INPUT
        self.switch.pull = digitalio.Pull.UP

    state = False

''' Array of the 11 switch objects: '''

switch = []

switch.append(Switch(board.GP0))    # Switch Encoder    CC 14
switch.append(Switch(board.GP1))    # Switch A          CC 15
switch.append(Switch(board.GP25))   # Switch B          CC 16
switch.append(Switch(board.GP24))   # Switch C          CC 17
switch.append(Switch(board.GP23))   # Switch D          CC 18
switch.append(Switch(board.GP20))   # Switch Up         CC 19
switch.append(Switch(board.GP9))    # Switch 1          CC 20
switch.append(Switch(board.GP10))   # Switch 2          CC 21
switch.append(Switch(board.GP11))   # Switch 3          CC 22
switch.append(Switch(board.GP18))   # Switch 3          CC 23
switch.append(Switch(board.GP19))   # Switch Down       CC 24

''' Initialize the rotary encoder: '''

encoder = rotaryio.IncrementalEncoder(board.GP2, board.GP3, 2)
last_position = 0
encoder_value = 38

''' Initialize the Analog Inputs: '''

exp1 = AnalogIn(board.A1)
exp2 = AnalogIn(board.A2)
bat = AnalogIn(board.A3)

exp1_min = 2048
exp1_max = 63488
exp2_min = 2048
exp2_max = 63488
exp1_old = 0
exp2_old = 0

vbat_state = 0
vbat_a = 0.01
vbat_b = 1-vbat_a
vbat_old = 0

''' Release any resources currently in use for displays: '''

displayio.release_displays()

''' Hardware assignment for the display: '''

tft_pwm = board.GP8
tft_cs = board.GP13
tft_dc = board.GP12
spi_mosi = board.GP15
spi_clk = board.GP14

spi = busio.SPI(spi_clk, spi_mosi)
while not spi.try_lock():
    spi.configure(baudrate=24000000)  # Configure SPI for 24MHz
spi.unlock()

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=None, baudrate=24000000)

display = ST7789(display_bus,
                 width=240, height=240,
                 rowstart=80, rotation=180)

''' Define the fonts: '''

f_s = bitmap_font.load_font("/fonts/PTSans-Regular-20.pcf")
f_l = bitmap_font.load_font("/fonts/PTSans-NarrowBold-54.pcf")
f_xl = bitmap_font.load_font("/fonts/PTSans-Bold-60.pcf")

''' Make splash screen assingments: '''

splash = displayio.Group()
display.rootgroup = splash

''' Position and size the 14 display elements: '''

x = [0, 120, 0, 60, 120, 180, 0, 0, 60, 120, 180, 0, 60, 120]
y = [0, 0, 30, 30, 30, 30, 60, 180, 180, 180, 180, 210, 210, 210]
w = [120, 120, 60, 60, 60, 60, 240, 60, 60, 60, 60, 60, 60, 120]
h = [30, 30, 30, 30, 30, 30, 120, 30, 30, 30, 30, 30, 30, 30]

''' Color, font, text and value of the 14 display elements: '''

c = [2, 2, 16, 16, 10, 12, 0, 8, 8, 8, 8, 0, 4, 4]
f = [f_s, f_s, f_s, f_s, f_s, f_s, f_l, f_s, f_s, f_s, f_s, f_s, f_s, f_s]
t = ["Position", "Mode", "Play", "Loop", "Tap", "Tune", HelloStr,
     "SP 1", "SP 2", "SP 3", "SP 4", "3.30 V", "Def.", "Master"]
v = [38, 38, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, encoder_value]

''' Flags idicatin changes in  color, value and text of the 14 display elements: '''

cc = [False, False, False, False, False, False, False, False,
      False, False, False, False, False, False]
vc = [False, False, False, False, False, False, False, False,
      False, False, False, False, False, False]
tc = [False, False, False, False, False, False, False, False,
      False, False, False, False, False, False]

''' Try to load user defined colors and texts from /setup/HKAudioSetup.txt: '''

try:
    with open('/setup/HKAudioSetup.txt', 'r') as setupfile:
        file_content = setupfile.read()
        for line in file_content.split('\n'):

            CCstr = line[0:line.find('#')]
            indexstr = line[line.find('#') + 1:line.find(':')]
            indexstr = indexstr.replace(' ', '')
            colorstr = line[line.find(':') + 1:line.find(',')]
            colorstr = colorstr.replace(' ', '')
            stext = line[line.find(', ') + 2:]
            if CCstr == 'CC':
                sindex = int(indexstr)
                scolor = int(colorstr)
                if sindex >= 11 and sindex <= 24 and scolor >= 0 and scolor <= 26:
                    # print ("CC#", str(sindex), ": ", str(scolor), ", ", stext)
                    color_index[sindex - 11] = scolor
                    di = display_index[sindex - 11]

                    if di > -1:

                        c[di] = scolor
                        t[di] = stext

except OSError:
    print('error: can''t open setup file')
    pass

''' Function for the outer rectangle of a display element: '''

def outer_rect(i):

    rect = Rect(x[i], y[i], w[i], h[i], fill=dark_palette[c[i]],
                outline=palette[26], stroke=1)
    return rect

''' Function for the inner rectangle of a display element: '''

def inner_rect(i):

    rect = Rect(x[i] + 1, y[i] + 1, int(v[i] / 127 * (w[i] - 2) + 0.5), h[i] - 2,
                fill=palette[c[i]], outline=palette[26], stroke=0)
    return rect

''' Function to redraw the outer rectangle of a display elment: '''

def redraw_outer_rect(i):

    splash[i].pop(0)
    splash[i].insert(0, outer_rect(i))

''' Function to redraw the inner rectangle of a display element: '''

def redraw_inner_rect(i):

    splash[i].pop(1)
    splash[i].insert(1, inner_rect(i))

''' Draw the 14 display elements in normal mode: '''

text_area = []
subgroup = []
for i in range(14):
    subgroup = displayio.Group()
    splash.append(subgroup)
    subgroup.append(outer_rect(i))
    subgroup.append(inner_rect(i))
    text_area.append(label.Label(f[i], text=" "*60, color=palette[26],
                                 line_spacing=0.95, anchor_point=(0.5, 0.5),
                                 anchored_position=(w[i]//2, h[i]//2)))
    text_group = displayio.Group(scale=1, x=x[i], y=y[i])
    text_group.append(text_area[i])
    subgroup.append(text_group)
    text_area[i].text = t[i]

''' Draw the hidden displays elements for the tuner mode: '''

TunerMode = False
NoteName = "----"
nc = False
Pitch = 0.0
pc = False

pitch_rect = Rect(116, 72, 8, 32, fill=green, outline=white, stroke=0)
splash[6].append(pitch_rect)
splash[6][3].hidden = True

text_area.append(label.Label(f_xl, text=""*8, color=white, line_spacing=1.00,
                 anchor_point=(0.5, 0.5), anchored_position=(120, 40)))
text_group = displayio.Group(scale=1, x=0, y=100)
text_group.append(text_area[14])
splash[6].append(text_group)
text_area[14].text = NoteName
splash[6][4].hidden = True

''' Function to draw the pitch pointer value: '''

def drawPitch():

    x = Pitch * 4

    if x > 3:

        pitch_rect = Rect(116+x, 72,  8, 32, fill=red, outline=white, stroke=0)

    elif x < -3:

        pitch_rect = Rect(116+x, 72,  8, 32, fill=blue, outline=white, stroke=0)

    else:

        pitch_rect = Rect(116, 72, 8, 32, fill=green, outline=white, stroke=0)

    splash[6].pop(3)
    splash[6].insert(3, pitch_rect)

''' Show the splash screen: '''

display.show(splash)

''' Create USB MIDI: '''

midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1],
                              out_channel=0,
                              midi_in=usb_midi.ports[0],
                              in_buf_size=512, debug=False)


'''Create serial MIDI: '''

uart = busio.UART(tx=board.GP16, rx=board.GP17, baudrate=31250, timeout=0.003,
                  receiver_buffer_size=512)

midi_ser = adafruit_midi.MIDI(midi_in=uart, midi_out=uart, out_channel=0,
                              in_buf_size=512, debug=False)


''' Function to parse MIDI messages: '''

def MIDI_parse(midimsg):

    di = 0
    global NoteName
    global nc
    global Pitch
    global pc
    global TunerMode
    global encoder_value

    if midimsg is not None:

        if isinstance(midimsg, ControlChange):

            cc_number = midimsg.control
            cc_val = midimsg.value

            if cc_number >= 11 and cc_number <= 24:

                # print("CC: ", str(cc_number), ", ", str(cc_val))

                if cc_number >= 15:

                    if cc_val > 63:

                        LED_on(cc_number - 15)
                    else:

                        LED_dim(cc_number - 15)

                di = display_index[cc_number-11]

                if di > -1:

                    if v[di] != cc_val:

                        v[di] = cc_val
                        vc[di] = True

                        if di == 13:
                            encoder_value = cc_val

            elif cc_number == 25:

                if cc_val > 63:

                    TunerMode = True
                    splash[6][2].hidden = True
                    splash[6][3].hidden = False
                    splash[6][4].hidden = False

                else:

                    TunerMode = False
                    splash[6][2].hidden = False
                    splash[6][3].hidden = True
                    splash[6][4].hidden = True

        elif isinstance(midimsg, SystemExclusive):

            SysExId = list(midimsg.manufacturer_id)
            SysExData = list(midimsg.data)

            if SysExId == [0x59] and len(SysExData) > 1:

                k_cc = SysExData[0]
                c_cc = SysExData[1]

                if k_cc >= 11 and k_cc <= 25 and c_cc < 27:

                    lable = ''.join(chr(int(cx)) for cx in SysExData[2:])

                    # print("SY: ", str(k_cc), ", ", str(c_cc), ", ", lable)

                    if len(lable) > 9:

                        words = lable.split()
                        words = lable.split()
                        words_length = len(words)
                        lable1 = words[0]

                        if len(lable1) > 10:

                            lable1 = lable1[:10]

                        lable2 = ""
                        unsplit = True

                        for i in range(1, words_length, 1):

                            if unsplit is True:

                                nextLable = lable1 + " " + words[i]

                                if len(nextLable) <= 9:

                                    lable1 = nextLable

                                else:

                                    lable1 = lable1 + "\n"
                                    unsplit = False
                                    lable2 = words[i]

                                    if len(lable2) > 10:

                                        lable2 = lable2[:10]

                            else:

                                nextLable = lable2 + " " + words[i]

                                if len(nextLable) <= 9:

                                    lable2 = nextLable

                                else:

                                    break

                        lable = lable1 + lable2

                    color_index[k_cc - 11] = c_cc
                    di = display_index[k_cc - 11]

                    if di > -1 and di != 6:

                        if c[di] != c_cc:

                            c[di] = c_cc
                            cc[di] = True
                            vc[di] = True

                    if di > -1 and t[di] != lable:

                        t[di] = lable
                        tc[di] = True

        elif isinstance(midimsg, NoteOn):

            if TunerMode:

                NoteNumber = midimsg.note
                Octave = int(NoteNumber / 12)
                NoteNumber = NoteNumber % 12
                newNoteName = NoteNames[NoteNumber] + str(Octave-1)

                # print("NN: ", newNoteName)

                if NoteName != newNoteName:
                    NoteName = newNoteName
                    nc = True

        elif isinstance(midimsg, NoteOff):

            if TunerMode:

                newNoteName = "----"

                # print("NO: ", newNoteName)

                if NoteName != newNoteName:
                    NoteName = newNoteName
                    nc = True
                    Pitch = 0
                    pc = True

        elif isinstance(midimsg, PitchBend):

            if TunerMode:

                newPitch = midimsg.pitch_bend
                newPitch = (newPitch - 8192) / 8192 * 200
                newPitch = int(newPitch)
                newPitch = min(29, newPitch)
                newPitch = max(-29, newPitch)

                # print("PW: ", str(newPitch))

                if Pitch != newPitch:
                    Pitch = newPitch
                    pc = True

''' Async function to detect and handle MIDI events: '''

async def MidiEvent():

    while True:

        midimsg = midi_usb.receive()
        MIDI_parse(midimsg)

        midimsg = midi_ser.receive()
        MIDI_parse(midimsg)

        await asyncio.sleep(0)

''' Async function to detect and handle switch events: '''

async def SwitchEvent():

    while True:

        for i in range(11):

            ''' Ignore "Up" and "Down" switches in tuner mode  '''
            if (i != 5 and i != 10) or (not TunerMode):

                if not switch[i].switch.value:
                    if not switch[i].state:
                        switch[i].state = True
                        midi_usb.send(ControlChange(14 + i, 127))
                        midi_ser.send(ControlChange(14 + i, 127))
                else:
                    if switch[i].state:
                        switch[i].state = False
                        midi_usb.send(ControlChange(14 + i, 0))
                        midi_ser.send(ControlChange(14 + i, 0))

        await asyncio.sleep(0)

''' Async function to detect and handle encoder events: '''

async def EncoderEvent():

    global last_position
    global encoder_value
    while True:

        position = encoder.position

        if position != last_position:

            delta_position = position - last_position
            last_position = position
            encoder_value = encoder_value + delta_position
            encoder_value = max(0, encoder_value)
            encoder_value = min(127, encoder_value)
            midi_usb.send(ControlChange(11, encoder_value))
            midi_ser.send(ControlChange(11, encoder_value))

        await asyncio.sleep(0.050)

''' Async function to detect and handle analog input events: '''

async def AnalogInEvent():

    global exp1_max
    global exp1_min
    global exp1_old
    global exp2_max
    global exp2_min
    global exp2_old
    global vbat_state
    global vbat_old

    while True:

        ''' Automatic calibration of expression pedal 1: '''

        exp1_value = exp1.value
        exp1_max = max(exp1_value, exp1_max)
        exp1_min = min(exp1_value, exp1_min)
        exp1_value = int((exp1_value - exp1_min) / (exp1_max - exp1_min) * 127)

        ''' Send CC#12  if value has changed and has been maxed.
            This avoids sending with open input '''

        if exp1_value != exp1_old and exp1_max > 63488:
            exp1_old = exp1_value
            midi_usb.send(ControlChange(12, exp1_value))
            midi_ser.send(ControlChange(12, exp1_value))

        ''' Automatic calibration of expression pedal 2: '''

        exp2_value = exp2.value
        exp2_max = max(exp2_value, exp2_max)
        exp2_min = min(exp2_value, exp2_min)
        exp2_value = int((exp2_value - exp2_min) / (exp2_max - exp2_min) * 127)

        ''' Send CC#13  if value has changed and has been maxed.
            This avoids sending with open input '''

        if exp2_value != exp2_old and exp2_max > 63488:
            exp2_old = exp2_value
            midi_usb.send(ControlChange(13, exp2_value))
            midi_ser.send(ControlChange(13, exp2_value))

        ''' Calculate low pass filtered battery voltage: '''

        vbat = bat.value / 65536 * 3.3 * 3
        vbat_state = vbat * vbat_a + vbat_state * vbat_b
        vbat = vbat_state
        vbat = int(vbat * 100 + 0.5) * 0.01

        ''' Display battery voltage if value has changed: '''

        if vbat != vbat_old:
            t[11] = str(vbat) + " V"
            tc[11] = True
            vbat_old = vbat

        await asyncio.sleep(0.000)

''' Async function to detect and handle redraw events for display elements: '''

async def ReDraw():

    global nc
    global pc

    while True:

        for i in range(14):

            if cc[i]:

                redraw_outer_rect(i)
                cc[i] = False
                await asyncio.sleep(0.050)

            if vc[i]:

                redraw_inner_rect(i)
                vc[i] = False
                await asyncio.sleep(0.050)

            if tc[i]:

                text_area[i].text = t[i]
                tc[i] = False
                await asyncio.sleep(0.050)

        if nc and TunerMode:

            text_area[14].text = NoteName
            nc = False
            await asyncio.sleep(0.050)

        if pc and TunerMode:

            drawPitch()
            pc = False
            await asyncio.sleep(0.050)

        await asyncio.sleep(0.00)

''' Async function for the main event loop: '''

async def main():

    MidiEventTask = asyncio.create_task(MidiEvent())
    SwitchEventTask = asyncio.create_task(SwitchEvent())
    EncoderEventTask = asyncio.create_task(EncoderEvent())
    AnalogInEventTask = asyncio.create_task(AnalogInEvent())
    ReDrawTask = asyncio.create_task(ReDraw())
    await asyncio.gather(MidiEventTask, SwitchEventTask, EncoderEventTask,
                         AnalogInEventTask, ReDrawTask)


''' Say "Hello": '''

print(HelloStr)

LED.fill(green)
time.sleep(1)

for i in range(10):
    LED_dim(i)

''' Run the main event loop: '''

asyncio.run(main())
