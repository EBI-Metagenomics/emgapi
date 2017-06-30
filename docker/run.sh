#!/bin/bash

set -eux

rm -f $HOME/src/emg/django.pid

echo "Installing EMG dependencies..."

python3.5 -m virtualenv $HOME/venv
set +o nounset
source $HOME/venv/bin/activate
set -o nounset

python -V

pip install -U pip
pip install -U -r $HOME/src/requirements.txt

echo "DB initialisation..."
until mysql -u root -h mysql -e 'show databases;'; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 5
done

>&2 echo "MySQL now accepts connections, creating database..."

echo "Start up..."
$HOME/venv/bin/python3.5 $HOME/src/emg/manage.py migrate emg_api 0001 --fake
$HOME/venv/bin/python3.5 $HOME/src/emg/manage.py migrate emg_api 0002
$HOME/venv/bin/python3.5 $HOME/src/emg/manage.py collectstatic --noinput
#$HOME/venv/bin/python3.5 $HOME/src/emg/manage.py runserver 0.0.0.0:8000

(cd $HOME/src/emg && $HOME/venv/bin/python3.5 \
  $HOME/venv/bin/gunicorn \
  -p $HOME/src/emg/django.pid \
  --bind 0.0.0.0:8000 \
  --workers 5 \
  --timeout 30 \
  --max-requests 0 \
  --reload \
  emg.wsgi:application)
