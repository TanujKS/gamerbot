import redis
import json
from decouple import config


r = redis.from_url(config("REDIS_URL"))

print(r.get('blacklisted'))
