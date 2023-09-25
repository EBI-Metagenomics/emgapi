FROM centos:centos7

RUN yum -y update && \
    yum clean all && \
    yum -y install epel-release gcc bzip2 git wget && \
    yum clean all

RUN yum -y install python3 python3-devel python3-setuptools mysql-devel && \
    pip3 install -U pip setuptools

RUN mkdir /opt/emgapi && mkdir -p /opt/staticfiles && mkdir -p /opt/results 

COPY pyproject.toml /opt/emgapi/
COPY emgcli/__init__.py /opt/emgapi/emgcli/
# needed for VERSION

RUN pip3 install /opt/emgapi[dev,admin,tests]

ENV PYTHONPATH="${PYTHONPATH}:/opt/emgapi/emgcli"

CMD ["tail", "-f", "/dev/null"]
