FROM python:3.8-bullseye

RUN mkdir /opt/emgapi && mkdir -p /opt/staticfiles && mkdir -p /opt/results

COPY requirements* /opt/emgapi/

RUN pip3 install git+https://github.com/EBI-Metagenomics/ena-api-handler.git
RUN pip3 install -r /opt/emgapi/requirements.txt
RUN pip3 install -r /opt/emgapi/requirements-test.txt

ENV PYTHONPATH="${PYTHONPATH}:/opt/emgapi/emgcli"

CMD ["tail", "-f", "/dev/null"]
