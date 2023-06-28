FROM python:3.8-bullseye

RUN mkdir /opt/emgapi && mkdir -p /opt/staticfiles && mkdir -p /opt/results

COPY pyproject.toml /opt/emgapi/

RUN pip3 install /opt/emgapi[dev,admin,tests]

ENV PYTHONPATH="${PYTHONPATH}:/opt/emgapi/emgcli"

CMD ["tail", "-f", "/dev/null"]
