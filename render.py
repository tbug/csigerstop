import falcon
import collections
import time
import hashlib
import re
from wand.image import Image, CHANNELS
from wand.color import Color
from wand.font import Font
from wand.drawing import Drawing

CACHE_SIZE = 64  # MB
TEXT_MAX_LEN = 100

HEX_COLOR_LIME = "#9AC61E"
HEX_COLOR_DARK = "#044638"
HEX_COLOR_DIM = "#ffffff50"

COLOR_LIME = Color(HEX_COLOR_LIME)
COLOR_DARK = Color(HEX_COLOR_DARK)
COLOR_DIM = Color(HEX_COLOR_DIM)

WIDTH_HEIGHT_RATIO = 1.5
OUTPUT_WIDTH = 600
OUTPUT_HEIGHT = int(OUTPUT_WIDTH * WIDTH_HEIGHT_RATIO)
FONT_WIDTH_RATIO = 0.23
FONT_SIZE = int(OUTPUT_WIDTH * FONT_WIDTH_RATIO)

PATH_FONT = "./fonts/Raleway-ExtraBoldItalic.ttf"
LZY_PATH_FONT = "./fonts/Raleway-Medium.ttf"
PATH_IMG_STOP = "./images/stop.svg"
PATH_IMG_PAYOFF = "./images/payoff.png"
PATH_IMG_NAME = "./images/name.png"
PATH_IMG_LOGO = "./images/logo.png"
PATH_IMG_DICKBUTT = "./images/dickbutt.png"

IMG_STOP_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)
IMG_PAYOFF_WIDTH_TARGET = int(0.20*OUTPUT_WIDTH)
IMG_NAME_WIDTH_TARGET = int(0.28*OUTPUT_WIDTH)
IMG_LOGO_WIDTH_TARGET = int(0.12*OUTPUT_WIDTH)
IMG_DICKBUTT_WIDTH_TARGET = int(0.05*OUTPUT_WIDTH)


class DataCache(object):
    def __init__(self, capacity):
        self.max_capacity = capacity
        self.current_capacity = 0
        self.cache = collections.OrderedDict()

    def get(self, key):
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return None

    def set(self, key, value):
        new_value_length = len(value)
        try:
            popped = self.cache.pop(key)
            self.current_capacity -= len(popped)
        except KeyError:
            if self.current_capacity + new_value_length > self.max_capacity:
                popped = self.cache.popitem(last=False)
                self.current_capacity -= len(popped)
        self.current_capacity += new_value_length
        self.cache[key] = value

    def get_keys(self):
        return self.cache.keys()


class Resource(object):

    def __init__(self):
        self.cache = DataCache(1024*1024*CACHE_SIZE)
        self._base_img = None

        # calc the offsets
        self.stop_offset = 0
        self.text_offset = 0
        self.name_offset = 0
        self.payoff_offset = 0
        self.logo_offset = 0

    @property
    def base_img(self):
        if not self._base_img:
            # compose the base image

            # "stop" image
            img_stop = Image(filename=PATH_IMG_STOP)
            scale = int(img_stop.height * IMG_STOP_WIDTH_TARGET / img_stop.width)
            img_stop.resize(IMG_STOP_WIDTH_TARGET, scale)

            # "payoff" image
            img_payoff = Image(filename=PATH_IMG_PAYOFF)
            scale = int(img_payoff.height * IMG_PAYOFF_WIDTH_TARGET / img_payoff.width)
            img_payoff.resize(IMG_PAYOFF_WIDTH_TARGET, scale)

            # name
            img_name = Image(filename=PATH_IMG_NAME)
            scale = int(img_name.height * IMG_NAME_WIDTH_TARGET / img_name.width)
            img_name.resize(IMG_NAME_WIDTH_TARGET, scale)

            # logo
            img_logo = Image(filename=PATH_IMG_LOGO)
            scale = int(img_logo.height * IMG_LOGO_WIDTH_TARGET / img_logo.width)
            img_logo.resize(IMG_LOGO_WIDTH_TARGET, scale)

            # dickbutt
            img_dickbutt = Image(filename=PATH_IMG_DICKBUTT)
            scale = int(img_dickbutt.height * IMG_DICKBUTT_WIDTH_TARGET / img_dickbutt.width)
            img_dickbutt.resize(IMG_DICKBUTT_WIDTH_TARGET, scale)

            # calc the offsets
            self.stop_offset = int(OUTPUT_HEIGHT*0.11)
            self.text_offset = int(self.stop_offset+img_stop.height)
            self.name_offset = int(OUTPUT_HEIGHT*0.88)
            self.payoff_offset = int(OUTPUT_HEIGHT*0.888)
            self.logo_offset = int(OUTPUT_HEIGHT*0.858)

            dickbutt_x_offset = int(OUTPUT_WIDTH*0.24)
            dickbutt_y_offset = int(OUTPUT_HEIGHT*0.9)

            # compose the base image
            base_img = Image(
                height=OUTPUT_HEIGHT,
                width=OUTPUT_WIDTH,
                background=COLOR_DARK)

            base_img.composite(img_stop, left=0, top=self.stop_offset)

            base_img.composite(img_name,
                               left=int(OUTPUT_WIDTH*0.08),
                               top=self.name_offset)
            base_img.composite(img_payoff,
                               left=int(OUTPUT_WIDTH*0.57),
                               top=self.payoff_offset)
            base_img.composite(img_logo,
                               left=int(OUTPUT_WIDTH*0.80),
                               top=self.logo_offset)

            base_img.composite_channel(
                channel="rgb_channels",
                image=img_dickbutt,
                left=dickbutt_x_offset,
                top=dickbutt_y_offset,
                operator='blend')

            with Drawing() as footer_draw:
                footer_draw.font = LZY_PATH_FONT
                footer_draw.font_size = 14
                footer_draw.fill_color = COLOR_DIM
                footer_draw.gravity = "south_east"
                footer_draw.text(5, 5, "csigerstop.dk")
                footer_draw.draw(base_img)

            img_stop.destroy()
            img_payoff.destroy()
            img_name.destroy()
            img_logo.destroy()

            self._base_img = base_img

        return self._base_img

    def draw_text(self, img, text):
        with Drawing() as draw:
            draw.font = PATH_FONT
            draw.fill_color = COLOR_LIME
            draw.text_antialias = True
            draw.gravity = "north_west"
            draw.text_kerning = 0
            draw.text_interline_spacing = -10
            lines = text.upper().split("\n")
            i = 0
            offset = 0

            for line in lines:
                # line can't be empty
                if len(line) < 1:
                    continue

                draw.font_size = FONT_SIZE
                fm = draw.get_font_metrics(img, line)
                iter_protect = 20
                while fm.text_width > OUTPUT_WIDTH and iter_protect > 0:
                    draw.font_size -= draw.font_size / 10
                    fm = draw.get_font_metrics(img, line)
                    iter_protect -= 1

                # each line as some spare room top and bottom due to font.
                # we want tight text, so we need to figure out what we can draw over
                spare_room_bottom = int(fm.text_height * 0.15)
                if "Å" in line:
                    spare_room_top = 0
                else:
                    spare_room_top = int(fm.text_height * 0.15)

                line_offset = self.text_offset + offset - spare_room_top

                draw.text(0, line_offset, line)

                offset += round(fm.text_height) - spare_room_top - spare_room_bottom

                i += 1

            draw.draw(img)

    def on_get(self, req, resp):
        image_data = None

        if req.get_header("If-None-Match") and req.get_header("Cache-Control") != "no-cache":
            resp.status = falcon.HTTP_304
            return

        text = req.get_param("text", True).strip()
        if len(text) > TEXT_MAX_LEN:
            resp.status = falcon.HTTP_403
            resp.body = "Text to long."
            return

        # if text has no newline, assume space is the newline
        if "\n" not in text:
            text = re.sub(r" +", "\n", text)

        image_data = self.cache.get(text)
        if not image_data:
            with self.base_img.clone() as canvas:
                self.draw_text(canvas, text)
                image_data = canvas.make_blob("png")
            self.cache.set(text, image_data)

        resp.set_header("Cache-Control", "public, max-age=3600")
        resp.set_header("Content-Type", "image/png")
        resp.set_header("ETag", hashlib.md5(text.encode("utf-8")).hexdigest())
        resp.body = image_data

    def on_post(self, req, resp):
        stats = [
            "%d items in cache" % len(self.cache.cache),
            "%f MB in cache" % ((self.cache.current_capacity or 0.1) / 1024 / 1024),
        ]

        resp.body = "\n".join(stats)
