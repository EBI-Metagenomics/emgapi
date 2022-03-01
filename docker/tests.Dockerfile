FROM centos:centos7

RUN yum -y update && \
    yum clean all && \
    yum -y install epel-release gcc bzip2 git wget && \
    yum clean all

RUN yum -y install python3 python3-devel python3-setuptools mysql-devel && \
    pip3 install -U pip setuptools

RUN mkdir /opt/emgapi && mkdir -p /opt/staticfiles && mkdir -p /opt/results

COPY requirements* /opt/emgapi/

RUN pip3 install git+git://github.com/EBI-Metagenomics/emg-backlog-schema.git
RUN pip3 install git+git://github.com/EBI-Metagenomics/ena-api-handler.git
RUN pip3 install -r /opt/emgapi/requirements.txt
RUN pip3 install -r /opt/emgapi/requirements-dev.txt
RUN pip3 install -r /opt/emgapi/requirements-test.txt
RUN pip3 install -r /opt/emgapi/requirements-admin.txt

ENV PYTHONPATH="${PYTHONPATH}:/opt/emgapi/emgcli"

CMD ["tail", "-f", "/dev/null"]
