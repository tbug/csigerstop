import falcon
from resources import render, index

app = falcon.API()

app.add_route("/render", render.Resource())
app.add_route("/", index.Resource())
