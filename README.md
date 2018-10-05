# Open Humans Oura connection

This project allows users to connect their Oura account to Open Humans and collect a record of their Oura data.ard.

To run the project from source:

- Install python dependencies using [pipenv](https://github.com/pypa/pipenv#installation)
```
pipenv install
```
- Populate the environment variables listed in `env.sample` in `.env`
- Apply migrations
```
python manage.py migrate
```
- Run server
```
python manage.py runserver
```
