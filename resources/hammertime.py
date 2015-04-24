import falcon


class Resource(object):

    def __init__(self):
        self.data = open("./images/compressed_hammertime.png", "rb").read()

    def on_get(self, req, resp):
        resp.content_type = "image/png"
        resp.body = self.data
