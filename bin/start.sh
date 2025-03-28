cd `dirname $0`/../src
gunicorn --capture-output -w 4 -b 0.0.0.0:8090 app:server