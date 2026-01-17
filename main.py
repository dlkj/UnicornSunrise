# Clock example with NTP synchronization
#
# Create a secrets.py with your Wifi details to be able to get the time
# when the Galactic Unicorn isn't connected to Thonny.
#
# secrets.py should contain:
# WIFI_SSID = "Your WiFi SSID"
# WIFI_PASSWORD = "Your WiFi password"
#
# Clock synchronizes time on start, and resynchronizes if you press the A button

import time
import math
import machine
import network
import ntptime
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY

try:
    from secrets import WIFI_SSID, WIFI_PASSWORD
    wifi_available = True
except ImportError:
    print("Create secrets.py with your WiFi credentials to get time from NTP")
    wifi_available = False


# constants for controlling the background colour throughout the day
MIDDAY_HUE = 1.1
MIDNIGHT_HUE = 0.8
HUE_OFFSET = -0.1

MIDDAY_SATURATION = 1.0
MIDNIGHT_SATURATION = 1.0

MIDDAY_VALUE = 0.8
MIDNIGHT_VALUE = 0.3


# create galactic object and graphics surface for drawing
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)

# create the rtc object
rtc = machine.RTC()

width = GalacticUnicorn.WIDTH
height = GalacticUnicorn.HEIGHT

# set up some pens to use later
WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)


@micropython.native  # noqa: F821
def from_hsv(h, s, v):
    i = math.floor(h * 6.0)
    f = h * 6.0 - i
    v *= 255.0
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    i = int(i) % 6
    if i == 0:
        return int(v), int(t), int(p)
    if i == 1:
        return int(q), int(v), int(p)
    if i == 2:
        return int(p), int(v), int(t)
    if i == 3:
        return int(p), int(q), int(v)
    if i == 4:
        return int(t), int(p), int(v)
    if i == 5:
        return int(v), int(p), int(q)


# function for drawing a gradient background
def gradient_background(start_hue, start_sat, start_val, end_hue, end_sat, end_val):
    half_width = width // 2
    for x in range(0, half_width):
        hue = ((end_hue - start_hue) * (x / half_width)) + start_hue
        sat = ((end_sat - start_sat) * (x / half_width)) + start_sat
        val = ((end_val - start_val) * (x / half_width)) + start_val
        colour = from_hsv(hue, sat, val)
        graphics.set_pen(graphics.create_pen(int(colour[0]), int(colour[1]), int(colour[2])))
        for y in range(0, height):
            graphics.pixel(x, y)
            graphics.pixel(width - x - 1, y)

    colour = from_hsv(end_hue, end_sat, end_val)
    graphics.set_pen(graphics.create_pen(int(colour[0]), int(colour[1]), int(colour[2])))
    #print(f'{colour}')
    for y in range(0, height):
        graphics.pixel(half_width, y)

def black_background():
    graphics.set_pen(BLACK)
    for x in range(0, width):
        for y in range(0, height):
            graphics.pixel(x, y)


def white_background():
    graphics.set_pen(WHITE)
    for x in range(0, width):
        for y in range(0, height):
            graphics.pixel(x, y)


# function for drawing outlined text
def outline_text(text, x, y):
    graphics.set_pen(BLACK)
    graphics.text(text, x - 1, y - 1, -1, 1)
    graphics.text(text, x, y - 1, -1, 1)
    graphics.text(text, x + 1, y - 1, -1, 1)
    graphics.text(text, x - 1, y, -1, 1)
    graphics.text(text, x + 1, y, -1, 1)
    graphics.text(text, x - 1, y + 1, -1, 1)
    graphics.text(text, x, y + 1, -1, 1)
    graphics.text(text, x + 1, y + 1, -1, 1)

    graphics.set_pen(WHITE)
    graphics.text(text, x, y, -1, 1)


# Connect to wifi and synchronize the RTC time from NTP
def sync_time():
    # if not wifi_available:
    #     return

    # Start connection
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Wait for connect success or failure
    max_wait = 1000
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(0.2)

        # redraw_display()
        white_background()
        gu.update(graphics)

    if max_wait > 0:
        print("Connected")

        try:
            ntptime.settime()
            print("Time set")
        except OSError:
            pass

    wlan.disconnect()
    wlan.active(False)


# NTP synchronizes the time to UTC, this allows you to adjust the displayed time
# by one hour increments from UTC by pressing the volume up/down buttons
#
# We use the IRQ method to detect the button presses to avoid incrementing/decrementing
# multiple times when the button is held.
utc_offset = 0

up_button = machine.Pin(GalacticUnicorn.SWITCH_VOLUME_UP, machine.Pin.IN, machine.Pin.PULL_UP)
down_button = machine.Pin(GalacticUnicorn.SWITCH_VOLUME_DOWN, machine.Pin.IN, machine.Pin.PULL_UP)


def adjust_utc_offset(pin):
    global utc_offset, last_second
    if pin == up_button:
        utc_offset += 1
        last_second = None
    if pin == down_button:
        utc_offset -= 1
        last_second = None


up_button.irq(trigger=machine.Pin.IRQ_FALLING, handler=adjust_utc_offset)
down_button.irq(trigger=machine.Pin.IRQ_FALLING, handler=adjust_utc_offset)


year, month, day, wd, hour, minute, second, _ = rtc.datetime()

last_second = second


def adjust_brightness():
    light = gu.light()
    target = max(0.01, min(1.0, (light/200.0)-.05))
    brightness = gu.get_brightness()

    #print(f'light: {light}, target: {target}, bright: {brightness}')

    if abs(brightness - target) > 0.05:
        if  brightness > target:
            gu.adjust_brightness(-0.005)
        else:
            gu.adjust_brightness(0.005)


def draw_clock_text(hour, minute, second, utc_offset):
        hour = (hour + utc_offset) % 12
        clock = "{:2}:{:02}".format(hour, minute)
        # clock = "{:2}:{:02}:{:02}".format(hour, minute, second)

        # calculate text position so that it is centred
        w = graphics.measure_text(clock, 1)
        x = int(width / 2 - w / 2 + 1)
        y = 2

        outline_text(clock, x, y)

def redraw_display():
    global year, month, day, wd, hour, minute, second, last_second
    year, month, day, wd, hour, minute, second, _ = rtc.datetime()

    if hour == 12 and minute == 59 and second == 30:
        if second != last_second:
            sync_time()

    if wd <= 4 and ((hour == 6 and minute >= 45) or (hour == 7 and minute < 15)):
        #sunrise
        if second != last_second:
            # Convert to minutes since 06:45
            minutes_since_start = (hour - 6) * 60 + minute - 45
            # Total duration is 30 minutes (06:45 to 07:15)
            rise_progress = minutes_since_start / 30.0

            gu.set_brightness(rise_progress)
            hue = 1.1
            sat = 1.0 - rise_progress
            val = rise_progress
            gradient_background(hue, sat, val,
                            hue + HUE_OFFSET, sat, val)
            draw_clock_text(hour, minute, second, utc_offset)
    elif wd <= 4 and ((hour == 7 and minute >= 15 and minute < 45)):
        if second != last_second:
            gu.set_brightness(1.0)
            white_background()
            draw_clock_text(hour, minute, second, utc_offset)
    else:
        #clock
        adjust_brightness()
        if second != last_second:
            black_background()
            draw_clock_text(hour, minute, second, utc_offset)

    last_second = second

# set the font
graphics.set_font("bitmap8")
gu.set_brightness(0.1)

sync_time()

while True:
    if gu.is_pressed(GalacticUnicorn.SWITCH_A):
        sync_time()

    redraw_display()

    # update the display
    gu.update(graphics)

    time.sleep(0.01)