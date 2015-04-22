import falcon
import render


app = falcon.API()

app.add_route("/render", render.Resource())
