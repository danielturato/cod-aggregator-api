import redis
from rq import Worker, Queue, Connection
from .depenencies import get_settings

listen = ['high', 'default', 'low']
settings = get_settings()

conn = redis.from_url(settings.redistogo_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
