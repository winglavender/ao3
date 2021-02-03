web: gunicorn server:app
worker: rq worker -u $REDISTOGO_URL worker-tasks 
