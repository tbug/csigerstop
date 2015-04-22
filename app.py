import falcon
import render
import index

app = falcon.API()

app.add_route("/render", render.Resource())
app.add_route("/", index.Resource())
