PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli" EMG_CONFIG=docker/config.yaml gunicorn emgcli.wsgi:application --reload
