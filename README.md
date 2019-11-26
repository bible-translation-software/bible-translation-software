# Bible Translation Software

Web app to aid teams translating the Bible (built on Django)

# Installation

On Ubuntu, you will need to install these dependencies:

    sudo apt-get install python3 python-dev python3-pip libpq-dev postgresql postgresql-contrib

Create the file `.env` and modify it appropriately, especially `SECRET_KEY`.

Modify the file `biblets/settings.py` and modify it appropriately, especially `ALLOWED_HOSTS`.

Run these commands:

    pip3 install --user pipenv
    export PATH="$PATH:$HOME/.local/bin"
    pipenv install
    pipenv run python manage.py migrate
    pipenv run python manage.py loaddata books kjv

You will need to create a database in PostgreSQL:

    sudo su - postgres
    $ psql
    $$ CREATE DATABASE "biblets";
    $$ CREATE USER "biblets" WITH PASSWORD 'biblets';
    $$ GRANT ALL PRIVILEGES ON DATABASE "biblets" to "biblets";
    $$ ALTER USER "biblets" LOGIN CREATEDB;
    $$ \q
    $ exit

# Running

Run:

    pipenv run python manage.py runserver
