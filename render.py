import falcon
import collections
from wand.image import Image
from wand.color import Color
from wand.font import Font
from wand.drawing import Drawing

CACHE_SIZE = 32  # MB
TEXT_MAX_LEN = 100

HEX_COLOR_LIME = "#9AC61E"
HEX_COLOR_DARK = "#044638"
HEX_COLOR_DIM = "#888"

COLOR_LIME = Color(HEX_COLOR_LIME)
COLOR_DARK = Color(HEX_COLOR_DARK)
COLOR_DIM = Color(HEX_COLOR_DIM)

WIDTH_HEIGHT_RATIO = 1.5
OUTPUT_WIDTH = 600
OUTPUT_HEIGHT = int(OUTPUT_WIDTH * WIDTH_HEIGHT_RATIO)

PATH_FONT = "./Raleway-ExtraBoldItalic.ttf"
LZY_PATH_FONT = "./Raleway-Medium.ttf"
PATH_IMG_STOP = "./stop.svg"
PATH_IMG_PAYOFF = "./payoff.png"
PATH_IMG_NAME = "./name.png"
PATH_IMG_LOGO = "./logo.png"

IMG_STOP_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)
IMG_PAYOFF_WIDTH_TARGET = int(0.20*OUTPUT_WIDTH)
IMG_NAME_WIDTH_TARGET = int(0.28*OUTPUT_WIDTH)
IMG_LOGO_WIDTH_TARGET = int(0.12*OUTPUT_WIDTH)


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


class Resource(object):

    def __init__(self):

        # "stop" image
        img_stop = Image(filename=PATH_IMG_STOP)
        scale = int(img_stop.height * IMG_STOP_WIDTH_TARGET / img_stop.width)
        img_stop.resize(IMG_STOP_WIDTH_TARGET, scale)
        self.img_stop = img_stop

        # "payoff" image
        img_payoff = Image(filename=PATH_IMG_PAYOFF)
        scale = int(img_payoff.height * IMG_PAYOFF_WIDTH_TARGET / img_payoff.width)
        img_payoff.resize(IMG_PAYOFF_WIDTH_TARGET, scale)
        self.img_payoff = img_payoff

        # name
        img_name = Image(filename=PATH_IMG_NAME)
        scale = int(img_name.height * IMG_NAME_WIDTH_TARGET / img_name.width)
        img_name.resize(IMG_NAME_WIDTH_TARGET, scale)
        self.img_name = img_name

        # logo
        img_logo = Image(filename=PATH_IMG_LOGO)
        scale = int(img_logo.height * IMG_LOGO_WIDTH_TARGET / img_logo.width)
        img_logo.resize(IMG_LOGO_WIDTH_TARGET, scale)
        self.img_logo = img_logo

        self.stop_offset = int(OUTPUT_HEIGHT*0.11)
        self.text_offset = self.stop_offset+self.img_stop.height-15
        self.name_offset = int(OUTPUT_HEIGHT*0.88)
        self.payoff_offset = int(OUTPUT_HEIGHT*0.888)
        self.logo_offset = int(OUTPUT_HEIGHT*0.858)

        self.cache = DataCache(1024*1024*CACHE_SIZE)

        footer_draw = Drawing()
        footer_draw.font = LZY_PATH_FONT
        footer_draw.font_size = 14
        footer_draw.fill_color = COLOR_DIM
        footer_draw.gravity = "south_east"
        footer_draw.text(5, 5, "stopc.lzy.dk")
        self.footer_draw = footer_draw

    def draw_footer(self, img):
        self.footer_draw.draw(img)

    def draw_text(self, img, text):
        with Drawing() as draw:
            draw.font = PATH_FONT
            draw.fill_color = COLOR_LIME
            draw.font_size = 148
            draw.text_antialias = True
            draw.gravity = "north_west"
            draw.text_kerning = -6
            draw.text_interline_spacing = -int(draw.font_size/3)
            draw.text(0, self.text_offset, text.upper())
            draw.draw(img)

    def on_get(self, req, resp):
        image_data = None

        text = req.get_param("text", True)
        if len(text) > TEXT_MAX_LEN:
            resp.body = "no"
        text = text.replace(" ", "\n")


        image_data = self.cache.get(text)

        if not image_data:
            with Image(
                    height=OUTPUT_HEIGHT,
                    width=OUTPUT_WIDTH,
                    background=COLOR_DARK) as canvas:

                canvas.composite(self.img_stop, left=0, top=self.stop_offset)

                canvas.composite(self.img_name,
                                 left=int(OUTPUT_WIDTH*0.08),
                                 top=self.name_offset)
                canvas.composite(self.img_payoff,
                                 left=int(OUTPUT_WIDTH*0.57),
                                 top=self.payoff_offset)
                canvas.composite(self.img_logo,
                                 left=int(OUTPUT_WIDTH*0.80),
                                 top=self.logo_offset)

                self.draw_text(canvas, text)
                self.draw_footer(canvas)

                image_data = canvas.make_blob("png")
            self.cache.set(text, image_data)

        resp.set_header("Content-Type", "image/png")
        resp.body = image_data
