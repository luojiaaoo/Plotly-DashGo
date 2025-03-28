cd /d %~dp0/../src
waitress-serve --host=0.0.0.0 --port=8090 --url-scheme=http --trusted-proxy=* --trusted-proxy-headers=x-forwarded-for --threads=8 app:app.server