import falcon
import time
from falcon.util import uri
from jinja2 import Environment, FileSystemLoader
from util import clean_text


def get_client_ip(req):
    try:
        return req.env['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
        return req.env['REMOTE_ADDR']


class Resource(object):

    def __init__(self, stats):
        self.stats = stats
        self.loader = FileSystemLoader("./templates")
        self.env = Environment(loader=self.loader)

        self.seen_ips = set()
        self._seen_ips_window = None

    def check_ip_window(self):
        current_hour = int(time.time() / 3600)
        if current_hour != self._seen_ips_window:
            self.seen_ips = set()  # clean
            self._seen_ips_window = current_hour  # and remember

    def on_get(self, req, resp):

        text = req.get_param("text")
        cleaned = clean_text(text)

        # redirect to clean version if possible
        if text != cleaned and req.get_param("r") != "0":
            resp.status = falcon.HTTP_301
            resp.location = "http://csigerstop.dk?text=%s&r=0" % cleaned
            return

        text = cleaned

        if "csigerstop.lzy.dk" in req.host:
            resp.status = falcon.HTTP_301
            if text:
                resp.location = "http://csigerstop.dk?text=%s" % text.lower()
            else:
                resp.location = "http://csigerstop.dk"
        else:

            if text and len(text) > 0:
                resp.add_link("/render?text=%s" % uri.encode(text), "prefetch")

                self.check_ip_window()  # handle cleanup etc of seen ip set
                ip = get_client_ip(req)

                if ip not in self.seen_ips:
                    self.seen_ips.add(ip)

                self.stats.increment(text)
                self.stats.clean()

            context = {
                "text": text or "",
                "popular": self.stats.get_top(4)
            }
            resp.set_header("Cache-Control", "max-age=3600")
            resp.set_header("Content-Type", "text/html; charset=utf8")
            resp.body = self.env.get_template("index.html").render(**context)
