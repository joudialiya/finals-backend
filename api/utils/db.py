from pymongo import MongoClient
from api.utils.const import SPORTS, ENTERTAINMENT, FOOD, SHOPPING


class DatabaseClient:
  def __init__(self):
    self.client = MongoClient()
    self.db = self.client['finals']
    self.users = self.db.get_collection('users')
    self.interactions = self.db.get_collection('interactions')


  def read_user(self, options) -> dict:
    """Read clint based on options"""
    return self.users.find_one(options)


  def create_user(self, username, password):
    """Create user"""
    user = {}
    user['username'] = username
    user['password'] = password

    # add categories
    user['preferences'] = {'inside': 0, 'outside': 0}
    # for cat in [*SPORTS, *ENTERTAINMENT, *FOOD, *SHOPPING]:
    #   user['preferences'][cat] = 0

    return self.users.insert_one(user)
  
  def update_interaction_places(self, interaction_id, places, token=None):
    self.interactions.update_one(
    {'_id': interaction_id},
    {
      '$push': {'places': {'$each': places}},
      '$set': {'next_page_token': token}
    })
db_client = DatabaseClient()
