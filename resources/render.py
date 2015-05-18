import falcon
import collections
import time
import hashlib
import re
from wand.image import Image, CHANNELS
from wand.color import Color
from wand.font import Font
from wand.drawing import Drawing
from lrucache import LRUCache
from util import clean_text

CACHE_SIZE = 16  # MB
THUMBNAIL_CACHE_SIZE = 8  # MB
TEXT_MAX_LEN = 100

HEX_COLOR_LIME = "#9AC61E"
HEX_COLOR_DARK = "#044638"
HEX_COLOR_DIM = "#ffffff50"

COLOR_LIME = Color(HEX_COLOR_LIME)
COLOR_DARK = Color(HEX_COLOR_DARK)
COLOR_DIM = Color(HEX_COLOR_DIM)


WIDTH_HEIGHT_RATIO = 1.5
IMAGE_WIDTH = 600
IMAGE_HEIGHT = int(IMAGE_WIDTH * WIDTH_HEIGHT_RATIO)

THUMBNAIL_WIDTH = 100
THUMBNAIL_HEIGHT = int(THUMBNAIL_WIDTH * WIDTH_HEIGHT_RATIO)


class ImageLayout(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ratio = height/width

        self.font_size = int(self.width * 0.23)

        self.img_stop_width_target = int(0.66*width)
        self.img_payoff_width_target = int(0.20*width)
        self.img_name_width_target = int(0.28*width)
        self.img_logo_width_target = int(0.12*width)

        self.path_font = "./fonts/Raleway-ExtraBoldItalic.ttf"
        self.lzy_path_font = "./fonts/Raleway-Medium.ttf"

        self.path_img_stop = "./images/stop.svg"
        self.path_img_payoff = "./images/payoff.png"
        self.path_img_name = "./images/name.png"
        self.path_img_logo = "./images/logo.png"

        self._base_image = None

    @property
    def base_image(self):
        if not self._base_image:
            self._base_image = self.compose_base_image()
        return self._base_image

    def compose_base_image(self):
        # compose the base image

        # "stop" image
        img_stop = Image(filename=self.path_img_stop)
        scale = int(img_stop.height * self.img_stop_width_target / img_stop.width)
        img_stop.resize(self.img_stop_width_target, scale)

        # "payoff" image
        img_payoff = Image(filename=self.path_img_payoff)
        scale = int(img_payoff.height * self.img_payoff_width_target / img_payoff.width)
        img_payoff.resize(self.img_payoff_width_target, scale)

        # name
        img_name = Image(filename=self.path_img_name)
        scale = int(img_name.height * self.img_name_width_target / img_name.width)
        img_name.resize(self.img_name_width_target, scale)

        # logo
        img_logo = Image(filename=self.path_img_logo)
        scale = int(img_logo.height * self.img_logo_width_target / img_logo.width)
        img_logo.resize(self.img_logo_width_target, scale)

        # calc the offsets
        self.stop_y_offset = int(self.height*0.11)
        self.stop_x_offset = 0

        self.text_y_offset = int(self.stop_y_offset+img_stop.height)
        self.text_x_offset = 0

        self.name_y_offset = int(self.height*0.88)
        self.name_x_offset = int(self.width*0.08)

        self.payoff_y_offset = int(self.height*0.888)
        self.payoff_x_offset = int(self.width*0.57)

        self.logo_y_offset = int(self.height*0.858)
        self.logo_x_offset = int(self.width*0.80)

        # compose the base image
        base_img = Image(
            height=self.height,
            width=self.width,
            background=COLOR_DARK)

        base_img.composite(img_stop,
                           left=self.stop_x_offset,
                           top=self.stop_y_offset)

        base_img.composite(img_name,
                           left=self.name_x_offset,
                           top=self.name_y_offset)
        base_img.composite(img_payoff,
                           left=self.payoff_x_offset,
                           top=self.payoff_y_offset)
        base_img.composite(img_logo,
                           left=self.logo_x_offset,
                           top=self.logo_y_offset)

        if self.width >= 200:
            with Drawing() as footer_draw:
                footer_draw.font = self.lzy_path_font
                footer_draw.font_size = 14
                footer_draw.fill_color = COLOR_DIM
                footer_draw.gravity = "south_east"
                footer_draw.text(5, 5, "csigerstop.lzy.dk")
                footer_draw.draw(base_img)

        img_stop.destroy()
        img_payoff.destroy()
        img_name.destroy()
        img_logo.destroy()

        return base_img


class Resource(object):

    def __init__(self):
        self.image_layout = ImageLayout(IMAGE_WIDTH, IMAGE_HEIGHT)
        self.thumbnail_layout = ImageLayout(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
        self.image_cache = LRUCache(1024*1024*CACHE_SIZE)
        self.thumbnail_cache = LRUCache(1024*1024*THUMBNAIL_CACHE_SIZE)

        self.latest_cache_hit_times = collections.deque(maxlen=50)
        self.latest_cache_miss_times = collections.deque(maxlen=50)
        self.latest_response_times = collections.deque(maxlen=50)

    @property
    def base_img(self):
        return self.image_layout.base_image

    def draw_text(self, layout, img, text):
        with Drawing() as draw:
            draw.font = layout.path_font
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

                draw.font_size = layout.font_size
                fm = draw.get_font_metrics(img, line)
                iter_protect = 20
                while fm.text_width > layout.width and iter_protect > 0:
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

                line_offset = layout.text_y_offset + offset - spare_room_top

                draw.text(0, line_offset, line)

                offset += round(fm.text_height) - spare_room_top - spare_room_bottom

                i += 1

            draw.draw(img)

    def on_get(self, req, resp):
        time_response_begin = time.time()

        is_thumbnail = bool(req.get_param("thumbnail"))

        if is_thumbnail:
            cache = self.thumbnail_cache
            layout = self.thumbnail_layout
        else:
            cache = self.image_cache
            layout = self.image_layout

        image_data = None

        # cache hack
        if req.get_header("If-None-Match") and req.get_header("Cache-Control") != "no-cache":
            resp.status = falcon.HTTP_304
            return

        text = clean_text(req.get_param("text", True))
        if len(text) > TEXT_MAX_LEN:
            resp.status = falcon.HTTP_403
            resp.body = "Text to long."
            return

        # if text has no newline, assume space is the newline
        if "\n" not in text:
            text = re.sub(r" +", "\n", text)
        text = re.sub(r"_+", " ", text)

        image_data = cache.get(text)
        cache_hit = image_data is not None
        if not cache_hit:
            time_render_begin = time.time()  # stats
            with layout.base_image.clone() as canvas:
                self.draw_text(layout, canvas, text)
                image_data = canvas.make_blob("png")
            cache.set(text, image_data)
            render_time = time.time() - time_render_begin  # stats
            self.latest_cache_miss_times.append(render_time)  # stats

        resp.set_header("Cache-Control", "public, max-age=3600")
        resp.set_header("Content-Type", "image/png")
        resp.set_header("ETag", hashlib.md5(text.encode("utf-8")).hexdigest())
        resp.body = image_data

        now = time.time()
        if cache_hit:
            cache_hit_time = time.time() - time_response_begin
        response_time = now - time_response_begin

        self.latest_response_times.append(response_time)
        if cache_hit:
            self.latest_cache_hit_times.append(cache_hit_time)



    def on_post(self, req, resp):

        stats = [
            "%d items in image cache" % len(self.image_cache.cache),
            "%f MB in image cache" % ((self.image_cache.current_capacity or 0.01) / 1024 / 1024),
            "",
            "%d items in thumbnail cache" % len(self.thumbnail_cache.cache),
            "%f MB in thumbnail cache" % ((self.thumbnail_cache.current_capacity or 0.01) / 1024 / 1024),
            "",
            "Average cache-miss time: %.2f ms" % (sum(self.latest_cache_miss_times)/(len(self.latest_cache_miss_times) or 1)*1000),
            "Average cache-hit  time: %.2f ms" % (sum(self.latest_cache_hit_times)/(len(self.latest_cache_hit_times) or 1)*1000),
            "Average respoonse  time: %.2f ms" % (sum(self.latest_response_times)/(len(self.latest_response_times) or 1)*1000),
        ]
        resp.body = "\n".join(stats)
