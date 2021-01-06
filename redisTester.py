import redis
from decouple import config


r = redis.from_url(config("REDIS_URL"))
value = r.lrange("blacklisted", 0, 10)
r.lremove('blacklisted', "e")
print(value)
