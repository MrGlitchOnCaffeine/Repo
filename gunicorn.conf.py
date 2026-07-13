# Gunicorn configuration for LEPS on Render free tier.
#
# Why these settings:
#
# workers=1
#   Render free tier has 512MB RAM. The ML model (RandomForest/XGBoost) is
#   loaded into memory per worker. Multiple workers each load their own copy,
#   exhausting RAM and causing SIGKILL. One worker avoids this.
#
# preload_app=True
#   Loads the app (including the ML model) once in the master process before
#   forking. Workers inherit the memory via copy-on-write, reducing peak RAM.
#
# timeout=120
#   Default is 30s. The first request after a cold start loads the ML model
#   from disk, which can take 10-20s on Render free tier. 120s prevents
#   premature worker kills during model loading.
#
# worker_class='sync'
#   Default sync workers are appropriate for this workload. Gevent/eventlet
#   are not needed and add complexity.

workers = 1
preload_app = True
timeout = 120
worker_class = 'sync'
bind = '0.0.0.0:10000'
accesslog = '-'
errorlog = '-'
loglevel = 'info'
