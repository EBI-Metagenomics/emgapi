#!/bin/bash

set -eux

rm -f $HOME/src/emg/django.pid

echo "Installing EMG dependencies..."

python3.5 -m virtualenv $HOME/venv
set +o nounset
source $HOME/venv/bin/activate
set -o nounset

python -V

pip install -U pip setuptools
pip install "git+git://github.com/django-json-api/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
pip install -U -r $HOME/src/requirements.txt

echo "DB startup..."
until mysql -u root -h mysql -e 'show databases;'; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 5
done

>&2 echo "MySQL now accepts connections, creating database..."

echo "EMG Run tests..."
export PYTHONPATH=$HOME/src/emg
export MYSQL_HOST='mysql'
# pytest $HOME/src
(cd $HOME/src && $HOME/venv/bin/python3.5 setup.py test)
