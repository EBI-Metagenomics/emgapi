#!/bin/bash

set -eux

entryPoint=${1:-}
srcDir=${SRCDIR:-"${HOME}/src"}
condaDir=${CONDADIR:-"${HOME}/miniconda"}
pythonVer=${PYTHON_VERSION:-"3.6"}

check_conda() {
  if [[ -f "/etc/profile.d/conda.sh" ]]; then
    command -v conda >/dev/null && echo "conda detected in $PATH"
  fi;
  conda info
  conda search "^python$"
}

create_venv() {
  wget --quiet https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
  /bin/bash miniconda.sh -b -p $condaDir
  export PATH=$condaDir/bin:$PATH
  rm -rf miniconda.sh
  hash -r
  # conda update -q conda
  conda info -a

  # TODO: wait until 4.4 https://github.com/conda/conda/issues/3200
  #conda create -q -n test-environment python=$pythonVer
  #source activate test-environment

}

is_db_running() {
  local conn=${1:-};

  echo "DB startup..."
  until mysql $conn -e 'show databases;'; do
    >&2 echo "MySQL is unavailable - sleeping"
    sleep 5
  done
  >&2 echo "MySQL now accepts connections, creating database..."
}

install_src() {
  echo "Installing EMG API..."
  pip install -U $srcDir
}

start() {
  echo "EMG API Start up..."

  # emgcli check --deploy
  emgcli migrate --fake-initial
  emgcli collectstatic --noinput

  # development server
  # emgcli runserver 0.0.0.0:8000
  emgdeploy -p ~/emgvar/django.pid --bind 0.0.0.0:8000 --workers 5 --reload emgcli.wsgi:application

}


# helpers
install() {
  create_venv
  python -V
  pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
}

install_docker() {
  install
  pip install -U "django-redis>=4.4"
  is_db_running "-u root -h mysql -P 3306"
}

docker() {
  install_docker
  install_src
  start
}

travis() {
  export PATH=$condaDir/bin:$PATH
  # Install source, otherwise OSError: [Errno 2] No such file or directory:
  #     '/home/travis/build/ola-t/ebi-metagenomics-api/staticfiles/'
  install_src
  cd $srcDir
  python -V
  python setup.py test
}


rm -f $srcDir/var/django.pid

if [ ! -z ${entryPoint} ] ; then
  eval $entryPoint
fi 
