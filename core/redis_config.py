import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
    print("Подключено к Redis!")
except redis.ConnectionError:
    print("Не удалось подключиться к Redis. Проверьте настройки docker-compose.")

def get_redis():
    return redis_client