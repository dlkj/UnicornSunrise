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

# import math
# import machine
# import network
# import ntptime
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN


class Display:
    def __init__(
        self, gu: GalacticUnicorn, graphics: PicoGraphics, width: int, height: int
    ):
        self.gu = gu
        self.graphics = graphics
        self.width = width
        self.height = height
        self.white_pen = graphics.create_pen(255, 255, 255)
        self.black_pen = graphics.create_pen(0, 0, 0)

    def draw_text_screen(self, text: str):
        self.graphics.set_pen(self.black_pen)
        self.graphics.clear()
        self.graphics.set_pen(self.white_pen)
        draw_width = self.graphics.measure_text(
            text, scale=1, spacing=1, fixed_width=False
        )
        x = int(self.width / 2 - draw_width / 2 + 1)
        y = 2
        self.graphics.text(
            text, x, y, wordwrap=-1, scale=1, spacing=1, angle=0, fixed_width=False
        )

    def set_min_brightness(self, b: float):
        if self.gu.get_brightness() < b:
            self.gu.set_brightness(b)

    def update(self):
        self.gu.update(self.graphics)


class ClockController:
    def __init__(self, gu: GalacticUnicorn, display: Display):
        self.gu = gu
        self.display = display

    def initialise(self):
        raise WifiException()

    def clock(self):
        pass

    def error(self):
        self.display.set_min_brightness(0.1)
        self.display.draw_text_screen("Error")
        self.display.update()

    def wifi_error(self):
        self.display.set_min_brightness(0.1)
        self.display.draw_text_screen("WiFi Error")
        self.display.update()


class WifiException(Exception):
    pass


class ClockApp:
    def __init__(self, gu: GalacticUnicorn, display: Display):
        self.controller = ClockController(gu, display)

    def run(self):
        try:
            self.controller.initialise()
            while True:
                self.controller.clock()
                time.sleep(0.01)
        except WifiException:
            self.controller.wifi_error()
        except Exception:
            self.controller.error()


# class ClockModel:
#     def __init__(self):
#         pass


# class ClockDisplayView:
#     def __init__(self):
#         pass


# class ClockDisplayViewModel:
#     def __init__(self):
#         pass


# class InitialiseView:
#     def __init__(self):
#         pass


# class InitialiseViewModel:
#     def __init__(self):
#         pass

gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY_GALACTIC_UNICORN)

display = Display(gu, graphics, GalacticUnicorn.WIDTH, GalacticUnicorn.HEIGHT)

app = ClockApp(gu, display)
app.run()
