import json
from flask import Flask, jsonify, request
from bson import ObjectId
from datetime import datetime
from api.views import main_views
from api.utils.db import db_client
from api.utils.redis import redis_client
from api.utils.utils import construct_error
from api.utils.auth_route import auth_route
from functools import wraps


class JSONEncoder(json.JSONEncoder):
    '''extend json-encoder class'''
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)
app.register_blueprint(main_views)
# use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.
app.json_encoder = JSONEncoder
# Disable strict slashes globally
app.url_map.strict_slashes = False


# handling CORS
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

# for testing
@app.route('/', methods=['GET', 'POST'])
@auth_route
def index():
    return 'Aaa\n'

# @app.errorhandler(Exception)
# def handle_exception(e: Exception):
#     # pass through HTTP errors
#     if isinstance(e, HTTPException):
#         return e
#     return {'error': str(e)}

if __name__ == '__main__':
    app.run()
