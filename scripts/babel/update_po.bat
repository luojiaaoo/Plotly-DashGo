cd /d %~dp0/../..
pybabel extract -o translations/messages.pot .
pybabel update -i translations/messages.pot -d translations
pybabel compile -d translations