#!/bin/bash

set -eux

srcDir=${SRCDIR:-"${HOME}/src"}
venvDir=${VENVDIR:-"${HOME}/venv"}

rm -f $srcDir/var/django.pid

python3 -V

virtualenv -p /usr/bin/python3 $venvDir --system-site-packages
# $HOME/venv/bin/pip install -U "django-redis>=4.4"

echo "Installing EMG API..."
  $venvDir/bin/pip install -U  "git+git://github.com/olatarkowska/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
$venvDir/bin/pip install -U $srcDir

echo "DB startup..."
until mysql -u root -h mysql -P 3306 -e 'show databases;'; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 5
done
>&2 echo "MySQL now accepts connections, creating database..."

echo "EMG API Start up..."

# $HOME/venv/bin/emgcli check --deploy
# $venvDir/bin/emgcli migrate --fake-initial
$venvDir/bin/emgcli collectstatic --noinput

# development server
# $HOME/venv/bin/emgcli runserver 0.0.0.0:8000
$venvDir/bin/emgdeploy -p $HOME/emg/emg.pid --bind 0.0.0.0:8000 --workers 5 --reload emgcli.wsgi:application
