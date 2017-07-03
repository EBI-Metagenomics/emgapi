# "ported" by Adam Miller <maxamillion@fedoraproject.org> from
#   https://github.com/fedora-cloud/Fedora-Dockerfiles
#
# Originally written for Fedora-Dockerfiles by
#   scollier <scollier@redhat.com>

FROM centos:centos7
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all

RUN yum -y install yum-utils groupinstall development
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum -y install python35u

RUN yum -y install epel-release gcc
RUN yum -y install python35u-pip python35u-devel git; yum clean all

RUN pip3.5 install virtualenv

# Install MySQL tools
RUN yum -y install mysql mysql-devel

RUN useradd centos
RUN chpasswd centos

ADD run.sh /tmp/docker/run.sh
RUN chmod a+x /tmp/docker/run.sh
RUN chown centos:centos /tmp/docker/run.sh

USER centos
ENV HOME /home/centos

ENTRYPOINT ["/tmp/docker/run.sh"]
