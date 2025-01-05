from flask import request, Response, make_response, jsonify, json
from api.views import main_views
from api.utils.db import db_client
from api.utils.redis import redis_client
from api.utils.utils import (
  construct_error,
  time_from_coords,
  weather_from_coords,
  calculate_go_outside_fator,
  generate_oudoor_activity,
  generate_indoor_activity,
  fetch_needed_places
)
from api.utils.auth_route import auth_route
from api.utils.const import ENTERTAINMENT, SPORTS
from bson import ObjectId
import random


@main_views.route('/interaction', methods=['POST'])
@auth_route
def post_interaction():
  # create new interaction
  body: dict = request.json
  if not body:
    body = {}
  if not body.get('latitude') or not body.get('longitude'):
    return construct_error('Bad request')
  result = db_client.interactions.insert_one({
    'user_id': request.user.get('_id'),
    'latitude': body.get('latitude'),
    'longitude': body.get('longitude'),
    'next_page_token': None,
    'places': [],
    })
  # init update
  places, next_page_token = fetch_needed_places(body.get('latitude'), body.get('longitude'))
  print(places, next_page_token)
  db_client.update_interaction_places(result.inserted_id, places, next_page_token)
  # -------------------------------------------
  return {
    'id': result.inserted_id,
    'latitude': body.get('latitude'),
    'longitude': body.get('longitude'),
  }


@main_views.route('/interaction', methods=['GET'], defaults={'id': None})
@main_views.route('/interaction/<id>', methods=['GET'])
@auth_route
def get_interaction(id):
  # list user interactions
  if not id:
    interactions = []
    cursor = db_client.interactions.find({'user_id': request.user.get('_id')})
    for interaction in cursor:
      interactions.append(interaction)
    return {'interactions': interactions}

@main_views.route('/interaction/<id>/activity', methods=['GET'])
@auth_route
def next_activity(id):
  """Get next activity"""
  user = request.user
  interaction = db_client.interactions.find_one({'_id': ObjectId(id)})
  if not interaction:
    return construct_error('Bad Interaction ID') 
  time = time_from_coords(interaction.get('latitude'), interaction.get('longitude'))
  weather = weather_from_coords(interaction.get('latitude'), interaction.get('longitude'))
  print(time, weather)
  outSideFactor = calculate_go_outside_fator(time, weather)
  if 1 >= outSideFactor:
    return generate_oudoor_activity(time, weather, user.get('preferences'), interaction)
  return generate_indoor_activity(time, weather)
