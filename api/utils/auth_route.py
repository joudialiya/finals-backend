from flask import Flask, json, jsonify, request
from bson import ObjectId
from datetime import datetime
from api.views import main_views
from api.utils.db import db_client
from api.utils.redis import redis_client
from api.utils.utils import construct_error
from functools import wraps

def auth_route(route_handler):
    @wraps(route_handler)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get('Authorization')
        if not authorization:
            return construct_error('Authorisation not provided')

        token = authorization.split(' ')[1]
        if not authorization:
            return construct_error('Authorisation format not right')
        
        # retrieve the user id based on the token/session id from redis
        user_id: bytes = redis_client.get_user_id_session(token)
        if not user_id:
            return construct_error('Authorisation token not right')
        
        # decode
        user_id = user_id.decode('utf-8')

        # retrieve the user from db
        user = db_client.read_user({'_id': ObjectId(user_id)})
        if not user:
            return construct_error('Authorisation token not right')
        setattr(request, 'user', user)
        return route_handler(*args, **kwargs)
    return wrapper
