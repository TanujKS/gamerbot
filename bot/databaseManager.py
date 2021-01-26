import redis
import json
from decouple import config

r = redis.from_url(config("REDIS_URL"))

r.set("shutdown", 'False')
value = r.get("shutdown")
