cd /d %~dp0/../..
pybabel extract -o translations/messages.pot .
pybabel init -i translations/messages.pot -d translations -l en