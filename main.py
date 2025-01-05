# import requests
# GOOGLE_API_KEY = 'AIzaSyCigD00c3X-UdEirr7ZYZzfZkKGx4woJbI'
# URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json" \
# "?location=-33.8670522%2C151.1957362" \
# "&radius=1500" \
# f"&key={GOOGLE_API_KEY}"
# print(URL)
# response = requests.get(URL)
# print(response.json())

from api.utils.utils import (
  time_from_coords,
  weather_from_coords,
  get_places_new_api,
  get_places_old_api,
  generate_indoor_activity,
  fetch_needed_places,
  select_places_of_type,
  generate_oudoor_activity)
from api.utils.const import SPORTS, ENTERTAINMENT, FOOD
from api.utils.db import db_client
from bson import ObjectId
from datetime import datetime
import openai
from functools import reduce


# print(time_from_coords(48.864716, 2.349014) < time(4, 0,0))
# print(weather_from_coords(48.86, 22.34))

# KEY = ''
# openai.api_key = KEY
# completion = openai.chat.completions.create(
#   model='gpt-4o-mini',
#   messages=[
#     {'role': 'user', 'content': 'hi'}
#   ]
# )
# print(completion.choices[0].message.content)

# get_places_new_api([], 48.8575, 2.3514)

# print(get_places_old_api([], 48.8575, 2.3514))
# print(generate_indoor_activity(datetime.now().time(), 'CLEAR'))

# -----------------------------------------------
# latitude, longitude = 34.0000552, -6.8636309
# response = db_client.interactions.insert_one({
#   'latitude': latitude,
#   'longitude': longitude,
#   'places': [],
#   'next_page_token': None
# })
# places, next_page_token = fetch_needed_places(34.0000552, -6.8636309)
# db_client.update_interaction_places(response.inserted_id, places, next_page_token)
# interaction = db_client.interactions.find_one(response.inserted_id)
# print(interaction)

interaction = db_client.interactions.find_one(ObjectId('677a6bc6130a29db38ee92ed'))

print(select_places_of_type('zoo', interaction))
preferences = reduce(lambda accumulated, type: {**accumulated, f'{type}': 0}, [*SPORTS, *ENTERTAINMENT, *FOOD], {})
print(generate_oudoor_activity(0, 'clear', preferences, interaction))
# -----------------------------------------------
