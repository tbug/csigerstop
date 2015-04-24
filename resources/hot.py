import falcon
import time
from falcon.util import uri
from jinja2 import Environment, FileSystemLoader
from util import clean_text


class Resource(object):

    def __init__(self, stats):
        self.stats = stats
        self.loader = FileSystemLoader("./templates")
        self.env = Environment(loader=self.loader)

    def on_get(self, req, resp):
            print (self.stats.get_top(4*4))
            context = {
                "popular": self.stats.get_top(4*4)
            }
            resp.set_header("Cache-Control", "max-age=3600")
            resp.set_header("Content-Type", "text/html; charset=utf8")
            resp.body = self.env.get_template("hot.html").render(**context)
