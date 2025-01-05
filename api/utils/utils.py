import requests
import datetime
import math
import openai
import random
import json
import os
from api.utils.const import ENTERTAINMENT, SPORTS, SUPPORTED_TYPES
from api.utils.db import db_client
from functools import reduce


KEY = os.environ['OPENAI_KEY']
GOOGLE_API_KEY = 'AIzaSyCigD00c3X-UdEirr7ZYZzfZkKGx4woJbI'

openai.api_key = KEY

class AppException(Exception):
  pass


def construct_error(msg: str, code: int=400):
  print(msg)
  return {'error': msg}, code

def document_to_dict(doc: dict):
  new_dic = {}
  for key, value in doc.items():
    if key == '_id':
      new_dic['id'] = value
    else:
      new_dic[key] = value


def time_from_coords(latitude: int, longitude: int):
  BASE_URL = 'https://timeapi.io/api/Time/current/coordinate/'
  response = requests.get(
     BASE_URL,
     params={'latitude': latitude, 'longitude': longitude},
     headers={'Content-type': 'application/json'})
  if response.status_code >= 300:
    return None # failed
  else:
    body = response.json()
    # print(body)
    return datetime.time(
      int(body['hour']),
      int(body['minute']),
      int(body['seconds']))


def weather_from_coords(latitude: int, longitude: int):
  # https://api.open-meteo.com/v1/forecast?latitude=52.523333&longitude=13.41&current=weather_code
  BASE_URL = 'https://api.open-meteo.com/v1/forecast'
  response = requests.get(
     BASE_URL,
     params={'latitude': latitude, 'longitude': longitude, 'current': 'weather_code'},
     headers={'Content-type': 'application/json'})
  body = response.json()
  # print(body)
  weather_code = body['current']['weather_code']
  if (weather_code == 0):
    return 'CLEAR'
  if (weather_code == 1):
      return 'MAINLY_CLEAR'
  if (weather_code == 2):
      return 'PARTLY_CLEAR'
  if (weather_code == 3):
      return 'OVERCAST'
  if ( weather_code >= 45 and  weather_code <= 48):
      return 'FOG'
  if ( weather_code >= 51 and weather_code <= 53):
      return 'LIGHT_DRIZZLE'
  if ( weather_code >= 55 and weather_code <= 57):
      return 'DENSE_DRIZZLE'
  if ( weather_code >= 61 and weather_code <= 67):
      return 'RAINY'
  if (weather_code >= 71 and weather_code <= 82):
      return 'SNOWY'
  return 'UNKNOWN'


def calculate_go_outside_fator(time, weather):
  goOutsideFactor = 0.2; # Initialize factor

  # time based adjustments
  if time >= datetime.time(8) and time <= datetime.time(20): # daytime
      goOutsideFactor += .2
  elif time >= datetime.time(4) and time <= datetime.time(7): # morning
      goOutsideFactor += .1
  elif time >= datetime.time(21) and time <= datetime.time(23): # evening
      goOutsideFactor += .3
  else: # nighttime (0-3)
      goOutsideFactor -= .1

  # weather based adjustments
  if weather == 'CLEAR' or weather == 'MAINLY_CLEAR' or weather == 'PARTLY_CLEAR':
      goOutsideFactor += .15
  elif weather == 'OVERCAST':
      goOutsideFactor += .05
  elif weather == 'FOG' or weather == 'LIGHT_DRIZZLE':
      goOutsideFactor -= .05
  elif weather == 'DENSE_DRIZZLE' or weather == 'RAINY' or weather == 'SNOWY':
      goOutsideFactor -= .15

  # ensure factor stays within a reasonable range [0, 1]
  goOutsideFactor = max(goOutsideFactor, 0)
  goOutsideFactor = min(goOutsideFactor, 1)

  return goOutsideFactor

def get_places_old_api(types: list, latitude, longitude, token: str=''):
  # https://maps.googleapis.com/maps/api/place/nearbysearch/json
  # ?keyword=cruise
  # &location=-33.8670522%2C151.1957362
  # &radius=1500
  # &type=restaurant
  # &key=YOUR_API_KEY

  BASE_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
  response = requests.get(
    BASE_URL,
    params={
      'location': f'{latitude} {longitude}',
      'radius': 1500,
      'type': 'restaurant',
      'type': ','.join(types),
      'key': GOOGLE_API_KEY,
      'pagetoken': token if token is not None else ''
    }
  )
  body: dict = response.json()

  return (
    list(map(lambda place: {
        'id': place.get('place_id'),
        'name': place.get('name'),
        'types': place.get('types')
      }, body.get('results'))),
    body.get('next_page_token', None)
    )

def get_places_new_api(types: list, latitude, longitude):
  BASE_URL = 'https://places.googleapis.com/v1/places:searchNearby' 
  data = {
    "includedTypes": types,
    "maxResultCount": 2,
    "locationRestriction": {
      "circle": {
        "center": {
          "latitude": latitude,
          "longitude": longitude
        },
        "radius": 1500.0
      }
    }
  }
  response = requests.post(
    BASE_URL,
    json=data,
    headers={
      'Content-Type': 'application/json',
      'X-Goog-FieldMask': 'places.displayName,places.types,places.name',
      'X-Goog-Api-Key': GOOGLE_API_KEY
    })
  # body = response.json()
  print(response.text)

def fetch_needed_places(latitude, longitude, next_page_token=None):
  return get_places_old_api(
    [*SPORTS, *ENTERTAINMENT],
    latitude,
    longitude,
    next_page_token
  )

def select_places_of_type(type: str, interaction):
  """The algorithm goes as follow we check for a place of giving type in the places pull,
  we repeat that up to 3 times while updating the places cache, we stop the search if we find aplace,
  or if the token of the next page is empty meaning no more places to fetch"""
  
  latitude = interaction.get('latitude')
  longitude = interaction.get('longitude')
  search_places = interaction.get('places')
  next_page_token = interaction.get('next_page_token')

  while True:
    print(search_places.__len__())
    selected_places = list(filter(
      lambda place: type in place.get('types'),
      search_places
    ))
    
    if selected_places or not next_page_token:
      break
    
    search_places, next_page_token = fetch_needed_places(latitude, longitude, next_page_token)
    db_client.update_interaction_places(interaction.get('_id'), search_places, next_page_token)

  return selected_places
  
def generate_outdor_activity_object(place):
  QUERY = (
    f"Place name: {place.get('name')}\n"
    f"Place types: {place.get('types')}\n"
    "Give me directly one fun little outdoor activity based on the given place information.\n"
    "While giving me the suggestion please take into account the name semantic meaning as well as place types.\n"
    "Compile the information and provide me with a simple brief description of 70 word max of the activity without mentioning "
    "that you have analysed the name semantically or referred to the google map categories.\n"
  )
  completion = openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': QUERY}]
  )
  description = completion.choices[0].message.content
  return {'description': description, 'types': ['outdoor', *place.get('types')],'place': place}
  
   
def generate_random_outdoor_activity(time: datetime.time, weather: str, preferences, interaction):
  # rand typereferences: dict,
  local_types = [*SUPPORTED_TYPES]
  while local_types:
    type = local_types[random.randint(0, local_types.__len__() - 1)]
    print(type)
    local_types.remove(type)
    selected_places = select_places_of_type(type, interaction)
    if selected_places:
      place = selected_places[random.randint(0, selected_places.__len__() - 1)]
      return generate_outdor_activity_object(place)
  return {}

def generate_based_outdoor_activity(time: datetime.time, weather: str, preferences: dict, interaction):
  pass

def generate_oudoor_activity(time: datetime.time, weather: str, preferences: dict, interaction):
  explodation_factor = 1
  return generate_random_outdoor_activity(time, weather, preferences, interaction)

  if random.uniform(0, 1) <= explodation_factor:
     return generate_random_outdoor_activity(time, weather, preferences, interaction)
  return generate_based_outdoor_activity(time, weather, preferences, interaction)

def generate_indoor_activity(time: datetime.time, weather: str):
  QUERY = ('Give me directly an in indoor fun activity that i can do\n' 
  f'i will let u know that the whether outside is kinda {weather.lower()}'
  f' and the current time is {time}\n'
  'Compile the information and provide me with a simple brief description of 70 words max '
  'of the activity without mentioning '
  'that you have analysed the weather or the time directly.\n')

  completion = openai.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': QUERY}]
    )
  description = completion.choices[0].message.content
  return {'description': description, 'types': ['indoor'],'place': None}
  