import falcon
import time
from falcon.util import uri
from jinja2 import Environment, FileSystemLoader
from util import clean_text

ROW_WIDTH = 4

class Resource(object):

    def __init__(self, stats):
        self.stats = stats
        self.loader = FileSystemLoader("./templates")
        self.env = Environment(loader=self.loader)

    def on_get(self, req, resp):
            popular = self.stats.get_top(ROW_WIDTH * 10)

            rows = len(popular) // ROW_WIDTH

            context = {
                "popular":  popular[:(rows*ROW_WIDTH)]
            }
            resp.set_header("Cache-Control", "max-age=3600")
            resp.set_header("Content-Type", "text/html; charset=utf8")
            resp.body = self.env.get_template("hot.html").render(**context)
