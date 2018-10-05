# Open Humans Spotify connection

This project allows users to connect their Spotify account to Open Humans and collect a record of what they've listened to. The project collects the last 50 tracks immediately and stores this list in a member's Open Humans account, then continues to update and build this list going forward.

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
