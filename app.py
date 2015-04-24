import falcon
from resources import render, index, hammertime

app = falcon.API()

app.add_route("/render", render.Resource())
app.add_route("/hammertime.png", hammertime.Resource())
app.add_route("/", index.Resource())
