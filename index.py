import falcon
from falcon.util import uri
from jinja2 import Environment, FileSystemLoader


class Resource(object):

    def __init__(self):
        self.loader = FileSystemLoader("./templates")
        self.env = Environment(loader=self.loader)

    def on_get(self, req, resp):
        text = req.get_param("text")

        resp.set_header("Cache-Control", "max-age=3600")
        resp.set_header("Content-Type", "text/html; charset=utf8")

        if text:
            resp.add_link("/render?text=%s" % uri.encode(text), "prefetch")

        resp.body = self.env.get_template("index.html").render(text=text)
