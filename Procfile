web: gunicorn server:app
worker: rq worker -u $REDIS_URL worker-tasks 
