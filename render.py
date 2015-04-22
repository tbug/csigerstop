import falcon
from wand.image import Image
from wand.color import Color
from wand.font import Font
from wand.drawing import Drawing

HEX_COLOR_LIME = "#9AC61E"
HEX_COLOR_DARK = "#044638"

COLOR_LIME = Color(HEX_COLOR_LIME)
COLOR_DARK = Color(HEX_COLOR_DARK)

WIDTH_HEIGHT_RATIO = 1.5
OUTPUT_WIDTH = 600
OUTPUT_HEIGHT = int(OUTPUT_WIDTH * WIDTH_HEIGHT_RATIO)

PATH_FONT = "./Raleway-ExtraBoldItalic.ttf"
PATH_IMG_STOP = "./stop.svg"
PATH_IMG_PAYOFF = "./payoff.png"
PATH_IMG_NAME = "./name.png"
PATH_IMG_LOGO = "./logo.png"

IMG_STOP_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)
IMG_PAYOFF_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)
IMG_NAME_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)
IMG_LOGO_WIDTH_TARGET = int(0.66*OUTPUT_WIDTH)


class Resource(object):

    def __init__(self):

        # "stop" image
        img_stop = Image(filename=PATH_IMG_STOP)
        img_stop.resize(IMG_STOP_WIDTH_TARGET,
                        int(img_stop.height * IMG_STOP_WIDTH_TARGET / img_stop.width))
        self.img_stop = img_stop

        # "payoff" image
        img_payoff = Image(filename=PATH_IMG_PAYOFF)
        img_payoff.resize(IMG_PAYOFF_WIDTH_TARGET,
                        int(img_payoff.height * IMG_PAYOFF_WIDTH_TARGET / img_payoff.width))
        self.img_payoff = img_payoff

        # name
        img_name = Image(filename=PATH_IMG_NAME)
        img_name.resize(IMG_NAME_WIDTH_TARGET,
                        int(img_name.height * IMG_NAME_WIDTH_TARGET / img_name.width))
        self.img_name = img_name

        # logo
        img_logo = Image(filename=PATH_IMG_LOGO)
        img_logo.resize(IMG_LOGO_WIDTH_TARGET,
                        int(img_logo.height * IMG_LOGO_WIDTH_TARGET / img_logo.width))
        self.img_logo = img_logo

        self.n_stop_offset = int(OUTPUT_HEIGHT*0.10)
        self.n_text_offset = self.n_stop_offset+self.img_stop.height-15

    def on_get(self, req, resp):
        image_data = None

        text = "under\nlige\nting"

        with Drawing() as draw:

            draw.font = PATH_FONT
            draw.fill_color = COLOR_LIME
            draw.font_size = 142
            draw.text_antialias = True
            draw.gravity = "north_west"
            draw.text_kerning = -6
            draw.text_interline_spacing = -int(draw.font_size/3)
            draw.text(7, self.n_text_offset, text.upper())

            with Image(
                    height=OUTPUT_HEIGHT,
                    width=OUTPUT_WIDTH,
                    background=COLOR_DARK) as canvas:
                canvas.composite(self.img_stop, left=0, top=self.n_stop_offset)

                draw.draw(canvas)

                image_data = canvas.make_blob("png")

        resp.set_header("Content-Type", "image/png")
        resp.body = image_data
