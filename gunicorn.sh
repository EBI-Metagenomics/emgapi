PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli" EMG_CONFIG=docker/config-test.yaml gunicorn emgcli.wsgi:application --reload
