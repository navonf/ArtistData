from flask import Flask
from flask_restful import Api, Resource, reqparse

import scraper

app = Flask(__name__)
api = Api(app)


class ArtistData(Resource):

    def get(self, name):
        return scraper.base_call(name), 200

api.add_resource(ArtistData, "/artistdata/<string:name>")
# app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
