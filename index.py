
import falcon


class Resource(object):

    def __init__(self):
        self.index = ""
        with open("./index.html") as f:
            self.index = f.read()

    def on_get(self, req, resp):
        resp.set_header("Cache-Control", "max-age=3600")
        resp.set_header("Content-Type", "text/html")
        resp.body = self.index
