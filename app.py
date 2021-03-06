import falcon
from resources import render, index, hammertime, hot
from stats import StatsObject

app = falcon.API()

stats = StatsObject()

app.add_route("/", index.Resource(stats))
app.add_route("/hot", hot.Resource(stats))
app.add_route("/render", render.Resource())
app.add_route("/hammertime.png", hammertime.Resource())
