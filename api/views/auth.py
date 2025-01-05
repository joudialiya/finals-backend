import json
from flask import request, Response, make_response, jsonify
from api.views import main_views
from api.utils.db import db_client
from api.utils.redis import redis_client
from api.utils.utils import construct_error


@main_views.route('/login', methods=['POST'])
def login():
  """Login"""
  credentials: dict= request.json
  print(credentials)
  if not credentials:
    return construct_error('Not credentials provided')
  if not credentials.get('username'):
    return construct_error('Messing user')
  if not credentials.get('password'):
    return construct_error('Messing password')
  user = db_client.read_user({'username': credentials.get('username')})
  if not user:
    return construct_error('User not found')
  print(user)
  session_id = redis_client.create_session(str(user.get('_id')))
  return jsonify({'token': session_id})


@main_views.route('/signup', methods=['POST'])
def signup():
  """sign"""
  credentials: dict= json.loads(request.data)
  if not credentials:
    return construct_error('Not credentials provided')
  if not credentials.get('username'):
    return construct_error('Messing user')
  if not credentials.get('password'):
    return construct_error('Messing password')
  user = db_client.read_user({'username': credentials.get('username')})
  if user:
    return construct_error('Username already exists')
  response = db_client.create_user(
    credentials.get('username'),
    credentials.get('password'))
  return jsonify({'_id': response.inserted_id})
