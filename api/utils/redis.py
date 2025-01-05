from redis import Redis
from uuid import uuid4

class RedisClient:
  """Redis Service"""
  def __init__(self):
    self.client = Redis()
  
  def create_session(self, user):
    session_id = str(uuid4())
    ex = 24 * 60 * 60
    self.client.set(session_id, user, ex=ex)
    return session_id

  def get_user_id_session(self, session_id):
    return self.client.get(session_id)

redis_client = RedisClient()
