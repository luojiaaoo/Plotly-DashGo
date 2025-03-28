cd `dirname $0`/..
gunicorn --capture-output -w 4 -b 0.0.0.0:8090 app:app.server